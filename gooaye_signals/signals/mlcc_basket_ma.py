"""Signal 2 — 被動元件籃子 vs 50MA（漲價題材是否還帶得動股價）。

追什麼：被動四雄（2327 國巨、2492 華新科、3026 禾伸堂、6173 信昌電）等權價格籃 vs
        50 日均線＋斜率。用「股價籃還站不站得住、還漲不漲」代理「漲價新聞照出、
        股價卻不漲＝題材退燒」。
長相　：一條 sparkline（籃走勢）＋斜率%。動起來＝貼近/跌破 50MA、斜率轉平轉負。
狀態　：🟢 站上 50MA 且向上＝題材資金仍在；🟡 站上但轉平/其一走弱＝鬆動；
        🔴 跌破 50MA 且轉折（籃 < 50MA 且 50MA 5 日斜率 < 0）＝漲價對股價失效、資金退潮。
資料　：FinMind TW 個股收盤。每交易日更新。
來源　：股癌 EP512 (2025-06-18)。

TODO(Phase 2)：實作 _compute。Phase 1 先回 gray（stub）。
"""
from __future__ import annotations

from core.indicators import basket_index, ma_slope_pct, mean
from core.spec import DataBinding, SignalResult, SignalSpec

# === 門檻常數 ===
# 國巨、華新科、禾伸堂、信昌電（yfinance 代碼；6173 在櫃買故用 .TWO）
BASKET = ("2327.TW", "2492.TW", "3026.TW", "6173.TWO")
MA_WINDOW = 50
SLOPE_LOOKBACK = 5        # 50MA 斜率取近幾日
NEAR_MA_PCT = 1.5         # 距 50MA 在 ±此% 內視為「貼近」（黃燈鬆動）
SHOWN_BARS = 60           # sparkline 顯示根數（同時畫籃子與 50MA 虛線）


def _compute(inputs: dict) -> SignalResult:
    # inputs["closes"] = {symbol: [close, ...]}（舊→新）
    closes = inputs.get("closes") or {}
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
    else:                                          # 貼近均線／轉平／鬆動
        light = "yellow"

    # 圖上同時畫「籃子(綠/紅實線)」與「50MA(灰虛線)」，站上/跌破直接可見
    shown = min(SHOWN_BARS, len(idx) - MA_WINDOW + 1)
    series = [round(x, 2) for x in idx[-shown:]]
    ma_series = [round(mean(idx[i - MA_WINDOW + 1:i + 1]), 2)
                 for i in range(len(idx) - shown, len(idx))]

    return SignalResult(
        light=light,
        value_label=f"{dist_pct:+.1f}%",
        series=series,
        extra={
            "ma_series": ma_series,
            "slope_pct": round(slope_pct, 2),
            "ma_window": MA_WINDOW,
            "caption": f"實線=籃子、虛線=50MA｜距MA {dist_pct:+.1f}%、MA斜率 {slope_pct:+.2f}%/{SLOPE_LOOKBACK}日",
        },
        detail={"dist_pct": round(dist_pct, 3), "slope_pct": round(slope_pct, 3),
                "ma_now": round(ma_now, 3)},
    )


SIGNAL = SignalSpec(
    id="mlcc_basket_ma",
    name="被動元件籃子 vs 50MA",
    cluster="semi_memory_top",
    tags=("半導體", "被動元件", "MLCC", "50MA"),
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
        "green": "被動元件籃站穩 50MA 且向上，漲價題材仍有資金追捧。",
        "yellow": "籃子貼近 50MA 或斜率轉平，漲價題材推力鈍化，觀察是否失守。",
        "red": "籃子跌破 50MA 且均線下彎，漲價新聞不再帶動股價，資金退潮。",
        "gray": "被動元件股價資料抓取失敗。",
    },
    episode_ref="EP512",
    episode_date="2025-06-18",
    cadence="trading_day",
    track="被動四雄（國巨、華新科、禾伸堂、信昌電）等權股價籃對 50 日均線的位置與斜率——代理「漲價新聞還帶不帶得動股價」。",
    shape="線圖貼近→跌破 50MA、斜率由正轉平轉負；跌破且均線下彎＝漲價題材對股價失效。",
    order=2,
    in_master=True,
    unit="%",
)
