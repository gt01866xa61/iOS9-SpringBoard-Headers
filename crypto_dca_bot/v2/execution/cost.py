"""回測成本模型(Round 1 Gap 4 拍板,2026-05-26)。

ref: architecture.md §6.2(executor 抽象)/ §8 Gap 4。
拍板:slippage = FixedBpsSlippage(5bps)、fee = FlatTakerFee(0.1%)default,
**都走 Protocol hook(default + override)** — framework 給合理 default,
策略 / 回測情境要特化可換,executor 不變。

數字是 placeholder:
- slippage 5bps:Binance spot BTC/ETH 流動性好,V2-B 後期用 M1 段
  high-low 價差校準
- fee 0.1%:Binance spot taker 業界基線,V2-D 前依真實 VIP tier 校準
"""
from __future__ import annotations

from typing import Protocol

# placeholders,校準時程見上
SLIPPAGE_BPS_DEFAULT = 5.0    # 0.05%
TAKER_FEE_RATE_DEFAULT = 0.001  # 0.1%


class SlippageModel(Protocol):
    """成交價 = f(參考價, side)。side: +1 買 / -1 賣。"""

    def fill_price(self, ref_price: float, side: int) -> float: ...


class FeeModel(Protocol):
    """手續費 = f(成交 notional in USDT)。回 USDT 費用(>= 0)。"""

    def fee(self, notional: float) -> float: ...


class ZeroSlippage:
    """sanity check 用:成交價 = 參考價。"""

    def fill_price(self, ref_price: float, side: int) -> float:
        return ref_price


class FixedBpsSlippage:
    """買滑高、賣滑低:ref × (1 ± bps/10000)。default 模型。"""

    def __init__(self, bps: float = SLIPPAGE_BPS_DEFAULT) -> None:
        if bps < 0:
            raise ValueError(f"bps must be >= 0, got {bps}")
        self._factor = bps / 10000.0

    def fill_price(self, ref_price: float, side: int) -> float:
        if side not in (1, -1):
            raise ValueError(f"side must be +1/-1, got {side}")
        return ref_price * (1.0 + side * self._factor)


class ZeroFee:
    def fee(self, notional: float) -> float:
        return 0.0


class FlatTakerFee:
    """notional × rate。default 模型。"""

    def __init__(self, rate: float = TAKER_FEE_RATE_DEFAULT) -> None:
        if rate < 0:
            raise ValueError(f"rate must be >= 0, got {rate}")
        self._rate = rate

    def fee(self, notional: float) -> float:
        return abs(notional) * self._rate
