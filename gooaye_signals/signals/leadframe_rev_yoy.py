"""Signal 7 — 順德(2351) 月營收 YoY（導線架景氣的先行溫度計）。

追什麼：導線架龍頭順德(2351)每月營收年增率(YoY)。導線架是傳統封裝（功率/車用/
        PMIC）的上游瓶頸，缺貨與漲價最終都要灌進營收——這是「交期還緊不緊」
        最可溯源的硬數據。順德為功率導線架全球市占第一（逾 17%）。
長相　：近 12 個月 YoY 長條圖，最新月高亮。動起來＝連續幾根往下掉、由正轉負。
狀態　：🟢 未連降＝上游動能延續；🟡 連降 1 月＝動能鈍化；🔴 連降 ≥2 月＝瓶頸緩解/需求轉弱。
資料　：FinMind 月營收（回傳已對齊、舊→新的 (month, yoy%)）。約每月 10 號更新。
來源　：股癌 EP678——導線架可當封測強度的先行指標，lead time 若續拉，
        封測的獲利行情就有延續性。
"""
from __future__ import annotations

from core.indicators import consec_declines
from core.spec import DataBinding, SignalResult, SignalSpec

# === 門檻常數（single source of truth）===
STOCK_ID = "2351"
BARS_SHOWN = 12          # 顯示月數
RED_CONSEC = 2           # YoY 連降幾月 = RED


def _compute(inputs: dict) -> SignalResult:
    # inputs["rev"] = [[month "YYYY-MM", yoy%], ...] 已對齊、舊→新（FinMind adapter 產出）
    rev = list(inputs.get("rev") or [])[-BARS_SHOWN:]
    if len(rev) < 2:
        return SignalResult(light="gray")
    labels = [str(m) for m, _ in rev]
    yoy = [float(v) for _, v in rev]

    consec = consec_declines(yoy)
    light = "red" if consec >= RED_CONSEC else "yellow" if consec == 1 else "green"
    return SignalResult(
        light=light,
        value_label=f"YoY {yoy[-1]:+.1f}%",
        series=[round(v, 2) for v in yoy],
        labels=labels,
        extra={"highlight_index": len(yoy) - 1, "unit": "% YoY", "zero_line": True},
        detail={"consecutive_down_months": consec},
    )


SIGNAL = SignalSpec(
    id="leadframe_rev_yoy",
    name="順德(2351) 月營收 YoY",   # 名稱保持中性——「延續與否」由燈色判定
    cluster="leadframe_osat",
    tags=("導線架", "封測", "功率元件", "月營收", "2351"),
    widget="bar_chart",
    bindings=(
        DataBinding(
            key="rev",
            source="finmind_revenue",
            params={"stock_id": STOCK_ID, "months": BARS_SHOWN + 2},
        ),
    ),
    compute=_compute,
    interpretations={
        "green": "順德營收年增仍在擴張，導線架缺貨/漲價動能延續，封測行情有基本面支撐。",
        "yellow": "YoY 首度轉弱，觀察是否為上游動能鈍化的起點，可能只是單月雜訊。",
        "red": "YoY 連 2 個月以上走低，導線架瓶頸緩解或需求轉弱，封測先行指標轉負。",
        "gray": "月營收資料尚未更新或抓取失敗。",
    },
    cadence="monthly",
    track="導線架龍頭順德(2351)每月營收年增率(YoY)——缺貨與漲價最終都要灌進營收，是「交期還緊不緊」最可溯源的硬數據；導線架是封測獲利行情能否延續的先行溫度計。",
    shape="長條逐月墊高＝漲價缺貨仍在收斂進財報；一根根往下、由正轉負＝上游瓶頸緩解，封測行情延續性打折。",
    order=7,
    in_master=True,
    unit="% YoY",
)
