"""共用 logger：stdout + rotating file，跨 import 冪等。時間鎖 Asia/Taipei。

沿用 crypto_dca_bot/logger.py 的模式與時區紀律（固定 UTC+8，不依賴 IANA tzdata）。
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_FILE = Path(__file__).resolve().parent / "build.log"
_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"
_TAIPEI = timezone(timedelta(hours=8), name="Asia/Taipei")


class _TaipeiFormatter(logging.Formatter):
    """log 時間一律用台北時間顯示。"""

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=_TAIPEI)
        return dt.strftime(datefmt) if datefmt else dt.isoformat(timespec="seconds")


def get_logger(name: str = "gooaye_signals") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logger.setLevel(level)
    logger.propagate = False

    formatter = _TaipeiFormatter(_FORMAT, datefmt=_DATEFMT)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # 檔案 handler 失敗（如唯讀 FS）不致命——CI 上 stdout 已足夠。
    try:
        file_handler = RotatingFileHandler(
            _LOG_FILE, maxBytes=2_000_000, backupCount=2, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        logger.warning("無法建立 log 檔 %s，僅輸出 stdout", _LOG_FILE)

    return logger
