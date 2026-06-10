"""Observability 最小核:log + alert 的 sink 介面。

ref: architecture.md §1(統一 event log + alert sink)。
B3 先定最小介面 + in-memory 實作(dispatcher 要發 log/alert);
B6 擴成完整 event log(schema)+ V1 notifier 接縫。
"""
from __future__ import annotations

from typing import Protocol


class Sink(Protocol):
    """log = 被動記錄等人查;alert = 主動推播(回測進記錄、實盤走 Telegram)。"""

    def log(self, kind: str, **data: object) -> None: ...

    def alert(self, message: str, **data: object) -> None: ...


class MemorySink:
    """測試 / 回測用:全部進記憶體。"""

    def __init__(self) -> None:
        self.records: list[tuple[str, dict]] = []
        self.alerts: list[tuple[str, dict]] = []

    def log(self, kind: str, **data: object) -> None:
        self.records.append((kind, dict(data)))

    def alert(self, message: str, **data: object) -> None:
        self.alerts.append((message, dict(data)))
        self.log("alert", message=message, **data)
