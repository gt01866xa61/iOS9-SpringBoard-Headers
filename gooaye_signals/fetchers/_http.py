"""外部 API 呼叫的共用重試包裝，沿用 crypto_dca_bot 的 _call 精神（記錄 + 重試 + 最終拋出）。

指數退避重試；最後一次仍失敗就把例外往上拋，交給 build.py 的 per-source 隔離處理。
"""
from __future__ import annotations

import time
from typing import Callable, TypeVar

from logger import get_logger

log = get_logger()
T = TypeVar("T")

DEFAULT_TRIES = 3
BASE_DELAY = 1.5  # 秒；第 n 次失敗後 sleep base_delay * n


def call_with_retry(fn: Callable[[], T], *, tries: int = DEFAULT_TRIES,
                    base_delay: float = BASE_DELAY, desc: str = "") -> T:
    last: Exception | None = None
    for attempt in range(1, tries + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — 統一重試，分類交給呼叫端
            last = exc
            tag = f" {desc}" if desc else ""
            log.warning("call%s 失敗 (%d/%d)：%s", tag, attempt, tries, exc)
            if attempt < tries:
                time.sleep(base_delay * attempt)
    assert last is not None
    raise last
