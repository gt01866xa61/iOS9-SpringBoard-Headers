"""Signal 8 — 導線架四雄籃 vs 50MA（資金面：最缺不一定最漲）。

追什麼：導線架四雄（2351 順德、6548 長科、5285 界霖、2486 一詮）等權股價籃
        對 50 日均線的位置與斜率。缺貨是基本面、股價是資金面，兩條線分開看——
        「市場在搶資金、故事太多，sentiment 轉差時好東西也沒人買」。
長相　：一條 sparkline（籃走勢）＋50MA 灰虛線。動起來＝貼著均線橫盤、跌破、或站穩向上。
狀態　：🟢 站上 50MA 且向上＝資金開始買單；🟡 貼近/橫盤＝基本面與資金面分歧（現況）；
        🔴 跌破 50MA 且轉折＝資金退潮、題材失寵。
資料　：yfinance 收盤（6548 上櫃 → .TWO、其餘上市 .TW，已逐檔查證交易所）。每交易日更新。
來源　：股癌 EP678——產業缺貨（基本面）與股價表現（資金面）是兩條線，
        別把前者直接當買進理由。
"""
from __future__ import annotations

from core.indicators import basket_index, ma_slope_pct, mean, unpack_closes
from core.spec import DataBinding, SignalResult, SignalSpec

# === 門檻常數 ===
# 順德、長科（上櫃→.TWO）、界霖、一詮（交易所後綴已逐檔查證，勿憑直覺改）
BASKET = ("2351.TW", "6548.TWO", "5285.TW", "2486.TW")
MA_WINDOW = 50
SLOPE_LOOKBACK = 5        # 50MA 斜率取近幾日
NEAR_MA_PCT = 1.5         # 距 50MA 在 ±此% 內視為「貼近」（黃燈分歧）
OVERHEAT_PCT = 25.0       # 乖離超過此% 加註過熱提醒（燈仍照規則判，僅提示）
SHOWN_BARS = 60           # sparkline 顯示根數（同時畫籃子與 50MA 虛線）


def _compute(inputs: dict) -> SignalResult:
    closes, _ = unpack_closes(inputs.get("closes"))
    idx = basket_index([closes.get(s) or [] for s in BASKET])
    if len(idx) < MA_WINDOW:
        return SignalResult(light="gray")

    ma_now = mean(idx[-MA_WINDOW:])
    dist_pct = (idx[-1] / ma_now - 1) * 100 if ma_now else 0.0
    slope = ma_slope_pct(idx, MA_WINDOW, SLOPE_LOOKBACK)
    slope_pct = 0.0 if slope is None else slope

    if dist_pct < 0 and slope_pct < 0:            # 跌破 50MA 且均線下彎
        light = "red"
    elif dist_pct > NEAR_MA_PCT and slope_pct > 0:  # 明確站上且向上
        light = "green"
    else:                                          # 貼近均線／橫盤／分歧
        light = "yellow"

    # 圖上同時畫「籃子(綠/紅實線)」與「50MA(灰虛線)」，站上/跌破直接可見
    shown = min(SHOWN_BARS, len(idx) - MA_WINDOW + 1)
    series = [round(x, 2) for x in idx[-shown:]]
    ma_series = [round(mean(idx[i - MA_WINDOW + 1:i + 1]), 2)
                 for i in range(len(idx) - shown, len(idx))]

    overheat = "・乖離偏大，留意均值回歸回檔" if dist_pct > OVERHEAT_PCT else ""
    # 缺料透明化：籃子少檔要明講，等權指數的組成不能悄悄改變
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
            # caption 進 SVG（空間有限只放數字）；note 是圖下方 HTML 行（會換行，放圖例與提醒）
            "caption": f"距MA {dist_pct:+.1f}%、MA斜率 {slope_pct:+.2f}%/{SLOPE_LOOKBACK}日",
            "note": f"實線＝籃子價格、灰虛線＝50日均線{overheat}{lack}",
        },
        detail={"dist_pct": round(dist_pct, 3), "slope_pct": round(slope_pct, 3),
                "ma_now": round(ma_now, 3)},
    )


SIGNAL = SignalSpec(
    id="leadframe_basket_ma",
    name="導線架四雄籃 vs 50MA",
    cluster="leadframe_osat",
    tags=("導線架", "封測", "50MA", "資金面"),
    widget="sparkline",
    bindings=(
        DataBinding(
            key="closes",
            source="yf_close",
            params={"symbols": list(BASKET), "days": 170},
        ),
    ),
    compute=_compute,
    interpretations={
        "green": "四雄籃站穩 50MA 且向上，資金面開始買單上游缺貨題材。",
        "yellow": "籃子貼著均線橫盤——缺貨歸缺貨、股價休息，基本面與資金面分歧。",
        "red": "籃子跌破 50MA 且均線下彎，資金退潮，缺貨題材對股價失效。",
        "gray": "導線架股價資料抓取失敗。",
    },
    cadence="trading_day",
    track="導線架四雄（順德(2351)、長科(6548)、界霖(5285)、一詮(2486)）等權股價籃對 50 日均線的位置與斜率——「最缺不一定最漲」，缺貨是基本面，這條線看資金面到底買不買單。",
    shape="籃子貼著均線橫盤＝資金還沒回來；跌破且均線下彎＝題材失寵；站穩且向上＝資金開始買單缺貨故事。",
    order=8,
    in_master=True,
    unit="%",
)
