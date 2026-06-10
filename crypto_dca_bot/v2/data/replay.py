"""Backtest replay driver(R3-② 雙 driver 的 backtest 端)。

ref: architecture.md §6.1。
no-lookahead by construction:事件**嚴格按時間序**吐出,引擎任一時刻
只看得到已吐出的過去 — 結構上沒有管道碰到未來資料。

determinism(M3 lock 需要可重現):同 ts 跨 field 的 tie 按 field 名
穩定排序;同一 field 內 ts 必須嚴格遞增(同 ts 兩筆 = LKV 語意不明,
直接拒收,fail fast)。
"""
from __future__ import annotations

import heapq
from datetime import datetime
from typing import Iterator

from .events import DataEvent
from .registry import get_source


class ReplaySeriesError(ValueError):
    """歷史序列不合法(沒按時間排序 / 同 ts 重複)。"""


class BacktestReplayDriver:
    """吃 per-field 歷史序列,合併後按 (ts, field) 時間序吐 DataEvent。

    series: {field: [(ts, value), ...]} — 各 field 序列必須 ts 嚴格遞增。
    field 必須存在於 DATA_SOURCES registry(建構時驗,fail fast)。
    """

    def __init__(self, series: dict[str, list[tuple[datetime, object]]]) -> None:
        for field, points in series.items():
            get_source(field)  # 不在 registry → UnknownDataSourceError
            for prev, cur in zip(points, points[1:]):
                if cur[0] <= prev[0]:
                    raise ReplaySeriesError(
                        f"{field}: ts not strictly increasing at {cur[0]} "
                        f"(prev {prev[0]})"
                    )
        self._series = series

    def events(self) -> Iterator[DataEvent]:
        def stream(field: str, points: list) -> Iterator[tuple]:
            for ts, value in points:
                yield ts, field, value

        streams = [stream(f, pts) for f, pts in sorted(self._series.items())]
        for ts, field, value in heapq.merge(*streams, key=lambda t: (t[0], t[1])):
            yield DataEvent(field=field, value=value, ts=ts)
