"""每 N 小時推一次存活訊號 + 今日進度。

防靜默死亡（程式 crash 但 OS 沒重啟，Telegram 6h 沒訊號 = 出事）。
"""
from __future__ import annotations

import json
from datetime import datetime

import config
from circuit_breaker import CircuitBreaker
from logger import get_logger
from notifier import get_notifier
from trader import BinanceTrader, STATE_FILE, TAIPEI_TZ


def send_heartbeat(trader: BinanceTrader, breaker: CircuitBreaker) -> None:
    log = get_logger()
    notifier = get_notifier()

    # Read today's DCA progress (narrow except — fail-loud on unexpected).
    # Cross-day guard: if state.date != today, treat today as 0 — avoids
    # showing yesterday's number in the morning before today's DCA fires.
    # trader._check_daily_cap will reset the file at the next buy.
    today_spent = 0.0
    today = datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d")
    try:
        daily = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if daily.get("date") == today:
            today_spent = float(daily.get("spent_usdt", 0.0))
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        log.warning("daily_state read failed in heartbeat: %s", exc)

    # Read balances (None on failure so heartbeat still sends a partial msg).
    # Old code used -1.0 as sentinel and (-1.0)*(-1.0) silently inflated total
    # by 2 USDT for each failed leg; switch to None + explicit guard below.
    usdt: float | None = None
    btc: float | None = None
    eth: float | None = None
    btc_p: float | None = None
    eth_p: float | None = None
    try:
        usdt = trader.get_balance("USDT") or 0.0
        btc = trader.get_balance("BTC") or 0.0
        eth = trader.get_balance("ETH") or 0.0
        btc_p = trader.get_price("BTC/USDT") or 0.0
        eth_p = trader.get_price("ETH/USDT") or 0.0
    except Exception as exc:  # noqa: BLE001
        log.warning("heartbeat balance/price read failed: %s", exc)

    if None in (usdt, btc, eth, btc_p, eth_p):
        total_str = "unknown — fetch failed"
    else:
        total_str = f"${usdt + btc * btc_p + eth * eth_p:.2f}"

    usdt_str = "?" if usdt is None else f"{usdt:.2f}"
    btc_str = "?" if btc is None else f"{btc:.8f}"
    eth_str = "?" if eth is None else f"{eth:.6f}"

    msg = (
        f"💓 Bot 存活\n"
        f"今日已花: {today_spent:.2f} / {config.DAILY_CAP_USDT} USDT\n"
        f"USDT: {usdt_str}\n"
        f"BTC: {btc_str}\n"
        f"ETH: {eth_str}\n"
        f"總估值: {total_str}\n"
        f"連敗計數: {breaker.failures}/{config.MAX_CONSECUTIVE_FAILURES}"
    )
    notifier.send(msg)
    log.info("heartbeat sent (total=%s, failures=%d)", total_str, breaker.failures)
