"""Donchian 通道突破(海龜經典版,long-only)— V2-S1 第一個真策略。

規格(使用者 2026-06-13 拍板):
- K 線:日線(*_kline_1d,Bar OHLCV)
- 進場:收盤價突破過去 `entry` 日最高價 → 開多(target = 1.0)
- 出場:收盤價跌破過去 `exit` 日最低價 → 平倉(target = 0.0)
- 方向:long-only(對齊 V2 邊界,不放空)
- 標的:BTC + ETH(一個 symbol 一個 instance,各自獨立通道)
- 停損:跌破 exit 日低出場即內建停損(海龜 ATR 停損列為之後可選)
- 參數 2 個:entry=20 / exit=10(簡單派 < 5)

暖機處理(rolling-window 策略的通則,V2-S1 釘清):
  rolling 通道需要逐 bar 累積歷史,但 framework 的 buffer-based is_ready
  gate(#2C1)會擋掉「還沒 ready」的 bar → 策略反而拿不到累積所需的 bar。
  解法:**min_history=0(framework 永遠 ready、每 bar 都 call on_bar)+
  策略內部自管暖機**(buffer 未滿 → 回 flat 0.0)。這在 default+override
  框架內(策略自理就緒語意),不動 framework。is_ready buffer-gate 留給
  「指標 = 當前 snapshot 純函式」那類策略。

通道「過去 N 日」**不含當根**(否則 close ≤ 自己的 high,突破永遠不觸發):
  先用「加入當根前」的 buffer 算通道 → 比對當根 close → 再把當根 high/low
  併入 buffer 供下一根用。
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from ..interfaces.strategy import SymbolStrategy
from ..interfaces.types import Bar, FieldSpec, Snapshot


class DonchianParams(BaseModel):
    model_config = {"frozen": True}
    symbol: str = "BTC"
    entry: int = Field(default=20, ge=1)  # 進場通道回看日數
    exit: int = Field(default=10, ge=1)   # 出場通道回看日數


class DonchianState(BaseModel):
    highs: list[float] = []       # 過去 bar 的 high(最新在後),capped entry
    lows: list[float] = []        # 過去 bar 的 low,capped exit
    in_position: bool = False


class DonchianBreakout(SymbolStrategy):
    params_schema = DonchianParams
    state_schema = DonchianState

    def __init__(self, params: DonchianParams | None = None) -> None:
        super().__init__(params or DonchianParams())
        self.state = DonchianState()
        self._field = f"{self.params.symbol}_kline_1d"

    @property
    def name(self) -> str:
        return f"Donchian_{self.params.symbol}"

    def required_data(self):
        # min_history=0:每 bar 都 fire,策略自管暖機(見模組 docstring)
        return {self._field: FieldSpec(min_history=0)}

    def initialize(self, snapshot: Snapshot) -> None:
        # 不在這預載:buffer 純由 on_bar 逐根累積,避免重複計入第一根
        pass

    def _as_bar(self, snapshot: Snapshot) -> Bar:
        v = snapshot.fields[self._field].value
        if isinstance(v, Bar):
            return v
        # 容錯:float-only feed(把 close 當 OHLC,僅供 smoke,不建議真用)
        f = float(v)
        return Bar(open=f, high=f, low=f, close=f)

    def on_bar(self, snapshot: Snapshot) -> dict[str, float]:
        bar = self._as_bar(snapshot)
        p = self.params
        s = self.state

        # 1) 用「加入當根前」的 buffer 算通道(不含當根)
        entry_high = max(s.highs[-p.entry:]) if len(s.highs) >= p.entry else None
        exit_low = min(s.lows[-p.exit:]) if len(s.lows) >= p.exit else None

        # 2) 突破判定(long-only 狀態機)
        in_pos = s.in_position
        if not in_pos:
            if entry_high is not None and bar.close > entry_high:
                in_pos = True
        else:
            if exit_low is not None and bar.close < exit_low:
                in_pos = False

        # 3) 當根 high/low 併入 buffer(供下一根),各自 cap
        self.state = DonchianState(
            highs=(s.highs + [bar.high])[-p.entry:],
            lows=(s.lows + [bar.low])[-p.exit:],
            in_position=in_pos,
        )

        return {p.symbol: 1.0 if in_pos else 0.0}
