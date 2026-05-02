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

    # Read balances (sentinels on failure so heartbeat still sends)
    usdt = btc = eth = btc_p = eth_p = -1.0
    try:
        usdt = trader.get_balance("USDT") or 0.0
        btc = trader.get_balance("BTC") or 0.0
        eth = trader.get_balance("ETH") or 0.0
        btc_p = trader.get_price("BTC/USDT") or 0.0
        eth_p = trader.get_price("ETH/USDT") or 0.0
    except Exception as exc:  # noqa: BLE001
        log.warning("heartbeat balance/price read failed: %s", exc)

    total_value = usdt + btc * btc_p + eth * eth_p if usdt >= 0 else -1.0

    msg = (
        f"💓 Bot 存活\n"
        f"今日已花: {today_spent:.2f} / {config.DAILY_CAP_USDT} USDT\n"
        f"USDT: {usdt:.2f}\n"
        f"BTC: {btc:.8f}\n"
        f"ETH: {eth:.6f}\n"
        f"總估值: ${total_value:.2f}\n"
        f"連敗計數: {breaker.failures}/{config.MAX_CONSECUTIVE_FAILURES}"
    )
    notifier.send(msg)
    log.info("heartbeat sent (total=%.2f, failures=%d)", total_value, breaker.failures)
