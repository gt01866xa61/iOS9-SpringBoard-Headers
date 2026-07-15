"""Signal 10 — 地端伺服器商籃 vs 50MA（資金面：市場信不信這個劇本）。

追什麼：DELL＋HPE 等權股價籃對 50 日均線——賣地端 AI 伺服器的兩家指標商。
        訂單一季才公布一次，股價天天跳且常比財報早反映；這條線是「提前聞味道」
        的溫度計，單獨看有雜訊，要跟訂單與事件簿互相印證。
長相　：sparkline 籃走勢＋50MA 灰虛線。站上向上／貼線橫盤／跌破下彎。
狀態　：🟢 站上且向上＝資金押這個故事；🟡 貼線橫盤＝觀望；🔴 跌破下彎＝資金否決。
資料　：yfinance 收盤（NYSE）。每交易日更新。SMCI 不收——單一 CSP 客戶占 62.6%
        營收（FY26Q2 10-Q），企業地端代表性最弱。
來源　：Satya「反向資訊悖論」文（2026-07-12）後的地端/混合雲討論串。
"""
from __future__ import annotations

from core.indicators import basket_index, ma_slope_pct, mean, unpack_closes
from core.spec import DataBinding, SignalResult, SignalSpec

# === 門檻常數 ===
BASKET = ("DELL", "HPE")
MA_WINDOW = 50
SLOPE_LOOKBACK = 5        # 50MA 斜率取近幾日
NEAR_MA_PCT = 1.5         # 距 50MA 在 ±此% 內視為「貼近」
OVERHEAT_PCT = 25.0       # 乖離超過此% 加註過熱提醒
SHOWN_BARS = 60


def _compute(inputs: dict) -> SignalResult:
    closes, _ = unpack_closes(inputs.get("closes"))
    idx = basket_index([closes.get(s) or [] for s in BASKET])
    if len(idx) < MA_WINDOW:
        return SignalResult(light="gray")

    ma_now = mean(idx[-MA_WINDOW:])
    dist_pct = (idx[-1] / ma_now - 1) * 100 if ma_now else 0.0
    slope = ma_slope_pct(idx, MA_WINDOW, SLOPE_LOOKBACK)
    slope_pct = 0.0 if slope is None else slope

    if dist_pct < 0 and slope_pct < 0:
        light = "red"
    elif dist_pct > NEAR_MA_PCT and slope_pct > 0:
        light = "green"
    else:
        light = "yellow"

    shown = min(SHOWN_BARS, len(idx) - MA_WINDOW + 1)
    series = [round(x, 2) for x in idx[-shown:]]
    ma_series = [round(mean(idx[i - MA_WINDOW + 1:i + 1]), 2)
                 for i in range(len(idx) - shown, len(idx))]

    overheat = "・乖離偏大，留意均值回歸回檔" if dist_pct > OVERHEAT_PCT else ""
    used = sum(1 for s in BASKET if closes.get(s))
    lack = f"・{len(BASKET) - used} 檔暫缺料，籃子以 {used} 檔計" if used < len(BASKET) else ""
    return SignalResult(
        light=light,
        value_label=f"距MA {dist_pct:+.1f}%",
        series=series,
        extra={
            "ma_series": ma_series,
            "slope_pct": round(slope_pct, 2),
            "ma_window": MA_WINDOW,
            "caption": f"距MA {dist_pct:+.1f}%、MA斜率 {slope_pct:+.2f}%/{SLOPE_LOOKBACK}日",
            "note": f"實線＝DELL+HPE 等權籃、灰虛線＝50日均線{overheat}{lack}",
        },
        detail={"dist_pct": round(dist_pct, 3), "slope_pct": round(slope_pct, 3),
                "ma_now": round(ma_now, 3)},
    )


SIGNAL = SignalSpec(
    id="onprem_basket_ma",
    name="地端伺服器商籃 vs 50MA",
    cluster="onprem_hybrid",
    tags=("地端AI", "混合雲", "伺服器", "50MA", "資金面"),
    widget="sparkline",
    bindings=(
        DataBinding(key="closes", source="yf_close",
                    params={"symbols": list(BASKET), "days": 170}),
    ),
    compute=_compute,
    interpretations={
        "green": "籃子站穩 50MA 且向上，資金正在押「企業地端 AI」的故事。",
        "yellow": "籃子貼著均線橫盤，市場觀望——等訂單數字說話。",
        "red": "籃子跌破 50MA 且均線下彎，資金否決這個劇本。",
        "gray": "股價資料抓取失敗。",
    },
    cadence="trading_day",
    track="DELL＋HPE 等權股價籃對 50 日均線——賣地端 AI 伺服器的兩家指標商（Dell 股價混 PC 與 neocloud 生意、HPE 較純，溫度計有稀釋）。股價天天跳、常比季報早反映；這是「提前聞味道」的溫度計，單獨有雜訊，要跟訂單卡互相印證。",
    shape="籃子先站上且向上＝有人先知道了什麼（等下一季訂單驗證）；訂單好但籃子橫盤＝市場不買帳——與導線架組「兩條線」同一套讀法。",
    order=10,
    in_master=True,
    unit="%",
)
