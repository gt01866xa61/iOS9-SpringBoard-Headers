"""價格 dataset。每次 get_price 成功後寫一筆 SQLite。
V3 回測直接 query，不必解析 bot.log。
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from logger import get_logger

_DDL = """
CREATE TABLE IF NOT EXISTS prices (
    timestamp INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    price REAL NOT NULL,
    source TEXT DEFAULT 'binance',
    PRIMARY KEY (timestamp, symbol)
);
CREATE INDEX IF NOT EXISTS idx_symbol_time ON prices(symbol, timestamp DESC);
"""


class PriceRecorder:
    def __init__(self, db_path: Path) -> None:
        self._log = get_logger()
        self._db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path) as conn:
            conn.executescript(_DDL)

    def record(self, symbol: str, price: float) -> None:
        try:
            with sqlite3.connect(self._db_path, timeout=5.0) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO prices (timestamp, symbol, price) "
                    "VALUES (?, ?, ?)",
                    (int(time.time()), symbol, price),
                )
        except sqlite3.Error as exc:
            # 寫入失敗只 warning，不阻擋核心流程（取價已成功）
            self._log.warning("price_recorder write failed for %s: %s", symbol, exc)
