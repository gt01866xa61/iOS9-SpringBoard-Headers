"""Phase 2 end-to-end check: Binance prices + balance + Telegram.

Usage:
    python test_phase2.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from logger import get_logger  # noqa: E402  (must load env first)
from notifier import get_notifier  # noqa: E402
from exchange_api import BinanceExchange  # noqa: E402


def main() -> int:
    log = get_logger()
    log.info("Phase 2 test starting")

    exchange = BinanceExchange()

    btc = exchange.get_price("BTC/USDT")
    eth = exchange.get_price("ETH/USDT")
    if btc is None or eth is None:
        log.error("Failed to fetch one or both prices; check bot.log")
        return 1

    usdt_bal: float | None = None
    btc_bal: float | None = None
    eth_bal: float | None = None
    try:
        usdt_bal = exchange.get_balance("USDT")
        btc_bal = exchange.get_balance("BTC")
        eth_bal = exchange.get_balance("ETH")
    except RuntimeError as exc:
        log.warning("API key 未設定，略過餘額查詢：%s", exc)

    msg = (
        f"Phase 2 行情 + 持倉快照\n"
        f"BTC/USDT: ${btc:,.2f}\n"
        f"ETH/USDT: ${eth:,.2f}"
    )
    if usdt_bal is not None:
        msg += (
            f"\n\nUSDT 餘額: {usdt_bal:.4f}\n"
            f"BTC 持倉: {btc_bal:.8f}\n"
            f"ETH 持倉: {eth_bal:.6f}"
        )

    if not get_notifier().send(msg):
        log.error("Telegram send returned False; check bot.log for details")
        return 1

    log.info("Phase 2 驗證通過")
    print("Phase 2 驗證通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
