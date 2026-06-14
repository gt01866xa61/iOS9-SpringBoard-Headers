"""V2-S3 MacroOverlay(真守門員 PortfolioStrategy)測試:

- overlay 邏輯:risk-off 門檻 / 多 indicator min 取最狠 / Bar+float level
- params validation
- ★ 整合:cap 真的套到 S1(Donchian)/ S2(FundingSkew)的下單上
- stale 時 framework 跳過 overlay → #3C fallback(缺席統一模型)
- LKV:VIX 週末不更新仍用 last known(staleness 容忍)
- 真資料 sanity:真 VIX(datahub)+ 真 BTC(CoinMetrics)2019-2024
"""
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from v2.data import BacktestReplayDriver, CsvLoader, LKVStore, DataEvent, build_snapshot
from v2.engine import Backtest, Dispatcher
from v2.interfaces import Bar, FieldSpec, NoOpParams, NoOpPortfolioStrategy
from v2.observability import MemorySink, kinds
from v2.strategies import (
    DonchianBreakout,
    DonchianParams,
    FundingSkew,
    FundingSkewParams,
    MacroIndicator,
    MacroOverlay,
    MacroOverlayParams,
)
from v2.testing import make_bar_series, make_funding_series

T0 = datetime(2026, 1, 1)


def t(hours: float) -> datetime:
    return T0 + timedelta(hours=hours)


def _snap_with(field_values: dict[str, object], now: datetime) -> "object":
    store = LKVStore()
    for f, v in field_values.items():
        store.update(DataEvent(field=f, value=v, ts=now))
    return build_snapshot(store, list(field_values), now=now)


# ---- params validation ----


def test_indicator_cap_in_range():
    with pytest.raises(ValidationError):
        MacroIndicator(field="vix_daily", risk_off_above=30, cap=1.5)


def test_params_need_indicators():
    with pytest.raises(ValidationError):
        MacroOverlayParams(indicators=[])


def test_params_need_symbols():
    with pytest.raises(ValidationError):
        MacroOverlayParams(symbols=[])


# ---- overlay 邏輯 ----


def test_calm_market_no_cap():
    ov = MacroOverlay(MacroOverlayParams(symbols=["BTC", "ETH"]))
    snap = _snap_with({"vix_daily": 18.0}, t(0))
    assert ov.on_bar(snap) == {"BTC": 1.0, "ETH": 1.0}  # VIX 18 < 30 → 放行


def test_risk_off_caps():
    ov = MacroOverlay(MacroOverlayParams(symbols=["BTC", "ETH"]))
    snap = _snap_with({"vix_daily": 45.0}, t(0))  # VIX 45 > 30 → risk off
    assert ov.on_bar(snap) == {"BTC": 0.5, "ETH": 0.5}


def test_level_reads_bar_close():
    ov = MacroOverlay(MacroOverlayParams(symbols=["BTC"]))
    snap = _snap_with({"vix_daily": Bar(open=20, high=46, low=20, close=45)}, t(0))
    assert ov.on_bar(snap)["BTC"] == 0.5  # 讀 close=45 > 30


def test_multi_indicator_min_takes_most_conservative():
    ov = MacroOverlay(MacroOverlayParams(
        symbols=["BTC"],
        indicators=[
            MacroIndicator(field="vix_daily", risk_off_above=30, cap=0.5),
            MacroIndicator(field="dxy_daily", risk_off_above=105, cap=0.3),
        ],
    ))
    # 兩個都 risk-off → 取 min(0.5, 0.3) = 0.3
    snap = _snap_with({"vix_daily": 40.0, "dxy_daily": 110.0}, t(0))
    assert ov.on_bar(snap)["BTC"] == 0.3
    # 只 VIX risk-off → 0.5
    snap2 = _snap_with({"vix_daily": 40.0, "dxy_daily": 100.0}, t(0))
    assert ov.on_bar(snap2)["BTC"] == 0.5


def test_missing_indicator_field_not_triggered():
    # dxy 還沒出現在 snapshot → 該 indicator 不觸發(只看 VIX)
    ov = MacroOverlay(MacroOverlayParams(
        symbols=["BTC"],
        indicators=[
            MacroIndicator(field="vix_daily", risk_off_above=30, cap=0.5),
            MacroIndicator(field="dxy_daily", risk_off_above=105, cap=0.3),
        ],
    ))
    snap = _snap_with({"vix_daily": 18.0}, t(0))  # 只有 vix,且 calm
    assert ov.on_bar(snap)["BTC"] == 1.0


def test_required_data_covers_all_indicators():
    ov = MacroOverlay(MacroOverlayParams(
        indicators=[
            MacroIndicator(field="vix_daily", risk_off_above=30, cap=0.5),
            MacroIndicator(field="dxy_daily", risk_off_above=105, cap=0.3),
        ],
    ))
    assert set(ov.required_data()) == {"vix_daily", "dxy_daily"}


# ---- ★ 整合:cap 真的套到 S1/S2 下單上 ----


def _btc_kline(closes, start=T0):
    return make_bar_series("BTC_kline_1d", start, closes)


def test_overlay_cap_flows_to_donchian_orders():
    """使用者點名:MacroOverlay 的 cap 真的把 S1(Donchian)的下單砍小。
    比較 risk-off vs calm 下同一 Donchian 進場的最終部位。"""

    def run(vix_level: float) -> float:
        bt = Backtest(initial_cash=10000, price_map={"BTC": "BTC_kline_1d"},
                      cooling=timedelta(0), dead_band=0.0)
        bt.add_symbol(DonchianBreakout(DonchianParams(symbol="BTC", entry=3, exit=2)))
        bt.add_portfolio(MacroOverlay(MacroOverlayParams(
            symbols=["BTC"],
            indicators=[MacroIndicator(field="vix_daily", risk_off_above=30, cap=0.5)],
        )))
        # BTC 突破上漲;VIX 固定 level(每日一筆,跟 kline 同步)
        closes = [100, 100, 100, 120, 130, 140]
        vix = make_bar_series("vix_daily", T0, [vix_level] * len(closes))
        series = {"BTC_kline_1d": _btc_kline(closes), "vix_daily": vix}
        res = bt.run(BacktestReplayDriver(series))
        return res.final_state.positions.get("BTC", 0.0)

    pos_calm = run(18.0)      # VIX calm → cap 1.0
    pos_riskoff = run(45.0)   # VIX 高 → cap 0.5
    assert pos_calm > 0
    assert pos_riskoff > 0
    # risk-off 部位該明顯小(被 cap 砍)— 證明 cap 流到下單
    assert pos_riskoff < pos_calm * 0.7


def test_overlay_cap_flows_to_funding_skew_orders():
    """同理驗 S2(FundingSkew):overlay cap 套到 funding 策略下單上。"""

    def run(vix_level: float) -> float:
        bt = Backtest(initial_cash=10000, price_map={"BTC": "BTC_kline_1d"},
                      cooling=timedelta(0), dead_band=0.0)
        bt.add_symbol(FundingSkew(FundingSkewParams(
            symbol="BTC", lookback_periods=2,
            low_threshold=0.00005, high_threshold=0.0003, dead_band=0)))
        bt.add_portfolio(MacroOverlay(MacroOverlayParams(
            symbols=["BTC"],
            indicators=[MacroIndicator(field="vix_daily", risk_off_above=30, cap=0.5)],
        )))
        # 持續低 funding → funding skew 滿倉;VIX 固定 level
        fundings = [0.0] * 8
        n_days = 5
        series = {
            "BTC_kline_1d": make_bar_series("BTC_kline_1d", T0, [50000] * n_days),
            "BTC_funding_8h": make_funding_series("BTC_funding_8h", T0, fundings),
            "vix_daily": make_bar_series("vix_daily", T0, [vix_level] * n_days),
        }
        res = bt.run(BacktestReplayDriver(series))
        return res.final_state.positions.get("BTC", 0.0)

    pos_calm = run(18.0)
    pos_riskoff = run(45.0)
    assert pos_calm > 0 and pos_riskoff > 0
    assert pos_riskoff < pos_calm * 0.7


# ---- stale → framework 跳過 overlay → #3C fallback(缺席統一模型)----


def test_stale_overlay_skipped_triggers_fallback():
    """VIX feed 斷流超過 max_staleness → overlay 被跳 → #3C fallback_cap 進 min 池。"""
    sink = MemorySink()
    d = Dispatcher(LKVStore(), sink)
    d.register(DonchianBreakout(DonchianParams(symbol="BTC", entry=2, exit=2)))
    d.register(MacroOverlay(MacroOverlayParams(symbols=["BTC"])))
    d.assert_startup_ok()

    # VIX 只給一次(t=0),之後 kline 連續多天 → VIX 終究超過 3d staleness
    d.on_event(DataEvent(field="vix_daily", value=18.0, ts=T0))
    fire = None
    for i in range(6):  # 連 6 天 kline,vix 早就 > 3d stale
        fire = d.on_event(DataEvent(field="BTC_kline_1d",
                                    value=Bar(open=100, high=100, low=100, close=100),
                                    ts=T0 + timedelta(days=i)))
    # 最後一次 fire:overlay 因 vix stale 被跳 → 在 absences
    assert "MacroOverlay" in fire.absences
    assert fire.absences["MacroOverlay"].reason == "stale"
    assert any(e.kind == kinds.SKIPPED_STALE and e.data.get("strategy") == "MacroOverlay"
               for e in sink.event_log)


def test_lkv_weekend_vix_tolerated():
    """VIX 週末不更新(1-2 天)在 3d 容忍內 → overlay 仍用 last known,不被跳。"""
    d = Dispatcher(LKVStore(), MemorySink())
    d.register(DonchianBreakout(DonchianParams(symbol="BTC", entry=2, exit=2)))
    d.register(MacroOverlay(MacroOverlayParams(symbols=["BTC"])))

    d.on_event(DataEvent(field="vix_daily", value=45.0, ts=T0))  # 週五 VIX 高
    # 週六、週日 BTC 照跑(crypto 24/7),VIX 1-2 天 stale < 3d → 不跳
    fire_sat = d.on_event(DataEvent(field="BTC_kline_1d",
                                    value=Bar(open=100, high=100, low=100, close=100),
                                    ts=T0 + timedelta(days=1)))
    assert "MacroOverlay" not in fire_sat.absences  # 沒被跳
    assert fire_sat.portfolio_outputs["MacroOverlay"]["BTC"] == 0.5  # 用週五 VIX 45 → cap


# ---- 真資料 sanity(真 VIX + 真 BTC,2019-2024)----

FIXTURES = Path(__file__).resolve().parents[1] / "data" / "fixtures"
_has = (FIXTURES / "vix_daily.csv").exists() and (FIXTURES / "btc_usd_1d.csv").exists()
requires_fixtures = pytest.mark.skipif(not _has, reason="vix/btc fixtures missing")


@requires_fixtures
def test_vix_fixture_loads_real_covid_spike():
    vix = CsvLoader(FIXTURES / "vix_daily.csv", "vix_daily").fetch()
    assert len(vix) == 1529  # 2019-2024 交易日
    by_date = {ts.date().isoformat(): bar for ts, bar in vix}
    # 2020-03-16 COVID:VIX 真實 close ≈ 82.69
    assert by_date["2020-03-16"].close > 80


@requires_fixtures
def test_macro_overlay_real_data_sanity():
    """真 VIX + 真 BTC 2019-2024:Donchian + MacroOverlay 跑通,COVID 期間
    overlay 真的 risk-off(cap < 1.0 至少出現過)。"""
    btc = CsvLoader(FIXTURES / "btc_usd_1d.csv", "BTC_kline_1d").fetch()
    vix = CsvLoader(FIXTURES / "vix_daily.csv", "vix_daily").fetch()
    series = {"BTC_kline_1d": btc, "vix_daily": vix}

    bt = Backtest(initial_cash=10000, price_map={"BTC": "BTC_kline_1d"})
    bt.add_symbol(DonchianBreakout(DonchianParams(symbol="BTC", entry=20, exit=10)))
    bt.add_portfolio(MacroOverlay(MacroOverlayParams(symbols=["BTC"])))
    res = bt.run(BacktestReplayDriver(series))

    assert res.fingerprint
    # event log 裡 pipeline 紀錄應出現過 cap < 1.0(2020/2022 VIX > 30 時段)
    capped = []
    for e in res.event_log.by_kind(kinds.PIPELINE):
        cap = e.data.get("cap") or {}
        if isinstance(cap, dict) and cap.get("BTC", 1.0) < 1.0:
            capped.append(e)
    assert capped, "2019-2024 含 COVID/2022 高 VIX,overlay 該至少 risk-off 過一次"
    # long-only
    for sym, qty in res.final_state.positions.items():
        assert qty >= -1e-9
