"""支援面板 — 觀測名單（不計入主燈）。

追什麼：跨主題最想快速體檢的個股（國巨、華新科、台積電、南亞科、緯穎、NVDA、美光）。
長相　：表格——每檔價格、漲跌%、站上 50MA 綠/紅點、迷你走勢，最快的個股體檢。
狀態　：🟢 多數站上均線＝體質偏強；🟡 強弱互見；🔴 多數跌破＝體質轉弱。
資料　：yfinance 收盤。每交易日更新。
"""
from __future__ import annotations

from core.indicators import above_ma, breadth_light, quote_row, unpack_closes
from core.spec import DataBinding, SignalResult, SignalSpec

# === 標的（yfinance 代碼 → 顯示名；表格會顯示成「名稱(代號)」）===
WATCH = {
    "2327.TW": "國巨",
    "2492.TW": "華新科",
    "2330.TW": "台積電",
    "2408.TW": "南亞科",
    "6669.TW": "緯穎",
    "NVDA": "輝達",
    "MU": "美光",
}
MA_WINDOW = 50


def _compute(inputs: dict) -> SignalResult:
    closes, asof = unpack_closes(inputs.get("closes"))
    rows: list[dict] = []
    above = counted = 0
    for sym, name in WATCH.items():
        series = closes.get(sym) or []
        rows.append(quote_row(name, series, MA_WINDOW, asof=asof.get(sym, ""), symbol=sym))
        amv = above_ma(series, MA_WINDOW)
        if amv is not None:
            counted += 1
            above += int(amv)

    if counted == 0:
        return SignalResult(light="gray", rows=rows,
                            extra={"columns": ["標的", "價格", "漲跌%", "站上50MA", "趨勢"]})

    return SignalResult(
        light=breadth_light(above, counted),
        value_label=f"{above}/{counted} 站上50MA",
        rows=rows,
        extra={"columns": ["標的", "價格", "漲跌%", "站上50MA", "趨勢"],
               "caption": "點＝收盤站上(綠)/跌破(紅) 50MA・線＝近月走勢方向(綠漲紅跌)"},
        detail={"above": above, "counted": counted},
    )


SIGNAL = SignalSpec(
    id="watchlist",
    name="觀測名單",
    cluster="semi_memory_top",
    tags=("觀測名單", "個股體檢"),
    widget="table",
    bindings=(
        DataBinding(key="closes", source="yf_close",
                    params={"symbols": list(WATCH), "days": 120}),
    ),
    compute=_compute,
    interpretations={
        "green": "觀測名單多數站上均線，個股體質偏強。",
        "yellow": "觀測名單強弱互見，分歧加大。",
        "red": "觀測名單多數跌破均線，個股體質轉弱。",
        "gray": "觀測名單報價抓取失敗。",
    },
    cadence="trading_day",
    track="跨主題最想快速體檢的個股（國巨(2327)、華新科(2492)、台積電(2330)、南亞科(2408)、緯穎(6669)、輝達(NVDA)、美光(MU)）——最快的一眼個股體檢。",
    shape="一列一檔：綠/紅點＝站上/跌破 50MA，迷你走勢看方向；紅點變多＝名單體質轉弱。",
    order=6,
    in_master=False,
    unit="",
)
