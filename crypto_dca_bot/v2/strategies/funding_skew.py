"""Funding rate skew(永續資金費率偏度)— V2-S2 第二個真策略。

ref: Round 2 #1 拍板(decisions 2026-05-21,5 params 簡單派)。
規格(V2 一 symbol 一 instance,跟 Donchian 同模式):
- 觸發:每 8h funding event(*_funding_8h)
- 訊號:過去 lookback_periods 個 8h funding 滾動平均 = raw_funding
- 進出場:
    raw ≤ low_threshold  → target 1.0 (滿倉:funding 低/負 = 空頭擁擠,反向做多 spot)
    raw ≥ high_threshold → target 0.0 (出場:funding 高 = 多頭擁擠,縮 spot 多單)
    else                 → linear interp(low→1.0,high→0.0)
- dead_band:|raw − 上次更新時的 raw| < dead_band → 維持上次 target
              (R3-③ 策略訊號級節流;跟 framework 執行政策層雙層分工)
- per symbol 各自獨立(BTC funding 對 BTC 部位)
- thesis:**不交易永續,只把 funding 當訊號用 spot**(V2 邊界對齊 long-only spot)

暖機處理(同 Donchian):min_history=0 + 策略內部自管(buffer 未滿回 flat)。
"""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from ..interfaces.strategy import SymbolStrategy
from ..interfaces.types import FieldSpec, Snapshot


class FundingSkewParams(BaseModel):
    model_config = {"frozen": True}
    symbol: str = "BTC"
    lookback_periods: int = Field(default=21, ge=1)  # 21 × 8h ≈ 7 天
    low_threshold: float = 0.00005   # 0.005% per 8h(滿倉門檻,Round 2 #1)
    high_threshold: float = 0.0003   # 0.03% per 8h(出場門檻)
    dead_band: float = 0.00002       # 0.002% raw 變動門檻(訊號級節流)

    @model_validator(mode="after")
    def _check(self):
        if self.low_threshold > self.high_threshold:
            raise ValueError(
                f"low_threshold ({self.low_threshold}) > high_threshold "
                f"({self.high_threshold})"
            )
        if self.dead_band < 0:
            raise ValueError(f"dead_band must be >= 0, got {self.dead_band}")
        return self


class FundingSkewState(BaseModel):
    fundings: list[float] = []      # rolling buffer(capped lookback_periods)
    last_raw: float | None = None   # 上次「更新 target 時」的 raw funding
    last_target: float = 0.0


class FundingSkew(SymbolStrategy):
    params_schema = FundingSkewParams
    state_schema = FundingSkewState

    def __init__(self, params: FundingSkewParams | None = None) -> None:
        super().__init__(params or FundingSkewParams())
        self.state = FundingSkewState()
        self._field = f"{self.params.symbol}_funding_8h"

    @property
    def name(self) -> str:
        return f"FundingSkew_{self.params.symbol}"

    def required_data(self):
        return {self._field: FieldSpec(min_history=0)}  # 暖機自管

    def initialize(self, snapshot: Snapshot) -> None:
        pass

    def _interp_target(self, raw: float) -> float:
        p = self.params
        if raw <= p.low_threshold:
            return 1.0
        if raw >= p.high_threshold:
            return 0.0
        # linear: low_threshold→1.0,high_threshold→0.0
        return 1.0 - (raw - p.low_threshold) / (p.high_threshold - p.low_threshold)

    def on_bar(self, snapshot: Snapshot) -> dict[str, float]:
        p = self.params
        s = self.state
        funding = float(snapshot.fields[self._field].value)

        # 1) 加入當下 funding,cap lookback
        new_buf = (s.fundings + [funding])[-p.lookback_periods:]

        # 2) buffer 未滿 → 自管暖機(維持 flat,buffer 累積但 last_raw/last_target 不動)
        if len(new_buf) < p.lookback_periods:
            self.state = FundingSkewState(
                fundings=new_buf,
                last_raw=s.last_raw,
                last_target=s.last_target,
            )
            return {p.symbol: 0.0}

        # 3) raw_funding = rolling mean
        raw = sum(new_buf) / len(new_buf)

        # 4) dead_band:訊號變動小 → 維持上次 target(訊號級節流)
        #    last_raw 不更新 → 漂移累積到超過 dead_band 才觸發 update
        if s.last_raw is not None and abs(raw - s.last_raw) < p.dead_band:
            self.state = FundingSkewState(
                fundings=new_buf,
                last_raw=s.last_raw,
                last_target=s.last_target,
            )
            return {p.symbol: s.last_target}

        # 5) 更新 target
        target = self._interp_target(raw)
        self.state = FundingSkewState(
            fundings=new_buf,
            last_raw=raw,
            last_target=target,
        )
        return {p.symbol: target}
