"""Phase 4 驗證：前端契約（不需瀏覽器的結構檢查）。

跑法（在 gooaye_signals/ 目錄下）：
    python tests/test_phase4_frontend.py
會先 demo build + 內嵌，再檢查 index.html 的 widget dispatch、schema guard、內嵌 fallback 同構。
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

os.environ["GOOAYE_DEMO"] = "1"

import build  # noqa: E402
import config  # noqa: E402
from core.spec import WIDGET_NAMES  # noqa: E402

EMBED_RE = re.compile(
    r'<script id="embedded" type="application/json">(.*?)</script>', re.DOTALL)
INDEX = config.WEB_DIR / "index.html"


def _prep() -> None:
    import importlib
    import web.build_embed as be
    assert build.main() == 0
    importlib.reload(be)
    assert be.main() == 0


def _check_index() -> None:
    html = config.WEB_DIR.joinpath("index.html").read_text(encoding="utf-8")

    # 1. 五種 widget 都在 dispatch 表
    for w in WIDGET_NAMES:
        assert re.search(rf"\b{re.escape(w)}\s*:", html), f"index.html WIDGETS 缺 {w}"
    assert "renderUnknown" in html, "缺未知 widget 的降級處理"

    # 2. schema_version guard
    assert "const SCHEMA" in html and "schema_version===SCHEMA" in html, "缺 schema_version guard"

    # 3. 自動刷新 + 回前景刷新；fallback 必須先畫，live 抓取有 timeout、去重與防舊覆新
    assert "setInterval(load" in html and "visibilitychange" in html, "缺自動刷新"
    fallback_pos = html.index("render(embeddedData, false);")
    background_pos = html.rindex("\nload();")
    assert fallback_pos < background_pos, "embedded fallback 必須先 render，再背景抓 live"
    assert all(token in html for token in (
        "FETCH_TIMEOUT_MS", "AbortController", "controller.abort()",
        "if(activeLoad) return activeLoad", "seq===requestSeq",
    )), "live fetch 缺 timeout／request 去重／防舊 request 覆寫"

    # 3b. 三層式窄卡：details/summary 掃視層、燈帶、變化置頂橫幅、重繪保留展開狀態
    assert '<details class="card' in html, "缺窄卡 details 結構"
    assert "stripHTML" in html, "缺燈號歷史帶 renderer"
    assert 'id="changes"' in html and "今日燈號變化" in html, "缺今日變化橫幅"
    assert "CSS.escape" in html and "keepOpen" in html, "缺重繪後還原展開狀態"
    assert all(token in html for token in (
        "lastRenderedJSON", "dataChanged", "activeId", "summary.focus({preventScroll:true})",
    )), "缺資料未變不重畫／重畫後焦點還原"
    assert "miniFor" in html, "缺掃視層縮圖"

    # 3c. 表格列的「資料至」標示：休市市場的凍結報價要自我說明，不像壞掉
    assert "maxAsof" in html and "資料至" in html, "缺表格列資料至（asof）標示"

    # 3d. row 來源與 signal 真實資料日期：純文字來源不當 href，僅 http(s) source_url 可連
    assert all(token in html for token in (
        "function safeHTTPURL", 'url.protocol==="http:"', 'url.protocol==="https:"',
        'lower.startsWith("http://")', 'lower.startsWith("https://")',
        "row.source||", "row.source_url||", "const plain=source||rawURL",
        "sig.data_as_of", "!sig.data_as_of&&sig.updated_at",
    )), "缺安全來源顯示或 data_as_of 優先顯示"

    # 3e. 無障礙：狀態更新可被宣告、表格欄位與色點/走勢有文字、裝飾圖不進 accessibility tree
    assert 'aria-live="polite"' in html and 'role="status"' in html, "動態狀態缺 aria-live"
    assert 'scope="col"' in html and 'class="sr-only"' in html, "表格缺欄名／隱藏文字"
    assert 'aria-hidden="true"' in html and "走勢：${trendLabel" in html, "色點或走勢仍只靠視覺"
    assert not re.search(r"\.lg\s*\{[^}]*opacity\s*:\s*\.5", html), "非當前燈文字對比仍被 opacity 壓低"

    # 4. 內嵌 fallback 是合法 JSON、schema 相符、且與 web/data/signals.json 同構
    m = EMBED_RE.search(html)
    assert m, "找不到 embedded <script>"
    assert "</script" not in m.group(1).lower(), "embedded JSON 內含可提早關閉 script 的字串"
    embedded = json.loads(m.group(1))
    assert embedded["schema_version"] == config.SCHEMA_VERSION
    assert embedded.get("clusters"), "內嵌 fallback 應含 clusters"

    served = json.loads(config.WEB_DATA_JSON.read_text(encoding="utf-8"))
    assert embedded == served, "內嵌 fallback 與 web/data/signals.json 不一致"
    assert set(embedded) >= {"master_light", "clusters", "errors", "generated_at"}
    print(f"  [OK] index.html：5 widget dispatch、schema guard、自動刷新、內嵌 fallback 同構"
          f"（{len(embedded['clusters'])} cluster）")


def _check_embed_writer() -> None:
    """內嵌 JSON 必須擋 raw-text 結束標籤，且不改變 JSON 解碼後的資料。"""
    import inspect
    import web.build_embed as be

    raw = json.dumps({"text": "</script><img src=x>", "plain": "1 < 2"}, ensure_ascii=False)
    safe = be._escape_json_for_html(raw)
    assert "<" not in safe and "</script" not in safe.lower(), safe
    assert json.loads(safe) == json.loads(raw), "HTML-safe escaping 改變 JSON 語意"
    source = inspect.getsource(be.main)
    assert "os.replace(tmp, INDEX)" in source, "build_embed 必須用 tmp + os.replace 原子寫"
    print("  [OK] build_embed：script 結束標籤安全處理＋JSON 同義＋原子替換")


def main() -> int:
    print("Phase 4 驗證中…")
    original = INDEX.read_text(encoding="utf-8")  # 測試會 re-embed，跑完還原，不弄髒已 commit 的檔
    try:
        _prep()
        _check_index()
        _check_embed_writer()
    finally:
        INDEX.write_text(original, encoding="utf-8")
    print("Phase 4 驗證通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
