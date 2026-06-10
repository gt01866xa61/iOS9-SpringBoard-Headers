"""B2 資料層測試:registry default+override / replay 時間序 / LKV / snapshot
per-fire 重建 / no-lookahead by construction(關鍵性質測試)。"""
from datetime import datetime, timedelta

import pytest

from v2.data import (
    BacktestReplayDriver,
    DataEvent,
    LKVStore,
    ReplaySeriesError,
    UnknownDataSourceError,
    build_snapshot,
    effective_alert_n,
    effective_staleness,
    get_source,
)
from v2.interfaces import FieldSpec

T0 = datetime(2026, 5, 26, 0, 0)


def t(hours: float) -> datetime:
    return T0 + timedelta(hours=hours)


# ---- registry(default + override)----


def test_get_source_known():
    assert get_source("BTC_kline_1h").cadence == timedelta(hours=1)


def test_get_source_unknown_raises():
    with pytest.raises(UnknownDataSourceError, match="not in DATA_SOURCES"):
        get_source("nope_field")


def test_effective_staleness_default():
    # 策略沒 override → registry default(BTC kline = 2h)
    assert effective_staleness("BTC_kline_1h", FieldSpec()) == timedelta(hours=2)


def test_effective_staleness_override_wins():
    spec = FieldSpec(max_staleness=timedelta(minutes=30))
    assert effective_staleness("BTC_kline_1h", spec) == timedelta(minutes=30)


def test_effective_alert_n():
    assert effective_alert_n("BTC_funding_8h", FieldSpec()) == 2
    assert effective_alert_n("BTC_funding_8h", FieldSpec(alert_n=9)) == 9


# ---- replay driver ----


def test_replay_merges_in_time_order():
    driver = BacktestReplayDriver(
        {
            "BTC_kline_1h": [(t(0), 100), (t(1), 101), (t(2), 102)],
            "BTC_funding_8h": [(t(0.5), 0.01)],
            "vix_daily": [(t(1.5), 18.0)],
        }
    )
    out = list(driver.events())
    assert [e.ts for e in out] == sorted(e.ts for e in out)
    assert [(e.ts, e.field) for e in out] == [
        (t(0), "BTC_kline_1h"),
        (t(0.5), "BTC_funding_8h"),
        (t(1), "BTC_kline_1h"),
        (t(1.5), "vix_daily"),
        (t(2), "BTC_kline_1h"),
    ]


def test_replay_tie_break_deterministic():
    # 同 ts 跨 field → 按 field 名穩定排序(M3 lock 可重現)
    driver = BacktestReplayDriver(
        {
            "vix_daily": [(t(0), 18.0)],
            "BTC_kline_1h": [(t(0), 100)],
        }
    )
    fields = [e.field for e in driver.events()]
    assert fields == ["BTC_kline_1h", "vix_daily"]


def test_replay_rejects_unsorted():
    with pytest.raises(ReplaySeriesError, match="strictly increasing"):
        BacktestReplayDriver({"BTC_kline_1h": [(t(1), 101), (t(0), 100)]})


def test_replay_rejects_duplicate_ts():
    with pytest.raises(ReplaySeriesError):
        BacktestReplayDriver({"BTC_kline_1h": [(t(0), 100), (t(0), 100.5)]})


def test_replay_rejects_unknown_field():
    with pytest.raises(UnknownDataSourceError):
        BacktestReplayDriver({"mystery": [(t(0), 1)]})


# ---- LKV store ----


def test_lkv_keeps_latest():
    store = LKVStore()
    assert store.update(DataEvent(field="BTC_kline_1h", value=100, ts=t(0)))
    assert store.update(DataEvent(field="BTC_kline_1h", value=101, ts=t(1)))
    assert store.get("BTC_kline_1h").value == 101


def test_lkv_ignores_out_of_order():
    # live 端遲到封包不能把 LKV 倒退(backtest 不會發生,這是 live 保險)
    store = LKVStore()
    store.update(DataEvent(field="BTC_kline_1h", value=101, ts=t(1)))
    assert store.update(DataEvent(field="BTC_kline_1h", value=100, ts=t(0))) is False
    assert store.get("BTC_kline_1h").value == 101


def test_lkv_unknown_field_none():
    assert LKVStore().get("BTC_kline_1h") is None


# ---- snapshot(per-fire 重建)----


def test_snapshot_point_in_time():
    # 先組的 snapshot 不受之後 store 更新影響 — per-fire 重建的核心性質
    store = LKVStore()
    store.update(DataEvent(field="BTC_kline_1h", value=100, ts=t(0)))
    snap = build_snapshot(store, ["BTC_kline_1h"], now=t(0.5))
    store.update(DataEvent(field="BTC_kline_1h", value=999, ts=t(1)))
    assert snap.fields["BTC_kline_1h"].value == 100  # 凍在組裝那一刻


def test_snapshot_omits_missing_fields():
    store = LKVStore()
    store.update(DataEvent(field="BTC_kline_1h", value=100, ts=t(0)))
    snap = build_snapshot(store, ["BTC_kline_1h", "vix_daily"], now=t(1))
    assert "BTC_kline_1h" in snap.fields
    assert "vix_daily" not in snap.fields  # 還沒資料 → 省略(判定歸 B3)


def test_snapshot_lkv_alignment():
    # 多 timeframe LKV 對齊:慢 field 拿到的是舊值 + 正確資料齡
    store = LKVStore()
    store.update(DataEvent(field="vix_daily", value=18.0, ts=t(0)))
    store.update(DataEvent(field="BTC_kline_1h", value=100, ts=t(26)))
    snap = build_snapshot(store, ["BTC_kline_1h", "vix_daily"], now=t(26))
    assert snap.age_of("vix_daily") == timedelta(hours=26)
    assert snap.age_of("BTC_kline_1h") == timedelta(0)


# ---- no-lookahead by construction(B2 關鍵性質測試)----


def test_no_lookahead_property():
    """replay 邊吐邊組 snapshot:任一時點,snapshot 內所有值的 ts 都 <= now。

    這是 R3-② 「結構上不可能偷看未來」的可執行驗證。
    """
    driver = BacktestReplayDriver(
        {
            "BTC_kline_1h": [(t(h), 100 + h) for h in range(0, 48)],
            "BTC_funding_8h": [(t(h), 0.01) for h in range(0, 48, 8)],
            "vix_daily": [(t(h), 18.0) for h in range(0, 48, 24)],
        }
    )
    store = LKVStore()
    all_fields = ["BTC_kline_1h", "BTC_funding_8h", "vix_daily"]
    for event in driver.events():
        store.update(event)
        snap = build_snapshot(store, all_fields, now=event.ts)
        for name, fv in snap.fields.items():
            assert fv.ts <= snap.ts, f"lookahead! {name} ts={fv.ts} > now={snap.ts}"
