"""Signal 3 — AI 類股廣度轉弱。

追什麼：AI 代表籃（NVDA、AVGO、TSM、2330、6669、2327）中，收在 50 日均線之上的
        比例＝廣度。指數/單股會騙人，「多少比例還站在均線上」最能看出是普遍強、
        還是只剩少數撐盤——廣度先壞、指數才壞。
長相　：一條 0–100% 的儀表（gauge），40 / 60 有刻度。動起來＝比例往下掉、破 60→破 40。
狀態　：🟢 >60%＝主題廣泛強勢；🟡 40–60%＝分歧、有股掉隊；🔴 <40%＝AI 股全面轉弱。
資料　：yfinance（美/台）收盤。每交易日更新。
來源　：股癌 EP515 (2025-07-02)。

TODO(Phase 2)：實作 _compute。Phase 1 先回 gray（stub）。
"""
from __future__ import annotations

from core.indicators import above_ma
from core.spec import DataBinding, SignalResult, SignalSpec

# === 門檻常數 ===
BASKET = ("NVDA", "AVGO", "TSM", "2330.TW", "6669.TW", "2327.TW")
MA_WINDOW = 50
RED_BELOW = 40.0          # 站上 50MA 比例 < 此% → RED
YELLOW_BELOW = 60.0       # < 此% → YELLOW，否則 GREEN


def _compute(inputs: dict) -> SignalResult:
    # inputs["closes"] = {symbol: [close, ...]}（舊→新）
    closes = inputs.get("closes") or {}
    above = counted = 0
    rows: list[dict] = []
    for sym in BASKET:
        amv = above_ma(closes.get(sym) or [], MA_WINDOW)
        if amv is None:                       # 個股缺資料不拖垮整體
            rows.append({"symbol": sym, "above": None})
            continue
        counted += 1
        above += int(amv)
        rows.append({"symbol": sym, "above": bool(amv)})

    if counted == 0:
        return SignalResult(light="gray")

    pct = round(100.0 * above / counted, 1)
    light = "red" if pct < RED_BELOW else "yellow" if pct < YELLOW_BELOW else "green"
    return SignalResult(
        light=light,
        value_label=f"{pct:.0f}%",
        rows=rows,
        extra={
            "percent": pct, "min": 0, "max": 100,
            "bands": [
                {"to": RED_BELOW, "light": "red"},
                {"to": YELLOW_BELOW, "light": "yellow"},
                {"to": 100, "light": "green"},
            ],
            "caption": f"{above}/{counted} 檔站上 {MA_WINDOW}MA", "unit": "%",
        },
        detail={"above": above, "counted": counted},
    )


SIGNAL = SignalSpec(
    id="ai_breadth",
    name="AI 類股廣度轉弱",
    cluster="semi_memory_top",
    tags=("AI", "半導體", "廣度", "50MA"),
    widget="gauge",
    bindings=(
        DataBinding(
            key="closes",
            source="yf_close",
            params={"symbols": list(BASKET), "days": 120},
        ),
    ),
    compute=_compute,
    interpretations={
        "green": "多數 AI 權值仍站上 50MA，主升段結構完整。",
        "yellow": "AI 籃廣度轉中性，領軍股撐盤、跟風股走弱，動能鈍化。",
        "red": "過半 AI 股跌破 50MA，廣度惡化，主升段動能流失。",
        "gray": "股價資料抓取失敗。",
    },
    episode_ref="EP515",
    episode_date="2025-07-02",
    cadence="trading_day",
    in_master=True,
    unit="%",
)
