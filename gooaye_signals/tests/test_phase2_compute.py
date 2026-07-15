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
import signals.menlo_opensource as menlo
import signals.mlcc_basket_ma as mlcc
import signals.onprem_ai_orders as oo
import signals.onprem_basket_ma as ob
import signals.onprem_events as oe
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
    assert yageo._compute(_rev([1, 2, 3, 4])).light == "green"          # 0 連降且為正
    assert yageo._compute(_rev([1, 2, 3, 2])).light == "yellow"         # 1 連降
    assert yageo._compute(_rev([1, 2, 4, 3, 2])).light == "red"         # 2 連降
    assert yageo._compute(_rev([1.0])).light == "gray"                  # 資料不足
    assert yageo._compute(_rev([-5, -4, -3])).light == "yellow"         # 年減中：降幅收斂≠擴張，水位守門
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


def _lf_rev_inputs(yoys_by_sid: dict) -> dict:
    """組四家營收輸入：{sid: [yoy...]} → {"r<sid>": [[月, yoy], ...]}。"""
    return {f"r{sid}": [[f"2026-{i+1:02d}", v] for i, v in enumerate(ys)]
            for sid, ys in yoys_by_sid.items()}


def _check_leadframe() -> None:
    """導線架 cluster 三訊號：核心燈色邊界（compute 與既有訊號同構，抽測關鍵行為）。"""
    up, down1, down2 = [1, 2, 3, 4], [1, 2, 3, 2], [1, 2, 4, 3, 2]
    sids = [sid for sid, _ in lf_rev.COMPANIES]

    # 四家營收動能：全綠→綠；一家連降1月→黃；兩家連降≥2月→紅（同主燈真值表）
    r = lf_rev._compute(_lf_rev_inputs({s: up for s in sids}))
    assert r.light == "green" and r.value_label == "4/4 擴張中", (r.light, r.value_label)
    assert len(r.rows) == 4 and r.rows[0]["dot"] == "green"
    r = lf_rev._compute(_lf_rev_inputs({sids[0]: down1, sids[1]: up, sids[2]: up, sids[3]: up}))
    assert r.light == "yellow", r.light
    r = lf_rev._compute(_lf_rev_inputs({sids[0]: down2, sids[1]: down2, sids[2]: up, sids[3]: up}))
    assert r.light == "red" and r.value_label == "2/4 擴張中", (r.light, r.value_label)
    # 年減中（YoY<0 但未連降）→ 該家黃、格子標「年減中」——水位守門，不得亮綠說擴張
    r = lf_rev._compute(_lf_rev_inputs({sids[0]: [-5, -4, -3], sids[1]: up, sids[2]: up, sids[3]: up}))
    assert r.light == "yellow" and r.rows[0]["dot"] == "yellow", (r.light, r.rows[0])
    assert r.rows[0]["cells"][2] == "年減中", r.rows[0]["cells"]
    # 一家沒資料 → 該列 gray、不計分母、caption 揭露；caption 帶「資料至」溯源
    r = lf_rev._compute(_lf_rev_inputs({sids[0]: up, sids[1]: up, sids[2]: up}))
    assert r.light == "green" and "1 家暫缺料" in r.extra["caption"], r.extra["caption"]
    assert "資料至 2026-04" in r.extra["caption"], r.extra["caption"]
    assert lf_rev._compute({}).light == "gray"
    # 晚報透明化：一家資料只到前一個月 → 該列 YoY 標「至X月」
    late = _lf_rev_inputs({s: up for s in sids})
    late[f"r{sids[3]}"] = late[f"r{sids[3]}"][:-1]   # 一詮少最新月
    r = lf_rev._compute(late)
    assert "（至3月）" in r.rows[3]["cells"][1], r.rows[3]["cells"]

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


def _check_onprem() -> None:
    """地端/混合雲 cluster 四訊號：核心燈色邊界。"""
    # 訂單動能：HPE QoQ ±20% 三態；缺季跳過以已知相鄰比較；Dell 不影響卡燈
    def orders(hpe_pair, dell_last="green隨便"):
        return {"orders": {
            "as_of": "2026-06-01",
            "hpe": [{"q": "Q1", "orders_b": hpe_pair[0], "backlog_b": 3.0, "src": "t"},
                    {"q": "Qx", "orders_b": None, "backlog_b": 4.0, "src": "t"},
                    {"q": "Q2", "orders_b": hpe_pair[1], "backlog_b": 5.0, "src": "t"}],
            "dell": [{"q": "Q1", "orders_b": 10.0, "backlog_b": 20.0, "src": "t"},
                     {"q": "Q2", "orders_b": 5.0, "backlog_b": 25.0, "src": "t"}],
        }}
    assert oo._compute(orders((1.0, 1.3))).light == "green"    # +30% 放量
    assert oo._compute(orders((1.9, 1.8))).light == "yellow"   # -5% 平
    assert oo._compute(orders((2.0, 1.5))).light == "red"      # -25% 反向
    r = oo._compute(orders((1.9, 1.8)))
    assert r.rows[1]["dot"] == "red", r.rows[1]                # Dell -50% 紅點但不計卡燈
    assert r.value_label.startswith("HPE $1.8B"), r.value_label
    assert oo._compute({}).light == "gray"

    # 事件簿：窗內淨值三態＋窗外事件不計
    def ev(dirs_in, dirs_out=()):
        # 事件擺在 as_of 前 1-3 個月，穩居 180 天窗內
        events = [{"date": f"2026-0{i+4}-01", "camp": "t", "dir": d, "what": "w", "src": "s"}
                  for i, d in enumerate(dirs_in)]
        events += [{"date": "2024-01-01", "camp": "t", "dir": d, "what": "舊", "src": "s"}
                   for d in dirs_out]
        return {"events": {"as_of": "2026-07-01", "events": events}}
    assert oe._compute(ev(["+", "+", "+"])).light == "green"           # net +3
    assert oe._compute(ev(["+", "+", "-"])).light == "yellow"          # net +1
    assert oe._compute(ev(["-", "-", "-"])).light == "red"             # net -3
    assert oe._compute(ev(["+"], dirs_out=["+", "+", "+"])).light == "yellow"  # 窗外不計
    assert oe._compute({}).light == "gray"

    # Menlo：回升/持平/續降
    def mn(vals):
        return {"menlo": {"series": [{"label": f"p{i}", "pct": v, "src": "t"}
                                     for i, v in enumerate(vals)]}}
    assert menlo._compute(mn([13, 11])).light == "red"
    assert menlo._compute(mn([11, 11.5])).light == "yellow"
    assert menlo._compute(mn([11, 14])).light == "green"
    assert menlo._compute(mn([11])).light == "gray"

    # 地端籃：與其他籃同構，抽測綠/紅
    up = {"closes": {s: [100.0 + i for i in range(60)] for s in ob.BASKET}}
    down = {"closes": {s: [200.0 - i for i in range(60)] for s in ob.BASKET}}
    assert ob._compute(up).light == "green"
    assert ob._compute(down).light == "red"
    print("  ✓ 地端/混合雲四訊號（訂單±20%三態 / 事件簿窗與淨值 / Menlo方向 / 籃）")


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
    # 地端/混合雲 cluster demo：籃綠＋訂單黃（未放量預設）＋事件黃＋Menlo紅
    assert lights["onprem_basket_ma"] == "green", lights
    assert lights["onprem_ai_orders"] == "yellow", lights
    assert lights["onprem_events"] == "yellow", lights
    assert lights["menlo_opensource"] == "red", lights
    assert all(v != "gray" for v in lights.values()), f"demo 有訊號 gray：{lights}"
    print(f"  ✓ demo 全流程離線通過：{lights}")


def main() -> int:
    print("Phase 2 驗證中…")
    _check_yageo()
    _check_ai()
    _check_mlcc()
    _check_support_panels()
    _check_leadframe()
    _check_onprem()
    _check_demo_pipeline()
    print("Phase 2 驗證通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
