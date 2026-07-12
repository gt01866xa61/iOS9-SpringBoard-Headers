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
import signals.leadframe_basket_ma as lf_basket
import signals.leadframe_rev_yoy as lf_rev
import signals.leadframe_watch as lf_watch
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
    # 缺料透明化：1 檔太短被略過 → caption 明講、不悄悄改分母
    assert "1 檔暫缺料" in r.extra["caption"], r.extra["caption"]
    assert "暫缺" not in ai._compute(_ai_closes(5, 1, 0)).extra["caption"]
    # fetcher 新形狀 {"series": ..., "asof": ...} 同樣可算（與舊形狀同結果）
    new_shape = {"closes": {"series": _ai_closes(3, 2, 1)["closes"], "asof": {}}}
    assert ai._compute(new_shape).extra["percent"] == 60.0
    print("  ✓ ai_breadth 邊界燈號＋缺料揭露＋新舊 fetch 形狀")


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

    # 資料至（asof）：新形狀帶日期 → 每列 quote_row 帶 asof，凍結市場（如美股休市）可自我說明
    syms = list(mem.NAMES)
    dated = {"closes": {"series": {s: UP for s in syms},
                        "asof": {s: ("2026-07-03" if s == "MU" else "2026-07-06") for s in syms}}}
    rows = mem._compute(dated).rows
    by_first = {r["cells"][0]: r for r in rows}
    # 名稱後掛上抓價代號（可溯源）：「美光 (MU)」「南亞科 (2408.TW)」；空格＝手機斷行點
    assert by_first[f'{mem.NAMES["MU"]} (MU)']["asof"] == "2026-07-03"
    assert by_first[f'{mem.NAMES["2408.TW"]} (2408.TW)']["asof"] == "2026-07-06"
    print("  ✓ 支援面板（memory_rs / raw_materials / watchlist）＋每列資料至日期＋名稱掛代號")


def _check_leadframe() -> None:
    """導線架 cluster 三訊號：核心燈色邊界（compute 與既有訊號同構，抽測關鍵行為）。"""
    # 順德月營收 YoY：連降 0/1/2 月 → 綠/黃/紅
    assert lf_rev._compute(_rev([1, 2, 3, 4])).light == "green"
    assert lf_rev._compute(_rev([1, 2, 3, 2])).light == "yellow"
    assert lf_rev._compute(_rev([1, 2, 4, 3, 2])).light == "red"
    assert lf_rev._compute(_rev([1.0])).light == "gray"

    # 四雄籃：強升/強跌/貼均線 → 綠/紅/黃
    up = {"closes": {s: [100.0 + i for i in range(60)] for s in lf_basket.BASKET}}
    down = {"closes": {s: [200.0 - i for i in range(60)] for s in lf_basket.BASKET}}
    flat = {"closes": {s: [150.0 + (i % 2) for i in range(60)] for s in lf_basket.BASKET}}
    assert lf_basket._compute(up).light == "green"
    assert lf_basket._compute(down).light == "red"
    assert lf_basket._compute(flat).light == "yellow"

    # 體檢表：銅列只顯示、不投票——四雄全站上 + 銅跌破 → 仍是綠、分母只算 4
    closes = {s: UP for s in lf_watch.STOCKS}
    closes["HG=F"] = DOWN
    r = lf_watch._compute({"closes": closes})
    assert r.light == "green" and r.value_label == "4/4 站上50MA", (r.light, r.value_label)
    assert len(r.rows) == 5, "銅列要顯示在表格裡"
    print("  ✓ 導線架三訊號（順德YoY / 四雄籃 / 體檢表銅不投票）")


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
    # 導線架 cluster demo：fixtures 設計成全綠（cluster2 綠 → 總燈仍由 cluster1 的黃決定）
    assert lights["leadframe_rev_yoy"] == "green", lights
    assert lights["leadframe_basket_ma"] == "green", lights
    assert lights["leadframe_watch"] == "green", lights
    assert all(v != "gray" for v in lights.values()), f"demo 有訊號 gray：{lights}"
    print(f"  ✓ demo 全流程離線通過：{lights}")


def main() -> int:
    print("Phase 2 驗證中…")
    _check_yageo()
    _check_ai()
    _check_mlcc()
    _check_support_panels()
    _check_leadframe()
    _check_demo_pipeline()
    print("Phase 2 驗證通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
