"""Phase 2 驗證：各 signal 的純 compute 在門檻邊界的燈號 + demo 全流程離線可跑。

跑法（在 gooaye_signals/ 目錄下）：
    python tests/test_phase2_compute.py          # 或 GOOAYE_DEMO=1 python tests/test_phase2_compute.py
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import config
import signals.ai_breadth as ai
import signals.mlcc_basket_ma as mlcc
import signals.yageo_rev_yoy as yageo
from fetchers import SOURCE_REGISTRY
from fetchers.cache import DayCache
from registry import discover

# --- 測試用序列 ---
UP = [float(i) for i in range(1, 61)]        # 遞增 → 站上 50MA
DOWN = [float(i) for i in range(60, 0, -1)]  # 遞減 → 跌破 50MA
SHORT = [1.0, 2.0, 3.0]                       # 太短 → 略過


def _rev(yoys: list[float]) -> dict:
    return {"rev": [[f"m{i}", v] for i, v in enumerate(yoys)]}


def _check_yageo() -> None:
    assert yageo._compute(_rev([1, 2, 3, 4])).light == "green"          # 0 連降
    assert yageo._compute(_rev([1, 2, 3, 2])).light == "yellow"         # 1 連降
    assert yageo._compute(_rev([1, 2, 4, 3, 2])).light == "red"         # 2 連降
    assert yageo._compute(_rev([1.0])).light == "gray"                  # 資料不足
    r = yageo._compute(_rev([5, 4, 3]))
    assert r.value_label == "YoY +3.0%" and r.extra["highlight_index"] == 2
    print("  ✓ yageo_rev_yoy 邊界燈號")


def _ai_closes(above_n: int, below_n: int, short_n: int) -> dict:
    syms = list(ai.BASKET)
    out, i = {}, 0
    for _ in range(above_n):
        out[syms[i]] = UP; i += 1
    for _ in range(below_n):
        out[syms[i]] = DOWN; i += 1
    for _ in range(short_n):
        out[syms[i]] = SHORT; i += 1
    return {"closes": out}


def _check_ai() -> None:
    assert ai._compute(_ai_closes(1, 4, 1)).light == "red"      # 20% (<40)
    assert ai._compute(_ai_closes(2, 3, 1)).light == "yellow"   # 40% (40-60)
    assert ai._compute(_ai_closes(3, 2, 1)).light == "green"    # 60% (>=60)
    assert ai._compute(_ai_closes(5, 1, 0)).light == "green"    # 83%
    assert ai._compute(_ai_closes(0, 0, 6)).light == "gray"     # 全略過
    r = ai._compute(_ai_closes(3, 2, 1))
    assert r.extra["percent"] == 60.0 and r.value_label == "廣度 60%"
    print("  ✓ ai_breadth 邊界燈號")


def _mlcc_closes(kind: str) -> dict:
    if kind == "up":
        s = [100.0 + i for i in range(60)]        # 強升
    elif kind == "down":
        s = [200.0 - i for i in range(60)]        # 強跌
    else:
        s = [150.0 + (i % 2) for i in range(60)]  # 貼近均線、平
    return {"closes": {sym: list(s) for sym in mlcc.BASKET}}


def _check_mlcc() -> None:
    assert mlcc._compute(_mlcc_closes("up")).light == "green"
    assert mlcc._compute(_mlcc_closes("down")).light == "red"
    assert mlcc._compute(_mlcc_closes("flat")).light == "yellow"
    assert mlcc._compute({"closes": {}}).light == "gray"
    print("  ✓ mlcc_basket_ma 邊界燈號")


def _check_support_panels() -> None:
    import signals.memory_rs as mem
    import signals.raw_materials as raw
    import signals.watchlist as wl

    all_up = lambda names: {"closes": {s: UP for s in names}}
    all_down = lambda names: {"closes": {s: DOWN for s in names}}

    assert mem._compute(all_up(mem.NAMES)).light == "green"
    assert mem._compute(all_down(mem.NAMES)).light == "red"
    assert mem._compute({"closes": {}}).light == "gray"
    assert raw._compute(all_up(raw.NAMES)).light == "green"
    assert raw._compute(all_down(raw.NAMES)).light == "red"
    assert wl._compute(all_up(wl.WATCH)).light == "green"
    assert wl._compute({"closes": {}}).light == "gray"
    # table widget 需帶 columns + rows
    r = mem._compute(all_up(mem.NAMES))
    assert r.extra.get("columns") and len(r.rows) == len(mem.NAMES)
    print("  ✓ 支援面板（memory_rs / raw_materials / watchlist）")


def _check_demo_pipeline() -> None:
    """用 demo fixtures 跑一遍所有 signal 的 fetch→compute，驗證離線全流程 + 預期燈號。"""
    cache = DayCache(config.CACHE_DIR, demo=True, fixtures_dir=config.DEMO_FIXTURES_DIR)
    lights = {}
    for spec in discover():
        inputs = {b.key: cache.get_or_fetch(b.source, b.params, SOURCE_REGISTRY[b.source])
                  for b in spec.bindings}
        lights[spec.id] = spec.compute(inputs).light

    assert lights["yageo_rev_yoy"] == "red", lights
    assert lights["mlcc_basket_ma"] == "yellow", lights
    assert lights["ai_breadth"] == "green", lights
    assert lights["memory_rs"] in {"red", "yellow", "green"}, lights
    assert all(v != "gray" for v in lights.values()), f"demo 有訊號 gray：{lights}"
    print(f"  ✓ demo 全流程離線通過：{lights}")


def main() -> int:
    print("Phase 2 驗證中…")
    _check_yageo()
    _check_ai()
    _check_mlcc()
    _check_support_panels()
    _check_demo_pipeline()
    print("Phase 2 驗證通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
