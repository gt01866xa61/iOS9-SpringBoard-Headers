"""Portfolio state(可變):cash / positions / last_trade_ts。

V2-B 階段 B4 用 placeholder(initial cash = 1000 USDT);實際更新由 B5
executor 成交回拋。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PortfolioState:
    cash: float = 1000.0  # USDT placeholder,真錢上場前 V2-D 接交易所餘額
    positions: dict[str, float] = field(default_factory=dict)  # symbol → qty
    last_trade_ts: dict[str, datetime] = field(default_factory=dict)

    def equity(self, prices: dict[str, float]) -> float:
        """總資產 (USDT) = cash + Σ positions × prices。"""
        return self.cash + sum(
            self.positions.get(s, 0.0) * prices[s] for s in self.positions if s in prices
        )

    def position_pct(self, symbol: str, prices: dict[str, float]) -> float:
        """current 部位佔總資產 % (用於 dead-band 比對)。"""
        eq = self.equity(prices)
        if eq <= 0:
            return 0.0
        return self.positions.get(symbol, 0.0) * prices.get(symbol, 0.0) / eq
