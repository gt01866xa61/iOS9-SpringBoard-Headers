"""支援面板 — 原物料成本（鈀 / 銀，不計入主燈）。

追什麼：鈀(PA=F)、銀(SI=F) 期貨價。被動元件/半導體的成本推力：金屬漲＝成本推升、
        撐得住漲價邏輯；金屬跌＝成本壓力緩解、漲價動能減弱。
長相　：表格——每項價格、漲跌%、站上 50MA 點、迷你走勢。
狀態　：🟢 同步走揚（撐漲價）；🟡 分歧；🔴 同步走弱（漲價動能減弱）。
資料　：yfinance 期貨收盤。每交易日更新。
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
        value_label=f"{above}/{counted} 站上50MA",
        rows=rows,
        extra={"columns": ["金屬", "價格", "漲跌%", "站上50MA", "趨勢"],
               "caption": "點＝收盤站上(綠)/跌破(紅) 50MA・線＝近月走勢方向(綠漲紅跌)・漲跌%為單日波動，燈號看均線位置"},
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
        "green": "鈀、銀皆站上 50 日均線，成本趨勢向上，支撐漲價邏輯。",
        "yellow": "一站上一跌破，成本趨勢分歧、訊號不明確。",
        "red": "鈀、銀皆跌破 50 日均線，成本推力轉弱，漲價故事鬆動。",
        "gray": "金屬報價抓取失敗。",
    },
    cadence="trading_day",
    track="鈀、銀期貨價——被動元件/半導體的成本推力：金屬價格趨勢向上＝成本推升撐漲價邏輯，趨勢向下＝漲價動能減弱。",
    shape="看「站上50MA」欄的點：兩點同綠＝成本推升；同紅＝成本推力轉弱；分歧＝訊號不明。",
    order=5,
    in_master=False,
    unit="",
)
