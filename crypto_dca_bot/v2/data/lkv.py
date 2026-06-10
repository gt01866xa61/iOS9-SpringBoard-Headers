"""LKV store(最新已知值)+ snapshot 組裝。

ref: architecture.md §3.4(LKV 對齊)/ §6.1(point-in-time)。
拍板(B2 開工,2026-05-26):**per-fire 重建** — 每次 fire 從 LKV store
重新組一份 Snapshot,不維護共享可變 snapshot。重建邏輯簡單到一眼可驗
no-lookahead;效能等真撞瓶頸再優化(策略 3 個 / field 個位數,不會撞)。
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable

from ..interfaces.types import FieldValue, Snapshot
from .events import DataEvent


class LKVStore:
    """吃 event、記每 field 的最新已知值。

    亂序保護:ts 舊於現值的 event 不覆蓋(LKV = 最新,live 端遲到封包
    不能把值倒退)。backtest replay 本來就嚴格時間序,這條是 live 的保險。
    """

    def __init__(self) -> None:
        self._values: dict[str, FieldValue] = {}

    def update(self, event: DataEvent) -> bool:
        """回 True = 已更新;False = 比現值舊,忽略。"""
        cur = self._values.get(event.field)
        if cur is not None and event.ts <= cur.ts:
            return False
        self._values[event.field] = FieldValue(value=event.value, ts=event.ts)
        return True

    def get(self, field: str) -> FieldValue | None:
        return self._values.get(field)

    def known_fields(self) -> set[str]:
        return set(self._values)


def build_snapshot(store: LKVStore, fields: Iterable[str], now: datetime) -> Snapshot:
    """per-fire 重建:從 store 取 requested fields 的 LKV 組成 frozen Snapshot。

    缺值 field(還沒任何資料)直接省略 — 就緒(is_ready)/ stale 判定是
    B3 dispatch 的事,本函式只負責「忠實呈現此刻已知的過去」。
    fields 傳策略自己的 → per-strategy 視圖;傳 store.known_fields() →
    全 field 共享視圖(Sub-Q3:snapshot 共享、判定 per-strategy)。
    """
    return Snapshot(
        ts=now,
        fields={
            f: fv for f in fields if (fv := store.get(f)) is not None
        },
    )
