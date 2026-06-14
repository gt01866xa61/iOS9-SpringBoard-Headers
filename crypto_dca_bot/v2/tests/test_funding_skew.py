"""V2-S2 Funding skew 測試:演算法(rolling mean / 進出場 / linear interp /
dead_band)+ params validation + 整合進 Backtest(合成 funding + mock kline)
+ M3 determinism + CsvFundingLoader."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from v2.data import (
    BacktestReplayDriver,
    CsvFundingLoader,
    DataEvent,
    LKVStore,
    build_snapshot,
)
from v2.engine import Backtest
from v2.interfaces import FieldSpec, NoOpParams, NoOpPortfolioStrategy
from v2.strategies import FundingSkew, FundingSkewParams, FundingSkewState
from v2.testing import make_bar_series, make_funding_series

T0 = datetime(2026, 1, 1)


def t(hours: float) -> datetime:
    return T0 + timedelta(hours=hours)


def feed(strat: FundingSkew, fundings: list[float],
         field: str = "BTC_funding_8h") -> list[float]:
    """直接逐筆餵 on_bar(繞 dispatcher),回每筆 target。"""
    store = LKVStore()
    out = []
    for i, f in enumerate(fundings):
        store.update(DataEvent(field=field, value=f, ts=t(8 * i)))
        snap = build_snapshot(store, [field], now=t(8 * i))
        target = strat.on_bar(snap)[strat.params.symbol]
        out.append(target)
    return out


# ---- params validation ----


def test_params_low_must_not_exceed_high():
    with pytest.raises(ValidationError):
        FundingSkewParams(low_threshold=0.001, high_threshold=0.0001)


def test_params_dead_band_non_negative():
    with pytest.raises(ValidationError):
        FundingSkewParams(dead_band=-0.0001)


def test_params_lookback_positive():
    with pytest.raises(ValidationError):
        FundingSkewParams(lookback_periods=0)


# ---- 演算法 ----


def test_warmup_flat_until_buffer_full():
    s = FundingSkew(FundingSkewParams(
        lookback_periods=5, low_threshold=0.0001, high_threshold=0.001, dead_band=0
    ))
    targets = feed(s, [0.0] * 4)
    assert targets == [0.0, 0.0, 0.0, 0.0]  # buffer 未滿全 flat


def test_target_one_on_low_funding():
    s = FundingSkew(FundingSkewParams(
        lookback_periods=3, low_threshold=0.0001, high_threshold=0.001, dead_band=0
    ))
    targets = feed(s, [0.0, 0.0, 0.0, 0.0])  # raw=0 < low → 滿倉
    assert targets[2] == 1.0
    assert targets[3] == 1.0


def test_target_one_on_negative_funding():
    s = FundingSkew(FundingSkewParams(
        lookback_periods=3, low_threshold=0.0001, high_threshold=0.001, dead_band=0
    ))
    targets = feed(s, [-0.0005, -0.0005, -0.0005])  # 負 funding → 滿倉(空頭擁擠)
    assert targets[2] == 1.0


def test_target_zero_on_high_funding():
    s = FundingSkew(FundingSkewParams(
        lookback_periods=3, low_threshold=0.0001, high_threshold=0.001, dead_band=0
    ))
    targets = feed(s, [0.002, 0.002, 0.002])  # raw=0.002 > high → 出場
    assert targets[2] == 0.0


def test_linear_interp_in_middle():
    s = FundingSkew(FundingSkewParams(
        lookback_periods=2, low_threshold=0.0001, high_threshold=0.001, dead_band=0
    ))
    # raw = 0.00055(中點)→ target = 0.5
    targets = feed(s, [0.00055, 0.00055])
    assert targets[1] == pytest.approx(0.5)


def test_interp_at_low_boundary_is_one():
    s = FundingSkew(FundingSkewParams(
        lookback_periods=1, low_threshold=0.0001, high_threshold=0.001, dead_band=0
    ))
    assert feed(s, [0.0001])[0] == 1.0  # 邊界含


def test_interp_at_high_boundary_is_zero():
    s = FundingSkew(FundingSkewParams(
        lookback_periods=1, low_threshold=0.0001, high_threshold=0.001, dead_band=0
    ))
    assert feed(s, [0.001])[0] == 0.0


# ---- dead_band(訊號級節流)----


def test_dead_band_suppresses_small_signal_changes():
    s = FundingSkew(FundingSkewParams(
        lookback_periods=2,
        low_threshold=0.0,
        high_threshold=0.001,
        dead_band=0.0001,
    ))
    # 第 1 筆 buffer 未滿 flat;第 2 筆 raw=0.0005 → target=0.5(初次,無 last_raw)
    # 第 3 筆 raw=0.000525 變動 0.000025 < dead_band 0.0001 → 維持 0.5
    targets = feed(s, [0.0005, 0.0005, 0.00055])
    assert targets[1] == pytest.approx(0.5)
    assert targets[2] == pytest.approx(0.5)  # dead_band 抑制


def test_dead_band_accumulates_to_trigger():
    """漂移累積超過 dead_band → 觸發 update(防漂移卡死)。"""
    s = FundingSkew(FundingSkewParams(
        lookback_periods=2,
        low_threshold=0.0,
        high_threshold=0.001,
        dead_band=0.0001,
    ))
    # 第 1 筆 flat,第 2 筆 raw=0.0005 target=0.5,last_raw=0.0005
    # 第 3-5 筆漸增,raw 累積跨過 dead_band → 觸發
    raws_seq = [0.0005, 0.0005, 0.00055, 0.00060, 0.00065]  # raws: NA,0.0005,0.000525,0.000575,0.000625
    # raws after rolling-2 means: -, 0.0005, 0.000525, 0.000575, 0.000625
    # |0.000625 - 0.0005| = 0.000125 >= dead_band → 觸發
    targets = feed(s, raws_seq)
    # target 第 4 筆應 update(0.000625 對比 0.0005 差 0.000125 >= 0.0001)
    assert targets[1] == pytest.approx(0.5)
    assert targets[2] == pytest.approx(0.5)  # 變動 0.000025 < dead_band
    assert targets[3] == pytest.approx(0.5)  # 變動 0.000075 < dead_band(累積)
    # 第 4 筆:raw=0.000625,|0.000625-0.0005|=0.000125 >= 0.0001 → 觸發
    expected = 1.0 - (0.000625 - 0.0) / (0.001 - 0.0)  # = 0.375
    assert targets[4] == pytest.approx(expected)


def test_dead_band_zero_means_always_update():
    s = FundingSkew(FundingSkewParams(
        lookback_periods=2,
        low_threshold=0.0,
        high_threshold=0.001,
        dead_band=0.0,
    ))
    targets = feed(s, [0.0005, 0.0005, 0.00055])
    # 每筆都 update
    assert targets[1] == pytest.approx(0.5)
    # raw 第 3 筆 = (0.0005+0.00055)/2 = 0.000525
    assert targets[2] == pytest.approx(1.0 - 0.000525 / 0.001)


# ---- per symbol 獨立 ----


def test_per_symbol_independent():
    btc = FundingSkew(FundingSkewParams(
        symbol="BTC", lookback_periods=2,
        low_threshold=0.0001, high_threshold=0.001, dead_band=0))
    eth = FundingSkew(FundingSkewParams(
        symbol="ETH", lookback_periods=2,
        low_threshold=0.0001, high_threshold=0.001, dead_band=0))
    feed(btc, [0.0, 0.0])             # BTC 低 → 1.0
    feed(eth, [0.002, 0.002], field="ETH_funding_8h")  # ETH 高 → 0.0
    assert btc.state.last_target == 1.0
    assert eth.state.last_target == 0.0
    assert btc.name == "FundingSkew_BTC"
    assert eth.name == "FundingSkew_ETH"


# ---- state 序列化(M3 lock)----


def test_state_serializable():
    s = FundingSkew(FundingSkewParams(
        lookback_periods=2, low_threshold=0.0001, high_threshold=0.001, dead_band=0))
    feed(s, [0.0, 0.0])
    st = s.get_state()
    assert isinstance(st, FundingSkewState)
    assert len(st.fundings) == 2
    assert st.last_target == 1.0


def test_state_restorable():
    s = FundingSkew(FundingSkewParams(
        lookback_periods=2, low_threshold=0.0001, high_threshold=0.001, dead_band=0))
    feed(s, [0.0, 0.0])
    snap_state = s.get_state()

    fresh = FundingSkew(FundingSkewParams(
        lookback_periods=2, low_threshold=0.0001, high_threshold=0.001, dead_band=0))
    fresh.set_state(snap_state)
    assert fresh.state.fundings == snap_state.fundings
    assert fresh.state.last_target == snap_state.last_target


# ---- 整合進 Backtest(合成 funding + mock daily kline 提供 mark price)----


def _make_series(fundings: list[float], n_days: int | None = None,
                 close: float = 50000.0):
    """合成 BTC funding(8h)+ kline(1d 同 close 提供 mark price)。
    n_days 預設 = ceil(len(fundings)*8h / 1d) + 2(暖機 + 緩衝)。
    """
    if n_days is None:
        n_days = max(1, (len(fundings) * 8) // 24 + 3)
    return {
        "BTC_kline_1d": make_bar_series("BTC_kline_1d", T0, [close] * n_days),
        "BTC_funding_8h": make_funding_series("BTC_funding_8h", T0, fundings),
    }


def _bt(*, dead_band: float = 0.0, lookback: int = 3) -> Backtest:
    bt = Backtest(initial_cash=10000,
                  price_map={"BTC": "BTC_kline_1d"},
                  cooling=timedelta(0), dead_band=0.0)
    bt.add_symbol(FundingSkew(FundingSkewParams(
        symbol="BTC",
        lookback_periods=lookback,
        low_threshold=0.00005,
        high_threshold=0.0003,
        dead_band=dead_band,
    )))
    bt.add_portfolio(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC"])))
    return bt


def test_in_backtest_buys_on_low_funding():
    bt = _bt()
    # 前 3 筆 buffer 暖機,後續持續低 funding(滿倉訊號)
    fundings = [0.0] * 8  # 全 0 < low_threshold → 滿倉
    series = _make_series(fundings)
    result = bt.run(BacktestReplayDriver(series))

    assert any(f.delta_qty > 0 for f in result.fills), "持續低 funding 該進場"
    assert result.final_state.positions.get("BTC", 0) > 0


def test_in_backtest_sells_on_high_funding():
    bt = _bt()
    # 先低後高:先進場滿倉,後 funding 飆高出場
    fundings = [0.0] * 5 + [0.001] * 5  # 後段遠高於 high_threshold
    series = _make_series(fundings)
    result = bt.run(BacktestReplayDriver(series))

    buys = [f for f in result.fills if f.delta_qty > 0]
    sells = [f for f in result.fills if f.delta_qty < 0]
    assert buys, "前半低 funding 該進場"
    assert sells, "後半高 funding 該出場"
    # 最終接近清倉
    assert result.final_state.positions.get("BTC", 0) == pytest.approx(0, abs=1e-9)


def test_in_backtest_deterministic():
    def run():
        bt = _bt()
        fundings = [0.0] * 5 + [0.001] * 5
        series = _make_series(fundings)
        return bt.run(BacktestReplayDriver(series)).fingerprint
    assert run() == run()  # M3 lock


# ---- CsvFundingLoader(真資料 fixture 缺則 skip,容器內合成 sanity)----


def test_csv_funding_loader_roundtrip(tmp_path: Path):
    # 用 CcxtFundingLoader.to_csv 寫 + CsvFundingLoader 讀往返(本機 ccxt 抓 →
    # to_csv → 帶回容器 → CsvFundingLoader 餵 的可重現驗證)
    from v2.data import CcxtFundingLoader
    series = [(t(8 * i), 0.0001 * i) for i in range(5)]
    p = tmp_path / "btc_funding_8h.csv"
    CcxtFundingLoader.to_csv(series, p)
    loaded = CsvFundingLoader(p, "BTC_funding_8h").fetch()
    assert len(loaded) == 5
    assert [ts for ts, _ in loaded] == [ts for ts, _ in series]
    assert [round(r, 10) for _, r in loaded] == [round(r, 10) for _, r in series]


def test_csv_funding_loader_skips_comments(tmp_path: Path):
    p = tmp_path / "with_comments.csv"
    p.write_text(
        "# header comment\n"
        "# multi line\n"
        "timestamp,funding_rate\n"
        f"{t(0).isoformat()},0.0001\n"
        f"{t(8).isoformat()},0.0002\n"
    )
    out = CsvFundingLoader(p, "BTC_funding_8h").fetch()
    assert len(out) == 2 and out[1][1] == pytest.approx(0.0002)


# 真資料 fixture sanity check(committed 時自動啟用,缺則 skip)
FIXTURES = Path(__file__).resolve().parents[1] / "data" / "fixtures"
_has_funding_fixture = (FIXTURES / "btc_funding_8h.csv").exists()
requires_funding_fixture = pytest.mark.skipif(
    not _has_funding_fixture,
    reason="real-data funding fixture missing (use CcxtFundingLoader on local env, commit CSV)",
)


@requires_funding_fixture
def test_funding_skew_real_data_sanity():
    """真資料 BTC funding sanity:不爆 + 進出場 + long-only + 確定性。
    Fixture 由使用者本機 ccxt 抓回 commit 啟用(同 BTC OHLCV pipeline)。
    """
    btc_funding = CsvFundingLoader(FIXTURES / "btc_funding_8h.csv", "BTC_funding_8h").fetch()
    # 需要 mark price,使用者也應同時 commit BTC daily kline fixture(已在 V2-S1)
    from v2.data import CsvLoader
    btc_kline = CsvLoader(FIXTURES / "btc_usd_1d.csv", "BTC_kline_1d").fetch()
    series = {"BTC_kline_1d": btc_kline, "BTC_funding_8h": btc_funding}

    bt = _bt(lookback=21)
    result = bt.run(BacktestReplayDriver(series))
    assert len(result.fills) > 0
    for sym, qty in result.final_state.positions.items():
        assert qty >= -1e-9  # long-only
    assert result.fingerprint
