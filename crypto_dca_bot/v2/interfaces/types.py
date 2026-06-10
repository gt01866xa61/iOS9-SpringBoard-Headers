"""共用型別:snapshot / field spec。

ref: architecture.md §3.4(LKV 對齊、每 field 帶 timestamp)、
     §5.4 Sub-Q3(max_staleness / alert_N 可 override,None = 用 registry default)。
"""
from __future__ import annotations

from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field


class FieldValue(BaseModel):
    """snapshot 中單一 field:最新已知值(LKV)+ 它的時戳。

    ts 是「這個值實際產生的時間」,不是 snapshot 組裝時間 —
    策略 / framework 靠它判斷 staleness。
    """

    model_config = ConfigDict(frozen=True)

    value: object
    ts: datetime


class Snapshot(BaseModel):
    """fire 那一刻的市場快照(point-in-time,只含已發生資料)。

    no-lookahead 保證由 B2 的組裝端負責(只能從已發生的 event 組);
    本型別只承諾形狀。
    """

    model_config = ConfigDict(frozen=True)

    ts: datetime  # fire 時刻
    fields: dict[str, FieldValue]

    def age_of(self, field: str) -> timedelta:
        """field 的資料齡(fire 時刻 − 該值產生時刻)。"""
        return self.ts - self.fields[field].ts


class FieldSpec(BaseModel):
    """策略對單一資料 field 的需求宣告(required_data() 的 value)。

    max_staleness / alert_n 為 None = 沿用 DATA_SOURCES registry 的
    per-source default(default + override pattern)。
    trigger=False = 只要這份資料、但它來新值時不要 fire 我。
    """

    model_config = ConfigDict(frozen=True)

    min_history: int = Field(default=0, ge=0)
    max_staleness: timedelta | None = None
    alert_n: int | None = Field(default=None, ge=1)
    trigger: bool = True


# required_data() 的回傳形狀:{field_name: FieldSpec}
DataSpec = dict[str, FieldSpec]
