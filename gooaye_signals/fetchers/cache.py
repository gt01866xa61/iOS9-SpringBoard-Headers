"""DayCache — 當輪抓取快取 + demo 攔截 + last-good 持久化。

三個職責：
1. get_or_fetch：同一輪內同一 (source, params) 只抓一次（去重）。
2. demo 模式：改讀 demo/fixtures/<source>.json，不打任何網路（本機/CI 離線可跑）。
3. last-good：把每個 signal 上一輪成功的卡片存到 data/cache/last_good.json，
   讓來源短暫故障時前端能沿用舊圖（stale）而不是空白。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, Iterable, Mapping, Optional


class DayCache:
    def __init__(self, cache_dir, *, demo: bool = False, fixtures_dir=None) -> None:
        self.cache_dir = Path(cache_dir)
        self.demo = demo
        self.fixtures_dir = Path(fixtures_dir) if fixtures_dir else None
        self._mem: dict[tuple[str, str], object] = {}
        self._fixtures: dict[str, object] = {}
        self._last_good: Optional[dict] = None
        self._last_good_path = self.cache_dir / "last_good.json"

    @staticmethod
    def _pkey(params: Mapping[str, object]) -> str:
        return json.dumps(params, sort_keys=True, default=str, ensure_ascii=False)

    # ---- 抓取 ----
    def get_or_fetch(self, source: str, params: Mapping[str, object],
                     fetch: Callable[[Mapping[str, object]], object]) -> object:
        key = (source, self._pkey(params))
        if key in self._mem:
            return self._mem[key]
        data = self._demo_fetch(source, params) if self.demo else fetch(params)
        self._mem[key] = data
        return data

    def prefetch(self, plan: Iterable[tuple[str, Mapping[str, object]]],
                 registry: Mapping[str, Callable]) -> None:
        """依 run-plan 預熱快取；warm 失敗不致命（留給 per-signal 再處理）。"""
        for source, params in plan:
            try:
                self.get_or_fetch(source, params, registry[source])
            except Exception:  # noqa: BLE001 — 預熱隔離
                pass

    def _demo_fetch(self, source: str, params: Mapping[str, object]) -> object:
        from fetchers.demo import DEMO_SHAPERS

        if source not in DEMO_SHAPERS:
            raise NotImplementedError(f"demo 模式沒有 '{source}' 的 shaper")
        return DEMO_SHAPERS[source](params, self._load_fixture(source))

    def _load_fixture(self, source: str) -> object:
        if source not in self._fixtures:
            if not self.fixtures_dir:
                raise RuntimeError("demo 模式需要 fixtures_dir")
            path = self.fixtures_dir / f"{source}.json"
            self._fixtures[source] = json.loads(path.read_text(encoding="utf-8"))
        return self._fixtures[source]

    # ---- last-good 持久化 ----
    def _load_last_good(self) -> dict:
        if self._last_good is None:
            try:
                self._last_good = json.loads(self._last_good_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                self._last_good = {}
        return self._last_good

    def last_good(self, signal_id: str) -> Optional[dict]:
        return self._load_last_good().get(signal_id)

    def save_last_good(self, signal_id: str, card: dict) -> None:
        lg = self._load_last_good()
        lg[signal_id] = card
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        tmp = self._last_good_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(lg, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self._last_good_path)
