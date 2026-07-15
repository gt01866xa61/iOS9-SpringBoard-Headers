"""支援面板 — Menlo 企業開源模型占比（不計入主燈，敘事 vs 數據的對照）。

追什麼：Menlo Ventures 半年更的企業調查：開源模型占企業 LLM 工作負載比例。
        「風向轉向開源」的敘事要有數據撐才算數——這條序列目前是反向的
        （19%→13%→11%，近腰斬），正好當敘事的照妖鏡。
長相　：長條圖，一點＝一次調查（半年一點）。回升／持平／續降。
狀態　：🟢 最新點回升 ≥1pp＝敘事開始有數據撐；🟡 ±1pp 持平；🔴 續降＝敘事歸敘事。
資料　：data/manual/menlo_opensource.json——報告公布後手動補點（年中約 7 月、
        年末約 12 月），逐點附報告名與樣本數。
"""
from __future__ import annotations

from core.spec import DataBinding, SignalResult, SignalSpec

# === 門檻常數 ===
FLAT_PP = 1.0    # 最新點與上一點差在 ±此 pp 內視為持平


def _compute(inputs: dict) -> SignalResult:
    data = inputs.get("menlo") or {}
    series = list(data.get("series") or [])
    if len(series) < 2:
        return SignalResult(light="gray")

    labels = [str(p["label"]) for p in series]
    vals = [float(p["pct"]) for p in series]
    chg = vals[-1] - vals[-2]
    light = "green" if chg >= FLAT_PP else "red" if chg <= -FLAT_PP else "yellow"

    return SignalResult(
        light=light,
        value_label=f"開源占比 {vals[-1]:.0f}%",
        series=vals,
        labels=labels,
        extra={"highlight_index": len(vals) - 1, "unit": "%", "zero_line": False,
               "caption": ""},
        detail={"chg_pp": round(chg, 1)},
    )


SIGNAL = SignalSpec(
    id="menlo_opensource",
    name="企業開源模型占比（Menlo）",
    cluster="onprem_hybrid",
    tags=("開源", "企業AI", "調查"),
    widget="bar_chart",
    bindings=(
        DataBinding(key="menlo", source="manual_series",
                    params={"key": "menlo_opensource"}),
    ),
    compute=_compute,
    interpretations={
        "green": "開源占比回升——「風向轉開源」的敘事第一次被數據支持。",
        "yellow": "占比持平，開源與閉源拉鋸。",
        "red": "占比續降——敘事歸敘事，企業工作負載仍往閉源集中。",
        "gray": "調查資料不足（半年一更）。",
    },
    cadence="manual",
    track="Menlo Ventures 半年更的企業調查：開源模型占企業 LLM 工作負載的比例——「風向轉向開源」敘事的照妖鏡，目前序列 19%→13%→11% 與敘事反向。",
    shape="半年一根長條：回升＝敘事開始有數據撐；續降＝敘事歸敘事。下一點約在年中/年末報告公布後補上。",
    order=13,
    in_master=False,
    unit="%",
)
