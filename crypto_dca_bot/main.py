"""Phase 4 主迴圈：排程 + signal + heartbeat。

主機系統時區必須設為 (UTC+8) Taipei——schedule 用本機時鐘排程，
不依賴 IANA tzdata（Phase 3 已踩過 Windows 缺 tzdata 雷）。
"""
from __future__ import annotations

import argparse
import os
import signal
import sys
import threading
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

import schedule  # noqa: E402

import config  # noqa: E402
from circuit_breaker import CircuitBreaker  # noqa: E402
from heartbeat import send_heartbeat  # noqa: E402
from high_water_mark import check_hwm  # noqa: E402
from logger import get_logger  # noqa: E402
from notifier import get_notifier  # noqa: E402
from trader import (  # noqa: E402
    BinanceTrader,
    MAX_SINGLE_BUY_USDT,
    MIN_SINGLE_BUY_USDT,
    TAIPEI_TZ,
)

log = get_logger()
notifier = get_notifier()
trader = BinanceTrader()
breaker = CircuitBreaker(max_failures=config.MAX_CONSECUTIVE_FAILURES)
shutdown_event = threading.Event()

# Env-var override (chaos [15/15] uses this; production leaves DRY_RUN config-driven)
if os.environ.get("DRY_RUN") == "1":
    config.DRY_RUN = True


def _today_symbol() -> str:
    """奇偶日輪流。Asia/Taipei 第幾天 mod 2。"""
    day = datetime.now(TAIPEI_TZ).day
    return config.SYMBOLS_ROTATION[day % len(config.SYMBOLS_ROTATION)]


def run_dca_cycle() -> None:
    """單次 DCA 週期。schedule 每天 DCA_TIME 觸發一次。"""
    symbol = _today_symbol()
    log.info("DCA cycle start: %s %.2f USDT", symbol, config.DCA_AMOUNT_USDT)

    if config.DRY_RUN:
        log.info("[DRY-RUN] would buy %.2f USDT %s", config.DCA_AMOUNT_USDT, symbol)
        notifier.send(f"🧪 [DRY-RUN] 模擬買 {config.DCA_AMOUNT_USDT} USDT {symbol}")
        return

    try:
        order = trader.place_market_buy(symbol, config.DCA_AMOUNT_USDT)
        if order is None:
            breaker.record_failure("place_market_buy returned None")
            return
        breaker.record_success()
        check_hwm(trader)
    except Exception as exc:  # noqa: BLE001
        log.exception("DCA cycle failed")
        breaker.record_failure(f"unhandled exception: {exc}")


def _signal_handler(sig, frame) -> None:
    """SIGINT (Ctrl+C) / SIGTERM → graceful shutdown。

    只 set event；正在跑的 schedule.run_pending() 跑完當前 job 才回到 while
    迴圈檢查 event。下單中途絕不被打斷。
    """
    log.info("Signal %d received, graceful shutdown initiated", sig)
    shutdown_event.set()


def main() -> int:
    parser = argparse.ArgumentParser(description="Crypto DCA bot main loop")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Pre-flight: print config + live USDT/BTC/ETH free balances, exit before starting schedule (no 🟢 上線 Telegram)",
    )
    parser.add_argument(
        "--deep-check",
        action="store_true",
        help="Like --check, plus call trader._get_min_notional() for each SYMBOLS_ROTATION symbol — proves the [2] range check inside place_market_buy will pass at 23:55 without actually placing an order.",
    )
    args = parser.parse_args()

    # Fail-fast on misconfig before any Telegram / schedule side-effects.
    config.validate()

    if args.check or args.deep_check:
        print(f"DRY_RUN: {config.DRY_RUN}")
        print(f"DCA_AMOUNT_USDT: {config.DCA_AMOUNT_USDT}")
        print(f"DCA_TIME: {config.DCA_TIME}")
        print(f"DAILY_CAP_USDT: {config.DAILY_CAP_USDT}")
        print(f"SYMBOLS_ROTATION: {config.SYMBOLS_ROTATION}")
        print(f"Today's symbol: {_today_symbol()}")

        for asset in ("USDT", "BTC", "ETH"):
            try:
                bal = trader.get_balance(asset)
            except Exception as exc:  # noqa: BLE001
                print(f"Balance {asset}: FAILED — {type(exc).__name__}: {exc}")
                return 1
            if bal is None:
                print(f"Balance {asset}: FAILED — get_balance returned None")
                return 1
            print(f"Balance {asset} free: {bal:.8f}")

        if args.deep_check:
            for symbol in config.SYMBOLS_ROTATION:
                try:
                    min_notional = trader._get_min_notional(symbol)
                except Exception as exc:  # noqa: BLE001
                    print(
                        f"_get_min_notional({symbol}): FAILED — "
                        f"{type(exc).__name__}: {exc}"
                    )
                    return 1
                effective_min = max(MIN_SINGLE_BUY_USDT, min_notional)
                ok = effective_min <= config.DCA_AMOUNT_USDT <= MAX_SINGLE_BUY_USDT
                print(
                    f"{symbol}: min_notional={min_notional:.4f}, "
                    f"effective_min={effective_min:.4f}, "
                    f"DCA={config.DCA_AMOUNT_USDT} in "
                    f"[{effective_min:.4f}, {MAX_SINGLE_BUY_USDT:.2f}] → "
                    f"{'OK' if ok else 'FAIL'}"
                )
                if not ok:
                    return 1

        print("Pre-flight OK")
        return 0

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    log.info(
        "Bot starting (DRY_RUN=%s, DCA=%s @ %s local)",
        config.DRY_RUN, config.DCA_AMOUNT_USDT, config.DCA_TIME,
    )
    notifier.send(
        f"🟢 Bot 上線\n"
        f"模式: {'DRY-RUN' if config.DRY_RUN else 'LIVE'}\n"
        f"每日 DCA: {config.DCA_AMOUNT_USDT} USDT @ {config.DCA_TIME}\n"
        f"今日標的: {_today_symbol()}"
    )

    # No tz arg — relies on host clock being Asia/Taipei
    schedule.every().day.at(config.DCA_TIME).do(run_dca_cycle)
    schedule.every(config.HEARTBEAT_HOURS).hours.do(send_heartbeat, trader, breaker)

    while not shutdown_event.is_set():
        schedule.run_pending()
        # wait() responds to event immediately; replaces time.sleep(1)
        shutdown_event.wait(timeout=1.0)

    log.info("Bot shutting down")
    notifier.send("🛑 Bot 下線")
    return 0


if __name__ == "__main__":
    sys.exit(main())
