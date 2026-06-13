"""Backtest runner:把六層串成一個 end-to-end 入口。

ref: architecture.md §2(完整 pipeline)。
資料流:EventSource(B2)→ Dispatcher(B3)→ run_pipeline(B4)→
        Executor(B5)→ EventLog(B6)。

prices 來源:V2-B 階段從「latest known close per symbol」推導(用 LKV store
裡 *_kline_1h 的值當 mark price)。真實 mark price / 多 venue 留 V2-S/D。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ..data.events import EventSource
from ..data.lkv import LKVStore
from ..engine.dispatcher import Dispatcher
from ..engine.execution_policy import OrderIntent
from ..engine.pipeline import PipelineResult, run_pipeline
from ..engine.portfolio_state import PortfolioState
from ..execution.executor import BacktestSimExecutor, Fill, Rejection
from ..interfaces.types import Bar
from ..observability.sink import EventLogSink
from ..observability.log import EventLog


# 哪個 field 對應哪個 symbol 的 mark price(V2-B 簡化:kline 收盤價)
def _default_price_map() -> dict[str, str]:
    return {"BTC": "BTC_kline_1h", "ETH": "ETH_kline_1h"}


@dataclass
class BacktestResult:
    final_state: PortfolioState
    event_log: EventLog
    fills: list[Fill] = field(default_factory=list)
    rejections: list[Rejection] = field(default_factory=list)
    pipeline_runs: int = 0
    fired_events: int = 0
    fingerprint: str = ""


class Backtest:
    """組裝 + 跑一場回測。

    用法:
        bt = Backtest(initial_cash=10000)
        bt.add_symbol(MyStrategy())
        bt.add_portfolio(MyOverlay())   # 或 NoOp
        result = bt.run(source)
    """

    def __init__(
        self,
        *,
        initial_cash: float = 10000.0,
        price_map: dict[str, str] | None = None,
        **pipeline_kwargs: object,
    ) -> None:
        self._store = LKVStore()
        self._sink = EventLogSink()
        self._dispatcher = Dispatcher(self._store, self._sink)
        self._state = PortfolioState(cash=initial_cash)
        self._executor = BacktestSimExecutor(self._state, self._sink)
        self._price_map = price_map or _default_price_map()
        self._pipeline_kwargs = pipeline_kwargs
        self._registered = False

    def add_symbol(self, strategy, *, crash_limit: int = 3) -> None:
        self._dispatcher.register(strategy, crash_limit=crash_limit)

    def add_portfolio(self, strategy, *, crash_limit: int = 3) -> None:
        self._dispatcher.register(strategy, crash_limit=crash_limit)

    def _mark_prices(self) -> dict[str, float]:
        """從 LKV store 取各 symbol 的 mark price(kline 收盤)。

        value 可能是 float(dummy)或 Bar(真 kline)→ 取 close。
        """
        out: dict[str, float] = {}
        for symbol, field_name in self._price_map.items():
            fv = self._store.get(field_name)
            if fv is None:
                continue
            v = fv.value
            if isinstance(v, Bar):
                out[symbol] = v.close
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                out[symbol] = float(v)
        return out

    def run(self, source: EventSource) -> BacktestResult:
        self._dispatcher.assert_startup_ok()  # #3A always-on 鎖
        result = BacktestResult(final_state=self._state, event_log=self._sink.event_log)

        for event in source.events():
            result.fired_events += 1
            fire = self._dispatcher.on_event(event)  # 缺席模型 / counter / 全 portfolio 評估都在這
            if not fire.symbol_outputs:
                continue  # 無交易決策(暖機 / 全缺席);portfolio stale 偵測已在 dispatch 完成
            prices = self._mark_prices()
            if not prices:
                continue  # 還沒任何 mark price(暖機初期)

            pres: PipelineResult = run_pipeline(
                fire,
                portfolio_names=self._dispatcher.portfolio_names(),
                symbol_names=self._dispatcher.symbol_names(),
                state=self._state,
                prices=prices,
                sink=self._sink,
                **self._pipeline_kwargs,
            )
            result.pipeline_runs += 1

            if pres.orders:
                fills, rejs = self._executor.execute(pres.orders, prices, event.ts)
                result.fills.extend(fills)
                result.rejections.extend(rejs)

        result.fingerprint = self._sink.event_log.fingerprint()
        return result
