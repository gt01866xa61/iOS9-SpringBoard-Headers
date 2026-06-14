"""策略 interface:SymbolStrategy / PortfolioStrategy / NoOpPortfolioStrategy。

ref: architecture.md §3(雙 interface / lifecycle 8 method / output 形狀)。
lifecycle 拍板對應:
  必要 — __init__ / required_data / initialize / on_bar      (#2A)
  可選 — is_ready(#2C1)/ on_stale(#2C2-B Sub-Q1)/ reset(#2A)
可選 method 的「framework default」用 override 偵測實現:
engine 用 uses_framework_default() 判斷策略有沒有自己寫,沒寫就走
framework 內建行為(is_ready → buffer-based;reset → 丟舊 instance 重 new)。
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel

from .types import DataSpec, Snapshot


class StrategyBase(ABC):
    """兩種策略的共同骨架。params/state 用 pydantic 嚴格 schema(Round 1)。"""

    # 子類宣告自己的 schema(class attr)
    params_schema: type[BaseModel]
    state_schema: type[BaseModel] | None = None  # 無狀態策略可不宣告

    def __init__(self, params: BaseModel) -> None:
        # 接 params + 合法性檢查:型別不符在這裡就炸,不帶病跑(#2A)
        if not isinstance(params, self.params_schema):
            raise TypeError(
                f"{type(self).__name__} expects params of type "
                f"{self.params_schema.__name__}, got {type(params).__name__}"
            )
        self.params = params
        self.state: BaseModel | None = None

    @property
    def name(self) -> str:
        return type(self).__name__

    # ---- 必要 lifecycle ----

    @abstractmethod
    def required_data(self) -> DataSpec:
        """宣告需要什麼資料(field → FieldSpec)。註冊時叫一次。"""

    @abstractmethod
    def initialize(self, snapshot: Snapshot) -> None:
        """暖機:load 歷史 prime indicators。第一根 bar 前叫一次。

        無暖機需求就明寫 pass — 暖機是一等公民,不藏 __init__ 偷做(#2A)。
        """

    @abstractmethod
    def on_bar(self, snapshot: Snapshot) -> dict[str, float]:
        """核心邏輯。SymbolStrategy 回 target%、PortfolioStrategy 回 cap。"""

    # ---- 可選 lifecycle(沒 override = framework default)----

    def is_ready(self) -> bool:
        """暖機完了沒。framework default = buffer-based(buffer 滿 min_history 即 ready)。

        硬約束(#2C1):override 版只能看歷史 buffer,不能看當前最新值 —
        鎖 backtest/paper/live 同 timestamp 結果必相同。
        """
        raise NotImplementedError(
            "framework provides buffer-based default; engine should not call "
            "the base implementation directly (use uses_framework_default())"
        )

    def on_stale(self, stale_fields: list[str]) -> None:
        """被 stale 跳過後的通知 hook。default no-op(#2C2-B Sub-Q1)。"""

    def reset(self) -> None:
        """walk-forward 切窗口前清狀態。framework default = 丟舊 instance 用同 params new。"""
        raise NotImplementedError(
            "framework default = discard instance and re-create with same params; "
            "engine should not call the base implementation directly"
        )

    # ---- state 序列化(M3 lock / walk-forward boundary)----

    def get_state(self) -> BaseModel | None:
        return self.state

    def set_state(self, state: BaseModel) -> None:
        if self.state_schema is not None and not isinstance(state, self.state_schema):
            raise TypeError(
                f"{self.name} expects state of type "
                f"{self.state_schema.__name__}, got {type(state).__name__}"
            )
        self.state = state


class SymbolStrategy(StrategyBase):
    """出價的人:per-symbol 部位意圖。on_bar 回 {symbol: target% ∈ [0,1]}。

    long-only spot:domain 鎖 [0,1](Round 1,V2 邊界)。
    """


class PortfolioStrategy(StrategyBase):
    """策略級守門員:portfolio 風控 overlay。on_bar 回 {symbol: cap ∈ [0,1]}。

    多個 PortfolioStrategy 的 cap 由 engine 取 min 合併(#3D)。
    可換 NoOp(#3A);Risk Engine 才是不可關的 framework 護欄(R3-①)。
    """


# ---- output 驗證(engine 在 dispatch 後呼叫;B1 先提供 helper)----


def validate_output(output: dict[str, float], *, owner: str) -> dict[str, float]:
    """驗 on_bar 輸出形狀:{symbol: float ∈ [0,1]}。違反 = 策略 bug,丟例外
    (走 #2D 策略缺席統一模型,由 engine catch)。"""
    if not isinstance(output, dict):
        raise TypeError(f"{owner}: on_bar must return dict, got {type(output).__name__}")
    for symbol, v in output.items():
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            raise TypeError(f"{owner}: value for {symbol!r} must be a number, got {v!r}")
        if not 0.0 <= float(v) <= 1.0:
            raise ValueError(f"{owner}: value for {symbol!r} out of [0,1]: {v}")
    return {s: float(v) for s, v in output.items()}


def uses_framework_default(strategy: StrategyBase, method_name: str) -> bool:
    """策略沒 override 這個可選 method → True(engine 走 framework default)。"""
    return getattr(type(strategy), method_name) is getattr(StrategyBase, method_name)


# ---- NoOp(#3A:不做策略級風控要明確表態,擺假人占位)----


class NoOpParams(BaseModel):
    model_config = {"frozen": True}
    symbols: list[str]


class NoOpPortfolioStrategy(PortfolioStrategy):
    """假人守門員:永遠 cap=1.0 全 symbol(放行不限制)。

    存在目的 = 使用者明確簽字「我選擇不做 portfolio 級風控」。
    min 合併下天然不干擾真守門員(min(x, 1.0) = x)。
    """

    params_schema = NoOpParams

    def required_data(self) -> DataSpec:
        return {}  # 無 required data → 不會 stale → #3C 天然豁免

    def initialize(self, snapshot: Snapshot) -> None:
        pass

    def is_ready(self) -> bool:
        return True  # 沒東西要暖,永遠就緒

    def on_bar(self, snapshot: Snapshot) -> dict[str, float]:
        return {s: 1.0 for s in self.params.symbols}
