"""B3 dispatch core 測試:訂閱觸發 / ready / stale(per-strategy 門檻)/
crash 隔離+累積停用 / #3A 鎖 / 湧現停機 / #3B 順序。"""
from datetime import datetime, timedelta

import pytest
from pydantic import BaseModel

from v2.data import DataEvent, LKVStore
from v2.engine import Dispatcher, StartupError
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


def ev(field: str, hours: float, value: object = 1.0) -> DataEvent:
    return DataEvent(field=field, value=value, ts=t(hours))


class P(BaseModel):
    model_config = {"frozen": True}


class KlineSymbol(SymbolStrategy):
    """訂 BTC kline;可調 min_history / staleness override / 行為注入。"""

    params_schema = P

    def __init__(self, params=None, *, min_history=0, max_staleness=None,
                 alert_n=None, crash_on=None, call_log=None, name=None):
        super().__init__(params or P())
        self._spec = FieldSpec(
            min_history=min_history, max_staleness=max_staleness, alert_n=alert_n
        )
        self._crash_on = crash_on  # snapshot value == crash_on → raise
        self._call_log = call_log if call_log is not None else []
        self._name = name or type(self).__name__
        self.init_count = 0
        self.stale_notices: list[list[str]] = []

    @property
    def name(self):
        return self._name

    def required_data(self):
        return {"BTC_kline_1h": self._spec}

    def initialize(self, snapshot):
        self.init_count += 1

    def on_bar(self, snapshot):
        self._call_log.append(self.name)
        v = snapshot.fields["BTC_kline_1h"].value
        if self._crash_on is not None and v == self._crash_on:
            raise RuntimeError("boom")
        return {"BTC": 0.5}


class KlineSymbolWithStaleHook(KlineSymbol):
    def on_stale(self, stale_fields):
        self.stale_notices.append(stale_fields)


class KlinePortfolio(PortfolioStrategy):
    params_schema = P

    def __init__(self, params=None, *, crash_on=None, call_log=None):
        super().__init__(params or P())
        self._crash_on = crash_on
        self._call_log = call_log if call_log is not None else []

    def required_data(self):
        return {"BTC_kline_1h": FieldSpec()}

    def initialize(self, snapshot):
        pass

    def on_bar(self, snapshot):
        self._call_log.append(self.name)
        if self._crash_on is not None and snapshot.fields["BTC_kline_1h"].value == self._crash_on:
            raise RuntimeError("portfolio boom")
        return {"BTC": 0.8}


def make() -> tuple[Dispatcher, MemorySink]:
    sink = MemorySink()
    return Dispatcher(LKVStore(), sink), sink


# ---- 註冊 + #3A ----


def test_register_unknown_field_raises():
    d, _ = make()

    class Bad(KlineSymbol):
        def required_data(self):
            return {"mystery": FieldSpec()}

    with pytest.raises(KeyError):
        d.register(Bad())


def test_register_duplicate_name_raises():
    d, _ = make()
    d.register(KlineSymbol())
    with pytest.raises(ValueError, match="already registered"):
        d.register(KlineSymbol())


def test_startup_lock_requires_portfolio():
    d, _ = make()
    d.register(KlineSymbol())
    with pytest.raises(StartupError, match="NoOp"):
        d.assert_startup_ok()


def test_startup_lock_satisfied_by_noop():
    d, _ = make()
    d.register(KlineSymbol())
    d.register(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC"])))
    d.assert_startup_ok()  # 不炸


def test_noop_evaluated_as_overlay_passthrough():
    # PortfolioStrategy 是 decision-time overlay → 每 fire 評估(不靠自己 trigger)。
    # NoOp 無 required data → 永遠 ready/不 stale → 回 cap 1.0(pass-through)。
    d, _ = make()
    d.register(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC"])))
    r = d.on_event(ev("BTC_kline_1h", 0))
    assert r.portfolio_outputs == {"NoOpPortfolioStrategy": {"BTC": 1.0}}
    assert r.absences == {}


# ---- 訂閱觸發 ----


def test_only_subscribers_fired():
    d, _ = make()
    d.register(KlineSymbol())
    r = d.on_event(ev("vix_daily", 0))
    assert r.symbol_outputs == {} and r.absences == {}  # 沒訂 vix → 不 fire


def test_trigger_false_not_fired():
    d, _ = make()

    class NonTrigger(KlineSymbol):
        def required_data(self):
            return {"BTC_kline_1h": FieldSpec(trigger=False)}

    d.register(NonTrigger())
    r = d.on_event(ev("BTC_kline_1h", 0))
    assert r.symbol_outputs == {} and r.absences == {}


# ---- ready(#2C1)----


def test_buffer_based_ready_blocks_until_min_history():
    d, _ = make()
    d.register(KlineSymbol(min_history=3, name="S"))
    assert d.on_event(ev("BTC_kline_1h", 0)).absences["S"].reason == "not_ready"
    assert d.on_event(ev("BTC_kline_1h", 1)).absences["S"].reason == "not_ready"
    r = d.on_event(ev("BTC_kline_1h", 2))  # 第 3 筆 → buffer 滿
    assert "S" in r.symbol_outputs


def test_ready_logged_and_streak_alert():
    sink = MemorySink()
    d = Dispatcher(LKVStore(), sink, ready_alert_n=2)
    d.register(KlineSymbol(min_history=99, name="S"))
    d.on_event(ev("BTC_kline_1h", 0))
    assert not sink.alerts  # streak 1,未達 2
    d.on_event(ev("BTC_kline_1h", 1))
    assert any("is_ready false x2" in m for m, _ in sink.alerts)
    assert sum(1 for k, _ in sink.records if k == "is_ready") == 2  # 強制 log


def test_custom_is_ready_override_used():
    d, _ = make()

    class NeverReady(KlineSymbol):
        def is_ready(self):
            return False

    d.register(NeverReady(name="S"))
    assert d.on_event(ev("BTC_kline_1h", 0)).absences["S"].reason == "not_ready"


def test_initialize_called_once_before_first_bar():
    d, _ = make()
    s = KlineSymbol(min_history=2, name="S")
    d.register(s)
    d.on_event(ev("BTC_kline_1h", 0))  # not ready
    assert s.init_count == 0
    d.on_event(ev("BTC_kline_1h", 1))  # ready → initialize + on_bar
    d.on_event(ev("BTC_kline_1h", 2))
    assert s.init_count == 1  # 只一次


# ---- stale(#2C2,Sub-Q3 per-strategy 門檻)----


def two_field_setup(sink_alert_n=None):
    """策略訂 kline(trigger)+ vix(非 trigger);vix 缺值/過期 → stale。"""

    class TwoField(KlineSymbolWithStaleHook):
        def required_data(self):
            return {
                "BTC_kline_1h": FieldSpec(),
                "vix_daily": FieldSpec(trigger=False, alert_n=sink_alert_n),
            }

    return TwoField


def test_stale_skips_and_calls_hook():
    d, sink = make()
    s = two_field_setup()(name="S")
    d.register(s)
    d.on_event(ev("vix_daily", 0))
    r = d.on_event(ev("BTC_kline_1h", 100))  # vix 100h 前 > 3d 預設 → stale
    assert r.absences["S"].reason == "stale"
    assert r.absences["S"].fields == ["vix_daily"]
    assert s.stale_notices == [["vix_daily"]]  # on_stale hook 收到
    assert any(k == "skipped_stale" for k, _ in sink.records)


def test_missing_field_counts_as_stale():
    d, _ = make()
    s = two_field_setup()(name="S")
    d.register(s)
    r = d.on_event(ev("BTC_kline_1h", 0))  # vix 從沒來過
    assert r.absences["S"].reason == "stale"


def test_stale_streak_alert_and_recovery():
    d, sink = make()
    s = two_field_setup(sink_alert_n=2)(name="S")  # override alert_n=2
    d.register(s)
    d.on_event(ev("vix_daily", 0))
    d.on_event(ev("BTC_kline_1h", 100))  # stale x1
    assert not sink.alerts
    d.on_event(ev("BTC_kline_1h", 101))  # stale x2 → alert
    assert any("stale x2" in m for m, _ in sink.alerts)
    d.on_event(ev("vix_daily", 101.5))   # vix 恢復
    r = d.on_event(ev("BTC_kline_1h", 102))
    assert "S" in r.symbol_outputs        # 跑回來了,streak 已歸零


def test_per_strategy_staleness_thresholds():
    # Sub-Q3 核心:同 field 兩策略不同門檻 → 一個跳一個跑,不互相綁架
    d, _ = make()
    strict = KlineSymbol(max_staleness=timedelta(minutes=30), name="Strict")
    loose = KlineSymbol(name="Loose")  # registry default 2h

    class FundingTrigger(KlineSymbol):
        def required_data(self):
            return {
                "BTC_kline_1h": FieldSpec(max_staleness=self._spec.max_staleness, trigger=False),
                "BTC_funding_8h": FieldSpec(),
            }

    strict.__class__ = type("Strict", (FundingTrigger,), {})
    loose.__class__ = type("Loose", (FundingTrigger,), {})
    d.register(strict)
    d.register(loose)
    d.on_event(ev("BTC_kline_1h", 0))
    r = d.on_event(ev("BTC_funding_8h", 1))  # kline 已 1h 舊
    assert r.absences["Strict"].reason == "stale"   # 30min 門檻 → 跳
    assert "Loose" in r.symbol_outputs              # 2h 門檻 → 照跑


# ---- crash(#2D)----


def test_crash_isolated_others_run():
    d, _ = make()
    d.register(KlineSymbol(crash_on=666, name="Crasher"))
    d.register(KlineSymbol(name="Healthy"))
    r = d.on_event(ev("BTC_kline_1h", 0, value=666))
    assert r.absences["Crasher"].reason == "crashed"
    assert "Healthy" in r.symbol_outputs  # 故障隔離


def test_crash_counter_cumulative_not_reset_by_success():
    d, sink = make()
    d.register(KlineSymbol(crash_on=666, name="S"), crash_limit=3)
    d.on_event(ev("BTC_kline_1h", 0, value=666))  # crash 1
    d.on_event(ev("BTC_kline_1h", 1, value=666))  # crash 2
    r = d.on_event(ev("BTC_kline_1h", 2, value=1))  # 成功 — 不豁免
    assert "S" in r.symbol_outputs
    d.on_event(ev("BTC_kline_1h", 3, value=666))  # crash 3 → 永久停用
    assert any("permanently disabled after 3" in m for m, _ in sink.alerts)
    r = d.on_event(ev("BTC_kline_1h", 4, value=1))
    assert r.absences["S"].reason == "disabled"


def test_guard_crash_limit_one():
    d, _ = make()
    d.register(KlineSymbol(crash_on=666, name="S"), crash_limit=1)
    d.on_event(ev("BTC_kline_1h", 0, value=666))
    assert d.on_event(ev("BTC_kline_1h", 1)).absences["S"].reason == "disabled"


def test_bad_output_counts_as_crash():
    d, _ = make()

    class BadOutput(KlineSymbol):
        def on_bar(self, snapshot):
            return {"BTC": 1.5}  # 超出 [0,1]

    d.register(BadOutput(name="S"), crash_limit=1)
    r = d.on_event(ev("BTC_kline_1h", 0))
    assert r.absences["S"].reason == "crashed"


def test_emergent_halt_when_last_portfolio_disabled():
    # #2D × #3A 湧現:最後一個守門員被永久停用 → framework 停機
    d, sink = make()
    d.register(KlinePortfolio(crash_on=666), crash_limit=1)
    d.assert_startup_ok()
    with pytest.raises(StartupError, match="always-on lock violated"):
        d.on_event(ev("BTC_kline_1h", 0, value=666))
    assert any("halting" in m for m, _ in sink.alerts)


# ---- #3B 順序 + 輸出分流 ----


def test_symbol_dispatched_before_portfolio():
    d, _ = make()
    order: list[str] = []
    d.register(KlinePortfolio(call_log=order))
    d.register(KlineSymbol(call_log=order, name="Sym"))
    r = d.on_event(ev("BTC_kline_1h", 0))
    assert order == ["Sym", "KlinePortfolio"]  # Symbol 先(#3B)
    assert "Sym" in r.symbol_outputs
    assert "KlinePortfolio" in r.portfolio_outputs
