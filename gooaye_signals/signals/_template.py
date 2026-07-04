"""訊號範本 — 複製這個檔開一個新訊號（底線開頭，registry 會跳過本檔）。

新增訊號 SOP（90% 情境）：
  1. cp signals/_template.py signals/<你的id>.py   （或複製最接近的既有訊號）
  2. 改下面每一處：把 id 設成「新檔名」、填門檻常數、bindings、_compute、
     四個 interpretations、episode_ref/date、cluster、widget、tags、in_master。
  3. GOOAYE_DEMO=1 python build.py → 開 web/index.html 確認卡片出現 → 加一條測試 → commit。

三個必答問題（填 docstring 與 metadata）：
  追什麼(track)：__________
  長相(shape) ：__________（挑一個 widget）
  狀態(states)：🟢__ / 🟡__ / 🔴__
"""
from __future__ import annotations

from core.spec import DataBinding, SignalResult, SignalSpec

# === 門檻常數（single source of truth，改參數只動這裡）===
# 例：MA_WINDOW = 50
#     RED_BELOW = 40.0


def _compute(inputs: dict) -> SignalResult:
    """純函式：inputs（由 bindings 抓來的資料）-> SignalResult。不抓網路、不看時鐘。

    務必處理資料不足/缺漏 → return SignalResult(light="gray")。
    """
    # data = inputs["<你的 binding key>"]
    # ...算燈號 light、value_label、series/labels 或 rows、extra...
    return SignalResult(light="gray", value_label="")


SIGNAL = SignalSpec(
    id="_template",                       # ← 必須改成「檔名」（不含 .py）
    name="範本訊號（請改名）",
    cluster="semi_memory_top",            # ← 必須是 core/clusters.py 有的 cluster id
    tags=("範本",),
    widget="light_card",                  # light_card / bar_chart / gauge / sparkline / table
    bindings=(
        DataBinding(key="data", source="yf_close", params={"symbols": ["TSM"], "days": 120}),
    ),
    compute=_compute,
    interpretations={
        "green": "（綠燈代表什麼）",
        "yellow": "（黃燈代表什麼）",
        "red": "（紅燈代表什麼）",
        "gray": "（資料缺漏時顯示什麼）",
    },
    episode_ref="?",                      # 記不清可填 "?"
    episode_date="2025-01-01",
    cadence="trading_day",               # daily / trading_day / monthly / manual
    track="（白話：在盯什麼、為什麼重要——會顯示在卡片名稱下方）",
    shape="（白話：動起來長什麼樣、往哪個方向變化算轉弱——會顯示在圖表下方）",
    order=99,                            # 同 cluster 內顯示順序 = 擴充順序（接在現有最大值後）
    in_master=True,                      # False = 只當佐證面板，不計入主燈
    unit="",
)
