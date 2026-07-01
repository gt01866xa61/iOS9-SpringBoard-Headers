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

from core.spec import DataBinding, SignalResult, SignalSpec

# === 門檻常數 ===
BASKET = ("2327", "2492", "3026", "6173")  # 國巨、華新科、禾伸堂、信昌電
MA_WINDOW = 50
SLOPE_LOOKBACK = 5        # 50MA 斜率取近幾日
NEAR_MA_PCT = 1.5         # 距 50MA 在 ±此% 內視為「貼近」（黃燈鬆動）


def _compute(inputs: dict) -> SignalResult:
    # Phase 1 stub；Phase 2 依 inputs["closes"] = {stock_id: [close,...]} 建等權籃、
    # 算籃 vs 50MA 與 50MA 斜率，決定燈號與 sparkline。
    return SignalResult(light="gray")


SIGNAL = SignalSpec(
    id="mlcc_basket_ma",
    name="被動元件籃子 vs 50MA",
    cluster="semi_memory_top",
    tags=("半導體", "被動元件", "MLCC", "50MA"),
    widget="sparkline",
    bindings=(
        DataBinding(
            key="closes",
            source="finmind_close",
            params={"stock_ids": list(BASKET), "days": 120},
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
    in_master=True,
    unit="%",
)
