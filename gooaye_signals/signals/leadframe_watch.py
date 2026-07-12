"""支援面板 — 導線架四雄 ＋ 銅價（不計入主燈，佐證用）。

追什麼：導線架四雄逐檔體檢＋銅期貨(HG=F)。銅是導線架最核心原材料、報價與國際
        銅價高度連動——銅價走揚＝成本推升撐漲價邏輯，走弱＝漲價動能減弱。
長相　：表格——每檔價格、漲跌%、站上 50MA 綠/紅點、迷你走勢；銅列為成本參考。
狀態　：🟢 四雄多數站上均線＝個股體質偏強；🟡 強弱互見；🔴 多數跌破＝體質轉弱。
        燈號只數四檔股票，銅列不投票（成本推力與股價強弱是兩件事，不混算）。
資料　：yfinance 收盤（台股＋COMEX 銅期貨）。每交易日更新。
來源　：股癌 EP678——漲價約 10-20%、隨國際銅價。
"""
from __future__ import annotations

from core.indicators import above_ma, breadth_light, quote_row, unpack_closes
from core.spec import DataBinding, SignalResult, SignalSpec

# === 標的（yfinance 代碼 → 顯示名；表格會顯示成「名稱 (代號)」）===
STOCKS = {
    "2351.TW": "順德",
    "6548.TWO": "長科",   # 上櫃 → .TWO（已查證，勿憑直覺改）
    "5285.TW": "界霖",
    "2486.TW": "一詮",
}
COPPER = {"HG=F": "銅"}   # 成本推力參考列，不計入燈號
NAMES = {**STOCKS, **COPPER}
MA_WINDOW = 50


def _compute(inputs: dict) -> SignalResult:
    closes, asof = unpack_closes(inputs.get("closes"))
    rows: list[dict] = []
    above = counted = 0
    for sym, name in NAMES.items():
        series = closes.get(sym) or []
        rows.append(quote_row(name, series, MA_WINDOW, asof=asof.get(sym, ""), symbol=sym))
        if sym in STOCKS:               # 銅列只顯示、不投票
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
               "caption": "點＝收盤站上(綠)/跌破(紅) 50MA・線＝近月走勢方向・銅＝成本推力參考，不計入燈號"},
        detail={"above": above, "counted": counted},
    )


SIGNAL = SignalSpec(
    id="leadframe_watch",
    name="導線架四雄 ＋ 銅價",
    cluster="leadframe_osat",
    tags=("導線架", "銅", "成本", "個股體檢"),
    widget="table",
    bindings=(
        DataBinding(key="closes", source="yf_close",
                    params={"symbols": list(NAMES), "days": 120}),
    ),
    compute=_compute,
    interpretations={
        "green": "導線架四雄多數站上均線，個股體質偏強。",
        "yellow": "四雄強弱互見，資金選邊中。",
        "red": "四雄多數跌破均線，個股體質轉弱。",
        "gray": "導線架報價抓取失敗。",
    },
    cadence="trading_day",
    track="導線架四雄逐檔體檢＋銅期貨(HG=F)——導線架報價隨國際銅價連動：股票列看誰站上均線，銅列看成本推力還在不在。",
    shape="一列一檔：綠/紅點＝站上/跌破 50MA；銅列走揚＝成本推升撐漲價、走弱＝漲價動能減弱（銅不計入本卡燈號）。",
    order=9,
    in_master=False,
    unit="",
)
