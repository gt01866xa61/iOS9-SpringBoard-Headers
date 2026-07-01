"""支援面板 — 原物料成本（鈀 / 銀，不計入主燈）。

追什麼：鈀(PA=F)、銀(SI=F) 期貨價。被動元件/半導體的成本推力：金屬漲＝成本推升、
        撐得住漲價邏輯；金屬跌＝成本壓力緩解、漲價動能減弱。
長相　：表格——每項價格、漲跌%、站上 50MA 點、迷你走勢。
狀態　：🟢 同步走揚（撐漲價）；🟡 分歧；🔴 同步走弱（漲價動能減弱）。
資料　：yfinance 期貨收盤。每交易日更新。
來源　：股癌節目多次提及成本面（episode_ref 待補）。
"""
from __future__ import annotations

from core.indicators import above_ma, quote_row
from core.spec import DataBinding, SignalResult, SignalSpec

# === 標的（yfinance 期貨代碼 → 顯示名）===
NAMES = {
    "PA=F": "鈀 Palladium",
    "SI=F": "銀 Silver",
}
MA_WINDOW = 50


def _compute(inputs: dict) -> SignalResult:
    closes = inputs.get("closes") or {}
    rows: list[dict] = []
    above = counted = 0
    for sym, name in NAMES.items():
        series = closes.get(sym) or []
        rows.append(quote_row(name, series, MA_WINDOW))
        amv = above_ma(series, MA_WINDOW)
        if amv is not None:
            counted += 1
            above += int(amv)

    if counted == 0:
        return SignalResult(light="gray", rows=rows,
                            extra={"columns": ["金屬", "價格", "漲跌%", "站上50MA", "趨勢"]})

    light = "green" if above == counted else "red" if above == 0 else "yellow"
    return SignalResult(
        light=light,
        value_label=f"{above}/{counted} 走揚",
        rows=rows,
        extra={"columns": ["金屬", "價格", "漲跌%", "站上50MA", "趨勢"]},
        detail={"above": above, "counted": counted},
    )


SIGNAL = SignalSpec(
    id="raw_materials",
    name="原物料成本（鈀 / 銀）",
    cluster="semi_memory_top",
    tags=("原物料", "鈀", "銀", "成本"),
    widget="table",
    bindings=(
        DataBinding(key="closes", source="yf_close",
                    params={"symbols": list(NAMES), "days": 120}),
    ),
    compute=_compute,
    interpretations={
        "green": "鈀、銀同步走高，成本推升，支撐漲價邏輯。",
        "yellow": "金屬價格分歧，成本訊號不明確。",
        "red": "鈀、銀同步走弱，成本壓力緩解，漲價動能減弱。",
        "gray": "金屬報價抓取失敗。",
    },
    episode_ref="?",
    episode_date="2025-05-01",
    cadence="trading_day",
    in_master=False,
    unit="",
)
