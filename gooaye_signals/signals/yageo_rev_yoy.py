"""Signal 1 — 國巨(2327) 月營收 YoY 轉弱。

追什麼：龍頭國巨(2327)每月營收的年增率(YoY)，是被動元件需求的風向球，也是最難
        作假的硬數據；龍頭營收轉降常領先股價。
長相　：近 12 個月 YoY 長條圖，最新月高亮。動起來＝連續幾根往下掉、由正轉負。
狀態　：🟢 未連降/高檔＝需求熱；🟡 連降 1 月＝動能鈍化；🔴 連降 ≥2 月＝營收動能反轉。
資料　：FinMind 月營收（回傳已對齊、舊→新的 (month, yoy%)）。約每月 10 號更新。
來源　：股癌 EP512 (2025-06-18)。

TODO(Phase 2)：實作 _compute。Phase 1 先回 gray（stub）。
"""
from __future__ import annotations

from core.indicators import consec_declines
from core.spec import DataBinding, SignalResult, SignalSpec

# === 門檻常數（single source of truth）===
STOCK_ID = "2327"
BARS_SHOWN = 12          # 顯示月數
RED_CONSEC = 2           # YoY 連降幾月 = RED


def _compute(inputs: dict) -> SignalResult:
    # inputs["rev"] = [[month "YYYY-MM", yoy%], ...] 已對齊、舊→新（FinMind adapter 產出）
    rev = list(inputs.get("rev") or [])[-BARS_SHOWN:]
    if len(rev) < 2:
        return SignalResult(light="gray")
    labels = [str(m) for m, _ in rev]
    yoy = [float(v) for _, v in rev]

    consec = consec_declines(yoy)
    light = "red" if consec >= RED_CONSEC else "yellow" if consec == 1 else "green"
    return SignalResult(
        light=light,
        value_label=f"YoY {yoy[-1]:+.1f}%",
        series=[round(v, 2) for v in yoy],
        labels=labels,
        extra={"highlight_index": len(yoy) - 1, "unit": "% YoY", "zero_line": True},
        detail={"consecutive_down_months": consec},
    )


SIGNAL = SignalSpec(
    id="yageo_rev_yoy",
    name="國巨(2327) 月營收 YoY",   # 名稱保持中性——「轉弱與否」由燈色判定
    cluster="semi_memory_top",
    tags=("半導體", "被動元件", "MLCC", "月營收", "2327"),
    widget="bar_chart",
    bindings=(
        DataBinding(
            key="rev",
            source="finmind_revenue",
            params={"stock_id": STOCK_ID, "months": BARS_SHOWN + 2},
        ),
    ),
    compute=_compute,
    interpretations={
        "green": "國巨營收年增仍在擴張，被動元件需求未見反轉。",
        "yellow": "YoY 首度轉弱，觀察是否為趨勢起點，可能只是單月雜訊。",
        "red": "YoY 連 2 個月以上走低，記憶體/被動元件循環見頂訊號浮現。",
        "gray": "月營收資料尚未更新或抓取失敗。",
    },
    cadence="monthly",
    track="龍頭國巨(2327)每月營收的年增率(YoY)——被動元件需求風向球，最難作假的硬數據，龍頭營收轉降常領先股價。",
    shape="長條一根根往下、由正轉負；關鍵看「連續下滑幾個月」，連降越久越接近反轉。",
    order=1,
    in_master=True,
    unit="% YoY",
)
