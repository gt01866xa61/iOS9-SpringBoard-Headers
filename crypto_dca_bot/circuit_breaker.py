"""連續失敗熔斷。N 次連敗 → 推播 + sys.exit(1)。

exit code 1 讓 Windows Task Scheduler 看到失敗，不盲目重啟。
"""
from __future__ import annotations

import sys

from logger import get_logger
from notifier import get_notifier


class CircuitBreaker:
    def __init__(self, max_failures: int = 5) -> None:
        self._max = max_failures
        self._failures = 0
        self._log = get_logger()
        self._notifier = get_notifier()

    @property
    def failures(self) -> int:
        return self._failures

    def record_failure(self, reason: str) -> None:
        self._failures += 1
        self._log.error(
            "Circuit breaker: failure %d/%d - %s",
            self._failures, self._max, reason,
        )
        if self._failures >= self._max:
            self._trip(reason)

    def record_success(self) -> None:
        if self._failures > 0:
            self._log.info("Circuit breaker reset (was %d)", self._failures)
        self._failures = 0

    def _trip(self, last_reason: str) -> None:
        msg = (
            f"🚨 Circuit breaker TRIPPED\n"
            f"連續 {self._max} 次失敗，bot 已停機\n"
            f"最後原因: {last_reason}\n"
            f"請人工檢查 bot.log + Binance 帳戶後重啟"
        )
        self._log.critical(msg)
        self._notifier.send(msg, level="ERROR")
        sys.exit(1)
