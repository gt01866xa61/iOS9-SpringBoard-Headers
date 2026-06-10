"""DATA_SOURCES registry(資料源登錄表)。

ref: architecture.md §1 / §5.4 Sub-Q3(default + override pattern)。
拍板(B2 開工,2026-05-26):**Python dict** — 改 registry 就改本檔;
未來升 YAML / DB 只需換 load 端,消費端(get_source / effective_*)不變。

所有數字(cadence / staleness / alert_n)都是 placeholder,V2-B 後期
用真資料校準(§8 carry over)。
"""
from __future__ import annotations

from datetime import timedelta

from pydantic import BaseModel, ConfigDict, Field

from ..interfaces.types import FieldSpec


class DataSourceSpec(BaseModel):
    """單一資料源的 registry 條目。"""

    model_config = ConfigDict(frozen=True)

    cadence: timedelta              # 預期 fire 頻率
    max_staleness_default: timedelta  # 超過多久算 stale(策略可 override)
    alert_n_default: int = Field(ge=1)  # 連續 stale 幾次升 alert(策略可 override)


class UnknownDataSourceError(KeyError):
    """策略 required_data() 引用了 registry 沒有的 field — 註冊時就炸,不帶病跑。"""


DATA_SOURCES: dict[str, DataSourceSpec] = {
    # K 線(1h):cadence 1h / stale 2h / 連 6 次 alert
    "BTC_kline_1h": DataSourceSpec(
        cadence=timedelta(hours=1),
        max_staleness_default=timedelta(hours=2),
        alert_n_default=6,
    ),
    "ETH_kline_1h": DataSourceSpec(
        cadence=timedelta(hours=1),
        max_staleness_default=timedelta(hours=2),
        alert_n_default=6,
    ),
    # funding(8h 結算):cadence 8h / stale 16h / 連 2 次 alert
    "BTC_funding_8h": DataSourceSpec(
        cadence=timedelta(hours=8),
        max_staleness_default=timedelta(hours=16),
        alert_n_default=2,
    ),
    "ETH_funding_8h": DataSourceSpec(
        cadence=timedelta(hours=8),
        max_staleness_default=timedelta(hours=16),
        alert_n_default=2,
    ),
    # macro 日線:cadence 1d / stale 3d / 連 3 次 alert
    "vix_daily": DataSourceSpec(
        cadence=timedelta(days=1),
        max_staleness_default=timedelta(days=3),
        alert_n_default=3,
    ),
    "dxy_daily": DataSourceSpec(
        cadence=timedelta(days=1),
        max_staleness_default=timedelta(days=3),
        alert_n_default=3,
    ),
}


def get_source(field: str) -> DataSourceSpec:
    try:
        return DATA_SOURCES[field]
    except KeyError:
        raise UnknownDataSourceError(
            f"field {field!r} not in DATA_SOURCES registry; "
            f"known: {sorted(DATA_SOURCES)}"
        ) from None


def effective_staleness(field: str, spec: FieldSpec) -> timedelta:
    """策略 override 優先,否則 registry default(Sub-Q3 雙層)。"""
    if spec.max_staleness is not None:
        return spec.max_staleness
    return get_source(field).max_staleness_default


def effective_alert_n(field: str, spec: FieldSpec) -> int:
    if spec.alert_n is not None:
        return spec.alert_n
    return get_source(field).alert_n_default
