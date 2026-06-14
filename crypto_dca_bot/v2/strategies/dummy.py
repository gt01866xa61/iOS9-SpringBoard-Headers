"""Dummy reference 策略(練全管線用,非真策略)。

真策略 codify 在 V2-S(trend / funding skew / macro overlay)。這裡只放
最簡可跑版本,證明 interface + engine 串得通 + 給 B7 整合測試當素材。
全部 long-only [0,1]、邏輯一句話,符合簡單派。
"""
from __future__ import annotations

from pydantic import BaseModel

from ..interfaces.strategy import PortfolioStrategy, SymbolStrategy
from ..interfaces.types import FieldSpec, Snapshot


class SmaCrossParams(BaseModel):
    model_config = {"frozen": True}
    symbol: str = "BTC"
    fast: int = 3
    slow: int = 10
    target_when_up: float = 0.6


class SmaCrossState(BaseModel):
    prices: list[float] = []  # 滾動收盤(最多 slow 個)


class SmaCrossSymbol(SymbolStrategy):
    """最簡 trend proxy:fast SMA > slow SMA → target_when_up,否則 0。

    暖機:需要 slow 根 K 線(min_history=slow)。
    """

    params_schema = SmaCrossParams
    state_schema = SmaCrossState

    def __init__(self, params: SmaCrossParams | None = None) -> None:
        super().__init__(params or SmaCrossParams())
        self.state = SmaCrossState()
        self._field = f"{self.params.symbol}_kline_1h"

    @property
    def name(self) -> str:
        return f"SmaCross_{self.params.symbol}"

    def required_data(self):
        return {self._field: FieldSpec(min_history=self.params.slow)}

    def initialize(self, snapshot: Snapshot) -> None:
        # 暖機:把當下已知值塞進 buffer(若有)
        fv = snapshot.fields.get(self._field)
        if fv is not None and isinstance(fv.value, (int, float)):
            self.state.prices.append(float(fv.value))

    def on_bar(self, snapshot: Snapshot) -> dict[str, float]:
        price = float(snapshot.fields[self._field].value)
        buf = (self.state.prices + [price])[-self.params.slow:]
        self.state = SmaCrossState(prices=buf)
        if len(buf) < self.params.slow:
            return {self.params.symbol: 0.0}
        fast = sum(buf[-self.params.fast:]) / self.params.fast
        slow = sum(buf) / len(buf)
        up = fast > slow
        return {self.params.symbol: self.params.target_when_up if up else 0.0}


class ThresholdOverlayParams(BaseModel):
    model_config = {"frozen": True}
    field: str = "vix_daily"
    risk_off_above: float = 30.0
    cap_when_risk_off: float = 0.3
    symbols: list[str] = ["BTC", "ETH"]


class ThresholdOverlay(PortfolioStrategy):
    """最簡 macro overlay proxy:看一個指標 > 門檻 → 全 symbol 砍 cap。

    無暖機(看當前值即可)。staleness 用 registry default。
    """

    params_schema = ThresholdOverlayParams

    def __init__(self, params: ThresholdOverlayParams | None = None) -> None:
        super().__init__(params or ThresholdOverlayParams())

    @property
    def name(self) -> str:
        return f"ThresholdOverlay_{self.params.field}"

    def required_data(self):
        return {self.params.field: FieldSpec()}

    def initialize(self, snapshot: Snapshot) -> None:
        pass

    def on_bar(self, snapshot: Snapshot) -> dict[str, float]:
        value = float(snapshot.fields[self.params.field].value)
        risk_off = value > self.params.risk_off_above
        cap = self.params.cap_when_risk_off if risk_off else 1.0
        return {s: cap for s in self.params.symbols}
