"""V2-S1 Donchian breakout 測試:通道邏輯 / 進出場狀態機 / 暖機自管 /
long-only / 整合進 Backtest(合成日線 Bar 序列)。"""
from datetime import datetime, timedelta

import pytest

from v2.data import BacktestReplayDriver, LKVStore, DataEvent, build_snapshot
from v2.engine import Backtest
from v2.interfaces import Bar, NoOpParams, NoOpPortfolioStrategy
from v2.strategies import DonchianBreakout, DonchianParams
from v2.testing import make_bar_series

D0 = datetime(2026, 1, 1)


def day(i: int) -> datetime:
    return D0 + timedelta(days=i)


def feed(strat: DonchianBreakout, closes, field="BTC_kline_1d", hl=0.0):
    """直接逐根餵 on_bar(繞過 dispatcher),回每根的 target。"""
    store = LKVStore()
    targets = []
    for i, c in enumerate(closes):
        bar = Bar(open=c, high=c + hl, low=c - hl, close=c)
        store.update(DataEvent(field=field, value=bar, ts=day(i)))
        snap = build_snapshot(store, [field], now=day(i))
        out = strat.on_bar(snap)
        targets.append(out[strat.params.symbol])
    return targets


# ---- 通道邏輯 / 狀態機 ----


def test_no_signal_during_warmup():
    # entry=20:前 20 根(buffer 未滿 20)不該進場,即使一直漲
    s = DonchianBreakout(DonchianParams(symbol="BTC", entry=20, exit=10))
    closes = [100 + i for i in range(20)]  # 持續漲但 buffer 還沒滿 20
    targets = feed(s, closes)
    assert all(t == 0.0 for t in targets)  # 暖機期全 flat


def test_entry_on_breakout_above_channel():
    s = DonchianBreakout(DonchianParams(symbol="BTC", entry=5, exit=3))
    # 5 根 ranging 100,第 6 根突破 > 過去 5 日高(100)→ 進場
    closes = [100, 100, 100, 100, 100, 101]
    targets = feed(s, closes)
    assert targets[:5] == [0, 0, 0, 0, 0]  # 暖機 + 無突破
    assert targets[5] == 1.0               # 101 > max(過去5日=100)→ 開多


def test_no_entry_if_not_exceeding_channel():
    s = DonchianBreakout(DonchianParams(symbol="BTC", entry=5, exit=3))
    closes = [100, 100, 100, 100, 100, 100]  # 第 6 根 = 100,不 > 100
    targets = feed(s, closes)
    assert targets[5] == 0.0  # 平盤不算突破(嚴格 >)


def test_exit_on_breakdown_below_channel():
    s = DonchianBreakout(DonchianParams(symbol="BTC", entry=3, exit=3))
    # 進場後跌破過去 3 日低 → 平倉
    closes = [100, 100, 100, 110, 109, 108, 90]
    targets = feed(s, closes)
    # day3 close 110 > max(過去3日 100) → 進場
    assert targets[3] == 1.0
    assert targets[4] == 1.0 and targets[5] == 1.0  # 持有
    # day6 close 90 < min(過去3日 low = 108) → 出場
    assert targets[6] == 0.0


def test_hold_position_between_entry_and_exit():
    s = DonchianBreakout(DonchianParams(symbol="BTC", entry=3, exit=3))
    closes = [100, 100, 100, 110, 111, 112, 113]  # 進場後續漲,不出場
    targets = feed(s, closes)
    assert targets[3] == 1.0
    assert targets[4:] == [1.0, 1.0, 1.0]  # 一路持有


def test_reentry_after_exit():
    s = DonchianBreakout(DonchianParams(symbol="BTC", entry=3, exit=3))
    closes = [100, 100, 100, 110, 105, 90, 100, 100, 130]
    targets = feed(s, closes)
    assert targets[3] == 1.0           # 進場
    assert targets[5] == 0.0           # 跌破出場
    # 之後再突破 → 再進場
    assert targets[8] == 1.0


def test_entry_uses_high_not_close():
    # 通道用 high(不是 close)→ 過去某根 high 很高,close 要超過 high 才進
    s = DonchianBreakout(DonchianParams(symbol="BTC", entry=3, exit=3))
    store = LKVStore()
    # 3 根:close 100 但 high 120(長上影)
    bars = [Bar(open=100, high=120, low=99, close=100) for _ in range(3)]
    bars.append(Bar(open=100, high=115, low=100, close=115))  # close 115 < 過去high 120
    targets = []
    for i, b in enumerate(bars):
        store.update(DataEvent(field="BTC_kline_1d", value=b, ts=day(i)))
        snap = build_snapshot(store, ["BTC_kline_1d"], now=day(i))
        targets.append(s.on_bar(snap)["BTC"])
    assert targets[3] == 0.0  # 115 沒突破過去 high 120 → 不進場


def test_state_serializable():
    s = DonchianBreakout(DonchianParams(entry=3, exit=3))
    feed(s, [100, 100, 100, 110])
    st = s.get_state()
    assert st.in_position is True
    assert len(st.highs) == 3  # capped at entry


# ---- 整合進 Backtest(合成日線 Bar 序列)----


def _btc_price_map():
    return {"BTC": "BTC_kline_1d", "ETH": "ETH_kline_1d"}


def test_donchian_in_backtest_enters_and_holds():
    bt = Backtest(initial_cash=10000, price_map=_btc_price_map(),
                  cooling=timedelta(0), dead_band=0.0)
    bt.add_symbol(DonchianBreakout(DonchianParams(symbol="BTC", entry=5, exit=3)))
    bt.add_portfolio(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC"])))

    # ranging 然後突破上漲
    closes = [100] * 6 + [110, 115, 120, 125]
    series = {"BTC_kline_1d": make_bar_series("BTC_kline_1d", D0, closes)}
    result = bt.run(BacktestReplayDriver(series))

    assert result.fills, "突破後該有進場成交"
    assert result.final_state.positions.get("BTC", 0) > 0  # 持有多單
    assert result.fingerprint


def test_donchian_in_backtest_exits_on_breakdown():
    bt = Backtest(initial_cash=10000, price_map=_btc_price_map(),
                  cooling=timedelta(0), dead_band=0.0)
    bt.add_symbol(DonchianBreakout(DonchianParams(symbol="BTC", entry=3, exit=3)))
    bt.add_portfolio(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC"])))

    # 進場上漲後崩跌破出場通道
    closes = [100, 100, 100, 120, 121, 122, 80, 80]
    series = {"BTC_kline_1d": make_bar_series("BTC_kline_1d", D0, closes)}
    result = bt.run(BacktestReplayDriver(series))

    # 最終應已平倉(跌破 exit 通道)
    assert result.final_state.positions.get("BTC", 0) == pytest.approx(0.0, abs=1e-9)


def test_donchian_btc_and_eth_independent_channels():
    # 兩個 instance(BTC / ETH)各自獨立通道
    bt = Backtest(initial_cash=10000, price_map=_btc_price_map(),
                  cooling=timedelta(0), dead_band=0.0)
    bt.add_symbol(DonchianBreakout(DonchianParams(symbol="BTC", entry=3, exit=3)))
    bt.add_symbol(DonchianBreakout(DonchianParams(symbol="ETH", entry=3, exit=3)))
    bt.add_portfolio(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC", "ETH"])))

    btc_closes = [100, 100, 100, 120, 121]   # BTC 突破
    eth_closes = [50, 50, 50, 49, 48]        # ETH 不突破
    series = {
        "BTC_kline_1d": make_bar_series("BTC_kline_1d", D0, btc_closes),
        "ETH_kline_1d": make_bar_series("ETH_kline_1d", D0, eth_closes),
    }
    result = bt.run(BacktestReplayDriver(series))
    assert result.final_state.positions.get("BTC", 0) > 0    # BTC 進場
    assert result.final_state.positions.get("ETH", 0) == pytest.approx(0, abs=1e-9)  # ETH 沒進


def test_donchian_backtest_deterministic():
    def run():
        bt = Backtest(initial_cash=10000, price_map=_btc_price_map())
        bt.add_symbol(DonchianBreakout(DonchianParams(symbol="BTC", entry=5, exit=3)))
        bt.add_portfolio(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC"])))
        closes = [100] * 6 + [110, 115, 120, 90, 80]
        series = {"BTC_kline_1d": make_bar_series("BTC_kline_1d", D0, closes)}
        return bt.run(BacktestReplayDriver(series)).fingerprint

    assert run() == run()  # M3 lock:同回測同指紋


# ---- 真資料 sanity check(CoinMetrics fixture,close-only;見 fixtures/build_fixture.py)----

from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[1] / "data" / "fixtures"
_has_fixtures = (FIXTURES / "btc_usd_1d.csv").exists() and (FIXTURES / "eth_usd_1d.csv").exists()

requires_fixtures = pytest.mark.skipif(not _has_fixtures, reason="real-data fixtures missing")


def _load_real():
    from v2.data import CsvLoader, build_replay_series
    return build_replay_series(
        CsvLoader(FIXTURES / "btc_usd_1d.csv", "BTC_kline_1d"),
        CsvLoader(FIXTURES / "eth_usd_1d.csv", "ETH_kline_1d"),
    )


@requires_fixtures
def test_fixture_loads_and_is_time_ordered():
    series = _load_real()
    btc, eth = series["BTC_kline_1d"], series["ETH_kline_1d"]
    # 範圍從 2019-01-01 起,長度 >= 2192(2019-2024 6 年最小);實際視最新更新而定
    assert len(btc) >= 2192
    assert len(eth) >= 2192
    assert len(btc) == len(eth), "BTC/ETH 同步抓應同範圍"
    for field, series_ in series.items():
        ts = [t for t, _ in series_]
        assert ts == sorted(ts), f"{field} 必須時間序(replay no-lookahead 前提)"
    # BTC 2019-01-01 ≈ $3800(真實歷史 sanity)
    assert 3000 < btc[0][1].close < 5000
    # 真 OHLC sanity:high >= close >= low(close-only fixture 退役驗證)
    sample = btc[100][1]
    assert sample.high >= sample.close >= sample.low
    assert sample.high > sample.low, "真 OHLC 該有日內波動"


@requires_fixtures
def test_donchian_real_data_sanity():
    """Donchian(entry=20/exit=10)跑真 BTC/ETH 2019-2024:不爆 + 進出場 +
    確定性 + 形狀合理(long-only 永遠 >=0,最終淨值 > 0)。"""
    series = _load_real()
    bt = Backtest(initial_cash=10000,
                  price_map={"BTC": "BTC_kline_1d", "ETH": "ETH_kline_1d"})
    bt.add_symbol(DonchianBreakout(DonchianParams(symbol="BTC", entry=20, exit=10)))
    bt.add_symbol(DonchianBreakout(DonchianParams(symbol="ETH", entry=20, exit=10)))
    bt.add_portfolio(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC", "ETH"])))
    res = bt.run(BacktestReplayDriver(series))

    n = len(series["BTC_kline_1d"]) + len(series["ETH_kline_1d"])
    assert res.fired_events == n
    assert len(res.fills) > 0, "多年真資料該有進出場成交"
    assert any(f.delta_qty > 0 for f in res.fills), "該有買進"
    assert any(f.delta_qty < 0 for f in res.fills), "該有賣出"
    # long-only:部位永不為負
    for sym, qty in res.final_state.positions.items():
        assert qty >= -1e-9, f"{sym} long-only 不該負部位"
    # 最終淨值 > 0(沒把帳戶跑爆)
    last_px = {"BTC": series["BTC_kline_1d"][-1][1].close,
               "ETH": series["ETH_kline_1d"][-1][1].close}
    assert res.final_state.equity(last_px) > 0
    assert res.fingerprint


@requires_fixtures
def test_donchian_real_data_deterministic():
    """真資料整場回測 M3 fingerprint 跨 run 可重現。"""
    def run():
        series = _load_real()
        bt = Backtest(initial_cash=10000,
                      price_map={"BTC": "BTC_kline_1d", "ETH": "ETH_kline_1d"})
        bt.add_symbol(DonchianBreakout(DonchianParams(symbol="BTC", entry=20, exit=10)))
        bt.add_symbol(DonchianBreakout(DonchianParams(symbol="ETH", entry=20, exit=10)))
        bt.add_portfolio(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC", "ETH"])))
        return bt.run(BacktestReplayDriver(series)).fingerprint

    assert run() == run()
