"""T2 Walk-forward runner(M2 樣本外驗證)。

ref: v2t_prereqs.md T2 + 2026-06-14 拍板(低頻策略 feasibility 修正)。

**為什麼不照 prereq 原本的「mean(OOS Sharpe)/mean(IS Sharpe)」**:真資料診斷
顯示三個策略都低頻(Donchian 一年才幾筆),3 個月 OOS 視窗每窗只有 2~5 筆交易,
任何 OOS 長度都湊不到「≥30 筆/窗」。每窗各算一個 Sharpe = 4 筆交易撐起來的噪音,
平均 19 個噪音仍是噪音。

**拍板的兩個算法(2026-06-14)**:
1. **pooled OOS WFE**(主):30/3 滑窗、每窗 strategy 重建(= reset + re-warm)、
   chronological 跑 IS+OOS、在 boundary 切 equity curve。把**全部 OOS 段的日報酬
   拼成一條**(OOS 段時間連續、不重疊 → 可直接拼)算 pooled OOS Sharpe;IS 視窗
   彼此重疊(不能拼報酬會重複計算)→ 取**per-window IS Sharpe 的平均**當分母。
   WFE = pooled_OOS_Sharpe / mean_IS_Sharpe。總 OOS 交易數十~數百筆 → 穩健。
2. **single IS/OOS split**(對照):前 train_frac(70%)訓練 / 後 30% 驗證,一段
   連續跑(不重建),boundary 切。OOS 27 個月 → 交易筆數夠(≥30)→ 最直觀切分。

兩個結論一致才信;打架 = 警訊要查。per-window 數字(含 OOS 交易筆數)照印當
診斷,**不當閘門頭條**。

**「訓練」語意(此 V2-T 階段)**:策略 params 固定、不做參數最佳化 → IS = 暖機 +
跑早段,OOS = held-out 晚段。WFE 測的是「策略跨時間 / regime 是否穩定」,不是
「最佳化有沒有過擬合」(那是 V2-E 接 dynamic allocator 後的事)。fresh 實例 per
window 在固定 params 下等價 reset(),且更不易出錯。
"""
from __future__ import annotations

import calendar
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from ..data.replay import BacktestReplayDriver
from ..engine.backtest import Backtest
from ..interfaces.strategy import PortfolioStrategy, SymbolStrategy
from .metrics import daily_equity, equity_returns, sharpe

# (symbol strategies, portfolio strategies) — 每呼叫回**全新**實例(per-window reset)
StrategyFactory = Callable[[], tuple[list[SymbolStrategy], list[PortfolioStrategy]]]
Series = dict[str, list[tuple[datetime, object]]]

DEFAULT_PRICE_MAP = {"BTC": "BTC_kline_1d", "ETH": "ETH_kline_1d"}


# ---------------------------------------------------------------------------
# 日期 / 切片工具
# ---------------------------------------------------------------------------

def add_months(dt: datetime, n: int) -> datetime:
    """dt + n 個月(處理月底溢位:1/31 + 1mo → 2/28)。"""
    m = dt.month - 1 + n
    y = dt.year + m // 12
    m = m % 12 + 1
    d = min(dt.day, calendar.monthrange(y, m)[1])
    return dt.replace(year=y, month=m, day=d)


def slice_series(series: Series, start: datetime, end: datetime) -> Series:
    """取 [start, end) 範圍(半開)— 每個 field 各自過濾,保持時間序。"""
    return {
        f: [(ts, v) for ts, v in rows if start <= ts < end]
        for f, rows in series.items()
    }


def _span(series: Series) -> tuple[datetime, datetime]:
    all_ts = [ts for rows in series.values() for ts, _ in rows]
    return min(all_ts), max(all_ts)


def windows(
    series: Series, *, is_months: int, oos_months: int, step_months: int
) -> list[tuple[datetime, datetime, datetime]]:
    """產生 (is_start, is_end=oos_start, oos_end) 視窗清單(最後 OOS 須在資料內)。"""
    first, last = _span(series)
    out: list[tuple[datetime, datetime, datetime]] = []
    is_start = first
    while True:
        is_end = add_months(is_start, is_months)
        oos_end = add_months(is_end, oos_months)
        if oos_end > last:
            break
        out.append((is_start, is_end, oos_end))
        is_start = add_months(is_start, step_months)
    return out


# ---------------------------------------------------------------------------
# 單段執行 + 指標
# ---------------------------------------------------------------------------

def _run(series: Series, factory: StrategyFactory, *,
         initial_cash: float, price_map: dict[str, str], **bt_kwargs):
    bt = Backtest(initial_cash=initial_cash, price_map=price_map, **bt_kwargs)
    syms, ports = factory()
    for s in syms:
        bt.add_symbol(s)
    for p in ports:
        bt.add_portfolio(p)
    return bt.run(BacktestReplayDriver(series))


def _curve_sharpe(curve: list[tuple[datetime, float]], *,
                  start: datetime | None = None, end: datetime | None = None,
                  periods_per_year: float) -> float:
    seg = [(t, e) for t, e in curve
           if (start is None or t >= start) and (end is None or t < end)]
    return sharpe(equity_returns(daily_equity(seg)), periods_per_year=periods_per_year)


def _seg_returns(curve: list[tuple[datetime, float]], start: datetime, end: datetime) -> list[float]:
    seg = [(t, e) for t, e in curve if start <= t < end]
    return equity_returns(daily_equity(seg))


# ---------------------------------------------------------------------------
# Walk-forward(pooled OOS WFE)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WindowResult:
    is_start: datetime
    oos_start: datetime
    oos_end: datetime
    is_sharpe: float
    oos_sharpe: float
    oos_trades: int      # OOS 段成交筆數(診斷:看每窗夠不夠)
    oos_return: float     # OOS 段總報酬


@dataclass
class WalkForwardResult:
    windows: list[WindowResult] = field(default_factory=list)
    pooled_oos_sharpe: float = 0.0   # 全部 OOS 段日報酬拼一條
    mean_is_sharpe: float = 0.0      # per-window IS Sharpe 平均
    wfe_pooled: float = 0.0          # pooled_oos / mean_is
    total_oos_trades: int = 0

    @property
    def n_windows(self) -> int:
        return len(self.windows)


def walk_forward(
    series: Series,
    factory: StrategyFactory,
    *,
    is_months: int = 30,
    oos_months: int = 3,
    step_months: int = 3,
    initial_cash: float = 10000.0,
    price_map: dict[str, str] | None = None,
    periods_per_year: float = 365.0,
    **bt_kwargs: object,
) -> WalkForwardResult:
    """滑窗 walk-forward;pooled OOS Sharpe / mean IS Sharpe = WFE。"""
    pm = price_map or DEFAULT_PRICE_MAP
    res = WalkForwardResult()
    pooled_oos_returns: list[float] = []
    is_sharpes: list[float] = []

    for is_start, oos_start, oos_end in windows(
        series, is_months=is_months, oos_months=oos_months, step_months=step_months
    ):
        # 每窗 fresh 策略 + 只餵該窗資料(IS+OOS),chronological 跑
        seg = slice_series(series, is_start, oos_end)
        run = _run(seg, factory, initial_cash=initial_cash, price_map=pm, **bt_kwargs)

        is_sh = _curve_sharpe(run.equity_curve, end=oos_start, periods_per_year=periods_per_year)
        oos_sh = _curve_sharpe(run.equity_curve, start=oos_start, periods_per_year=periods_per_year)
        oos_rets = _seg_returns(run.equity_curve, oos_start, oos_end)
        oos_trades = sum(1 for f in run.fills if oos_start <= f.ts < oos_end)
        oos_ret = _segment_total_return(run.equity_curve, oos_start, oos_end)

        res.windows.append(WindowResult(
            is_start=is_start, oos_start=oos_start, oos_end=oos_end,
            is_sharpe=is_sh, oos_sharpe=oos_sh, oos_trades=oos_trades, oos_return=oos_ret,
        ))
        pooled_oos_returns.extend(oos_rets)
        is_sharpes.append(is_sh)
        res.total_oos_trades += oos_trades

    res.pooled_oos_sharpe = sharpe(pooled_oos_returns, periods_per_year=periods_per_year)
    res.mean_is_sharpe = (sum(is_sharpes) / len(is_sharpes)) if is_sharpes else 0.0
    res.wfe_pooled = (
        res.pooled_oos_sharpe / res.mean_is_sharpe if res.mean_is_sharpe > 0 else float("nan")
    )
    return res


def _segment_total_return(curve: list[tuple[datetime, float]], start: datetime, end: datetime) -> float:
    eq = daily_equity([(t, e) for t, e in curve if start <= t < end])
    if len(eq) < 2 or eq[0] <= 0:
        return 0.0
    return eq[-1] / eq[0] - 1.0


# ---------------------------------------------------------------------------
# 對照:單一 IS/OOS split(70/30)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SplitResult:
    split_ts: datetime
    is_sharpe: float
    oos_sharpe: float
    wfe: float
    oos_trades: int
    oos_return: float


def single_split(
    series: Series,
    factory: StrategyFactory,
    *,
    train_frac: float = 0.7,
    initial_cash: float = 10000.0,
    price_map: dict[str, str] | None = None,
    periods_per_year: float = 365.0,
    **bt_kwargs: object,
) -> SplitResult:
    """前 train_frac 訓練 / 後段驗證,**一段連續**跑(不重建),boundary 切。"""
    pm = price_map or DEFAULT_PRICE_MAP
    all_ts = sorted({ts for rows in series.values() for ts, _ in rows})
    split_ts = all_ts[int(len(all_ts) * train_frac)]

    run = _run(series, factory, initial_cash=initial_cash, price_map=pm, **bt_kwargs)
    is_sh = _curve_sharpe(run.equity_curve, end=split_ts, periods_per_year=periods_per_year)
    oos_sh = _curve_sharpe(run.equity_curve, start=split_ts, periods_per_year=periods_per_year)
    oos_trades = sum(1 for f in run.fills if f.ts >= split_ts)
    oos_eq = daily_equity([(t, e) for t, e in run.equity_curve if t >= split_ts])
    oos_ret = (oos_eq[-1] / oos_eq[0] - 1.0) if len(oos_eq) >= 2 and oos_eq[0] > 0 else 0.0

    return SplitResult(
        split_ts=split_ts, is_sharpe=is_sh, oos_sharpe=oos_sh,
        wfe=(oos_sh / is_sh if is_sh > 0 else float("nan")),
        oos_trades=oos_trades, oos_return=oos_ret,
    )
