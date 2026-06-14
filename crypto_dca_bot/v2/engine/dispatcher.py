"""Dispatch core:event → fire 訂閱者 → 收集 output + 策略缺席統一模型。

ref: architecture.md §2(pipeline 階段 1-2)/ §3.4(#2B dispatch table)/
     §5(always-on 鎖 #3A、缺席統一模型 #2C2+#2D、crash counter #2D)/
     §3.3(is_ready #2C1、on_stale #2C2-B Sub-Q1)。

缺席統一模型:策略「這輪不能用」不分原因(not_ready / stale / crashed /
disabled)一律 = 缺席,輸出進 FireResult.absences,風控後果(#3C
fallback_cap 丟 min 池)由 B4 合併端處理。

counter 兩種語意(#2D 拍板):
- stale / not_ready streak:**連續**計數,恢復即歸零(transient I/O)
- crash counter:**累積**不歸零(crash = persistent bug,成功一輪不豁免),
  達 crash_limit → 永久停用 + alert

數字 placeholder(ready_alert_n / crash_limit default)V2-B 校準。
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from datetime import datetime

from ..data.events import DataEvent
from ..data.lkv import LKVStore, build_snapshot
from ..data.registry import effective_alert_n, effective_staleness, get_source
from ..interfaces.strategy import (
    PortfolioStrategy,
    StrategyBase,
    SymbolStrategy,
    uses_framework_default,
    validate_output,
)
from ..observability.sink import Sink


class StartupError(RuntimeError):
    """#3A always-on 鎖:0 個 PortfolioStrategy → refuse to start。"""


@dataclass
class Absence:
    reason: str  # not_ready / stale / crashed / disabled
    fields: list[str] = dc_field(default_factory=list)  # stale 時:哪些 field 過期


@dataclass
class FireResult:
    """單一 event 的 dispatch 結果,交 B4 風控管線接手。"""

    ts: datetime
    trigger_field: str
    symbol_outputs: dict[str, dict[str, float]] = dc_field(default_factory=dict)
    portfolio_outputs: dict[str, dict[str, float]] = dc_field(default_factory=dict)
    absences: dict[str, Absence] = dc_field(default_factory=dict)


@dataclass
class _Record:
    """per-strategy 的 framework 側狀態(策略自己無感)。"""

    strategy: StrategyBase
    crash_limit: int
    crashes: int = 0
    disabled: bool = False
    initialized: bool = False
    ready_false_streak: int = 0
    stale_streaks: dict[str, int] = dc_field(default_factory=dict)


class Dispatcher:
    def __init__(self, store: LKVStore, sink: Sink, *, ready_alert_n: int = 3) -> None:
        self._store = store
        self._sink = sink
        self._ready_alert_n = ready_alert_n
        self._records: dict[str, _Record] = {}
        self._field_counts: dict[str, int] = {}  # buffer-based is_ready 用
        # SymbolStrategy 走 event-driven 訂閱(#2B):field → [symbol names]
        self._dispatch_table: dict[str, list[str]] = {}
        # PortfolioStrategy 是 decision-time overlay:每次 fire 都評估(architecture
        # §2 per-fire pipeline / #3B),不靠自己的 trigger — 否則只在 overlay 資料
        # tick 才 cap、實際下單決策(symbol tick)反而沒守門員。註冊序保證 determinism。
        self._portfolio_order: list[str] = []

    # ---- 註冊 ----

    def register(self, strategy: StrategyBase, *, crash_limit: int = 3) -> None:
        name = strategy.name
        if name in self._records:
            raise ValueError(f"strategy {name!r} already registered")
        spec = strategy.required_data()
        for f in spec:
            get_source(f)  # 不在 registry → 註冊時就炸(fail fast)
        self._records[name] = _Record(strategy=strategy, crash_limit=crash_limit)
        if isinstance(strategy, PortfolioStrategy):
            self._portfolio_order.append(name)
        else:  # SymbolStrategy:event-driven 訂閱觸發欄位
            for f, fs in spec.items():
                if fs.trigger:
                    self._dispatch_table.setdefault(f, []).append(name)
        self._sink.log("registered", strategy=name, fields=sorted(spec))

    def portfolio_names(self) -> set[str]:
        """已註冊的 PortfolioStrategy 名單(B4 風控合併判定缺席用)。"""
        return {
            n for n, r in self._records.items()
            if isinstance(r.strategy, PortfolioStrategy)
        }

    def symbol_names(self) -> set[str]:
        return {
            n for n, r in self._records.items()
            if isinstance(r.strategy, SymbolStrategy)
        }

    def assert_startup_ok(self) -> None:
        """#3A always-on 鎖:至少 1 個 PortfolioStrategy(NoOp 也算 — 明確表態)。"""
        if not any(
            isinstance(r.strategy, PortfolioStrategy) for r in self._records.values()
        ):
            raise StartupError(
                "no PortfolioStrategy registered; refuse to start "
                "(register NoOpPortfolioStrategy to explicitly opt out, ref #3A)"
            )

    # ---- 主迴圈入口 ----

    def on_event(self, event: DataEvent) -> FireResult:
        self._store.update(event)
        self._field_counts[event.field] = self._field_counts.get(event.field, 0) + 1

        result = FireResult(ts=event.ts, trigger_field=event.field)
        # #3B:Symbol 先(訂閱觸發)、Portfolio 後(decision-time overlay,每 fire 評估)
        for n in self._dispatch_table.get(event.field, ()):
            self._dispatch_one(self._records[n], event.ts, result)
        for n in self._portfolio_order:
            self._dispatch_one(self._records[n], event.ts, result)
        return result

    # ---- 單一策略 dispatch(缺席統一模型)----

    def _dispatch_one(self, rec: _Record, now: datetime, result: FireResult) -> None:
        s = rec.strategy
        if rec.disabled:
            result.absences[s.name] = Absence("disabled")
            return

        spec = s.required_data()

        if not self._check_ready(rec, spec, now):
            result.absences[s.name] = Absence("not_ready")
            return

        stale = self._check_stale(rec, spec, now)
        if stale:
            result.absences[s.name] = Absence("stale", stale)
            self._sink.log("skipped_stale", strategy=s.name, fields=stale, ts=now)
            if not uses_framework_default(s, "on_stale"):
                try:
                    s.on_stale(stale)
                except Exception as exc:  # hook 失敗只記不停用(非 on_bar,#2D 範圍外)
                    self._sink.log("on_stale_hook_error", strategy=s.name, error=repr(exc))
            return

        snapshot = build_snapshot(self._store, spec.keys(), now)
        try:
            if not rec.initialized:
                s.initialize(snapshot)  # 第一根 bar 前,只一次(#2A)
                rec.initialized = True
            output = validate_output(s.on_bar(snapshot), owner=s.name)
        except Exception as exc:
            self._on_crash(rec, exc, now)
            result.absences[s.name] = Absence("crashed")
            return

        if isinstance(s, PortfolioStrategy):
            result.portfolio_outputs[s.name] = output
        else:
            result.symbol_outputs[s.name] = output

    # ---- ready(#2C1)----

    def _check_ready(self, rec: _Record, spec: dict, now: datetime) -> bool:
        s = rec.strategy
        if uses_framework_default(s, "is_ready"):
            # buffer-based default:所有 required field 收滿 min_history
            ready = all(
                self._field_counts.get(f, 0) >= fs.min_history
                for f, fs in spec.items()
            )
        else:
            ready = bool(s.is_ready())
        self._sink.log("is_ready", strategy=s.name, ready=ready, ts=now)  # 強制 log
        if ready:
            rec.ready_false_streak = 0
            return True
        rec.ready_false_streak += 1
        if rec.ready_false_streak == self._ready_alert_n:
            self._sink.alert(
                f"{s.name}: is_ready false x{rec.ready_false_streak} (consecutive)",
                strategy=s.name,
            )
        return False

    # ---- stale(#2C2,per-strategy 門檻 Sub-Q3)----

    def _check_stale(self, rec: _Record, spec: dict, now: datetime) -> list[str]:
        s = rec.strategy
        stale: list[str] = []
        for f, fs in spec.items():
            fv = self._store.get(f)
            is_stale = fv is None or (now - fv.ts) > effective_staleness(f, fs)
            if is_stale:
                stale.append(f)
                streak = rec.stale_streaks.get(f, 0) + 1
                rec.stale_streaks[f] = streak
                if streak == effective_alert_n(f, fs):
                    self._sink.alert(
                        f"{s.name}: field {f!r} stale x{streak} (consecutive)",
                        strategy=s.name,
                        field=f,
                    )
            else:
                rec.stale_streaks[f] = 0  # 恢復即歸零(transient)
        return stale

    # ---- crash(#2D:累積不歸零,達限永久停用)----

    def _on_crash(self, rec: _Record, exc: Exception, now: datetime) -> None:
        s = rec.strategy
        rec.crashes += 1
        self._sink.log(
            "strategy_crashed", strategy=s.name, error=repr(exc),
            crashes=rec.crashes, ts=now,
        )
        if rec.crashes >= rec.crash_limit:
            rec.disabled = True
            self._sink.alert(
                f"{s.name}: permanently disabled after {rec.crashes} crashes",
                strategy=s.name,
            )
            # 湧現停機(#2D × #3A):最後一個活著的守門員被停 → 撞 always-on 鎖
            if isinstance(s, PortfolioStrategy) and not any(
                isinstance(r.strategy, PortfolioStrategy) and not r.disabled
                for r in self._records.values()
            ):
                self._sink.alert("all PortfolioStrategies disabled; halting (#3A)")
                raise StartupError(
                    "all PortfolioStrategies permanently disabled; "
                    "always-on lock violated, framework halts (ref #2D x #3A)"
                )
