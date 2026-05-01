"""Shared logger: rotating file handler + stdout, idempotent across imports."""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_FILE = Path(__file__).resolve().parent / "bot.log"
_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"
_TAIPEI = timezone(timedelta(hours=8), name="Asia/Taipei")


class _TaipeiFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=_TAIPEI)
        return dt.strftime(datefmt) if datefmt else dt.isoformat(timespec="seconds")


def get_logger(name: str = "dca_bot") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logger.setLevel(level)
    logger.propagate = False

    formatter = _TaipeiFormatter(_FORMAT, datefmt=_DATEFMT)

    file_handler = RotatingFileHandler(
        _LOG_FILE, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
