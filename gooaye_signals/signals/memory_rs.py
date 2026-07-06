"""支援面板 — 記憶體循環相對強度（不計入主燈，佐證用）。

追什麼：記憶體族群（美光、晟碟、三星、SK海力士、南亞科、華邦、威剛、群聯）站上均線
        的相對強弱。南韓大擴產＝觸頂訊號已點火，這裡看記憶體股是否開始轉弱當佐證。
長相　：表格——每檔價格、漲跌%、站上 50MA 綠/紅點、迷你走勢。
狀態　：🟢 多數站上均線＝仍強；🟡 強弱分歧；🔴 多數跌破＝循環轉弱（呼應擴產見頂）。
資料　：yfinance 收盤（美/韓/台）。每交易日更新。
來源　：股癌 EP505 (2025-04-02)。
"""
from __future__ import annotations

from core.indicators import above_ma, breadth_light, quote_row, unpack_closes
from core.spec import DataBinding, SignalResult, SignalSpec

# === 標的（yfinance 代碼 → 顯示名）===
NAMES = {
    "MU": "美光 MU",
    "SNDK": "晟碟 SNDK",
    "005930.KS": "三星電子",
    "000660.KS": "SK海力士",
    "2408.TW": "南亞科",
    "2344.TW": "華邦電",
    "3260.TWO": "威剛",   # 上櫃 → .TWO（.TW 會 404，部署實測抓到的 bug）
    "8299.TWO": "群聯",
}
MA_WINDOW = 50


def _compute(inputs: dict) -> SignalResult:
    closes, asof = unpack_closes(inputs.get("closes"))
    rows: list[dict] = []
    above = counted = 0
    for sym, name in NAMES.items():
        series = closes.get(sym) or []
        rows.append(quote_row(name, series, MA_WINDOW, asof=asof.get(sym, "")))
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
    id="memory_rs",
    name="記憶體循環相對強度",
    cluster="semi_memory_top",
    tags=("記憶體", "DRAM", "NAND", "南韓擴產"),
    widget="table",
    bindings=(
        DataBinding(key="closes", source="yf_close",
                    params={"symbols": list(NAMES), "days": 120}),
    ),
    compute=_compute,
    interpretations={
        "green": "記憶體族群普遍站上均線，循環仍強，擴產利空尚未反映到股價。",
        "yellow": "記憶體族群強弱分歧，留意是否開始領跌。",
        "red": "多數記憶體股跌破均線，循環轉弱，與韓廠大擴產的見頂邏輯呼應。",
        "gray": "記憶體股報價抓取失敗。",
    },
    cadence="trading_day",
    track="記憶體族群（美光、晟碟、三星、SK海力士、南亞科、華邦、威剛、群聯）站上均線的家數——南韓大擴產後，看記憶體股是否開始轉弱當佐證。",
    shape="表格裡綠點變紅點、迷你走勢翻下；跌破均線的家數越多，循環越接近轉折。",
    order=4,
    in_master=False,
    unit="",
)
