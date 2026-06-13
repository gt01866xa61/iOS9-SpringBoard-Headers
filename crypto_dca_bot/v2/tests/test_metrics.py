"""T1 績效指標層測試:用已知曲線手算釘死 Sharpe / Sortino / maxDD / Calmar /
滾動 Sharpe / equity-curve 轉換,加上真資料 backtest 整合 sanity。"""
import math
from datetime import datetime, timedelta

import pytest

from v2.analysis import (
    PerformanceMetrics,
    cagr,
    calmar,
    compute_metrics,
    daily_equity,
    equity_returns,
    max_drawdown,
    metrics_from_curve,
    rolling_sharpe,
    sharpe,
    sortino,
)


# ---- equity → returns ----


def test_equity_returns_basic():
    r = equity_returns([100, 110, 99])
    assert r == pytest.approx([0.1, -0.1])


def test_equity_returns_length():
    assert len(equity_returns([1, 2, 3, 4, 5])) == 4


def test_equity_returns_guards_nonpositive_prev():
    # e_{t-1} <= 0 → 該期報酬 0(不爆)
    assert equity_returns([0, 10]) == [0.0]
    assert equity_returns([-5, 10]) == [0.0]


# ---- Sharpe ----


def test_sharpe_known_value():
    # mean=0.01, pstdev=0.02 → 0.5 × sqrt(252)
    s = sharpe([0.03, -0.01, 0.03, -0.01], periods_per_year=252)
    assert s == pytest.approx(0.5 * math.sqrt(252), rel=1e-9)


def test_sharpe_zero_mean_is_zero():
    assert sharpe([0.01, -0.01, 0.01, -0.01]) == 0.0


def test_sharpe_constant_positive_is_inf():
    # 零波動正報酬 = 無限 risk-adjusted(數學誠實約定)
    assert sharpe([0.02, 0.02, 0.02]) == math.inf


def test_sharpe_constant_negative_is_neg_inf():
    assert sharpe([-0.02, -0.02, -0.02]) == -math.inf


def test_sharpe_too_few_returns_is_zero():
    assert sharpe([0.05]) == 0.0
    assert sharpe([]) == 0.0


def test_sharpe_risk_free_lowers_it():
    rets = [0.03, -0.01, 0.03, -0.01]
    assert sharpe(rets, periods_per_year=252, risk_free=0.10) < sharpe(
        rets, periods_per_year=252
    )


# ---- Sortino ----


def test_sortino_known_value():
    # downside_dev = sqrt(mean([0, .0001, 0, .0001])) = sqrt(0.00005)
    s = sortino([0.03, -0.01, 0.03, -0.01], periods_per_year=252)
    assert s == pytest.approx(0.01 / math.sqrt(0.00005) * math.sqrt(252), rel=1e-9)


def test_sortino_no_downside_is_inf():
    assert sortino([0.01, 0.02, 0.0]) == math.inf  # 無嚴格負報酬


def test_sortino_ge_sharpe_when_downside_concentrated():
    # 同一序列 Sortino 通常 > Sharpe(只罰下行)
    rets = [0.03, -0.01, 0.03, -0.01]
    assert sortino(rets, periods_per_year=252) > sharpe(rets, periods_per_year=252)


# ---- max drawdown ----


def test_max_drawdown_known():
    # peak 120 → trough 80 → (120-80)/120 = 1/3
    assert max_drawdown([100, 120, 90, 110, 80]) == pytest.approx(1 / 3)


def test_max_drawdown_monotone_up_is_zero():
    assert max_drawdown([100, 101, 102, 200]) == 0.0


def test_max_drawdown_single_point_zero():
    assert max_drawdown([100]) == 0.0


# ---- CAGR / Calmar ----


def test_cagr_doubling_over_one_year():
    # 365 個日報酬使資產翻倍 → CAGR ≈ 100%
    eq = [100.0 * (2 ** (i / 365)) for i in range(366)]
    assert cagr(eq, periods_per_year=365) == pytest.approx(1.0, rel=1e-9)


def test_cagr_too_short_zero():
    assert cagr([100]) == 0.0


def test_calmar_is_cagr_over_maxdd():
    eq = [100.0 * (2 ** (i / 365)) for i in range(366)]  # 單調漲 → maxDD 0
    # 單調漲 maxDD=0 → Calmar = +inf(CAGR>0)
    assert calmar(eq, periods_per_year=365) == math.inf


def test_calmar_finite_with_drawdown():
    eq = [100, 120, 90, 110, 80, 130]
    c = calmar(eq, periods_per_year=365)
    expect = cagr(eq, periods_per_year=365) / max_drawdown(eq)
    assert c == pytest.approx(expect)


# ---- rolling Sharpe ----


def test_rolling_sharpe_length_and_windows():
    rets = [0.01, 0.02, -0.01, 0.03, 0.0]
    rs = rolling_sharpe(rets, 3)
    assert len(rs) == 3  # 5 - 3 + 1
    # 每個元素 = 對應窗的 sharpe
    assert rs[0] == sharpe(rets[0:3])
    assert rs[-1] == sharpe(rets[2:5])


def test_rolling_sharpe_window_too_big_empty():
    assert rolling_sharpe([0.01, 0.02], 5) == []


# ---- equity curve 轉換 ----


def test_daily_equity_takes_last_per_day():
    d0 = datetime(2026, 1, 1)
    curve = [
        (d0, 100.0),
        (d0 + timedelta(hours=8), 105.0),
        (d0 + timedelta(hours=16), 102.0),  # 同日後到 → 當日收盤 102
        (d0 + timedelta(days=1), 110.0),
    ]
    assert daily_equity(curve) == [102.0, 110.0]


def test_daily_equity_sorted_by_date():
    d0 = datetime(2026, 1, 5)
    curve = [(d0 + timedelta(days=2), 3.0), (d0, 1.0), (d0 + timedelta(days=1), 2.0)]
    assert daily_equity(curve) == [1.0, 2.0, 3.0]


# ---- compute_metrics 彙總 ----


def test_compute_metrics_fields_consistent():
    eq = [100, 120, 90, 110, 80, 130]
    pm = compute_metrics(eq, periods_per_year=365)
    assert isinstance(pm, PerformanceMetrics)
    assert pm.n_periods == 5
    assert pm.total_return == pytest.approx(130 / 100 - 1)
    assert pm.max_drawdown == pytest.approx(max_drawdown(eq))
    assert pm.cagr == pytest.approx(cagr(eq, periods_per_year=365))
    assert pm.sharpe == pytest.approx(sharpe(equity_returns(eq), periods_per_year=365))


def test_compute_metrics_degenerate_short():
    pm = compute_metrics([100])
    assert pm == PerformanceMetrics(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


def test_metrics_from_curve_resamples_then_computes():
    d0 = datetime(2026, 1, 1)
    curve = [(d0 + timedelta(days=i), 100.0 + i) for i in range(5)]
    pm = metrics_from_curve(curve, periods_per_year=365)
    assert pm.n_periods == 4  # 5 日 → 4 報酬
    assert pm.total_return == pytest.approx(104 / 100 - 1)


# ---- 整合:真資料 backtest 的 equity_curve 算得出合理指標 ----

from pathlib import Path

from v2.data import BacktestReplayDriver, CsvLoader
from v2.engine import Backtest
from v2.interfaces import NoOpParams, NoOpPortfolioStrategy
from v2.strategies import DonchianBreakout, DonchianParams

FIXTURES = Path(__file__).resolve().parents[1] / "data" / "fixtures"
_has = (FIXTURES / "btc_usd_1d.csv").exists() and (FIXTURES / "eth_usd_1d.csv").exists()
requires_fixtures = pytest.mark.skipif(not _has, reason="real-data fixtures missing")


@requires_fixtures
def test_backtest_emits_equity_curve_and_metrics_sane():
    series = {
        "BTC_kline_1d": CsvLoader(FIXTURES / "btc_usd_1d.csv", "BTC_kline_1d").fetch(),
        "ETH_kline_1d": CsvLoader(FIXTURES / "eth_usd_1d.csv", "ETH_kline_1d").fetch(),
    }
    bt = Backtest(initial_cash=10000, price_map={"BTC": "BTC_kline_1d", "ETH": "ETH_kline_1d"})
    bt.add_symbol(DonchianBreakout(DonchianParams(symbol="BTC", entry=20, exit=10)))
    bt.add_symbol(DonchianBreakout(DonchianParams(symbol="ETH", entry=20, exit=10)))
    bt.add_portfolio(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC", "ETH"])))
    res = bt.run(BacktestReplayDriver(series))

    assert res.equity_curve, "應記到 mark-to-market equity 曲線"
    # 時間序(no-lookahead 前提 + daily resample 正確性)
    ts = [t for t, _ in res.equity_curve]
    assert ts == sorted(ts)

    pm = metrics_from_curve(res.equity_curve)
    assert pm.n_periods > 100              # 多年資料
    assert 0.0 <= pm.max_drawdown < 1.0    # crypto 大回撤但沒歸零
    assert math.isfinite(pm.sharpe)
    assert math.isfinite(pm.sortino) or pm.sortino == math.inf


@requires_fixtures
def test_metrics_deterministic_across_runs():
    def run():
        series = {
            "BTC_kline_1d": CsvLoader(FIXTURES / "btc_usd_1d.csv", "BTC_kline_1d").fetch(),
            "ETH_kline_1d": CsvLoader(FIXTURES / "eth_usd_1d.csv", "ETH_kline_1d").fetch(),
        }
        bt = Backtest(initial_cash=10000,
                      price_map={"BTC": "BTC_kline_1d", "ETH": "ETH_kline_1d"})
        bt.add_symbol(DonchianBreakout(DonchianParams(symbol="BTC", entry=20, exit=10)))
        bt.add_symbol(DonchianBreakout(DonchianParams(symbol="ETH", entry=20, exit=10)))
        bt.add_portfolio(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC", "ETH"])))
        return metrics_from_curve(bt.run(BacktestReplayDriver(series)).equity_curve)

    assert run() == run()  # M3 風味:同回測同指標
