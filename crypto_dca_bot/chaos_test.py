"""Chaos / failure-injection tests for Phase 1 + Phase 2 + Phase 3.

Verifies that the safety nets in notifier / exchange_api / trader hold
under bad conditions. Run after test_phase{1,2,3}.py succeed.

Tests automated here:
  Phase 1 (notifier):
    [1/11] Bad token        -> notifier.send() returns False, no crash
    [2/11] Bad chat_id      -> Telegram "chat not found", returns False
    [3/11] Missing CHAT_ID  -> TelegramNotifier() raises RuntimeError

  Phase 2 (exchange_api):
    [4/11] Bad API key      -> get_balance() raises ccxt.AuthenticationError
    [5/11] Bad symbol       -> get_price() returns None, NO Telegram sent
    [6/11] No-key balance   -> get_balance() raises RuntimeError

  Phase 3 (trader, all local checks — no real Binance calls):
    [8/11]  Symbol off whitelist -> place_market_buy raises ValueError
    [9/11]  Below min notional   -> place_market_buy raises ValueError
    [10/11] Above max single buy -> place_market_buy raises ValueError
    [11/11] Daily cap exceeded   -> ValueError + state file unchanged + cleaned

Semi-manual:
    [7/11] Wrong IP whitelist -> SKIP unless you've prepared per the README.
                                When prepared, raises ccxt.AuthenticationError
                                (Binance code -2015; verified empirically).

Manual (not part of this script):
  - Unplug network, run test_phase1.py: must log ERROR and exit cleanly.
  - SIGINT (Ctrl+C) during a long run: must log shutdown line (Phase 4).

Usage:
    python chaos_test.py
    python chaos_test.py --run-wrong-ip   # opt-in to [7/11] (still needs setup)
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
    print("[1/11] Bad token (Telegram should return 401/404, log + return False)")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "1942404023")
    notifier = TelegramNotifier(
        token="0000000000:ChAoS_invalid_token_for_testing_xxxxx",
        chat_id=chat_id,
    )
    return _expect_false("bad token",
                         notifier.send("chaos: should never arrive (bad token)"))


def chaos_bad_chat_id() -> str:
    print("[2/11] Bad chat_id (Telegram should return 400 'chat not found')")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("  SKIP  TELEGRAM_BOT_TOKEN not set in .env")
        return _SKIP
    notifier = TelegramNotifier(token=token, chat_id="999999999")
    return _expect_false("bad chat_id",
                         notifier.send("chaos: should never arrive (bad chat_id)"))


def chaos_missing_chat_id_env() -> str:
    print("[3/11] Missing CHAT_ID env (TelegramNotifier should raise RuntimeError)")
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
    print("[4/11] Bad API key (get_balance should raise ccxt.AuthenticationError)")
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
    print("[5/11] Bad symbol (get_price should return None, NO Telegram sent)")
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
    print("[6/11] No-key get_balance (should raise RuntimeError)")
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
    print("[7/11] Wrong IP whitelist (semi-manual)")
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
    """Helper: pop BINANCE_* env keys, run fn, restore. Mirrors [5/11] [6/11]."""
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
    print("[8/11] Symbol off whitelist (place_market_buy should raise ValueError)")
    return _without_env_keys(lambda: _expect_raises(
        "symbol not in whitelist",
        ValueError,
        lambda: BinanceTrader(notify_on_error=False).place_market_buy(
            "DOGE/USDT", 11.0,
        ),
    ))


def chaos_below_min_notional() -> str:
    print("[9/11] Below min notional (place_market_buy should raise ValueError)")
    return _without_env_keys(lambda: _expect_raises(
        "below min notional",
        ValueError,
        lambda: BinanceTrader(notify_on_error=False).place_market_buy(
            "BTC/USDT", 1.0,
        ),
    ))


def chaos_exceed_max_single_buy() -> str:
    print("[10/11] Above max single buy (place_market_buy should raise ValueError)")
    return _without_env_keys(lambda: _expect_raises(
        "exceed max single buy",
        ValueError,
        lambda: BinanceTrader(notify_on_error=False).place_market_buy(
            "BTC/USDT", MAX_SINGLE_BUY_USDT + 5.0,
        ),
    ))


def chaos_exceed_daily_cap() -> str:
    print("[11/11] Daily cap exceeded (state should be untouched, file cleaned)")
    today = datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d")
    # pre_spent + buy_amount must exceed DAILY_CAP_USDT to trigger step 5,
    # AND buy_amount must be in [MIN_SINGLE_BUY_USDT, MAX_SINGLE_BUY_USDT]
    # so step 2 doesn't reject it first. With DAILY_CAP=50, MIN_BUY=10,
    # MAX_BUY=25: pre_spent=45 + buy=10 → 55 > 50 → step 5 fires correctly.
    pre_spent = DAILY_CAP_USDT - 5.0
    buy_amount = 10.0
    pre_state = {"date": today, "spent_usdt": pre_spent}
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
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
        STATE_FILE.unlink(missing_ok=True)
        if saved_key is not None:
            os.environ["BINANCE_API_KEY"] = saved_key
        if saved_secret is not None:
            os.environ["BINANCE_API_SECRET"] = saved_secret


def main() -> int:
    opted_in_wrong_ip = "--run-wrong-ip" in sys.argv

    print("Chaos tests starting\n")
    log.info("chaos_test starting (Phase 1 + Phase 2 + Phase 3)")

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
