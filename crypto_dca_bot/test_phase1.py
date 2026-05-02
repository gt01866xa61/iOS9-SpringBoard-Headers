"""Phase 1 end-to-end check: logger writes, Telegram push arrives.

Usage:
    cp .env.example .env   # fill in TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
    pip install -r requirements.txt
    python test_phase1.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from logger import get_logger  # noqa: E402  (must load env first)
from notifier import get_notifier  # noqa: E402


def main() -> int:
    log = get_logger()
    log.info("Phase 1 test starting")
    log.warning("Warning-level log sample")
    log.error("Error-level log sample (not a real error)")

    try:
        notifier = get_notifier()
    except RuntimeError as exc:
        log.error("Notifier init failed: %s", exc)
        return 1

    ok = notifier.send(
        "Bot 初始化成功 ✅\n階段: Phase 1 — logger + Telegram notifier",
        level="INFO",
    )
    if not ok:
        log.error("Telegram send returned False; check bot.log for details")
        return 1

    log.info("Phase 1 驗證通過")
    print("Phase 1 驗證通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
