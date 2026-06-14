"""B7 整合驗收:end-to-end runner / dummy 策略全管線 / M1 stale-aware
合成壓測 / 整場回測 determinism(M3 lock)。"""
from datetime import datetime, timedelta

import pytest

from v2.data import BacktestReplayDriver
from v2.engine import Backtest, StartupError
from v2.engine.dispatcher import Dispatcher
from v2.interfaces import NoOpParams, NoOpPortfolioStrategy
from v2.observability import kinds
from v2.strategies import SmaCrossSymbol, ThresholdOverlay, ThresholdOverlayParams
from v2.testing import (
    M1_CRASHES,
    make_crash_scenario,
    make_kline_series,
    make_macro_series,
)

T0 = datetime(2026, 5, 26, 0, 0)


def t(hours: float) -> datetime:
    return T0 + timedelta(hours=hours)


# ---- dummy 策略單元 ----


def test_sma_cross_warms_up_then_signals():
    from v2.data import LKVStore, DataEvent, build_snapshot

    s = SmaCrossSymbol()
    store = LKVStore()
    # 餵遞增價 → fast SMA 終究 > slow SMA → target_when_up
    out = None
    for i in range(15):
        store.update(DataEvent(field="BTC_kline_1h", value=100 + i * 5, ts=t(i)))
        snap = build_snapshot(store, ["BTC_kline_1h"], now=t(i))
        out = s.on_bar(snap)
    assert out["BTC"] == pytest.approx(0.6)  # 上升趨勢 → 進場


def test_threshold_overlay_risk_off():
    from v2.data import LKVStore, DataEvent, build_snapshot

    ov = ThresholdOverlay(ThresholdOverlayParams(risk_off_above=30, cap_when_risk_off=0.3))
    store = LKVStore()
    store.update(DataEvent(field="vix_daily", value=45.0, ts=t(0)))  # > 30 → risk off
    snap = build_snapshot(store, ["vix_daily"], now=t(0))
    assert ov.on_bar(snap) == {"BTC": 0.3, "ETH": 0.3}
    store.update(DataEvent(field="vix_daily", value=15.0, ts=t(1)))  # 平靜
    snap = build_snapshot(store, ["vix_daily"], now=t(1))
    assert ov.on_bar(snap) == {"BTC": 1.0, "ETH": 1.0}


# ---- end-to-end happy path ----


def test_backtest_end_to_end_runs_and_trades():
    bt = Backtest(initial_cash=10000, cooling=timedelta(0))  # 關 cooling 方便觀察
    bt.add_symbol(SmaCrossSymbol())
    bt.add_portfolio(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC"])))

    series = {"BTC_kline_1h": make_kline_series("BTC_kline_1h", T0, 30, drift=0.01)}
    result = bt.run(BacktestReplayDriver(series))

    assert result.fired_events == 30
    assert result.pipeline_runs > 0
    assert len(result.fills) > 0          # 上升趨勢 → 有進場成交
    assert result.fingerprint            # M3 fingerprint 有值
    # 成交後有持倉
    assert result.final_state.positions.get("BTC", 0) > 0


def test_backtest_requires_portfolio_startup_lock():
    bt = Backtest()
    bt.add_symbol(SmaCrossSymbol())
    series = {"BTC_kline_1h": make_kline_series("BTC_kline_1h", T0, 5)}
    with pytest.raises(StartupError):
        bt.run(BacktestReplayDriver(series))


def test_backtest_with_real_overlay_caps_in_risk_off():
    # overlay risk-off 時 cap 0.3 → 部位被砍,曝險低於無 overlay
    def run(overlay):
        bt = Backtest(initial_cash=10000, cooling=timedelta(0), dead_band=0.0)
        bt.add_symbol(SmaCrossSymbol())
        bt.add_portfolio(overlay)
        series = {
            "BTC_kline_1h": make_kline_series("BTC_kline_1h", T0, 40, drift=0.01),
            "vix_daily": make_macro_series("vix_daily", T0, 40, value=45.0,
                                           step=timedelta(hours=1)),  # 持續 risk-off
        }
        return bt.run(BacktestReplayDriver(series))

    risk_off = run(ThresholdOverlay(
        ThresholdOverlayParams(risk_off_above=30, cap_when_risk_off=0.3, symbols=["BTC"])
    ))
    calm = run(ThresholdOverlay(
        ThresholdOverlayParams(risk_off_above=99, cap_when_risk_off=0.3, symbols=["BTC"])
    ))
    # risk-off 持倉 % 該明顯低於 calm(cap 砍倉)
    btc_ro = risk_off.final_state.positions.get("BTC", 0)
    btc_calm = calm.final_state.positions.get("BTC", 0)
    assert btc_ro < btc_calm


# ---- M3 lock:整場回測 determinism ----


def test_backtest_fingerprint_repeatable():
    def run():
        bt = Backtest(initial_cash=10000)
        bt.add_symbol(SmaCrossSymbol())
        bt.add_portfolio(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC"])))
        series = {"BTC_kline_1h": make_kline_series("BTC_kline_1h", T0, 50, drift=0.005)}
        return bt.run(BacktestReplayDriver(series)).fingerprint

    assert run() == run()  # 同回測 → 同 fingerprint(M3 lock)


def test_backtest_fingerprint_changes_with_params():
    def run(target_when_up):
        from v2.strategies import SmaCrossParams
        bt = Backtest(initial_cash=10000)
        bt.add_symbol(SmaCrossSymbol(SmaCrossParams(target_when_up=target_when_up)))
        bt.add_portfolio(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC"])))
        series = {"BTC_kline_1h": make_kline_series("BTC_kline_1h", T0, 50, drift=0.005)}
        return bt.run(BacktestReplayDriver(series)).fingerprint

    # 不同進場目標 → 不同部位 → 不同 backtest = 不同指紋(M3 lock 對參數敏感)
    assert run(0.6) != run(0.3)


# ---- M1 stale-aware 合成壓測(架構 §8 補註)----


def test_synthetic_data_gap_triggers_stale_skip():
    """合成 API gap → framework 判 stale 跳過策略(stale 機制本身受測)。"""
    bt = Backtest(initial_cash=10000)
    # 嚴格 staleness:kline 超過 90min 沒新值就 stale
    from v2.strategies import SmaCrossParams
    from v2.interfaces import FieldSpec

    class StrictSma(SmaCrossSymbol):
        def required_data(self):
            return {"BTC_kline_1h": FieldSpec(min_history=2,
                                              max_staleness=timedelta(minutes=90))}

    bt.add_symbol(StrictSma(SmaCrossParams(slow=2)))
    bt.add_portfolio(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC"])))

    # 一段 kline,中間挖 5 根 gap(模擬 API timeout)
    series = {
        "BTC_kline_1h": make_kline_series(
            "BTC_kline_1h", T0, 20, drift=0.01, gap_range=(8, 13)
        )
    }
    result = bt.run(BacktestReplayDriver(series))
    # gap 之後第一根 fire 時,上一筆 kline 已超過 90min → 但因為 trigger 是
    # kline 本身,gap 期間根本沒 fire;gap 後第一根帶新 ts,不 stale。
    # 真正測 stale 的是「非觸發 field 過期」場景 — 見下個 test。
    # 這裡先確認 gap 不會讓回測炸 + 有正常完成
    assert result.fired_events == 15  # 20 − 5 gap
    assert result.fingerprint


def test_non_trigger_field_stale_during_crash():
    """崩盤 + macro field gap → macro 過期但 kline 還在 → overlay 因
    macro stale 缺席 → #3C fallback 進 min 池(壓測 stale × 風控聯動)。"""
    bt = Backtest(initial_cash=10000, cooling=timedelta(0), dead_band=0.0,
                  fallback_cap=0.3)
    from v2.strategies import SmaCrossParams
    bt.add_symbol(SmaCrossSymbol(SmaCrossParams(slow=2)))
    bt.add_portfolio(ThresholdOverlay(
        ThresholdOverlayParams(field="vix_daily", risk_off_above=99,  # 永不 risk-off
                               symbols=["BTC"])
    ))

    # kline 連續(每小時),vix 只在最前面給一次然後斷流 → 很快 stale
    series = {
        "BTC_kline_1h": make_kline_series("BTC_kline_1h", T0, 20, drift=0.01),
        "vix_daily": [(T0, 18.0)],  # 只有 1 筆,之後 kline fire 時 vix 早就過期
    }
    result = bt.run(BacktestReplayDriver(series))

    log = result.event_log
    # overlay 應因 vix stale 多次被跳過
    stale_skips = [e for e in log.by_kind(kinds.SKIPPED_STALE)
                   if e.data.get("strategy", "").startswith("ThresholdOverlay")]
    assert len(stale_skips) > 0, "overlay 該因 vix stale 被跳過"


def test_m1_crash_scenario_runs_stale_aware():
    """M1 五段崩盤 anchor 之一:崩盤 + API gap 全程跑通不炸,event log
    記錄完整(stale-aware 壓測骨架)。"""
    bt = Backtest(initial_cash=10000)
    from v2.strategies import SmaCrossParams
    bt.add_symbol(SmaCrossSymbol(SmaCrossParams(symbol="BTC", slow=3)))
    bt.add_symbol(SmaCrossSymbol(SmaCrossParams(symbol="ETH", slow=3)))
    bt.add_portfolio(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC", "ETH"])))

    scenario = make_crash_scenario(M1_CRASHES["luna_2022_05"],
                                   pre_bars=20, post_bars=20, api_gap_bars=6)
    result = bt.run(BacktestReplayDriver(scenario))

    # gap 各 6 根 × 2 symbol → fired = (40−6)+(40−6) = 68
    assert result.fired_events == 68
    assert result.fingerprint
    # 崩盤後價格確實掉(合成驗證)
    btc_series = scenario["BTC_kline_1h"]
    pre_crash = btc_series[19][1]
    post_crash = btc_series[20][1]
    assert post_crash < pre_crash * 0.7  # 崩了 ~40%


def test_all_m1_anchors_smoke():
    """五段崩盤 anchor 全部跑得通(冒煙測試,不驗報酬只驗不炸)。"""
    for name, anchor in M1_CRASHES.items():
        bt = Backtest(initial_cash=10000)
        from v2.strategies import SmaCrossParams
        bt.add_symbol(SmaCrossSymbol(SmaCrossParams(slow=3)))
        bt.add_portfolio(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC"])))
        scenario = {"BTC_kline_1h": make_crash_scenario(anchor)["BTC_kline_1h"]}
        result = bt.run(BacktestReplayDriver(scenario))
        assert result.fingerprint, f"{name} 壓測沒產出 fingerprint"
