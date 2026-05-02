"""持倉總估值達設定門檻且為歷史新高 → 推播。
state 累積在 runtime_state.json（跟 daily_state.json 分開）。
"""
from __future__ import annotations

import json

import config
from logger import get_logger
from notifier import get_notifier
from trader import BinanceTrader


def check_hwm(trader: BinanceTrader) -> None:
    log = get_logger()
    notifier = get_notifier()

    try:
        btc = trader.get_balance("BTC") or 0.0
        eth = trader.get_balance("ETH") or 0.0
        btc_p = trader.get_price("BTC/USDT") or 0.0
        eth_p = trader.get_price("ETH/USDT") or 0.0
        total = btc * btc_p + eth * eth_p
    except Exception as exc:  # noqa: BLE001
        log.warning("hwm check failed: %s", exc)
        return

    state = _load_runtime_state()
    last = float(state.get("hwm_usdt", 0.0))

    if total >= config.HIGH_WATER_MARK_USDT and total > last:
        notifier.send(
            f"🚀 持倉新高\n"
            f"BTC: {btc:.8f} (${btc * btc_p:.2f})\n"
            f"ETH: {eth:.6f} (${eth * eth_p:.2f})\n"
            f"總估值: ${total:.2f}\n"
            f"前次新高: ${last:.2f}\n"
            f"💡 可考慮提領至冷錢包"
        )
        state["hwm_usdt"] = round(total, 2)
        _save_runtime_state(state)
        log.info("HWM updated: %.2f -> %.2f", last, total)


def _load_runtime_state() -> dict:
    try:
        return json.loads(config.RUNTIME_STATE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_runtime_state(state: dict) -> None:
    """原子化寫回（沿用 trader.py tmp + replace 模式）。"""
    config.RUNTIME_STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = config.RUNTIME_STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(config.RUNTIME_STATE)
