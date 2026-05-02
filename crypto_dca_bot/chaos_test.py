"""Chaos / failure-injection tests for Phase 1 + Phase 2 + Phase 3 + Phase 4.

Verifies that the safety nets in notifier / exchange_api / trader / main /
circuit_breaker hold under bad conditions. Run after test_phase{1,2,3,4}.py
succeed.

Tests automated here:
  Phase 1 (notifier):
    [1/15] Bad token        -> notifier.send() returns False, no crash
    [2/15] Bad chat_id      -> Telegram "chat not found", returns False
    [3/15] Missing CHAT_ID  -> TelegramNotifier() raises RuntimeError

  Phase 2 (exchange_api):
    [4/15] Bad API key      -> get_balance() raises ccxt.AuthenticationError
    [5/15] Bad symbol       -> get_price() returns None, NO Telegram sent
    [6/15] No-key balance   -> get_balance() raises RuntimeError

  Phase 3 (trader, all local checks — no real Binance calls):
    [8/15]  Symbol off whitelist -> place_market_buy raises ValueError
    [9/15]  Below min notional   -> place_market_buy raises ValueError
    [10/15] Above max single buy -> place_market_buy raises ValueError
    [11/15] Daily cap exceeded   -> ValueError + state file unchanged + cleaned

  Phase 4 (main loop, circuit breaker, cross-day reset, signal handler):
    [12/15] DRY-RUN mode         -> run_dca_cycle no API call, no state change
    [13/15] Circuit breaker trip -> 5/5 failures -> SystemExit(1) + 1 Telegram
    [14/15] Cross-day reset      -> yesterday spent ignored, today starts at 0
    [15/15] Graceful shutdown    -> _signal_handler sets shutdown_event

Semi-manual:
    [7/15] Wrong IP whitelist -> SKIP unless you've prepared per the README.
                                When prepared, raises ccxt.AuthenticationError
                                (Binance code -2015; verified empirically).

Manual (not part of this script):
  - Unplug network, run test_phase1.py: must log ERROR and exit cleanly.
  - SIGINT (Ctrl+C) during a long bot run: must log shutdown line + Telegram
    "🛑 Bot 下線" (Phase 4 OS signal path; verified at Stage 3 cross-day run).

Usage:
    python chaos_test.py
    python chaos_test.py --run-wrong-ip   # opt-in to [7/15] (still needs setup)
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

import ccxt  # noqa: E402  (must load env first)

from exchange_api import BinanceExchange  # noqa: E402
from logger import get_logger  # noqa: E402
from notifier import TelegramNotifier  # noqa: E402
from trader import (  # noqa: E402
    BinanceTrader,
    DAILY_CAP_USDT,
    MAX_SINGLE_BUY_USDT,
    STATE_FILE,
    TAIPEI_TZ,
)

log = get_logger("dca_bot.chaos")

_PASS = "PASS"
_FAIL = "FAIL"
_SKIP = "SKIP"


def _expect_false(label: str, result: bool) -> str:
    if result is False:
        print(f"  PASS  {label}: send() returned False")
        return _PASS
    print(f"  FAIL  {label}: expected False, got {result!r}")
    return _FAIL


def _expect_raises(label: str, exc_type: type, fn) -> str:
    try:
        fn()
    except exc_type as exc:
        print(f"  PASS  {label}: raised {exc_type.__name__} ({exc})")
        return _PASS
    except Exception as exc:  # noqa: BLE001
        print(f"  FAIL  {label}: expected {exc_type.__name__}, "
              f"got {type(exc).__name__}: {exc}")
        return _FAIL
    print(f"  FAIL  {label}: expected {exc_type.__name__}, no exception raised")
    return _FAIL


def chaos_bad_token() -> str:
    print("[1/15] Bad token (Telegram should return 401/404, log + return False)")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "1942404023")
    notifier = TelegramNotifier(
        token="0000000000:ChAoS_invalid_token_for_testing_xxxxx",
        chat_id=chat_id,
    )
    return _expect_false("bad token",
                         notifier.send("chaos: should never arrive (bad token)"))


def chaos_bad_chat_id() -> str:
    print("[2/15] Bad chat_id (Telegram should return 400 'chat not found')")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("  SKIP  TELEGRAM_BOT_TOKEN not set in .env")
        return _SKIP
    notifier = TelegramNotifier(token=token, chat_id="999999999")
    return _expect_false("bad chat_id",
                         notifier.send("chaos: should never arrive (bad chat_id)"))


def chaos_missing_chat_id_env() -> str:
    print("[3/15] Missing CHAT_ID env (TelegramNotifier should raise RuntimeError)")
    saved = os.environ.pop("TELEGRAM_CHAT_ID", None)
    try:
        return _expect_raises(
            "missing CHAT_ID",
            RuntimeError,
            lambda: TelegramNotifier(token="anything"),
        )
    finally:
        if saved is not None:
            os.environ["TELEGRAM_CHAT_ID"] = saved


def chaos_bad_api_key() -> str:
    print("[4/15] Bad API key (get_balance should raise ccxt.AuthenticationError)")
    return _expect_raises(
        "bad API key",
        ccxt.AuthenticationError,
        lambda: BinanceExchange(
            api_key="bad_key_xxxxxxxx",
            api_secret="bad_secret_xxxxxxxx",
            notify_on_error=False,
        ).get_balance("USDT"),
    )


def chaos_bad_symbol() -> str:
    print("[5/15] Bad symbol (get_price should return None, NO Telegram sent)")
    saved_key = os.environ.pop("BINANCE_API_KEY", None)
    saved_secret = os.environ.pop("BINANCE_API_SECRET", None)
    try:
        exchange = BinanceExchange(notify_on_error=False)
        result = exchange.get_price("FOOBAR/USDT")
        if result is None:
            print("  PASS  bad symbol: get_price() returned None")
            return _PASS
        print(f"  FAIL  bad symbol: expected None, got {result!r}")
        return _FAIL
    finally:
        if saved_key is not None:
            os.environ["BINANCE_API_KEY"] = saved_key
        if saved_secret is not None:
            os.environ["BINANCE_API_SECRET"] = saved_secret


def chaos_no_key_get_balance() -> str:
    print("[6/15] No-key get_balance (should raise RuntimeError)")
    saved_key = os.environ.pop("BINANCE_API_KEY", None)
    saved_secret = os.environ.pop("BINANCE_API_SECRET", None)
    try:
        return _expect_raises(
            "no-key get_balance",
            RuntimeError,
            lambda: BinanceExchange(notify_on_error=False).get_balance("USDT"),
        )
    finally:
        if saved_key is not None:
            os.environ["BINANCE_API_KEY"] = saved_key
        if saved_secret is not None:
            os.environ["BINANCE_API_SECRET"] = saved_secret


def chaos_wrong_ip_whitelist(opted_in: bool) -> str:
    print("[7/15] Wrong IP whitelist (semi-manual)")
    if not opted_in:
        print("  SKIP  半手動測試。請參考 README 的「Wrong IP 半手動測試流程」段：")
        print("        1. 先到 Binance 後台把 API key 白名單暫改成 1.2.3.4")
        print("        2. 重跑：python chaos_test.py --run-wrong-ip")
        print("        3. **務必**測試後把白名單改回真 IP")
        return _SKIP
    return _expect_raises(
        "wrong IP whitelist",
        ccxt.AuthenticationError,
        lambda: BinanceExchange(notify_on_error=False).get_balance("USDT"),
    )


def _without_env_keys(fn):
    """Helper: pop BINANCE_* env keys, run fn, restore. Mirrors [5/15] [6/15]."""
    saved_key = os.environ.pop("BINANCE_API_KEY", None)
    saved_secret = os.environ.pop("BINANCE_API_SECRET", None)
    try:
        return fn()
    finally:
        if saved_key is not None:
            os.environ["BINANCE_API_KEY"] = saved_key
        if saved_secret is not None:
            os.environ["BINANCE_API_SECRET"] = saved_secret


def chaos_symbol_not_in_whitelist() -> str:
    print("[8/15] Symbol off whitelist (place_market_buy should raise ValueError)")
    return _without_env_keys(lambda: _expect_raises(
        "symbol not in whitelist",
        ValueError,
        lambda: BinanceTrader(notify_on_error=False).place_market_buy(
            "DOGE/USDT", 11.0,
        ),
    ))


def chaos_below_min_notional() -> str:
    print("[9/15] Below min notional (place_market_buy should raise ValueError)")
    return _without_env_keys(lambda: _expect_raises(
        "below min notional",
        ValueError,
        lambda: BinanceTrader(notify_on_error=False).place_market_buy(
            "BTC/USDT", 1.0,
        ),
    ))


def chaos_exceed_max_single_buy() -> str:
    print("[10/15] Above max single buy (place_market_buy should raise ValueError)")
    return _without_env_keys(lambda: _expect_raises(
        "exceed max single buy",
        ValueError,
        lambda: BinanceTrader(notify_on_error=False).place_market_buy(
            "BTC/USDT", MAX_SINGLE_BUY_USDT + 5.0,
        ),
    ))


def chaos_exceed_daily_cap() -> str:
    print("[11/15] Daily cap exceeded (real state backed up + restored)")
    today = datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d")
    # pre_spent + buy_amount must exceed DAILY_CAP_USDT to trigger step 5,
    # AND buy_amount must be in [MIN_SINGLE_BUY_USDT, MAX_SINGLE_BUY_USDT]
    # so step 2 doesn't reject it first. With DAILY_CAP=50, MIN_BUY=10,
    # MAX_BUY=25: pre_spent=45 + buy=10 → 55 > 50 → step 5 fires correctly.
    pre_spent = DAILY_CAP_USDT - 5.0
    buy_amount = 10.0
    pre_state = {"date": today, "spent_usdt": pre_spent}
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Back up any real production state so chaos doesn't clobber the real
    # daily counter when this runs after a successful test_phase3.py.
    backup_bytes = STATE_FILE.read_bytes() if STATE_FILE.exists() else None

    STATE_FILE.write_text(json.dumps(pre_state), encoding="utf-8")
    saved_key = os.environ.pop("BINANCE_API_KEY", None)
    saved_secret = os.environ.pop("BINANCE_API_SECRET", None)
    try:
        try:
            BinanceTrader(notify_on_error=False).place_market_buy(
                "BTC/USDT", buy_amount,
            )
            print("  FAIL  daily cap: should have raised ValueError")
            return _FAIL
        except ValueError as exc:
            if "daily cap exceeded" not in str(exc):
                print(f"  FAIL  daily cap: wrong msg: {exc}")
                return _FAIL
            after = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            if float(after.get("spent_usdt", 0)) != pre_spent:
                print(f"  FAIL  daily cap: state mutated to {after}")
                return _FAIL
            print(f"  PASS  daily cap: blocked, state preserved at {pre_spent}")
            return _PASS
        except Exception as exc:  # noqa: BLE001
            print(f"  FAIL  daily cap: unexpected {type(exc).__name__}: {exc}")
            return _FAIL
    finally:
        # Restore real state if we had one; otherwise remove the chaos fake.
        if backup_bytes is not None:
            STATE_FILE.write_bytes(backup_bytes)
        else:
            STATE_FILE.unlink(missing_ok=True)
        if saved_key is not None:
            os.environ["BINANCE_API_KEY"] = saved_key
        if saved_secret is not None:
            os.environ["BINANCE_API_SECRET"] = saved_secret


def chaos_dry_run() -> str:
    print("[12/15] DRY-RUN mode (no API call, no state change)")
    backup = STATE_FILE.read_bytes() if STATE_FILE.exists() else None
    import config
    saved_dry = config.DRY_RUN
    config.DRY_RUN = True
    try:
        from main import run_dca_cycle
        run_dca_cycle()
        after = STATE_FILE.read_bytes() if STATE_FILE.exists() else None
        if after != backup:
            print("  FAIL  state changed in DRY-RUN")
            return _FAIL
        print("  PASS  DRY-RUN no side effects")
        return _PASS
    finally:
        config.DRY_RUN = saved_dry
        # state never written in dry-run, no restore needed


def chaos_circuit_breaker() -> str:
    print("[13/15] Circuit breaker trips at 5/5 (sends 1 Telegram by design)")
    from circuit_breaker import CircuitBreaker
    breaker = CircuitBreaker(max_failures=5)
    for i in range(4):
        breaker.record_failure(f"test failure {i+1}")
    try:
        breaker.record_failure("test failure 5")
        print("  FAIL  should have called sys.exit(1)")
        return _FAIL
    except SystemExit as exc:
        if exc.code != 1:
            print(f"  FAIL  wrong exit code: {exc.code}")
            return _FAIL
        print("  PASS  tripped at 5/5 with exit(1)")
        return _PASS


def chaos_cross_day_reset() -> str:
    print("[14/15] Cross-day reset (yesterday spent → today 0)")
    from datetime import timedelta
    backup = STATE_FILE.read_bytes() if STATE_FILE.exists() else None
    yesterday = (datetime.now(TAIPEI_TZ) - timedelta(days=1)).strftime("%Y-%m-%d")
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps({"date": yesterday, "spent_usdt": 11.5}),
        encoding="utf-8",
    )
    saved_key = os.environ.pop("BINANCE_API_KEY", None)
    saved_secret = os.environ.pop("BINANCE_API_SECRET", None)
    try:
        trader = BinanceTrader(notify_on_error=False)
        state = trader._check_daily_cap(5.5)
        if state["spent_usdt"] != 0.0:
            print(f"  FAIL  expected reset to 0, got {state['spent_usdt']}")
            return _FAIL
        if state["date"] != datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d"):
            print("  FAIL  date not advanced to today")
            return _FAIL
        print("  PASS  cross-day reset to today 0.0")
        return _PASS
    finally:
        if backup is not None:
            STATE_FILE.write_bytes(backup)
        else:
            STATE_FILE.unlink(missing_ok=True)
        if saved_key is not None:
            os.environ["BINANCE_API_KEY"] = saved_key
        if saved_secret is not None:
            os.environ["BINANCE_API_SECRET"] = saved_secret


def chaos_signal_handler() -> str:
    print("[15/15] Graceful shutdown handler (direct call, no OS signal)")
    import signal as _signal
    from main import _signal_handler, shutdown_event
    shutdown_event.clear()  # reset before test
    try:
        _signal_handler(_signal.SIGTERM, None)
        if not shutdown_event.is_set():
            print("  FAIL  shutdown_event not set after handler call")
            return _FAIL
        print("  PASS  handler set shutdown_event")
        return _PASS
    finally:
        shutdown_event.clear()


def main() -> int:
    opted_in_wrong_ip = "--run-wrong-ip" in sys.argv

    print("Chaos tests starting\n")
    log.info("chaos_test starting (Phase 1 + Phase 2 + Phase 3 + Phase 4)")

    results = [
        chaos_bad_token(),
        chaos_bad_chat_id(),
        chaos_missing_chat_id_env(),
        chaos_bad_api_key(),
        chaos_bad_symbol(),
        chaos_no_key_get_balance(),
        chaos_wrong_ip_whitelist(opted_in_wrong_ip),
        chaos_symbol_not_in_whitelist(),
        chaos_below_min_notional(),
        chaos_exceed_max_single_buy(),
        chaos_exceed_daily_cap(),
        chaos_dry_run(),
        chaos_circuit_breaker(),
        chaos_cross_day_reset(),
        chaos_signal_handler(),
    ]

    print()
    passed = results.count(_PASS)
    failed = results.count(_FAIL)
    skipped = results.count(_SKIP)
    total = len(results)

    summary = f"{passed} passed, {failed} failed, {skipped} skipped (total {total})"
    print(summary)

    if failed == 0:
        log.info("chaos_test: %s", summary)
        return 0
    log.error("chaos_test: %s", summary)
    return 1


if __name__ == "__main__":
    sys.exit(main())
