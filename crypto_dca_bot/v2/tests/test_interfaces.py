"""B1 interface 層測試:lifecycle contract / output 驗證 / NoOp / framework-default 偵測。"""
from datetime import datetime, timedelta

import pytest
from pydantic import BaseModel

from v2.interfaces import (
    FieldSpec,
    FieldValue,
    NoOpParams,
    NoOpPortfolioStrategy,
    Snapshot,
    StrategyBase,
    SymbolStrategy,
    uses_framework_default,
    validate_output,
)


class DummyParams(BaseModel):
    model_config = {"frozen": True}
    lookback: int = 5


class DummyState(BaseModel):
    counter: int = 0


class DummySymbol(SymbolStrategy):
    params_schema = DummyParams
    state_schema = DummyState

    def required_data(self):
        return {"BTC_kline_1h": FieldSpec(min_history=5)}

    def initialize(self, snapshot):
        pass

    def on_bar(self, snapshot):
        return {"BTC": 0.6}


def make_snapshot(**field_ages_minutes) -> Snapshot:
    now = datetime(2026, 5, 26, 10, 0)
    return Snapshot(
        ts=now,
        fields={
            name: FieldValue(value=123.0, ts=now - timedelta(minutes=age))
            for name, age in field_ages_minutes.items()
        },
    )


# ---- lifecycle contract ----


def test_abstract_methods_enforced():
    class Incomplete(SymbolStrategy):
        params_schema = DummyParams

    with pytest.raises(TypeError):
        Incomplete(DummyParams())  # 缺 required_data/initialize/on_bar


def test_params_type_checked():
    class WrongParams(BaseModel):
        x: int = 1

    with pytest.raises(TypeError, match="expects params"):
        DummySymbol(WrongParams())


def test_state_type_checked():
    s = DummySymbol(DummyParams())
    with pytest.raises(TypeError, match="expects state"):
        s.set_state(DummyParams())
    s.set_state(DummyState(counter=3))
    assert s.get_state().counter == 3


# ---- framework default 偵測(可選 method)----


def test_framework_default_detection():
    s = DummySymbol(DummyParams())
    # Dummy 沒 override is_ready / reset / on_stale → engine 走 framework default
    assert uses_framework_default(s, "is_ready")
    assert uses_framework_default(s, "reset")
    assert uses_framework_default(s, "on_stale")

    noop = NoOpPortfolioStrategy(NoOpParams(symbols=["BTC"]))
    assert not uses_framework_default(noop, "is_ready")  # NoOp 有 override


def test_on_stale_default_is_noop():
    s = DummySymbol(DummyParams())
    s.on_stale(["BTC_kline_1h"])  # 不炸 = no-op


def test_base_is_ready_and_reset_guarded():
    # base 實作不該被直接呼叫(engine 要先做 override 偵測)
    s = DummySymbol(DummyParams())
    with pytest.raises(NotImplementedError):
        s.is_ready()
    with pytest.raises(NotImplementedError):
        s.reset()


# ---- output 驗證 ----


def test_validate_output_ok():
    assert validate_output({"BTC": 0.6, "ETH": 0}, owner="x") == {"BTC": 0.6, "ETH": 0.0}


@pytest.mark.parametrize(
    "bad",
    [
        {"BTC": 1.2},          # 超出 [0,1]
        {"BTC": -0.1},
        {"BTC": "60%"},        # 非數字
        {"BTC": True},         # bool 不算數
        ["BTC", 0.6],          # 非 dict
    ],
)
def test_validate_output_rejects(bad):
    with pytest.raises((TypeError, ValueError)):
        validate_output(bad, owner="x")


# ---- Snapshot ----


def test_snapshot_age():
    snap = make_snapshot(BTC_kline_1h=30, vix_daily=60 * 26)
    assert snap.age_of("BTC_kline_1h") == timedelta(minutes=30)
    assert snap.age_of("vix_daily") == timedelta(hours=26)


def test_snapshot_frozen():
    snap = make_snapshot(BTC_kline_1h=0)
    with pytest.raises(Exception):
        snap.ts = datetime(2030, 1, 1)


# ---- FieldSpec(default + override)----


def test_fieldspec_defaults_mean_registry():
    spec = FieldSpec(min_history=21)
    assert spec.max_staleness is None  # None = 用 registry default
    assert spec.alert_n is None
    assert spec.trigger is True


def test_fieldspec_override():
    spec = FieldSpec(min_history=200, max_staleness=timedelta(minutes=30), alert_n=2)
    assert spec.max_staleness == timedelta(minutes=30)


# ---- NoOp(#3A)----


def test_noop_returns_cap_one_for_all_symbols():
    noop = NoOpPortfolioStrategy(NoOpParams(symbols=["BTC", "ETH"]))
    snap = make_snapshot()
    assert noop.on_bar(snap) == {"BTC": 1.0, "ETH": 1.0}


def test_noop_has_no_required_data():
    noop = NoOpPortfolioStrategy(NoOpParams(symbols=["BTC"]))
    assert noop.required_data() == {}  # 不會 stale → #3C 天然豁免


def test_noop_always_ready():
    noop = NoOpPortfolioStrategy(NoOpParams(symbols=["BTC"]))
    assert noop.is_ready() is True
