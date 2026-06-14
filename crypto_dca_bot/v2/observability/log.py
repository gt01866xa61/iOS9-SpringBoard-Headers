"""結構化 event log:single source of truth for debug / replay / M5 對照 /
M3 lock 鎖檔。

ref: architecture.md §1(統一 event log)/ §6.1(M5 paper-vs-backtest)
     / Round 1 M3(backtest lock 需可重現 fingerprint)。

LogEntry.ts 規則:append 時從 data sniff `ts` 欄位(若是 datetime)當業務
時間;否則 fallback wall clock。Backtest 中業務 ts 跟 wall clock 差很多,
query 用業務 ts 才合理。
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timedelta
from typing import Iterable


@dataclass(frozen=True)
class LogEntry:
    ts: datetime
    kind: str
    data: dict[str, object]
    business_ts: bool = True  # True = ts 是真實事件時間;False = wall clock fallback(setup/admin)

    def get(self, key: str, default: object = None) -> object:
        return self.data.get(key, default)


def _jsonable(obj: object) -> object:
    """遞迴轉 JSON 友善型別。pydantic v2 / dataclass / datetime / timedelta /
    set 都認;不認的 → repr() 兜底(不炸,但 fingerprint 不保證跨機器)。"""
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(x) for x in obj]
    if isinstance(obj, (set, frozenset)):
        return sorted((_jsonable(x) for x in obj), key=repr)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, timedelta):
        return obj.total_seconds()
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if hasattr(obj, "model_dump"):  # pydantic v2
        return _jsonable(obj.model_dump())
    if is_dataclass(obj) and not isinstance(obj, type):
        return _jsonable(asdict(obj))
    return repr(obj)


class EventLog:
    """append-only 時序記錄。debug / replay / M3 fingerprint。"""

    def __init__(self) -> None:
        self._entries: list[LogEntry] = []

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self):
        return iter(self._entries)

    def append(self, kind: str, **data: object) -> LogEntry:
        raw_ts = data.get("ts")
        business = isinstance(raw_ts, datetime)
        ts = raw_ts if business else datetime.now()
        entry = LogEntry(ts=ts, kind=kind, data=dict(data), business_ts=business)
        self._entries.append(entry)
        return entry

    # ---- query ----

    def all(self) -> list[LogEntry]:
        return list(self._entries)

    def by_kind(self, kind: str) -> list[LogEntry]:
        return [e for e in self._entries if e.kind == kind]

    def by_strategy(self, name: str) -> list[LogEntry]:
        return [e for e in self._entries if e.data.get("strategy") == name]

    def between(self, start: datetime, end: datetime) -> list[LogEntry]:
        return [e for e in self._entries if start <= e.ts <= end]

    def kinds(self) -> set[str]:
        return {e.kind for e in self._entries}

    # ---- 序列化(M3 lock)----

    def to_jsonl(self, *, only_business: bool = False) -> str:
        """每行一個 canonical JSON object(sort_keys),保證 fingerprint deterministic。

        only_business=True → 排除 wall-clock-only entries(setup/admin),
        fingerprint 用這個確保 backtest 可重現。
        """
        lines: list[str] = []
        for e in self._entries:
            if only_business and not e.business_ts:
                continue
            obj = {
                "ts": e.ts.isoformat(),
                "kind": e.kind,
                "data": _jsonable(e.data),
            }
            lines.append(json.dumps(obj, sort_keys=True))
        return "\n".join(lines)

    def fingerprint(self) -> str:
        """SHA-256 of to_jsonl(only_business=True) — M3 backtest lock 鎖檔用。

        只算有真實事件時間的 entries,排除 setup/admin(那些用 wall clock,
        每次跑必不一樣)。同 backtest 序列 → 同 hash,改任一筆內容/順序 → 變。
        """
        return hashlib.sha256(
            self.to_jsonl(only_business=True).encode("utf-8")
        ).hexdigest()

    def fingerprint_all(self) -> str:
        """全部 entries(含 wall-clock setup)的 hash — debug 對照用,
        不保證跨 run 一致。"""
        return hashlib.sha256(self.to_jsonl().encode("utf-8")).hexdigest()

    def extend(self, entries: Iterable[LogEntry]) -> None:
        """從別處(例如 deserialize)灌資料 — 測試 / 跨 process 對照用。"""
        self._entries.extend(entries)
