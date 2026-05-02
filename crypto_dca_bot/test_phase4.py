"""Phase 4 整合驗證：起 main、跑一次 dry-run cycle + 一次 heartbeat、停止。

純整合測試。不用 schedule / threading 跑等待，直接呼叫每個模組驗證能串起來。
簡化 + 跨平台。
"""
from __future__ import annotations

import signal
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

import config  # noqa: E402

config.DRY_RUN = True  # 強制 dry-run，全程不打 Binance 寫端

from circuit_breaker import CircuitBreaker  # noqa: E402
from heartbeat import send_heartbeat  # noqa: E402
from logger import get_logger  # noqa: E402
from main import _signal_handler, run_dca_cycle, shutdown_event  # noqa: E402
from trader import BinanceTrader  # noqa: E402


def main() -> int:
    log = get_logger()
    log.info("Phase 4 integration test starting (DRY-RUN forced)")
    trader = BinanceTrader()
    breaker = CircuitBreaker(max_failures=5)

    # 1. Direct dry-run DCA cycle
    run_dca_cycle()  # 預期 Telegram: 🧪 [DRY-RUN] 模擬買 ...

    # 2. Direct heartbeat
    send_heartbeat(trader, breaker)  # 預期 Telegram: 💓 Bot 存活 ...

    # 3. Verify graceful shutdown signal
    shutdown_event.clear()
    _signal_handler(signal.SIGTERM, None)
    if not shutdown_event.is_set():
        log.error("shutdown_event not set after handler")
        return 1
    shutdown_event.clear()

    log.info("Phase 4 整合驗證通過")
    print("Phase 4 整合驗證通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
