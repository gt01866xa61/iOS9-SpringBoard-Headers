"""Regime 診斷測試:ER / net_return / classify 釘死 + bucket_windows 分桶。"""
from dataclasses import dataclass
from datetime import datetime

import pytest

from v2.analysis import (
    CHOP,
    DOWN,
    UP,
    bucket_windows,
    classify,
    closes_in_range,
    efficiency_ratio,
    net_return,
)


# ---- efficiency ratio ----


def test_er_straight_line_is_one():
    assert efficiency_ratio([1, 2, 3, 4]) == pytest.approx(1.0)


def test_er_round_trip_is_zero():
    # 漲回原點:淨變動 0 → ER 0
    assert efficiency_ratio([1, 2, 1, 2, 1]) == 0.0


def test_er_choppy_partial():
    # net=2, path=|11-10|+|9-11|+|12-9| = 1+2+3 = 6 → 2/6
    assert efficiency_ratio([10, 11, 9, 12]) == pytest.approx(2 / 6)


def test_er_too_short_zero():
    assert efficiency_ratio([5]) == 0.0
    assert efficiency_ratio([]) == 0.0


# ---- net return ----


def test_net_return_basic():
    assert net_return([100, 150]) == pytest.approx(0.5)
    assert net_return([100, 80]) == pytest.approx(-0.2)


def test_net_return_short_zero():
    assert net_return([100]) == 0.0


# ---- classify ----


def test_classify_up_down_chop():
    assert classify(0.20) == UP
    assert classify(-0.20) == DOWN
    assert classify(0.05) == CHOP
    assert classify(-0.10) == CHOP


def test_classify_threshold_boundary_is_chop():
    # 邊界(== threshold)算盤整(嚴格 >)
    assert classify(0.15) == CHOP
    assert classify(-0.15) == CHOP
    assert classify(0.151) == UP


def test_classify_custom_threshold():
    assert classify(0.10, trend_threshold=0.05) == UP


# ---- closes_in_range ----


def test_closes_in_range_half_open_and_bar_or_float():
    @dataclass
    class B:
        close: float

    series = [(datetime(2026, 1, i), B(close=float(i))) for i in range(1, 6)]
    cs = closes_in_range(series, datetime(2026, 1, 2), datetime(2026, 1, 4))
    assert cs == [2.0, 3.0]  # end 排除
    # float value 也吃
    fseries = [(datetime(2026, 1, 1), 9.0), (datetime(2026, 1, 2), 8.0)]
    assert closes_in_range(fseries, datetime(2026, 1, 1), datetime(2026, 1, 3)) == [9.0, 8.0]


# ---- bucket_windows ----


@dataclass
class FakeWindow:
    oos_start: datetime
    oos_end: datetime
    oos_return: float


def _mk_price(start: datetime, days: int, daily_factor: float):
    return [(datetime(start.year, start.month, start.day + i), 100.0 * daily_factor**i)
            for i in range(days)]


def test_bucket_windows_groups_by_market_regime():
    # 兩個視窗:一個市場上升(+>15%)、一個盤整(~0)
    w_up = FakeWindow(datetime(2026, 1, 1), datetime(2026, 1, 11), oos_return=0.10)
    w_chop = FakeWindow(datetime(2026, 2, 1), datetime(2026, 2, 11), oos_return=-0.05)
    # 上升市場價格(每日 +3% 連10天 ≈ +30%)
    up_px = _mk_price(datetime(2026, 1, 1), 10, 1.03)
    # 盤整市場(回原點)
    chop_px = [(datetime(2026, 2, 1 + i), 100.0 + (5 if i % 2 else 0)) for i in range(10)]
    series = up_px + chop_px

    buckets = bucket_windows([w_up, w_chop], series)
    assert buckets[UP].n_windows == 1
    assert buckets[UP].mean_oos_return == pytest.approx(0.10)
    assert buckets[UP].win_rate == 1.0
    assert buckets[CHOP].n_windows == 1
    assert buckets[CHOP].mean_oos_return == pytest.approx(-0.05)
    assert buckets[CHOP].win_rate == 0.0
    assert buckets[DOWN].n_windows == 0


def test_bucket_windows_winrate_and_mean():
    # 三個都落在上升市場 → 同桶,驗 mean / win_rate 聚合
    px = _mk_price(datetime(2026, 1, 1), 12, 1.03)  # +>15%
    wins = [
        FakeWindow(datetime(2026, 1, 1), datetime(2026, 1, 13), 0.2),
        FakeWindow(datetime(2026, 1, 1), datetime(2026, 1, 13), -0.1),
        FakeWindow(datetime(2026, 1, 1), datetime(2026, 1, 13), 0.3),
    ]
    b = bucket_windows(wins, px)[UP]
    assert b.n_windows == 3
    assert b.mean_oos_return == pytest.approx((0.2 - 0.1 + 0.3) / 3)
    assert b.win_rate == pytest.approx(2 / 3)
