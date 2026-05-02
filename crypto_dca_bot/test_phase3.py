"""Phase 3 真實下單驗證: 花 11 USDT 買 BTC。

Pre-req:
  - API key 已升 Spot & Margin Trading 權限
  - 帳戶有 ≥ 12 USDT 的可動餘額

Usage:
    python test_phase3.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from logger import get_logger  # noqa: E402  (must load env first)
from trader import BinanceTrader  # noqa: E402


def main() -> int:
    log = get_logger()
    log.info("Phase 3 test starting")

    trader = BinanceTrader()
    try:
        order = trader.place_market_buy("BTC/USDT", quote_amount_usdt=11.0)
    except ValueError as exc:
        log.error("safety check failed: %s", exc)
        print(f"安全檢查失敗: {exc}")
        return 1

    if order is None:
        log.error("下單失敗 — 看 bot.log")
        print("下單失敗，看 bot.log")
        return 1

    cost = float(order.get("cost") or 0.0)
    filled = float(order.get("filled") or 0.0)
    avg = order.get("average")
    avg_str = f" @ {float(avg):,.2f}" if avg else ""
    log.info("Phase 3 驗證通過")
    print("Phase 3 驗證通過")
    print(f"成交：花 {cost:.4f} USDT 買到 {filled:.8f} BTC{avg_str}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
