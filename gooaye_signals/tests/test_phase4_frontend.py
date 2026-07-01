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

    # 3. 自動刷新 + 回前景刷新
    assert "setInterval(load" in html and "visibilitychange" in html, "缺自動刷新"

    # 4. 內嵌 fallback 是合法 JSON、schema 相符、且與 web/data/signals.json 同構
    m = EMBED_RE.search(html)
    assert m, "找不到 embedded <script>"
    embedded = json.loads(m.group(1))
    assert embedded["schema_version"] == config.SCHEMA_VERSION
    assert embedded.get("clusters"), "內嵌 fallback 應含 clusters"

    served = json.loads(config.WEB_DATA_JSON.read_text(encoding="utf-8"))
    assert embedded == served, "內嵌 fallback 與 web/data/signals.json 不一致"
    assert set(embedded) >= {"master_light", "clusters", "errors", "generated_at"}
    print(f"  ✓ index.html：5 widget dispatch、schema guard、自動刷新、內嵌 fallback 同構"
          f"（{len(embedded['clusters'])} cluster）")


def main() -> int:
    print("Phase 4 驗證中…")
    original = INDEX.read_text(encoding="utf-8")  # 測試會 re-embed，跑完還原，不弄髒已 commit 的檔
    try:
        _prep()
        _check_index()
    finally:
        INDEX.write_text(original, encoding="utf-8")
    print("Phase 4 驗證通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
