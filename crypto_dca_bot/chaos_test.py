"""Phase 1 chaos / failure-injection tests.

Verifies that the notifier's safety nets actually hold under bad conditions.
Run after test_phase1.py succeeds; this confirms the防呆 designs work.

Tests automated here:
  1. Bad token         -> notifier.send() returns False, logs ERROR with
                          Telegram description, no crash.
  2. Bad chat_id       -> same as #1 but Telegram returns "chat not found".
  3. Missing CHAT_ID   -> TelegramNotifier() raises RuntimeError loudly
                          (predictable failure, no silent skip).

Manual tests (not automated, do these on prod machine after deploy):
  - Unplug network, run test_phase1.py: must log ERROR and exit cleanly.
  - SIGINT (Ctrl+C) during a long run: must log shutdown line (Phase 4).

Usage:
    python chaos_test.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from logger import get_logger  # noqa: E402  (must load env first)
from notifier import TelegramNotifier  # noqa: E402

log = get_logger("dca_bot.chaos")


def _expect_false(label: str, result: bool) -> bool:
    if result is False:
        print(f"  PASS  {label}: send() returned False")
        return True
    print(f"  FAIL  {label}: expected False, got {result!r}")
    return False


def _expect_raises(label: str, exc_type: type, fn) -> bool:
    try:
        fn()
    except exc_type as exc:
        print(f"  PASS  {label}: raised {exc_type.__name__} ({exc})")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  FAIL  {label}: expected {exc_type.__name__}, "
              f"got {type(exc).__name__}: {exc}")
        return False
    print(f"  FAIL  {label}: expected {exc_type.__name__}, no exception raised")
    return False


def chaos_bad_token() -> bool:
    print("[1/3] Bad token (Telegram should return 401/404, we should log + return False)")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "1942404023")
    notifier = TelegramNotifier(
        token="0000000000:ChAoS_invalid_token_for_testing_xxxxx",
        chat_id=chat_id,
    )
    return _expect_false("bad token",
                         notifier.send("chaos test: should never arrive (bad token)"))


def chaos_bad_chat_id() -> bool:
    print("[2/3] Bad chat_id (Telegram should return 400 'chat not found')")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("  SKIP  TELEGRAM_BOT_TOKEN not set in .env")
        return True
    notifier = TelegramNotifier(token=token, chat_id="999999999")
    return _expect_false("bad chat_id",
                         notifier.send("chaos test: should never arrive (bad chat_id)"))


def chaos_missing_chat_id_env() -> bool:
    print("[3/3] Missing CHAT_ID env (TelegramNotifier should raise RuntimeError)")
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


def main() -> int:
    print("Phase 1 chaos tests starting\n")
    log.info("chaos_test starting")

    results = [
        chaos_bad_token(),
        chaos_bad_chat_id(),
        chaos_missing_chat_id_env(),
    ]

    print()
    passed = sum(results)
    total = len(results)
    if passed == total:
        msg = f"All {total}/{total} chaos tests passed"
        print(msg)
        log.info(msg)
        return 0

    msg = f"{passed}/{total} chaos tests passed"
    print(msg)
    log.error(msg)
    return 1


if __name__ == "__main__":
    sys.exit(main())
