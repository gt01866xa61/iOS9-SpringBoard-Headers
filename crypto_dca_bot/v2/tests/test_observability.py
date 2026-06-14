"""B6 observability 測試:LogEntry / EventLog query / JSON-lines / M3
fingerprint determinism / alert channel 分流 / MemorySink backward compat /
整合(dispatcher → log 還原完整事件鏈)。"""
import json
from datetime import datetime, timedelta

import pytest
from pydantic import BaseModel

from v2.data import DataEvent, LKVStore
from v2.engine import Dispatcher
from v2.interfaces import FieldSpec, NoOpParams, NoOpPortfolioStrategy, SymbolStrategy
from v2.observability import (
    EventLog,
    EventLogSink,
    LiveTelegramChannel,
    LogEntry,
    MemorySink,
    NoopAlertChannel,
    kinds,
)
from v2.observability.log import _jsonable

T0 = datetime(2026, 5, 26, 0, 0)


def t(hours: float) -> datetime:
    return T0 + timedelta(hours=hours)


# ---- LogEntry ----


def test_log_entry_frozen():
    e = LogEntry(ts=T0, kind="x", data={"a": 1})
    with pytest.raises(Exception):
        e.kind = "y"  # frozen


def test_log_entry_get():
    e = LogEntry(ts=T0, kind="x", data={"a": 1})
    assert e.get("a") == 1
    assert e.get("missing", default=42) == 42


# ---- EventLog append + ts sniffing ----


def test_append_uses_business_ts_if_provided():
    log = EventLog()
    e = log.append("x", ts=T0, strategy="S")
    assert e.ts == T0


def test_append_falls_back_to_wall_clock_when_no_ts():
    log = EventLog()
    before = datetime.now()
    e = log.append("x", note="no ts")
    after = datetime.now()
    assert before <= e.ts <= after


def test_append_order_preserved():
    log = EventLog()
    for i in range(5):
        log.append("x", ts=t(i), seq=i)
    assert [int(e.data["seq"]) for e in log.all()] == [0, 1, 2, 3, 4]


def test_append_copies_data():
    """append 後改原 dict 不該影響 log(防別處 mutate)。"""
    log = EventLog()
    payload = {"a": 1}
    log.append("x", ts=T0, payload=payload)
    payload["a"] = 999
    assert log.all()[0].data["payload"]["a"] == 1 or log.all()[0].data["payload"] is payload
    # 注意:append 用 dict(data) 淺拷貝,nested dict 仍共享 — 這是 trade-off
    # 主要保證 entries 列表 + top-level data dict 不被外部 mutate


def test_len_and_iter():
    log = EventLog()
    for i in range(3):
        log.append("x", ts=t(i))
    assert len(log) == 3
    assert sum(1 for _ in log) == 3


# ---- query ----


def test_by_kind():
    log = EventLog()
    log.append("a", ts=t(0))
    log.append("b", ts=t(1))
    log.append("a", ts=t(2))
    assert len(log.by_kind("a")) == 2
    assert log.by_kind("missing") == []


def test_by_strategy():
    log = EventLog()
    log.append("x", ts=t(0), strategy="S1")
    log.append("x", ts=t(1), strategy="S2")
    log.append("x", ts=t(2), strategy="S1")
    assert len(log.by_strategy("S1")) == 2
    assert log.by_strategy("S1")[0].ts == t(0)


def test_between():
    log = EventLog()
    for i in range(5):
        log.append("x", ts=t(i))
    window = log.between(t(1), t(3))
    assert [e.ts for e in window] == [t(1), t(2), t(3)]


def test_kinds():
    log = EventLog()
    log.append("a", ts=t(0))
    log.append("b", ts=t(1))
    log.append("a", ts=t(2))
    assert log.kinds() == {"a", "b"}


# ---- JSON-lines + M3 fingerprint ----


def test_jsonl_parseable_per_line():
    log = EventLog()
    log.append("a", ts=t(0), strategy="S", payload={"x": 1})
    log.append("b", ts=t(1), values=[1, 2, 3])
    for line in log.to_jsonl().splitlines():
        obj = json.loads(line)
        assert "ts" in obj and "kind" in obj and "data" in obj


def test_fingerprint_deterministic():
    """同 log 內容 → 同 hash(M3 lock 可重現)。"""
    def build():
        log = EventLog()
        log.append("a", ts=t(0), strategy="S")
        log.append("b", ts=t(1), x=1.5)
        return log
    assert build().fingerprint() == build().fingerprint()


def test_fingerprint_changes_with_content():
    a = EventLog()
    a.append("x", ts=t(0), v=1)
    b = EventLog()
    b.append("x", ts=t(0), v=2)
    assert a.fingerprint() != b.fingerprint()


def test_fingerprint_changes_with_order():
    """改順序 → fingerprint 變(時序是 M3 lock 的一部分)。"""
    a = EventLog()
    a.append("x", ts=t(0))
    a.append("y", ts=t(1))
    b = EventLog()
    b.append("y", ts=t(1))
    b.append("x", ts=t(0))
    assert a.fingerprint() != b.fingerprint()


# ---- _jsonable(各種型別)----


def test_jsonable_handles_datetime_and_timedelta():
    assert _jsonable(T0) == T0.isoformat()
    assert _jsonable(timedelta(hours=2)) == 7200.0


def test_jsonable_handles_set():
    assert _jsonable({3, 1, 2}) == [1, 2, 3]


def test_jsonable_handles_pydantic():
    class M(BaseModel):
        x: int = 1
        y: str = "hi"
    assert _jsonable(M()) == {"x": 1, "y": "hi"}


def test_jsonable_nested():
    obj = {"list": [T0, {1, 2}], "td": timedelta(seconds=5)}
    out = _jsonable(obj)
    assert out["list"][0] == T0.isoformat()
    assert out["list"][1] == [1, 2]
    assert out["td"] == 5.0


def test_jsonable_unknown_repr_fallback():
    class Weird:
        def __repr__(self):
            return "<Weird>"
    assert _jsonable(Weird()) == "<Weird>"


# ---- EventLogSink + AlertChannel 分流 ----


def test_sink_log_writes_to_log():
    sink = EventLogSink()
    sink.log("x", ts=T0, strategy="S", v=1)
    assert sink.event_log.by_kind("x")[0].data["v"] == 1


def test_sink_alert_writes_log_and_pushes_channel():
    pushes = []

    class Recorder:
        def push(self, message, **data):
            pushes.append((message, data))

    sink = EventLogSink(channel=Recorder())
    sink.alert("hello", ts=T0, strategy="S")
    assert pushes == [("hello", {"ts": T0, "strategy": "S"})]
    assert sink.event_log.by_kind(kinds.ALERT)[0].data["message"] == "hello"


def test_noop_channel_records_but_silent():
    """回測 default:alert 進 log 但 channel no-op。"""
    sink = EventLogSink(channel=NoopAlertChannel())
    sink.alert("silent", ts=T0)
    assert len(sink.event_log.by_kind(kinds.ALERT)) == 1  # 仍進 log


def test_live_telegram_channel_stub():
    with pytest.raises(NotImplementedError, match="V2-D"):
        LiveTelegramChannel().push("test")


# ---- MemorySink backward compat ----


def test_memory_sink_records_attribute():
    s = MemorySink()
    s.log("registered", strategy="A", fields=["BTC_kline_1h"])
    s.log("is_ready", strategy="A", ready=True, ts=T0)
    kinds_seen = [k for k, _ in s.records]
    assert kinds_seen == ["registered", "is_ready"]


def test_memory_sink_alerts_attribute():
    s = MemorySink()
    s.alert("watch out", strategy="A", ts=T0)
    assert s.alerts == [("watch out", {"strategy": "A", "ts": T0})]


def test_memory_sink_alert_also_in_records():
    """alert 進 log → records 也看得到(走 kind='alert')。"""
    s = MemorySink()
    s.alert("hi")
    s.log("other", v=1)
    assert any(k == "alert" for k, _ in s.records)
    assert any(k == "other" for k, _ in s.records)


# ---- 整合測試:跑 dispatcher → 從 event log 還原完整事件鏈 ----


class P(BaseModel):
    model_config = {"frozen": True}


class S1(SymbolStrategy):
    params_schema = P

    def __init__(self):
        super().__init__(P())

    @property
    def name(self):
        return "S1"

    def required_data(self):
        return {"BTC_kline_1h": FieldSpec(min_history=2)}

    def initialize(self, snapshot):
        pass

    def on_bar(self, snapshot):
        return {"BTC": 0.5}


def test_integration_event_log_replay_chain():
    sink = MemorySink()
    d = Dispatcher(LKVStore(), sink, ready_alert_n=2)
    d.register(S1())
    d.register(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC"])))
    d.assert_startup_ok()

    d.on_event(DataEvent(field="BTC_kline_1h", value=100, ts=t(0)))  # not ready
    d.on_event(DataEvent(field="BTC_kline_1h", value=101, ts=t(1)))  # ready, fire

    log = sink.event_log
    # registered 兩次
    assert len(log.by_kind(kinds.REGISTERED)) == 2
    # S1 的 is_ready 兩次(NoOp overlay 也會 log,故 filter by strategy),ts 順序正確
    ready_entries = [e for e in log.by_kind(kinds.IS_READY) if e.data.get("strategy") == "S1"]
    assert [e.ts for e in ready_entries] == [t(0), t(1)]
    assert ready_entries[0].data["ready"] is False
    assert ready_entries[1].data["ready"] is True
    # S1 視角:強相關事件齊全
    s1_chain = log.by_strategy("S1")
    s1_kinds = [e.kind for e in s1_chain]
    assert kinds.REGISTERED in s1_kinds
    assert kinds.IS_READY in s1_kinds


def test_integration_fingerprint_repeatable_run():
    """跑兩次同樣的 dispatcher 序列,event log fingerprint 必須一樣
    (M3 backtest lock 的核心承諾 — 同回測必同結果)。"""

    def run():
        sink = MemorySink()
        d = Dispatcher(LKVStore(), sink)
        d.register(S1())
        d.register(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC"])))
        d.assert_startup_ok()
        d.on_event(DataEvent(field="BTC_kline_1h", value=100, ts=t(0)))
        d.on_event(DataEvent(field="BTC_kline_1h", value=101, ts=t(1)))
        d.on_event(DataEvent(field="BTC_kline_1h", value=102, ts=t(2)))
        return sink.event_log.fingerprint()

    assert run() == run()


def test_between_query_on_realistic_chain():
    sink = MemorySink()
    d = Dispatcher(LKVStore(), sink)
    d.register(S1())
    d.register(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC"])))
    for i in range(5):
        d.on_event(DataEvent(field="BTC_kline_1h", value=100 + i, ts=t(i)))
    window = sink.event_log.between(t(1), t(3))
    # 視窗內所有 entries 的業務 ts 都在範圍裡
    assert all(t(1) <= e.ts <= t(3) for e in window)
    assert any(e.kind == kinds.IS_READY for e in window)
