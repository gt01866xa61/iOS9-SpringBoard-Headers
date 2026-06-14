"""Event 型別 + event source 介面(R3-② 統一 event bus 的最小核)。

ref: architecture.md §6.1 — 一個 event 介面、底下兩個 driver:
backtest replay(B2,本 milestone)/ live feed(V2-D 才接)。
引擎只認 EventSource,完全不知資料是歷史還是即時 — parity by construction。
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterator, Protocol

from pydantic import BaseModel, ConfigDict


class DataEvent(BaseModel):
    """某 field 來了一筆新資料。引擎消費的唯一輸入單位。"""

    model_config = ConfigDict(frozen=True)

    field: str
    value: object
    ts: datetime  # 資料產生時刻(不是抵達時刻)


class EventSource(Protocol):
    """兩個 driver 的共同形狀:吐時間序 DataEvent 的 iterator。

    backtest replay 吐完即止;live driver 是無限 blocking iterator。
    引擎主迴圈一律 `for event in source.events()`,不分來源。
    """

    def events(self) -> Iterator[DataEvent]: ...
