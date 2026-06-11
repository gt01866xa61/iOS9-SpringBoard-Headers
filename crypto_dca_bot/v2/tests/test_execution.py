"""B5 executor 測試:cost models / sim 成交 / state 副作用 / rejection /
determinism / long-only 防呆 / LiveExecutor stub。"""
from datetime import datetime, timedelta

import pytest

from v2.engine.execution_policy import OrderIntent
from v2.engine.portfolio_state import PortfolioState
from v2.execution import (
    BacktestSimExecutor,
    FixedBpsSlippage,
    FlatTakerFee,
    LiveExecutor,
    ZeroFee,
    ZeroSlippage,
)
from v2.observability import MemorySink

T0 = datetime(2026, 5, 26, 0, 0)


def buy(symbol, target, current):
    return OrderIntent(symbol=symbol, target_qty=target, current_qty=current,
                       delta_qty=target - current, reason="rebalance")


# ---- cost models ----


def test_zero_slippage():
    assert ZeroSlippage().fill_price(100.0, 1) == 100.0


def test_fixed_bps_buy_higher_sell_lower():
    s = FixedBpsSlippage(bps=10.0)  # 0.1%
    assert s.fill_price(100.0, 1) == pytest.approx(100.1)   # 買滑高
    assert s.fill_price(100.0, -1) == pytest.approx(99.9)   # 賣滑低


def test_slippage_validates():
    with pytest.raises(ValueError):
        FixedBpsSlippage(bps=-1)
    with pytest.raises(ValueError):
        FixedBpsSlippage().fill_price(100.0, 0)


def test_flat_taker_fee():
    assert FlatTakerFee(rate=0.001).fee(10000) == pytest.approx(10.0)
    assert FlatTakerFee().fee(-5000) == pytest.approx(5.0)  # abs
    assert ZeroFee().fee(10000) == 0.0


def test_fee_validates():
    with pytest.raises(ValueError):
        FlatTakerFee(rate=-0.1)


# ---- sim 成交 + state 副作用 ----


def test_buy_updates_state_with_cost():
    state = PortfolioState(cash=10000)
    ex = BacktestSimExecutor(state, MemorySink(),
                             slippage=ZeroSlippage(), fee_model=ZeroFee())
    fills, rej = ex.execute([buy("BTC", 0.1, 0.0)], {"BTC": 50000}, T0)
    assert not rej
    assert fills[0].delta_qty == pytest.approx(0.1)
    assert fills[0].notional == pytest.approx(5000)
    assert state.cash == pytest.approx(5000)        # 10000 − 5000
    assert state.positions["BTC"] == pytest.approx(0.1)
    assert state.last_trade_ts["BTC"] == T0


def test_buy_applies_slippage_and_fee():
    state = PortfolioState(cash=10000)
    ex = BacktestSimExecutor(state, MemorySink(),
                             slippage=FixedBpsSlippage(10), fee_model=FlatTakerFee(0.001))
    fills, _ = ex.execute([buy("BTC", 0.1, 0.0)], {"BTC": 50000}, T0)
    # 成交價 50000 × 1.001 = 50050;notional 5005;fee 5.005
    assert fills[0].fill_price == pytest.approx(50050)
    assert fills[0].notional == pytest.approx(5005)
    assert fills[0].fee == pytest.approx(5.005)
    assert state.cash == pytest.approx(10000 - 5005 - 5.005)


def test_sell_updates_state():
    state = PortfolioState(cash=0, positions={"BTC": 0.1})
    ex = BacktestSimExecutor(state, MemorySink(),
                             slippage=ZeroSlippage(), fee_model=ZeroFee())
    fills, _ = ex.execute(
        [OrderIntent("BTC", target_qty=0.0, current_qty=0.1, delta_qty=-0.1, reason="close")],
        {"BTC": 50000}, T0,
    )
    assert fills[0].delta_qty == pytest.approx(-0.1)
    assert state.cash == pytest.approx(5000)
    assert state.positions["BTC"] == pytest.approx(0.0)


# ---- rejection 路徑 ----


def test_insufficient_cash_rejected():
    state = PortfolioState(cash=100)  # 不夠買 0.1 BTC @ 50000
    ex = BacktestSimExecutor(state, MemorySink())
    fills, rej = ex.execute([buy("BTC", 0.1, 0.0)], {"BTC": 50000}, T0)
    assert not fills
    assert rej[0].reason == "insufficient_cash"
    assert state.cash == 100  # 沒動


def test_no_price_rejected():
    state = PortfolioState(cash=10000)
    ex = BacktestSimExecutor(state, MemorySink())
    _, rej = ex.execute([buy("BTC", 0.1, 0.0)], {}, T0)
    assert rej[0].reason == "no_price"


def test_zero_delta_rejected():
    state = PortfolioState(cash=10000)
    ex = BacktestSimExecutor(state, MemorySink())
    _, rej = ex.execute(
        [OrderIntent("BTC", 0.1, 0.1, delta_qty=0.0, reason="rebalance")],
        {"BTC": 50000}, T0,
    )
    assert rej[0].reason == "zero_delta"


# ---- long-only 防呆(不賣超過持有,no short)----


def test_cannot_sell_more_than_held():
    state = PortfolioState(cash=0, positions={"BTC": 0.05})
    ex = BacktestSimExecutor(state, MemorySink(),
                             slippage=ZeroSlippage(), fee_model=ZeroFee())
    # 想賣 0.1 但只有 0.05 → 只賣 0.05,不變空頭
    fills, _ = ex.execute(
        [OrderIntent("BTC", target_qty=0.0, current_qty=0.1, delta_qty=-0.1, reason="close")],
        {"BTC": 50000}, T0,
    )
    assert fills[0].delta_qty == pytest.approx(-0.05)
    assert state.positions["BTC"] == pytest.approx(0.0)  # 不會變負


def test_sell_with_no_position_rejected():
    state = PortfolioState(cash=0)
    ex = BacktestSimExecutor(state, MemorySink())
    _, rej = ex.execute(
        [OrderIntent("BTC", 0.0, 0.0, delta_qty=-0.1, reason="close")],
        {"BTC": 50000}, T0,
    )
    assert rej[0].reason == "no_position"


# ---- determinism(M3 lock)----


def test_determinism_same_input_same_output():
    def run():
        state = PortfolioState(cash=10000)
        ex = BacktestSimExecutor(state, MemorySink())
        fills, _ = ex.execute([buy("BTC", 0.1, 0.0)], {"BTC": 50000}, T0)
        return fills[0]

    a, b = run(), run()
    assert a == b  # frozen dataclass equality — 完全相同


# ---- 多單批次 ----


def test_batch_mixed_fills_and_rejections():
    state = PortfolioState(cash=6000)
    ex = BacktestSimExecutor(state, MemorySink(),
                             slippage=ZeroSlippage(), fee_model=ZeroFee())
    fills, rej = ex.execute(
        [buy("BTC", 0.1, 0.0), buy("ETH", 1.0, 0.0)],  # BTC 5000 OK,ETH 3000 不夠
        {"BTC": 50000, "ETH": 3000}, T0,
    )
    assert len(fills) == 1 and fills[0].symbol == "BTC"
    assert len(rej) == 1 and rej[0].symbol == "ETH"


# ---- LiveExecutor stub ----


def test_live_executor_not_implemented():
    with pytest.raises(NotImplementedError, match="V2-D"):
        LiveExecutor().execute([], {}, T0)


# ---- cooling 接點(成交更新 last_trade_ts,執行政策層下次擋)----


def test_fill_sets_last_trade_ts_for_cooling():
    state = PortfolioState(cash=10000)
    ex = BacktestSimExecutor(state, MemorySink())
    ex.execute([buy("BTC", 0.1, 0.0)], {"BTC": 50000}, T0)
    assert state.last_trade_ts["BTC"] == T0
    # 沒成交的不該設(rejection 不更新)
    ex.execute([buy("ETH", 99.0, 0.0)], {"ETH": 3000}, T0 + timedelta(hours=1))
    assert "ETH" not in state.last_trade_ts
