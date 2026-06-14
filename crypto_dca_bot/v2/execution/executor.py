"""Executor 抽象 + 雙 driver(R3-④ 輸出側 parity)。

ref: architecture.md §6.2 / §6.4(V1 落點表)。
一個 Executor 介面,底下兩個 driver:
- BacktestSimExecutor(本 milestone):用參考價 + 成本模型模擬成交
- LiveExecutor(V2-D 才實作):包 V1 trader.py + exchange_api

引擎輸出 OrderIntent → 同一介面 → 不知是模擬還真送(parity by construction)。
成交回拋 Fill,由 caller(B7 engine loop / pipeline 後)更新 PortfolioState。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from ..engine.execution_policy import OrderIntent
from ..engine.portfolio_state import PortfolioState
from ..observability.sink import Sink
from .cost import (
    FeeModel,
    FixedBpsSlippage,
    FlatTakerFee,
    SlippageModel,
)


@dataclass(frozen=True)
class Fill:
    """一筆成交結果。delta_qty 正 = 買進、負 = 賣出。"""

    symbol: str
    delta_qty: float
    fill_price: float
    notional: float   # |delta_qty| × fill_price(USDT)
    fee: float
    ts: datetime


@dataclass(frozen=True)
class Rejection:
    """訂單未成交(餘額不足 / 數量為零等)。"""

    symbol: str
    reason: str


class Executor(Protocol):
    def execute(
        self, orders: list[OrderIntent], prices: dict[str, float], now: datetime
    ) -> tuple[list[Fill], list[Rejection]]: ...


class BacktestSimExecutor:
    """模擬成交器:參考價(prices)套 slippage 得成交價 + fee,更新 state。

    determinism(M3 lock):無隨機 — 同輸入必同 Fill。
    state 副作用:成交即更新 state.positions / cash / last_trade_ts。
    買單餘額不足 → Rejection(不部分成交,V2-B 階段 fail-safe 保守;
    partial fill 留 V2-D 沿用 V1 trader 對帳)。
    """

    def __init__(
        self,
        state: PortfolioState,
        sink: Sink,
        *,
        slippage: SlippageModel | None = None,
        fee_model: FeeModel | None = None,
    ) -> None:
        self._state = state
        self._sink = sink
        self._slip = slippage or FixedBpsSlippage()
        self._fee = fee_model or FlatTakerFee()

    def execute(
        self, orders: list[OrderIntent], prices: dict[str, float], now: datetime
    ) -> tuple[list[Fill], list[Rejection]]:
        fills: list[Fill] = []
        rejections: list[Rejection] = []
        for o in orders:
            fill, rej = self._execute_one(o, prices, now)
            if fill is not None:
                fills.append(fill)
            if rej is not None:
                rejections.append(rej)
        return fills, rejections

    def _execute_one(self, o: OrderIntent, prices: dict[str, float], now: datetime):
        delta = o.delta_qty
        if delta == 0:
            return None, Rejection(o.symbol, "zero_delta")
        ref = prices.get(o.symbol)
        if ref is None or ref <= 0:
            return None, Rejection(o.symbol, "no_price")

        side = 1 if delta > 0 else -1
        price = self._slip.fill_price(ref, side)
        notional = abs(delta) * price
        fee = self._fee.fee(notional)

        if side == 1:
            cost = notional + fee
            if cost > self._state.cash + 1e-9:
                self._sink.log(
                    "order_rejected", symbol=o.symbol, reason="insufficient_cash",
                    need=cost, have=self._state.cash,
                )
                return None, Rejection(o.symbol, "insufficient_cash")
            self._state.cash -= cost
            self._state.positions[o.symbol] = self._state.positions.get(o.symbol, 0.0) + delta
        else:
            held = self._state.positions.get(o.symbol, 0.0)
            sell_qty = min(abs(delta), held)  # 不賣超過持有(long-only,no short)
            if sell_qty <= 0:
                return None, Rejection(o.symbol, "no_position")
            notional = sell_qty * price
            fee = self._fee.fee(notional)
            self._state.cash += notional - fee
            self._state.positions[o.symbol] = held - sell_qty
            delta = -sell_qty

        self._state.last_trade_ts[o.symbol] = now
        fill = Fill(
            symbol=o.symbol, delta_qty=delta, fill_price=price,
            notional=notional, fee=fee, ts=now,
        )
        self._sink.log(
            "fill", symbol=o.symbol, delta=delta, price=price,
            notional=notional, fee=fee, ts=now,
        )
        return fill, None


class LiveExecutor:
    """實盤成交:V2-D 才實作(包 V1 trader.py + exchange_api)。"""

    def execute(self, orders, prices, now):
        raise NotImplementedError(
            "LiveExecutor lands in V2-D (wraps V1 trader.py + exchange_api); "
            "V2-B uses BacktestSimExecutor"
        )
