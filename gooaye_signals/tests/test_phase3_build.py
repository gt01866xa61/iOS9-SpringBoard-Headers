"""Phase 3 驗證：build.py 端到端（demo）+ 失敗隔離 + last-good-stale + 整輪保底 + 原子寫。

跑法（在 gooaye_signals/ 目錄下）：
    python tests/test_phase3_build.py
一律走 demo（離線），不需金鑰、不打網路。
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import sys
from dataclasses import replace

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

os.environ["GOOAYE_DEMO"] = "1"  # 強制 demo，須在 import config/build 前設定
os.environ["GOOAYE_FORCE_HISTORY"] = "1"  # demo 預設不寫燈史；測試強制開啟以驗證該邏輯

import build  # noqa: E402
import config  # noqa: E402
from core.spec import SignalResult  # noqa: E402
from registry import discover as _real_discover  # noqa: E402

# 燈史導向 gitignore 的 cache/ 暫存檔——測試絕不可刪改 bot 維護的真實 data/history.json
config.HISTORY_JSON = config.CACHE_DIR / "test_history.json"

REQUIRED_TOP = {"schema_version", "generated_at", "master_light", "clusters", "errors", "changes"}


def _clean() -> None:
    if config.SIGNALS_JSON.exists():
        config.SIGNALS_JSON.unlink()
    if config.HISTORY_JSON.exists():
        config.HISTORY_JSON.unlink()
    if config.CACHE_DIR.exists():
        shutil.rmtree(config.CACHE_DIR)


def _load() -> dict:
    return json.loads(config.SIGNALS_JSON.read_text(encoding="utf-8"))


def _find_card(data: dict, sid: str) -> dict:
    for cl in data["clusters"]:
        for c in cl["signals"] + cl["supporting"]:
            if c["id"] == sid:
                return c
    raise KeyError(sid)


def _check_full_build() -> None:
    _clean()
    assert build.main() == 0
    data = _load()
    assert REQUIRED_TOP.issubset(data), f"缺頂層欄位：{set(data) ^ REQUIRED_TOP}"
    assert data["schema_version"] == config.SCHEMA_VERSION
    assert data["generated_at"].endswith("+08:00"), data["generated_at"]
    assert data["master_light"] in {"red", "yellow", "green", "gray"}
    assert data["clusters"], "至少要有一個 cluster"

    cl = data["clusters"][0]
    assert cl["master"]["light"] == "yellow", cl["master"]  # 國巨紅 + MLCC黃 + AI綠 → 黃
    assert data["master_light"] == "yellow", data["master_light"]
    # 每張卡都帶前端必需欄位（含三個必答問題：track / shape / interpretations 全燈對照）
    for c in cl["signals"] + cl["supporting"]:
        for k in ("widget", "light", "interpretation", "widget_data", "ok", "stale",
                  "track", "shape", "order", "interpretations"):
            assert k in c, f"{c['id']} 缺 {k}"
        assert set(c["interpretations"]) >= {"green", "yellow", "red", "gray"}, c["id"]
    # 排序 = 擴充順序（order 欄位），不是檔名字母序
    assert [c["id"] for c in cl["signals"]] == ["yageo_rev_yoy", "mlcc_basket_ma", "ai_breadth"]
    assert [c["id"] for c in cl["supporting"]] == ["memory_rs", "raw_materials", "watchlist"]
    assert _find_card(data, "yageo_rev_yoy")["light"] == "red"
    assert not config.SIGNALS_JSON.with_suffix(".json.tmp").exists(), "殘留 .tmp（原子寫失敗）"

    # 第二 cluster（導線架/封測）：order=2 排第二、demo 全綠；總燈仍取較嚴重的黃且點名主題
    assert len(data["clusters"]) == 3, [c["id"] for c in data["clusters"]]
    cl2 = data["clusters"][1]
    assert cl2["id"] == "leadframe_osat"
    assert [c["id"] for c in cl2["signals"]] == ["leadframe_rev_yoy", "leadframe_basket_ma"]
    assert [c["id"] for c in cl2["supporting"]] == ["leadframe_watch"]
    assert cl2["master"]["light"] == "green", cl2["master"]
    assert "半導體" in data["master_reason"], data["master_reason"]

    # 第三 cluster（地端/混合雲）：籃綠＋訂單黃 → 主題黃（未驗證預設）
    cl3 = data["clusters"][2]
    assert cl3["id"] == "onprem_hybrid"
    assert [c["id"] for c in cl3["signals"]] == ["onprem_basket_ma", "onprem_ai_orders"]
    assert [c["id"] for c in cl3["supporting"]] == ["onprem_events", "menlo_opensource"]
    assert cl3["master"]["light"] == "yellow", cl3["master"]
    print("  ✓ 全流程 demo build → schema-valid、三 cluster、主燈黃、原子寫")


def _check_last_good_stale() -> None:
    """先跑成功一輪填 last-good，再讓某 signal compute raise → 該卡走 last-good + stale。"""
    _clean()
    assert build.main() == 0                     # 第一輪成功，存 last-good
    good_light = _find_card(_load(), "ai_breadth")["light"]

    orig = _real_discover()

    def _boom(_inputs):
        raise RuntimeError("模擬 compute 爆炸")

    patched = [replace(s, compute=_boom) if s.id == "ai_breadth" else s for s in orig]
    build.discover = lambda: patched            # monkeypatch build 命名空間裡的 discover
    try:
        assert build.main() == 0                 # 單卡爆炸不影響整體 exit code
        data = _load()
        ai = _find_card(data, "ai_breadth")
        assert ai["stale"] is True and ai["ok"] is False, ai
        assert ai["light"] == good_light, (ai["light"], good_light)   # 沿用上一版燈
        assert ai["error"], "應記錄 error"
        assert any(e["signal_id"] == "ai_breadth" for e in data["errors"]), data["errors"]
        # 其他卡仍正常
        assert _find_card(data, "yageo_rev_yoy")["ok"] is True
    finally:
        build.discover = _real_discover
    print("  ✓ 單一 signal 爆炸 → last-good + stale + errors[]，其餘完好、exit 0")


def _check_whole_run_backstop() -> None:
    """全部 signal 都 gray（無 last-good）且已有舊檔 → 保留舊檔、不覆蓋、exit 0。"""
    _clean()
    assert build.main() == 0
    before = config.SIGNALS_JSON.read_text(encoding="utf-8")
    # 清掉 last-good，讓失敗只能是 gray（無 fallback）
    if config.CACHE_DIR.exists():
        shutil.rmtree(config.CACHE_DIR)

    orig = _real_discover()

    def _boom(_inputs):
        raise RuntimeError("all down")

    patched = [replace(s, compute=_boom) for s in orig]
    build.discover = lambda: patched
    try:
        assert build.main() == 0
        after = config.SIGNALS_JSON.read_text(encoding="utf-8")
        assert after == before, "整輪失敗時不該覆蓋舊 signals.json"
    finally:
        build.discover = _real_discover
    print("  ✓ 整輪無可用資料 → 保留上一版 signals.json（保底）")


def _check_history_and_changes() -> None:
    """燈號歷史：首輪建檔無變化 → 造昨日不同燈 → 偵測變燈 + 檔案裁剪。"""
    _clean()
    assert build.main() == 0
    data = _load()
    assert data["changes"] == [], data["changes"]
    ai = _find_card(data, "ai_breadth")
    assert len(ai["history"]) == 1 and ai["history"][0][1] == ai["light"]
    assert ai["changed"] is False and ai["prev_light"] is None

    # 造「昨天 ai_breadth 是紅」→ 今輪(綠)應偵測 紅→綠；yageo 塞 59 筆驗證裁剪
    hist = json.loads(config.HISTORY_JSON.read_text(encoding="utf-8"))
    hist["signals"]["ai_breadth"] = [["2000-01-01", "red"]]
    hist["signals"]["yageo_rev_yoy"] = (
        [[f"1999-01-{i:02d}", "green"] for i in range(1, 32)]
        + [[f"1999-02-{i:02d}", "green"] for i in range(1, 29)]
    )
    config.HISTORY_JSON.write_text(json.dumps(hist), encoding="utf-8")

    assert build.main() == 0
    data = _load()
    ai = _find_card(data, "ai_breadth")
    assert ai["changed"] is True and ai["prev_light"] == "red", ai["prev_light"]
    assert any(c["id"] == "ai_breadth" and c["from"] == "red" and c["to"] == ai["light"]
               for c in data["changes"]), data["changes"]
    hist2 = json.loads(config.HISTORY_JSON.read_text(encoding="utf-8"))
    assert len(hist2["signals"]["yageo_rev_yoy"]) <= config.HISTORY_KEEP_DAYS
    assert len(ai["history"]) <= config.HISTORY_SHOW_DAYS
    print("  ✓ 燈號歷史：首輪建檔、變燈偵測(紅→綠)、保留天數裁剪")


def main() -> int:
    print("Phase 3 驗證中…")
    _check_full_build()
    _check_last_good_stale()
    _check_whole_run_backstop()
    _check_history_and_changes()
    _clean()
    print("Phase 3 驗證通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
