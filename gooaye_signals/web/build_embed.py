"""把最新的 signals.json 內嵌回 web/index.html 的 fallback <script>，讓頁面永不空白。

在 build.py 之後跑（CI 或本機）。優先用 web/data/signals.json，沒有就用 data/signals.json。
只替換 <script id="embedded"> 內容，不動其他 HTML。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config

INDEX = config.WEB_DIR / "index.html"
_PATTERN = re.compile(
    r'(<script id="embedded" type="application/json">)(.*?)(</script>)',
    re.DOTALL,
)


def main() -> int:
    src = config.WEB_DATA_JSON if config.WEB_DATA_JSON.exists() else config.SIGNALS_JSON
    if not src.exists():
        print(f"找不到 {src}，請先跑 build.py", file=sys.stderr)
        return 1

    payload = src.read_text(encoding="utf-8").strip()
    html = INDEX.read_text(encoding="utf-8")
    if not _PATTERN.search(html):
        print("index.html 找不到 embedded <script> 區塊", file=sys.stderr)
        return 1

    new_html = _PATTERN.sub(lambda m: m.group(1) + "\n" + payload + "\n" + m.group(3), html)
    INDEX.write_text(new_html, encoding="utf-8")
    print(f"已把 {src.name} 內嵌進 {INDEX.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
