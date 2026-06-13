"""B4 風控管線測試 — Symbol 加總 / Portfolio min 合併 + #3C fallback /
Risk Engine 三 sub-stage / 算量站 / 執行政策層 / 整段 pipeline 整合。

關鍵性質(架構承諾變成可執行驗證):
- #3D min 取最狠 + #3C fallback 丟進同一個 min 池(非二次施加)
- min 池單調性:加守門員或缺席 fallback 都只會更保守、永遠不放寬
- gross 上限超過時比例壓縮(非單砍)
- 雙層節流:策略訊號 + framework dead-band/cooling 各管各的
- pipeline 整段 + dispatcher 串通(SymbolStrategy 缺席不該觸發 #3C
  fallback,只 PortfolioStrategy 缺席才該)
"""
from datetime import datetime, timedelta

import pytest
from pydantic import BaseModel

from v2.data import DataEvent, LKVStore
from v2.engine import (
    COOLING_DEFAULT,
    DEAD_BAND_DEFAULT,
    Dispatcher,
    IdentityVolEstimator,
    PortfolioState,
    aggregate_symbol_targets,
    apply_execution_policy,
    apply_risk_engine,
    merge_portfolio_caps,
    run_pipeline,
    size_to_quantity,
)
from v2.engine.dispatcher import Absence, FireResult
from v2.interfaces import (
    FieldSpec,
    NoOpParams,
    NoOpPortfolioStrategy,
    PortfolioStrategy,
    SymbolStrategy,
)
from v2.observability import MemorySink

T0 = datetime(2026, 5, 26, 0, 0)


def t(hours: float) -> datetime:
    return T0 + timedelta(hours=hours)


# ---- aggregation ----


def test_aggregate_equal_weight_default():
    # 兩策略各想 BTC 0.6 / 0.4 → equal-weight 平均 0.5
    r = aggregate_symbol_targets({"A": {"BTC": 0.6}, "B": {"BTC": 0.4}})
    assert r == {"BTC": 0.5}


def test_aggregate_missing_symbol_counts_zero():
    # B 對 ETH 沒興趣 → 出 0,平均 0.15
    r = aggregate_symbol_targets({"A": {"BTC": 0.6, "ETH": 0.3}, "B": {"BTC": 0.4}})
    assert r["BTC"] == 0.5
    assert r["ETH"] == pytest.approx(0.15)


def test_aggregate_capital_weights():
    # A 兩倍權:0.6×2 + 0.4×1 = 1.6 / 3 ≈ 0.533
    r = aggregate_symbol_targets(
        {"A": {"BTC": 0.6}, "B": {"BTC": 0.4}}, weights={"A": 2.0, "B": 1.0}
    )
    assert r["BTC"] == pytest.approx(1.6 / 3)


def test_aggregate_empty():
    assert aggregate_symbol_targets({}) == {}


# ---- merge_portfolio_caps (#3D + #3C) ----


def test_min_takes_most_conservative():
    r = merge_portfolio_caps(
        {"macro": {"BTC": 0.5}, "sentiment": {"BTC": 0.7}},
        absent_portfolios=set(),
        symbols={"BTC"},
    )
    assert r["BTC"] == 0.5  # 最狠者勝


def test_fallback_into_min_pool_not_second_apply():
    """#3C × #3D 核心:fallback 是 min 池候選,**不會放寬**現場明眼守門員。

    場景:現場守門員看到危險喊 0.3;缺席守門員用 fallback 0.5。
    若 fallback 是「事後 override」會被放寬到 0.5(錯);丟 min 池正確 = 0.3。
    """
    r = merge_portfolio_caps(
        {"macro": {"BTC": 0.3}},
        absent_portfolios={"sentiment"},
        symbols={"BTC"},
        fallback_cap=0.5,
    )
    assert r["BTC"] == 0.3  # 明眼守門員的緊 cap 不被瞎子兜底放寬


def test_fallback_tightens_when_stricter_than_existing():
    # 對稱情況:fallback 比現場更狠,自然勝出
    r = merge_portfolio_caps(
        {"macro": {"BTC": 0.7}},
        absent_portfolios={"sentiment"},
        symbols={"BTC"},
        fallback_cap=0.4,
    )
    assert r["BTC"] == 0.4


def test_empty_pool_is_one_not_naked():
    # 空池 = 1.0(Risk Engine 把關,non-bypass 不算裸奔)
    r = merge_portfolio_caps({}, absent_portfolios=set(), symbols={"BTC"})
    assert r["BTC"] == 1.0


def test_min_pool_monotone_more_voters_never_relax():
    """加守門員或加缺席 fallback,結果**只會更保守或不變,絕不放寬**(#3D 單調性)。"""
    base = merge_portfolio_caps(
        {"a": {"BTC": 0.7}}, absent_portfolios=set(), symbols={"BTC"}
    )
    plus_voter = merge_portfolio_caps(
        {"a": {"BTC": 0.7}, "b": {"BTC": 0.5}},
        absent_portfolios=set(),
        symbols={"BTC"},
    )
    plus_absent = merge_portfolio_caps(
        {"a": {"BTC": 0.7}},
        absent_portfolios={"b"},
        symbols={"BTC"},
        fallback_cap=0.4,
    )
    assert plus_voter["BTC"] <= base["BTC"]
    assert plus_absent["BTC"] <= base["BTC"]


def test_fallback_cap_validates():
    with pytest.raises(ValueError):
        merge_portfolio_caps({}, set(), {"BTC"}, fallback_cap=1.5)


# ---- Risk Engine ----


def test_risk_engine_pass_through_default():
    # default vol-targeting = identity,gross OK → 不變
    r = apply_risk_engine({"BTC": 0.4, "ETH": 0.3})
    assert r == {"BTC": 0.4, "ETH": 0.3}


def test_gross_limit_scales_proportionally():
    # 0.6 + 0.5 = 1.1 > 0.95 → 比例壓縮(同方向同比例,不單砍)
    r = apply_risk_engine({"BTC": 0.6, "ETH": 0.5}, gross_limit=0.95)
    assert sum(r.values()) == pytest.approx(0.95)
    assert r["BTC"] / r["ETH"] == pytest.approx(0.6 / 0.5)


def test_vol_estimator_hook():
    class HalfBTC:
        def scale(self, symbol):
            return 0.5 if symbol == "BTC" else 1.0

    r = apply_risk_engine({"BTC": 0.6, "ETH": 0.3}, vol_estimator=HalfBTC())
    assert r["BTC"] == pytest.approx(0.3)
    assert r["ETH"] == pytest.approx(0.3)


def test_terminal_fallback_when_all_absent():
    r = apply_risk_engine(
        {"BTC": 0.8}, all_strategies_absent=True, terminal_fallback_cap=0.3
    )
    assert r["BTC"] == 0.3  # 砍到 conservative


def test_terminal_fallback_only_tightens():
    # 不會放寬:若 target 本來就 < terminal_fallback,維持
    r = apply_risk_engine(
        {"BTC": 0.1}, all_strategies_absent=True, terminal_fallback_cap=0.3
    )
    assert r["BTC"] == 0.1


# ---- Risk Engine:組合視角 gross(V2-T 前置 2,cross-symbol 修正)----


def test_gross_accounts_for_held_elsewhere():
    """本 fire 只管 ETH 想滿倉,但別處(BTC)已持 80% → 整桌 0.95 上限只剩
    0.15 給 ETH(gross 看整桌、不只看當下 fire 的幣)。"""
    r = apply_risk_engine({"ETH": 1.0}, held_elsewhere_pct=0.80, gross_limit=0.95)
    assert r["ETH"] == pytest.approx(0.15)


def test_gross_full_book_elsewhere_zeros_the_fire():
    """別處已占滿 gross_limit → 本 fire 配 0(不產生買不起的單,reject 從源頭消失)。"""
    r = apply_risk_engine({"ETH": 1.0}, held_elsewhere_pct=0.95, gross_limit=0.95)
    assert r["ETH"] == pytest.approx(0.0)


def test_gross_held_elsewhere_over_limit_clamps_to_zero_not_relax():
    """別處因價格漂移已超過 gross_limit → remaining clamp 0,**不放寬**(單調性)。"""
    r = apply_risk_engine({"ETH": 0.5}, held_elsewhere_pct=0.98, gross_limit=0.95)
    assert r["ETH"] == pytest.approx(0.0)


def test_gross_held_elsewhere_default_zero_backward_compatible():
    """held_elsewhere 預設 0 = 舊行為(只看本 fire 總和)。"""
    r = apply_risk_engine({"BTC": 0.6, "ETH": 0.5}, gross_limit=0.95)
    assert sum(r.values()) == pytest.approx(0.95)


def test_gross_held_elsewhere_splits_two_firing_symbols_proportionally():
    """兩個 firing symbol + 別處持倉:剩餘額度在 firing 之間按比例分。"""
    r = apply_risk_engine(
        {"BTC": 0.6, "ETH": 0.4}, held_elsewhere_pct=0.45, gross_limit=0.95
    )
    # 剩餘 0.5,按 0.6:0.4 分 → 0.3 / 0.2
    assert r["BTC"] == pytest.approx(0.30)
    assert r["ETH"] == pytest.approx(0.20)
    assert sum(r.values()) + 0.45 == pytest.approx(0.95)


# ---- 算量站 ----


def test_sizing_basic():
    # 60% × 10000 / 50000 = 0.12 BTC
    r = size_to_quantity({"BTC": 0.6}, {"BTC": 50000}, equity=10000)
    assert r["BTC"] == pytest.approx(0.12)


def test_sizing_skips_missing_price():
    r = size_to_quantity({"BTC": 0.6, "ETH": 0.3}, {"BTC": 50000}, equity=10000)
    assert "BTC" in r
    assert "ETH" not in r  # 寧可不下單也不亂下


def test_sizing_zero_equity():
    assert size_to_quantity({"BTC": 0.6}, {"BTC": 50000}, equity=0) == {}


# ---- 執行政策層 ----


def test_dead_band_blocks_small_changes():
    sent, blocked = apply_execution_policy(
        desired_pct={"BTC": 0.51},
        desired_qty={"BTC": 0.102},
        current_qty={"BTC": 0.100},
        current_pct={"BTC": 0.50},  # 差 1% < default 2%
        last_trade_ts={},
        now=t(0),
    )
    assert not sent
    assert blocked[0].reason == "dead_band"


def test_dead_band_passes_big_change():
    sent, _ = apply_execution_policy(
        desired_pct={"BTC": 0.60},
        desired_qty={"BTC": 0.12},
        current_qty={"BTC": 0.10},
        current_pct={"BTC": 0.50},
        last_trade_ts={},
        now=t(0),
    )
    assert sent[0].symbol == "BTC"
    assert sent[0].delta_qty == pytest.approx(0.02)


def test_cooling_blocks_recent_trades():
    last = t(0)
    sent, blocked = apply_execution_policy(
        desired_pct={"BTC": 0.60},
        desired_qty={"BTC": 0.12},
        current_qty={"BTC": 0.10},
        current_pct={"BTC": 0.50},
        last_trade_ts={"BTC": last},
        now=last + timedelta(minutes=1),
        cooling=timedelta(minutes=5),
    )
    assert not sent
    assert blocked[0].reason == "cooling"


def test_regime_hook_blocks():
    class DenyAll:
        def allow(self, symbol, now):
            return False

    sent, blocked = apply_execution_policy(
        desired_pct={"BTC": 0.60},
        desired_qty={"BTC": 0.12},
        current_qty={"BTC": 0.10},
        current_pct={"BTC": 0.50},
        last_trade_ts={},
        now=t(0),
        regime_hook=DenyAll(),
    )
    assert not sent
    assert blocked[0].reason == "regime"


def test_intent_reason_classification():
    # open / close / rebalance
    sent, _ = apply_execution_policy(
        desired_pct={"BTC": 0.50, "ETH": 0.00, "SOL": 0.40},
        desired_qty={"BTC": 0.10, "ETH": 0.00, "SOL": 2.0},
        current_qty={"BTC": 0.05, "ETH": 0.20, "SOL": 0.0},
        current_pct={"BTC": 0.30, "ETH": 0.30, "SOL": 0.0},
        last_trade_ts={},
        now=t(0),
        dead_band=0.05,
    )
    by_sym = {o.symbol: o.reason for o in sent}
    assert by_sym["BTC"] == "rebalance"
    assert by_sym["ETH"] == "close"
    assert by_sym["SOL"] == "open"


# ---- portfolio state ----


def test_equity_and_position_pct():
    st = PortfolioState(cash=5000, positions={"BTC": 0.1})
    prices = {"BTC": 50000}  # BTC 部位 5000 → 總 10000 → BTC = 50%
    assert st.equity(prices) == 10000
    assert st.position_pct("BTC", prices) == 0.5
    assert st.position_pct("ETH", prices) == 0.0


# ---- 整段 pipeline 整合 ----


class P(BaseModel):
    model_config = {"frozen": True}


class FixedSym(SymbolStrategy):
    """測試用 SymbolStrategy:固定回 target%。"""
    params_schema = P

    def __init__(self, target_pct: dict[str, float], *, name: str, fields=None):
        super().__init__(P())
        self._target = target_pct
        self._name = name
        self._fields = fields or {"BTC_kline_1h": FieldSpec()}

    @property
    def name(self):
        return self._name

    def required_data(self):
        return self._fields

    def initialize(self, snapshot):
        pass

    def on_bar(self, snapshot):
        return dict(self._target)


class FixedPort(PortfolioStrategy):
    params_schema = P

    def __init__(self, caps: dict[str, float], *, name: str, fields=None,
                 crash=False):
        super().__init__(P())
        self._caps = caps
        self._name = name
        self._fields = fields or {"BTC_kline_1h": FieldSpec()}
        self._crash = crash

    @property
    def name(self):
        return self._name

    def required_data(self):
        return self._fields

    def initialize(self, snapshot):
        pass

    def on_bar(self, snapshot):
        if self._crash:
            raise RuntimeError("boom")
        return dict(self._caps)


def test_pipeline_end_to_end_happy_path():
    d = Dispatcher(LKVStore(), MemorySink())
    d.register(FixedSym({"BTC": 0.6}, name="Trend"))
    d.register(FixedPort({"BTC": 1.0}, name="Macro"))
    d.assert_startup_ok()

    fire = d.on_event(DataEvent(field="BTC_kline_1h", value=50000, ts=t(0)))
    result = run_pipeline(
        fire,
        portfolio_names=d.portfolio_names(),
        symbol_names=d.symbol_names(),
        state=PortfolioState(cash=10000),
        prices={"BTC": 50000},
        sink=MemorySink(),
    )
    assert result.combined_target["BTC"] == 0.6
    assert result.effective_cap["BTC"] == 1.0
    assert result.final_target["BTC"] == 0.6
    assert result.risk_adjusted["BTC"] == 0.6
    assert result.desired_qty["BTC"] == pytest.approx(0.12)
    assert len(result.orders) == 1
    assert result.orders[0].reason == "open"


def test_pipeline_portfolio_crash_triggers_fallback_in_min_pool():
    """關鍵性質:Portfolio crash → fallback 進 min 池(#3C 與 dispatcher 串通)。"""
    d = Dispatcher(LKVStore(), MemorySink())
    d.register(FixedSym({"BTC": 0.6}, name="Trend"))
    d.register(FixedPort({"BTC": 1.0}, name="P1"))
    d.register(FixedPort({"BTC": 1.0}, name="P2_crash", crash=True), crash_limit=10)
    d.assert_startup_ok()

    fire = d.on_event(DataEvent(field="BTC_kline_1h", value=50000, ts=t(0)))
    # P2 crash 進 absences,該進 #3C fallback
    assert "P2_crash" in fire.absences
    assert fire.absences["P2_crash"].reason == "crashed"

    result = run_pipeline(
        fire,
        portfolio_names=d.portfolio_names(),
        symbol_names=d.symbol_names(),
        state=PortfolioState(cash=10000),
        prices={"BTC": 50000},
        sink=MemorySink(),
        fallback_cap=0.5,
    )
    # min(P1=1.0, fallback=0.5) = 0.5(明眼 P1 在,但 fallback 更狠勝出)
    assert result.effective_cap["BTC"] == 0.5
    assert result.final_target["BTC"] == pytest.approx(0.6 * 0.5)


def test_pipeline_symbol_absence_does_not_trigger_portfolio_fallback():
    """Symbol 缺席不該觸發 portfolio fallback(分流正確):
    缺席的是出價的人,不是守門員,#3C 不適用。"""
    d = Dispatcher(LKVStore(), MemorySink())
    d.register(FixedSym({"BTC": 0.6}, name="SymCrash"), crash_limit=1)
    d.register(FixedSym({"BTC": 0.4}, name="SymOK"))  # 不同名,訂同 field
    d.register(FixedPort({"BTC": 1.0}, name="Macro"))
    d.assert_startup_ok()

    # SymCrash 寫一個會炸的策略:用 monkeypatch 模擬 — 改 on_bar
    # 簡單做法:重註冊一個炸的版本
    bad = type(
        "BadSym",
        (FixedSym,),
        {"on_bar": lambda self, s: (_ for _ in ()).throw(RuntimeError("boom"))},
    )
    d2 = Dispatcher(LKVStore(), MemorySink())
    d2.register(bad({"BTC": 0.6}, name="SymCrash"), crash_limit=1)
    d2.register(FixedSym({"BTC": 0.4}, name="SymOK"))
    d2.register(FixedPort({"BTC": 1.0}, name="Macro"))

    fire = d2.on_event(DataEvent(field="BTC_kline_1h", value=50000, ts=t(0)))
    # SymCrash 在 absences、Macro 正常
    assert "SymCrash" in fire.absences
    assert "Macro" not in fire.absences
    result = run_pipeline(
        fire,
        portfolio_names=d2.portfolio_names(),
        symbol_names=d2.symbol_names(),
        state=PortfolioState(cash=10000),
        prices={"BTC": 50000},
        sink=MemorySink(),
        fallback_cap=0.3,
    )
    # Symbol 缺席:Macro 正常出 1.0,沒有 portfolio fallback 進池 → cap 1.0
    assert result.effective_cap["BTC"] == 1.0
    # SymCrash 缺席 → equal-weight 只有 SymOK 0.4 一個有效
    assert result.combined_target["BTC"] == 0.4


def test_pipeline_dead_band_blocks_at_current_position():
    """dead-band 對「沒變化」的 symbol 不送單(現有部位 ≈ 目標)。"""
    d = Dispatcher(LKVStore(), MemorySink())
    d.register(FixedSym({"BTC": 0.5}, name="Trend"))
    d.register(FixedPort({"BTC": 1.0}, name="Macro"))

    state = PortfolioState(
        cash=5000, positions={"BTC": 0.1}  # 50000 × 0.1 = 5000 → 50%
    )
    fire = d.on_event(DataEvent(field="BTC_kline_1h", value=50000, ts=t(0)))
    result = run_pipeline(
        fire,
        portfolio_names=d.portfolio_names(),
        symbol_names=d.symbol_names(),
        state=state,
        prices={"BTC": 50000},
        sink=MemorySink(),
    )
    # current 50% ≈ target 50% → dead-band 擋住
    assert not result.orders
    assert result.blocked and result.blocked[0].reason == "dead_band"


def test_pipeline_noop_treated_as_pass_through_no_fallback():
    """NoOp 沒訂閱 → 不被 fire → 不在 absences → 不觸發 fallback。"""
    d = Dispatcher(LKVStore(), MemorySink())
    d.register(FixedSym({"BTC": 0.5}, name="Trend"))
    d.register(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC"])))
    d.assert_startup_ok()  # NoOp 滿足 #3A 鎖

    fire = d.on_event(DataEvent(field="BTC_kline_1h", value=50000, ts=t(0)))
    assert "NoOpPortfolioStrategy" not in fire.absences  # 沒訂閱 = 不該 fire = 不算缺席
    result = run_pipeline(
        fire,
        portfolio_names=d.portfolio_names(),
        symbol_names=d.symbol_names(),
        state=PortfolioState(cash=10000),
        prices={"BTC": 50000},
        sink=MemorySink(),
    )
    # 空池(沒任何 vote)= 1.0
    assert result.effective_cap["BTC"] == 1.0
    assert result.final_target["BTC"] == 0.5


def test_pipeline_single_symbol_fire_respects_held_elsewhere():
    """V2-T 前置 2 核心:event-driven 一次只 fire 一個幣,別處已持倉時本 fire
    被壓進剩餘額度 → 不再產生「想花 95% 但現金只有 5%」的破表單。"""
    d = Dispatcher(LKVStore(), MemorySink())
    d.register(FixedSym({"BTC": 1.0}, name="BtcTrend"))  # BTC 想滿倉
    d.register(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC", "ETH"])))
    d.assert_startup_ok()

    # 帳戶:現金 2000 + ETH 部位 8000(80%);BTC fire 想滿倉
    state = PortfolioState(cash=2000, positions={"ETH": 4.0})  # 4.0 × 2000 = 8000
    prices = {"BTC": 50000, "ETH": 2000}  # equity = 10000,ETH = 80%

    fire = d.on_event(DataEvent(field="BTC_kline_1h", value=50000, ts=t(0)))
    result = run_pipeline(
        fire,
        portfolio_names=d.portfolio_names(),
        symbol_names=d.symbol_names(),
        state=state,
        prices=prices,
        sink=MemorySink(),
        gross_limit=0.95,
    )
    # ETH 已 80% → BTC 只剩 0.15(不是破表的 1.0/0.95)
    assert result.risk_adjusted["BTC"] == pytest.approx(0.15)
    # 送出的單真的買得起(cost ≤ cash),這才是 reject 從源頭消失的關鍵
    assert result.orders, "0.15 vs current 0% 大於 dead-band,應送單"
    o = result.orders[0]
    cost = o.delta_qty * prices["BTC"]
    assert o.delta_qty > 0 and cost <= state.cash + 1e-9
