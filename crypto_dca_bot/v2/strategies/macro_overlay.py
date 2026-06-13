"""Macro overlay(宏觀風控)— V2-S3 第一個真守門員(PortfolioStrategy)。

ref: v2_roadmap 起步策略池 #3(DXY/VIX 上升時減倉)/ Round 1 PortfolioStrategy
interface / R3-① Risk Engine 之外的「策略級」風控(可換 NoOp)。

設計:多 indicator 門檻 overlay。每個 indicator = (field, risk_off_above, cap)。
某 symbol 的 cap = **所有觸發(level > 門檻)indicator 的 cap 取 min**(最狠者勝,
內部沿用 #3D 哲學);無觸發 → 1.0(不限制)。

V2-S3 真資料:**VIX-primary**(datahub finance-vix 真 OHLC 可達)。DXY 找不到
reputable 公開源(FRED/datahub 皆無/擋)→ 留 optional indicator hook,使用者
本機抓 dxy_daily 後加進 indicators 即生效(同 funding fixture 機制)。

staleness:overlay required_data 宣告 indicator fields;若 field stale(超過
registry max_staleness,VIX 預設 3d → 容忍週末不開盤)→ **framework 跳過 overlay
→ #3C fallback_cap 進 min 池**(缺席統一模型,overlay 自己不處理 stale)。

無 state(讀當前 snapshot level)。indicator level 支援 Bar(取 close)或 float。
"""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from ..interfaces.strategy import PortfolioStrategy
from ..interfaces.types import Bar, FieldSpec, Snapshot


class MacroIndicator(BaseModel):
    model_config = {"frozen": True}
    field: str                       # 例 "vix_daily" / "dxy_daily"
    risk_off_above: float            # level 超過此 → risk-off
    cap: float = Field(ge=0.0, le=1.0)  # 觸發時的 cap multiplier


def _vix_default() -> list[MacroIndicator]:
    # VIX > 30 → 砍到 0.5(數字 placeholder,V2-T 校準)
    return [MacroIndicator(field="vix_daily", risk_off_above=30.0, cap=0.5)]


class MacroOverlayParams(BaseModel):
    model_config = {"frozen": True}
    symbols: list[str] = Field(default_factory=lambda: ["BTC", "ETH"])
    indicators: list[MacroIndicator] = Field(default_factory=_vix_default)

    @model_validator(mode="after")
    def _check(self):
        if not self.symbols:
            raise ValueError("symbols must be non-empty")
        if not self.indicators:
            raise ValueError("indicators must be non-empty (use NoOp to opt out of risk control)")
        return self


def _level(value: object) -> float:
    """indicator 的 level:Bar 取 close、否則當 float。"""
    if isinstance(value, Bar):
        return value.close
    return float(value)


class MacroOverlay(PortfolioStrategy):
    params_schema = MacroOverlayParams

    def __init__(self, params: MacroOverlayParams | None = None) -> None:
        super().__init__(params or MacroOverlayParams())

    @property
    def name(self) -> str:
        return "MacroOverlay"

    def required_data(self):
        # 各 indicator field 都要(staleness 用 registry default,VIX 3d 容忍週末)
        return {ind.field: FieldSpec() for ind in self.params.indicators}

    def initialize(self, snapshot: Snapshot) -> None:
        pass

    def on_bar(self, snapshot: Snapshot) -> dict[str, float]:
        # framework 保證 required fields 不 stale(stale → 整個 overlay 被跳,#2C2/#3C);
        # 但個別 field 可能尚未出現在 snapshot(暖機初期)→ 該 indicator 視為未觸發。
        triggered_caps: list[float] = []
        for ind in self.params.indicators:
            fv = snapshot.fields.get(ind.field)
            if fv is None:
                continue
            if _level(fv.value) > ind.risk_off_above:
                triggered_caps.append(ind.cap)

        cap = min(triggered_caps) if triggered_caps else 1.0  # 最狠者勝(#3D 哲學)
        return {s: cap for s in self.params.symbols}
