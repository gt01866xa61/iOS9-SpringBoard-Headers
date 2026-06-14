"""Sink:log(被動記錄)+ alert(主動推播)。

ref: architecture.md §1 / glossary「Alert vs Log vs Hook」(Log = 給 debug、
Alert = 給人、Hook = 給策略)。

分流:alert 兩件事一起做 — 進 event log(留檔)+ 推 AlertChannel(回測
no-op、實盤 V2-D 接 V1 notifier)。回測時 channel = NoopAlertChannel,
alert 仍進 log 可查;實盤時 channel = LiveTelegramChannel(V2-D)。

B6 引入 EventLogSink;MemorySink 改成 EventLogSink 的 backward-compat
facade(維持 .records / .alerts attribute 給 B3-B5 既有 tests)。
"""
from __future__ import annotations

from typing import Protocol

from .kinds import ALERT
from .log import EventLog, LogEntry


class Sink(Protocol):
    """log + alert 雙軌:任何模組都能往 sink 寫,sink 內部分流到 log/channel。"""

    def log(self, kind: str, **data: object) -> None: ...

    def alert(self, message: str, **data: object) -> None: ...


class AlertChannel(Protocol):
    """alert 真正的推播管道。回測 = no-op、實盤 = Telegram(V2-D)。"""

    def push(self, message: str, **data: object) -> None: ...


class NoopAlertChannel:
    """回測 default:不推播。alert 仍進 event log 留存,只是不打擾使用者。"""

    def push(self, message: str, **data: object) -> None:
        pass


class LiveTelegramChannel:
    """V2-D 才實作:wrap V1 notifier.py。

    架構 hook 落點 — V2-B 階段拋 NotImplementedError 防誤用。
    """

    def push(self, message: str, **data: object) -> None:
        raise NotImplementedError(
            "LiveTelegramChannel lands in V2-D (wraps V1 notifier.py); "
            "V2-B uses NoopAlertChannel (alerts still recorded in event log)"
        )


class EventLogSink:
    """B6 主要 Sink:log 進 EventLog、alert 進 log + 推 AlertChannel。"""

    def __init__(
        self,
        log: EventLog | None = None,
        channel: AlertChannel | None = None,
    ) -> None:
        self._log = log if log is not None else EventLog()
        self._channel = channel if channel is not None else NoopAlertChannel()

    @property
    def event_log(self) -> EventLog:
        return self._log

    def log(self, kind: str, **data: object) -> None:
        self._log.append(kind, **data)

    def alert(self, message: str, **data: object) -> None:
        self._log.append(ALERT, message=message, **data)
        self._channel.push(message, **data)


class MemorySink(EventLogSink):
    """B1-B5 既有 API 的 facade(.records / .alerts tuples)。

    新 code 應該用 EventLogSink + EventLog query API(by_kind / between /
    fingerprint);MemorySink 保留是為了讓 B3-B5 tests 不必改。
    """

    @property
    def records(self) -> list[tuple[str, dict]]:
        """全部 entries 攤平成 (kind, data) tuples。"""
        return [(e.kind, dict(e.data)) for e in self._log.all()]

    @property
    def alerts(self) -> list[tuple[str, dict]]:
        """alert 攤平成 (message, rest) tuples。"""
        out: list[tuple[str, dict]] = []
        for e in self._log.by_kind(ALERT):
            data = dict(e.data)
            message = data.pop("message", "")
            out.append((str(message), data))
        return out


def _alert_entries(log: EventLog) -> list[LogEntry]:
    """helper for tests."""
    return log.by_kind(ALERT)
