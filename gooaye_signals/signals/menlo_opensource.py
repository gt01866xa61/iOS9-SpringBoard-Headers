"""支援面板 — 企業開源模型：風向 × 體量（不計入主燈，敘事 vs 數據的對照）。

追什麼：Menlo 半年更企業調查的兩條線一起看，避免分母效應誤讀（使用者指正）：
        ① 風向＝開源占企業 LLM 工作負載的占比（19→13→11%）
        ② 體量＝占比 × 同報告的模型 API 總支出（$3.5B→$8.4B→$12.5B）＝
           推算開源絕對額（$0.67B→$1.09B→$1.38B，方向級參考）
        占比下降的同時絕對額一路成長——「開源在萎縮」與「風向轉開源」都不對，
        真實狀態是「開源在長，但新增的錢壓倒性流向閉源」。
長相　：表格三列——占比、總支出（分母）、推算開源額（分子），各附迷你走勢。
狀態　：雙變數真值表：🟢 占比回升＝風向真的轉向開源；
        🟡 占比降/平但推算額仍升＝開源跑輸大盤但體量仍在長（現況）；
        🔴 推算額也轉降＝開源真的在萎縮；⚪ 資料不足。
        無總量資料的波次退回風向-only 判定（回升綠／持平黃／續降紅）。
資料　：data/manual/menlo_opensource.json——逐點附報告名、樣本數與總量出處。
但書　：pct 是工作負載占比、total 是支出金額，兩口徑相乘屬方向級推算非精確值；
        三波 total 口徑略異（年末水準/半年/全年）；發布者為 AI 創投（利害關係人）
        且為問卷調查——證據強度低一級，故放補充面板不計主燈。
"""
from __future__ import annotations

from core.spec import DataBinding, SignalResult, SignalSpec

# === 門檻常數 ===
FLAT_PP = 1.0    # 占比最新點與上一點差在 ±此 pp 內視為持平


def _compute(inputs: dict) -> SignalResult:
    data = inputs.get("menlo") or {}
    series = list(data.get("series") or [])
    if len(series) < 2:
        return SignalResult(light="gray")

    labels = [str(p["label"]) for p in series]
    pcts = [float(p["pct"]) for p in series]
    totals = [float(p["total_b"]) if p.get("total_b") is not None else None for p in series]
    implied = [round(pc / 100.0 * t, 2) if t is not None else None
               for pc, t in zip(pcts, totals)]

    pct_chg = pcts[-1] - pcts[-2]
    imp_chg = (implied[-1] - implied[-2]
               if implied[-1] is not None and implied[-2] is not None else None)

    # 雙變數真值表：風向（占比）優先，體量（推算額）決定黃或紅
    if pct_chg >= FLAT_PP:
        light = "green"
    elif imp_chg is None:
        # 無總量資料 → 退回風向-only
        light = "yellow" if pct_chg > -FLAT_PP else "red"
    elif imp_chg >= 0:
        light = "yellow"
    else:
        light = "red"

    def _spk(vals):
        xs = [v for v in vals if v is not None]
        return xs if len(xs) >= 2 else []

    def _dir(chg, up="↑", down="↓"):
        if chg is None:
            return "—"
        return up if chg > 0 else down if chg < 0 else "→"

    tot_chg = (totals[-1] - totals[-2]
               if totals[-1] is not None and totals[-2] is not None else None)
    rows = [
        {"cells": ["開源占比（風向）", f"{pcts[-1]:.0f}%", _dir(pct_chg)],
         "dot": "green" if pct_chg > 0 else "red" if pct_chg < 0 else "yellow",
         "spark": pcts},
        {"cells": ["模型API總支出（分母）",
                   f"${totals[-1]:.1f}B" if totals[-1] is not None else "—", _dir(tot_chg)],
         "dot": "gray", "spark": _spk(totals)},
        {"cells": ["推算開源額（分子）",
                   f"${implied[-1]:.2f}B" if implied[-1] is not None else "—", _dir(imp_chg)],
         "dot": "green" if (imp_chg or 0) > 0 else "red" if (imp_chg or 0) < 0 else "gray",
         "spark": _spk(implied)},
    ]

    return SignalResult(
        light=light,
        value_label=(f"占比 {pcts[-1]:.0f}%・額{_dir(imp_chg, '仍增', '轉減')}"
                     if imp_chg is not None else f"占比 {pcts[-1]:.0f}%"),
        rows=rows,
        extra={
            "columns": ["指標", "最新", "向", "點", "走勢"],
            "caption": (f"調查波次：{labels[0]}→{labels[-1]}・推算額＝占比×總支出"
                        "（口徑混合，方向級參考）・分母列灰點＝僅供脈絡・出處逐點在 data/manual"),
        },
        detail={"pct_chg_pp": round(pct_chg, 1),
                "implied_series_b": implied, "totals_b": totals},
    )


SIGNAL = SignalSpec(
    id="menlo_opensource",
    name="企業開源模型：風向×體量",
    cluster="onprem_hybrid",
    tags=("開源", "企業AI", "調查"),
    widget="table",
    bindings=(
        DataBinding(key="menlo", source="manual_series",
                    params={"key": "menlo_opensource"}),
    ),
    compute=_compute,
    interpretations={
        "green": "開源占比回升——「風向轉開源」的敘事第一次被數據支持（新增預算開始流向開源）。",
        "yellow": "開源絕對額仍在成長、但占比續降——開源在長，只是每塊新增的錢壓倒性流向閉源；風向未轉、體量未衰。",
        "red": "連推算絕對額都轉降——開源在企業端真的在萎縮。",
        "gray": "調查資料不足（半年一更）。",
    },
    cadence="manual",
    track="Menlo 半年更調查的兩條線：開源占比（風向）＋「占比×模型API總支出」的推算開源額（體量）——分開看才不會把「占比降」誤讀成「開源萎縮」：總量暴增期，占比腰斬的同時絕對額可能照樣成長。",
    shape="看兩列的方向組合：占比↑＝風向轉開源（綠）；占比↓但推算額↑＝開源跑輸大盤但仍在長（黃，現況）；推算額↓＝真萎縮（紅）。推算額為方向級參考（占比與支出口徑不同）。",
    order=13,
    in_master=False,
    unit="",
)
