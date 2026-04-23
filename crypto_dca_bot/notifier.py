"""Telegram Bot notifier. Keys are read from .env; never hard-code credentials."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

import requests

from logger import get_logger

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
_TIMEOUT_SECONDS = 10


class TelegramNotifier:
    def __init__(
        self,
        token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ) -> None:
        self._token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self._chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
        if not self._token or not self._chat_id:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in the "
                "environment (see .env.example)."
            )
        self._log = get_logger("dca_bot.notifier")

    def send(self, message: str, level: str = "INFO") -> bool:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "chat_id": self._chat_id,
            "text": f"[{level}] {timestamp}\n{message}",
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        url = _TELEGRAM_API.format(token=self._token)
        try:
            resp = requests.post(url, json=payload, timeout=_TIMEOUT_SECONDS)
            resp.raise_for_status()
            body = resp.json()
            if not body.get("ok"):
                self._log.error("Telegram API returned ok=false: %s", body)
                return False
            self._log.info("Telegram notification sent (level=%s)", level)
            return True
        except requests.RequestException as exc:
            self._log.error("Telegram notification failed: %s", exc)
            return False
        except ValueError as exc:
            self._log.error("Telegram response JSON decode failed: %s", exc)
            return False


_notifier: Optional[TelegramNotifier] = None


def get_notifier() -> TelegramNotifier:
    global _notifier
    if _notifier is None:
        _notifier = TelegramNotifier()
    return _notifier
