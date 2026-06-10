"""風控管線整合:FireResult → OrderIntent。

ref: architecture.md §2(per-fire pipeline 階段 2-7)。
串接順序:
  Symbol aggregate → Portfolio min 合併 (+ #3C fallback) → Risk Engine
    → 算量站 → 執行政策層 → OrderIntents

把 prices 抽出來當參數(算量站 / portfolio_state 都要,B5 由 executor
回拋實際成交價更新 PortfolioState,V2-B 階段測試用 mock prices)。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ..observability.sink import Sink
from .aggregation import (
    FALLBACK_CAP_DEFAULT,
    aggregate_symbol_targets,
    merge_portfolio_caps,
)
from .dispatcher import FireResult
from .execution_policy import (
    COOLING_DEFAULT,
    DEAD_BAND_DEFAULT,
    FilteredOut,
    OrderIntent,
    RegimeHook,
    apply_execution_policy,
)
from .portfolio_state import PortfolioState
from .risk_engine import (
    GROSS_LIMIT_DEFAULT,
    TERMINAL_FALLBACK_CAP,
    VolEstimator,
    apply_risk_engine,
)
from .sizing import size_to_quantity


@dataclass
class PipelineResult:
    """整段管線跑完後的紀錄(進 event log + 交 B5 executor)。"""

    ts: datetime
    trigger_field: str
    combined_target: dict[str, float] = field(default_factory=dict)
    effective_cap: dict[str, float] = field(default_factory=dict)
    final_target: dict[str, float] = field(default_factory=dict)      # post-cap
    risk_adjusted: dict[str, float] = field(default_factory=dict)     # post-Risk Engine
    desired_qty: dict[str, float] = field(default_factory=dict)
    orders: list[OrderIntent] = field(default_factory=list)
    blocked: list[FilteredOut] = field(default_factory=list)


def run_pipeline(
    fire: FireResult,
    portfolio_names: set[str],
    symbol_names: set[str],
    state: PortfolioState,
    prices: dict[str, float],
    sink: Sink,
    *,
    capital_weights: dict[str, float] | None = None,
    vol_estimator: VolEstimator | None = None,
    regime_hook: RegimeHook | None = None,
    fallback_cap: float = FALLBACK_CAP_DEFAULT,
    gross_limit: float = GROSS_LIMIT_DEFAULT,
    terminal_fallback_cap: float = TERMINAL_FALLBACK_CAP,
    dead_band: float = DEAD_BAND_DEFAULT,
    cooling=COOLING_DEFAULT,
) -> PipelineResult:
    result = PipelineResult(ts=fire.ts, trigger_field=fire.trigger_field)

    # 階段 2:Symbol 加總(per-strategy capital weight)
    result.combined_target = aggregate_symbol_targets(
        fire.symbol_outputs, weights=capital_weights
    )

    # 階段 3:Portfolio min 合併 + #3C fallback
    absent_portfolios = portfolio_names & set(fire.absences)
    symbols = set(result.combined_target)
    result.effective_cap = merge_portfolio_caps(
        fire.portfolio_outputs,
        absent_portfolios=absent_portfolios,
        symbols=symbols,
        fallback_cap=fallback_cap,
    )

    # final_target = combined × cap(post-cap)
    result.final_target = {
        sym: result.combined_target[sym] * result.effective_cap.get(sym, 1.0)
        for sym in symbols
    }

    # 階段 4:Risk Engine(framework 護欄,always-on)
    absent_symbols = symbol_names & set(fire.absences)
    all_relevant_absent = bool(symbol_names) and absent_symbols == symbol_names
    result.risk_adjusted = apply_risk_engine(
        result.final_target,
        all_strategies_absent=all_relevant_absent,
        vol_estimator=vol_estimator,
        gross_limit=gross_limit,
        terminal_fallback_cap=terminal_fallback_cap,
    )

    # 階段 5:算量站
    equity = state.equity(prices)
    result.desired_qty = size_to_quantity(result.risk_adjusted, prices, equity)

    # 階段 6:執行政策層
    current_pct = {sym: state.position_pct(sym, prices) for sym in result.desired_qty}
    current_qty = {sym: state.positions.get(sym, 0.0) for sym in result.desired_qty}
    result.orders, result.blocked = apply_execution_policy(
        desired_pct=result.risk_adjusted,
        desired_qty=result.desired_qty,
        current_qty=current_qty,
        current_pct=current_pct,
        last_trade_ts=state.last_trade_ts,
        now=fire.ts,
        dead_band=dead_band,
        cooling=cooling,
        regime_hook=regime_hook,
    )

    sink.log(
        "pipeline",
        ts=fire.ts,
        trigger=fire.trigger_field,
        combined=result.combined_target,
        cap=result.effective_cap,
        risk_adjusted=result.risk_adjusted,
        orders=[(o.symbol, o.delta_qty, o.reason) for o in result.orders],
        blocked=[(b.symbol, b.reason) for b in result.blocked],
    )
    return result
