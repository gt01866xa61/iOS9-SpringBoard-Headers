"""T1 績效指標層:從 equity curve 算 risk-adjusted 績效。

ref: v2t_prereqs.md T1。M2-M7 拍閘要的指標:
- Sharpe(年化 risk-adjusted return)
- Sortino(只罰下行波動的 risk-adjusted)
- max drawdown(最大回撤)
- Calmar(年化報酬 / max DD)
- 滾動 Sharpe(window-by-window,M7 退役監控用)
- (WFE = OOS Sharpe / IS Sharpe 由 T2 walk-forward 用這裡的 sharpe() 組)

設計原則:
- **純函式 + 可釘死**:輸入 equity / returns,輸出數字,無隨機、無 I/O。test
  用已知曲線手算驗證。
- **純 Python**(stdlib statistics)— 對齊 codebase 無 numpy 風格 + 確定性。
- **std 用 population(ddof=0)**:刻意選擇。理由:(a) 績效數字主要拿來做
  **相對比較**(WFE 比值 / 閘門檻),ddof 在多點時影響可忽略;(b) population
  邊界行為乾淨(單點不炸);(c) 釘死測試數字漂亮。文件化,別日後當 bug。
- **年化**:crypto 無休市 → 日頻 `PERIODS_PER_YEAR_DAILY = 365`。equity curve
  先 resample 成日頻(每日最後一筆)再算,讓不規則 event(日線 + 8h funding)
  的報酬可比、年化有定義。

degenerate 約定(寫死,免得日後困惑):
- 報酬數 < 2 → 所有比率回 0.0(樣本不足)
- std == 0(報酬全相等):mean == 0 → 0.0;mean != 0 → ±inf(數學誠實:零波動
  正報酬 = 無限 risk-adjusted)。Sortino 同理(無下行 → +inf)。
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from statistics import mean, pstdev

PERIODS_PER_YEAR_DAILY = 365.0  # crypto 24/7,無休市


# ---------------------------------------------------------------------------
# 基礎轉換
# ---------------------------------------------------------------------------

def equity_returns(equity: list[float]) -> list[float]:
    """連續 equity → 簡單週期報酬 r_t = e_t / e_{t-1} − 1(長度 = n−1)。

    e_{t-1} <= 0(帳戶歸零/負)→ 該期報酬記 0.0(無可靠報酬資訊,不爆)。
    """
    out: list[float] = []
    for prev, cur in zip(equity, equity[1:]):
        out.append(cur / prev - 1.0 if prev > 0 else 0.0)
    return out


def daily_equity(curve: list[tuple[datetime, float]]) -> list[float]:
    """(ts, equity) 序列 → 日頻 equity(每日最後一筆;curve 須時間序)。

    不規則 event(日線 + 8h funding)→ 每日取最後一個 equity 觀測,讓報酬
    年化有定義。回傳 equity 值序列(已按日期排序)。
    """
    by_day: dict[object, float] = {}
    for ts, eq in curve:
        by_day[ts.date()] = eq  # 同日後到的覆蓋前面 → 當日收盤 equity
    return [by_day[d] for d in sorted(by_day)]


# ---------------------------------------------------------------------------
# 核心指標(純函式)
# ---------------------------------------------------------------------------

def _annualized_ratio(numer_per_period: float, denom: float, periods_per_year: float) -> float:
    """mean/denom × sqrt(ppy),含 degenerate 約定。"""
    if denom == 0.0:
        if numer_per_period == 0.0:
            return 0.0
        return math.copysign(math.inf, numer_per_period)
    return numer_per_period / denom * math.sqrt(periods_per_year)


def sharpe(
    returns: list[float],
    *,
    periods_per_year: float = PERIODS_PER_YEAR_DAILY,
    risk_free: float = 0.0,
) -> float:
    """年化 Sharpe = mean(excess) / std(returns) × sqrt(ppy)。

    risk_free 為**年化**無風險利率,內部轉成每期(/ppy)扣掉。
    """
    if len(returns) < 2:
        return 0.0
    rf_per = risk_free / periods_per_year
    excess = [r - rf_per for r in returns]
    return _annualized_ratio(mean(excess), pstdev(excess), periods_per_year)


def sortino(
    returns: list[float],
    *,
    periods_per_year: float = PERIODS_PER_YEAR_DAILY,
    risk_free: float = 0.0,
) -> float:
    """年化 Sortino = mean(excess) / downside_deviation × sqrt(ppy)。

    downside_deviation = sqrt(mean(min(0, excess)^2))(分母用**全部**期數,
    target downside deviation 慣例)。無下行 → 分母 0 → +inf。
    """
    if len(returns) < 2:
        return 0.0
    rf_per = risk_free / periods_per_year
    excess = [r - rf_per for r in returns]
    downside = math.sqrt(mean(min(0.0, e) ** 2 for e in excess))
    return _annualized_ratio(mean(excess), downside, periods_per_year)


def max_drawdown(equity: list[float]) -> float:
    """最大回撤(正分數,0=無回撤,0.33=從高點跌三分之一)。

    maxDD = max_t (peak_so_far − e_t) / peak_so_far。
    """
    if len(equity) < 2:
        return 0.0
    peak = equity[0]
    mdd = 0.0
    for e in equity:
        if e > peak:
            peak = e
        if peak > 0:
            mdd = max(mdd, (peak - e) / peak)
    return mdd


def cagr(equity: list[float], *, periods_per_year: float = PERIODS_PER_YEAR_DAILY) -> float:
    """年化複合報酬 = (e_end / e_start) ^ (ppy / n_periods) − 1。"""
    if len(equity) < 2 or equity[0] <= 0:
        return 0.0
    n_periods = len(equity) - 1
    growth = equity[-1] / equity[0]
    if growth <= 0:
        return -1.0  # 全部賠光
    return growth ** (periods_per_year / n_periods) - 1.0


def calmar(equity: list[float], *, periods_per_year: float = PERIODS_PER_YEAR_DAILY) -> float:
    """Calmar = CAGR / maxDD(無回撤 → ±inf,依 CAGR 正負)。"""
    mdd = max_drawdown(equity)
    c = cagr(equity, periods_per_year=periods_per_year)
    if mdd == 0.0:
        if c == 0.0:
            return 0.0
        return math.copysign(math.inf, c)
    return c / mdd


def rolling_sharpe(
    returns: list[float],
    window: int,
    *,
    periods_per_year: float = PERIODS_PER_YEAR_DAILY,
    risk_free: float = 0.0,
) -> list[float]:
    """滑窗年化 Sharpe(M7 退役監控:連 N 窗 < backtest 50% → 退役)。

    回傳長度 = len(returns) − window + 1(不足一窗 → 空)。
    """
    if window < 2 or len(returns) < window:
        return []
    return [
        sharpe(returns[i : i + window], periods_per_year=periods_per_year, risk_free=risk_free)
        for i in range(len(returns) - window + 1)
    ]


# ---------------------------------------------------------------------------
# 彙總
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PerformanceMetrics:
    n_periods: int           # 報酬期數(= len(equity) − 1)
    total_return: float      # e_end / e_start − 1
    cagr: float
    sharpe: float
    sortino: float
    max_drawdown: float
    calmar: float


def compute_metrics(
    equity: list[float],
    *,
    periods_per_year: float = PERIODS_PER_YEAR_DAILY,
    risk_free: float = 0.0,
) -> PerformanceMetrics:
    """一次算齊。equity = 已 resample 的 equity 值序列(時間序)。"""
    if len(equity) < 2 or equity[0] <= 0:
        return PerformanceMetrics(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    rets = equity_returns(equity)
    return PerformanceMetrics(
        n_periods=len(rets),
        total_return=equity[-1] / equity[0] - 1.0,
        cagr=cagr(equity, periods_per_year=periods_per_year),
        sharpe=sharpe(rets, periods_per_year=periods_per_year, risk_free=risk_free),
        sortino=sortino(rets, periods_per_year=periods_per_year, risk_free=risk_free),
        max_drawdown=max_drawdown(equity),
        calmar=calmar(equity, periods_per_year=periods_per_year),
    )


def metrics_from_curve(
    curve: list[tuple[datetime, float]],
    *,
    periods_per_year: float = PERIODS_PER_YEAR_DAILY,
    risk_free: float = 0.0,
) -> PerformanceMetrics:
    """從 Backtest 的 (ts, equity) 曲線:先日頻 resample 再算齊。"""
    return compute_metrics(
        daily_equity(curve), periods_per_year=periods_per_year, risk_free=risk_free
    )
