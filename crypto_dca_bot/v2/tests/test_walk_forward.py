"""T2 walk-forward runner 測試:日期/切窗工具釘死 + 合成資料滾動跑 +
single-split 對照 + determinism + 真資料整合(視窗數 / 兩法一致性)。"""
import math
from datetime import datetime

import pytest

from v2.analysis import (
    SplitResult,
    WalkForwardResult,
    add_months,
    single_split,
    slice_series,
    walk_forward,
    windows,
)
from v2.interfaces import NoOpParams, NoOpPortfolioStrategy
from v2.strategies import DonchianBreakout, DonchianParams
from v2.testing import make_bar_series

D0 = datetime(2019, 1, 1)


# ---- add_months ----


def test_add_months_basic():
    assert add_months(datetime(2020, 1, 15), 1) == datetime(2020, 2, 15)
    assert add_months(datetime(2020, 1, 15), 30) == datetime(2022, 7, 15)


def test_add_months_year_wrap():
    assert add_months(datetime(2020, 12, 10), 1) == datetime(2021, 1, 10)


def test_add_months_month_end_clamps():
    # 1/31 + 1mo → 2/29 (2020 閏) / 2/28 (2021)
    assert add_months(datetime(2020, 1, 31), 1) == datetime(2020, 2, 29)
    assert add_months(datetime(2021, 1, 31), 1) == datetime(2021, 2, 28)


# ---- slice_series(半開 [start,end))----


def _series(field, start, n):
    return {field: make_bar_series(field, start, [100.0 + i for i in range(n)])}


def test_slice_series_half_open():
    s = _series("BTC_kline_1d", D0, 10)  # D0..D0+9
    sl = slice_series(s, datetime(2019, 1, 3), datetime(2019, 1, 6))
    ts = [t for t, _ in sl["BTC_kline_1d"]]
    assert ts == [datetime(2019, 1, 3), datetime(2019, 1, 4), datetime(2019, 1, 5)]  # end 排除


# ---- windows 切窗數量 ----


def test_windows_count_exact():
    # 60 個月 span,IS=30 OOS=3 step=3 → 10 窗(is_start 0,3,...,27)
    s = {"BTC_kline_1d": [(D0, None), (datetime(2024, 1, 1), None)]}  # 只看 span
    w = windows(s, is_months=30, oos_months=3, step_months=3)
    assert len(w) == 10
    assert w[0] == (D0, datetime(2021, 7, 1), datetime(2021, 10, 1))
    # 最後一窗 OOS 須在資料內
    assert w[-1][2] <= datetime(2024, 1, 1)


def test_windows_none_when_too_short():
    s = {"BTC_kline_1d": [(D0, None), (datetime(2020, 1, 1), None)]}  # 12mo < IS+OOS
    assert windows(s, is_months=30, oos_months=3, step_months=3) == []


# ---- walk_forward 合成跑 ----


def _donchian_factory():
    return (
        [DonchianBreakout(DonchianParams(symbol="BTC", entry=5, exit=3))],
        [NoOpPortfolioStrategy(NoOpParams(symbols=["BTC"]))],
    )


def _trending_series(n_days: int):
    # 鋸齒上升 → Donchian 會進出場(產生 OOS 交易)
    closes = []
    price = 100.0
    for i in range(n_days):
        price *= 1.01 if (i // 10) % 2 == 0 else 0.99
        closes.append(price)
    return {"BTC_kline_1d": make_bar_series("BTC_kline_1d", D0, closes)}


def test_walk_forward_produces_windows_and_aggregate():
    series = _trending_series(600)  # ~20 個月
    wf = walk_forward(series, _donchian_factory,
                      is_months=6, oos_months=3, step_months=3,
                      price_map={"BTC": "BTC_kline_1d"})
    assert isinstance(wf, WalkForwardResult)
    assert wf.n_windows >= 3
    assert wf.total_oos_trades == sum(w.oos_trades for w in wf.windows)
    # WFE = pooled_oos / mean_is(或 NaN 當 mean_is<=0)
    assert math.isfinite(wf.pooled_oos_sharpe)
    if wf.mean_is_sharpe > 0:
        assert wf.wfe_pooled == pytest.approx(wf.pooled_oos_sharpe / wf.mean_is_sharpe)


def test_walk_forward_deterministic():
    series = _trending_series(600)
    a = walk_forward(series, _donchian_factory, is_months=6, oos_months=3,
                     step_months=3, price_map={"BTC": "BTC_kline_1d"})
    b = walk_forward(series, _donchian_factory, is_months=6, oos_months=3,
                     step_months=3, price_map={"BTC": "BTC_kline_1d"})
    assert a.wfe_pooled == b.wfe_pooled or (math.isnan(a.wfe_pooled) and math.isnan(b.wfe_pooled))
    assert a.pooled_oos_sharpe == b.pooled_oos_sharpe
    assert [w.oos_trades for w in a.windows] == [w.oos_trades for w in b.windows]


def test_walk_forward_oos_windows_are_contiguous_non_overlapping():
    """OOS 段時間連續、不重疊(pooled 拼報酬的前提)。"""
    series = _trending_series(600)
    wf = walk_forward(series, _donchian_factory, is_months=6, oos_months=3,
                      step_months=3, price_map={"BTC": "BTC_kline_1d"})
    for prev, nxt in zip(wf.windows, wf.windows[1:]):
        assert nxt.oos_start == prev.oos_end  # 接續,不重疊


# ---- single_split 對照 ----


def test_single_split_structure():
    series = _trending_series(600)
    sp = single_split(series, _donchian_factory, train_frac=0.7,
                      price_map={"BTC": "BTC_kline_1d"})
    assert isinstance(sp, SplitResult)
    assert sp.split_ts > D0
    assert math.isfinite(sp.is_sharpe)
    if sp.is_sharpe > 0:
        assert sp.wfe == pytest.approx(sp.oos_sharpe / sp.is_sharpe)


def test_single_split_deterministic():
    series = _trending_series(600)
    a = single_split(series, _donchian_factory, price_map={"BTC": "BTC_kline_1d"})
    b = single_split(series, _donchian_factory, price_map={"BTC": "BTC_kline_1d"})
    assert a == b


# ---- 真資料整合 ----

from pathlib import Path

from v2.data import CsvLoader

FIXTURES = Path(__file__).resolve().parents[1] / "data" / "fixtures"
_has = (FIXTURES / "btc_usd_1d.csv").exists() and (FIXTURES / "eth_usd_1d.csv").exists()
requires_fixtures = pytest.mark.skipif(not _has, reason="real-data fixtures missing")


def _real_kline():
    return {
        "BTC_kline_1d": CsvLoader(FIXTURES / "btc_usd_1d.csv", "BTC_kline_1d").fetch(),
        "ETH_kline_1d": CsvLoader(FIXTURES / "eth_usd_1d.csv", "ETH_kline_1d").fetch(),
    }


def _real_donchian_factory():
    return (
        [DonchianBreakout(DonchianParams(symbol="BTC", entry=20, exit=10)),
         DonchianBreakout(DonchianParams(symbol="ETH", entry=20, exit=10))],
        [NoOpPortfolioStrategy(NoOpParams(symbols=["BTC", "ETH"]))],
    )


@requires_fixtures
def test_walk_forward_real_data_window_count_and_pooled():
    series = _real_kline()
    wf = walk_forward(series, _real_donchian_factory,
                      price_map={"BTC": "BTC_kline_1d", "ETH": "ETH_kline_1d"})
    assert wf.n_windows == 19          # 7.45 年 / 30-3-3
    assert wf.total_oos_trades > 30    # aggregate 夠(per-window 少但拼起來夠)
    assert math.isfinite(wf.pooled_oos_sharpe)
    assert math.isfinite(wf.wfe_pooled)
    # in-sample 多年 Donchian 該有正 IS Sharpe
    assert wf.mean_is_sharpe > 0


@requires_fixtures
def test_real_data_two_methods_agree_on_gate():
    """拍板的交叉驗證:pooled 與 single-split 對 M2 閘(>50%)結論該一致。"""
    series = _real_kline()
    pm = {"BTC": "BTC_kline_1d", "ETH": "ETH_kline_1d"}
    wf = walk_forward(series, _real_donchian_factory, price_map=pm)
    sp = single_split(series, _real_donchian_factory, price_map=pm)
    # Donchian 2019-2026 OOS 退化 → 兩法都該 FAIL(<50%)
    assert wf.wfe_pooled < 0.50
    assert sp.wfe < 0.50
