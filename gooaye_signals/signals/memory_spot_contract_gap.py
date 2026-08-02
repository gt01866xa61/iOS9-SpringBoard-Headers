"""支援面板 — 記憶體現貨/合約價差（先建立同品項月度基準，不計主燈）。

追什麼：同一 DRAM 品項的現貨與合約價。現貨是零買市場、通常先反映庫存變化；若現貨
        明顯走弱而合約仍持穩，才是本卡定義的早期警訊。
長相　：每月一筆同品項快照，顯示現貨、合約、現貨/合約倍數；首筆只建基準，不判趨勢。
狀態　：綠＝兩者都不跌；黃＝混合/尚在建立基準；紅＝同品項現貨月變動 ≤ -3%、合約
        未跌超過 1%，即「現貨先鬆、合約仍撐」。
資料　：data/manual/memory_spot_contract_gap.json——TrendForce/DRAMeXchange 每月同品項快照。
"""
from __future__ import annotations

from core.spec import DataBinding, SignalResult, SignalSpec

SPOT_SOFTEN_PCT = -3.0
CONTRACT_FIRM_PCT = -1.0


def _source(point: dict) -> dict:
    out = {"source": str(point.get("src") or "")}
    url = str(point.get("src_url") or "")
    if url.startswith(("https://", "http://")):
        out["source_url"] = url
    return out


def _latest_row(point: dict, dot: str, source: dict) -> dict:
    spot = float(point["spot"])
    contract = float(point["contract"])
    row = {
        "cells": [str(point["item"]), f"{spot:.3f}", f"{contract:.3f}", f"{spot / contract:.2f}×"],
        "dot": dot, "spark": [], "source": source["source"],
    }
    if source.get("source_url"):
        row["source_url"] = source["source_url"]
    return row


def _compute(inputs: dict) -> SignalResult:
    data = inputs.get("prices") or {}
    series = sorted(list(data.get("series") or []), key=lambda point: str(point.get("date") or ""))
    if not series:
        return SignalResult(light="gray")

    latest = series[-1]
    source = _source(latest)
    same_item = [point for point in series
                 if str(point.get("item")) == str(latest.get("item"))
                 and str(point.get("currency")) == str(latest.get("currency"))]
    caption = ("只比較同一品項、同一幣別的月度快照；首筆只建立基準。"
               f"紅＝現貨月變動 ≤ {SPOT_SOFTEN_PCT:.0f}% 且合約未跌超過 {abs(CONTRACT_FIRM_PCT):.0f}%。")

    if len(same_item) < 2:
        return SignalResult(
            light="gray", value_label=f"首次基準 {float(latest['spot']) / float(latest['contract']):.2f}×",
            rows=[_latest_row(latest, "gray", source)],
            extra={"columns": ["品項", "現貨", "合約", "現/合", "燈", ""], "caption": caption},
            detail={"as_of": str(data.get("as_of") or ""), "baseline_only": True},
            data_as_of=str(latest.get("date") or data.get("as_of") or ""), sources=(source,),
        )

    previous = same_item[-2]
    spot_chg = (float(latest["spot"]) / float(previous["spot"]) - 1) * 100
    contract_chg = (float(latest["contract"]) / float(previous["contract"]) - 1) * 100
    if spot_chg <= SPOT_SOFTEN_PCT and contract_chg >= CONTRACT_FIRM_PCT:
        light = "red"
    elif spot_chg >= 0 and contract_chg >= 0:
        light = "green"
    else:
        light = "yellow"

    sources = tuple(_source(point) for point in same_item[-2:])
    return SignalResult(
        light=light,
        value_label=f"現/合 {float(latest['spot']) / float(latest['contract']):.2f}×",
        rows=[_latest_row(latest, light, source)],
        extra={"columns": ["品項", "現貨", "合約", "現/合", "燈", ""], "caption": caption},
        detail={"spot_change_pct": round(spot_chg, 2), "contract_change_pct": round(contract_chg, 2),
                "as_of": str(data.get("as_of") or "")},
        data_as_of=str(latest.get("date") or data.get("as_of") or ""), sources=sources,
    )


SIGNAL = SignalSpec(
    id="memory_spot_contract_gap",
    name="記憶體現貨／合約價差",
    cluster="semi_memory_top",
    tags=("記憶體", "DRAM", "現貨價", "合約價", "庫存"),
    widget="table",
    bindings=(
        DataBinding(key="prices", source="manual_series", params={"key": "memory_spot_contract_gap"}),
    ),
    compute=_compute,
    interpretations={
        "green": "同品項現貨與合約都未走跌，未見「現貨先鬆」的分歧。",
        "yellow": "價格走勢混合，或還在建立第二筆可比快照；不把單一價差當成反轉。",
        "red": "同品項現貨先明顯下滑、合約仍撐住；留意庫存是否開始累積。",
        "gray": "僅有第一筆同品項快照，先建立基準，尚不能判趨勢。",
    },
    cadence="manual",
    track="同一 DRAM 品項的現貨價與合約價。現貨是零買市場，通常比合約更敏感；本卡只在現貨先鬆、合約仍撐時亮紅。",
    shape="每月補一筆相同品項與幣別的快照。首筆灰＝建立基準；兩者都不跌＝綠；走勢混合＝黃；現貨月跌至少 3%、合約跌幅不超過 1%＝紅。",
    order=9,
    in_master=False,
    unit="",
)
