"""支援面板 — CSP 巨頭資本支出指引（需求側早期預警，不計主燈）。

追什麼：Alphabet、Microsoft、Meta 在法說會親自給出的下一期 CapEx 方向。大型買家若
        明確放緩或削減，這比供應鏈營收更接近需求端的第一手訊號。
長相　：三列法說追蹤表；每家公司只取最新一筆具來源的正式指引，缺資料不假裝成中性。
狀態　：綠＝三家最新指引都加碼；黃＝尚無削減、但有維持/缺資料；紅＝任一家明確放緩
        或削減。
資料　：data/manual/csp_capex_guidance.json——每次三家財報後手動更新，逐筆附 IR 出處。
"""
from __future__ import annotations

from core.spec import DataBinding, SignalResult, SignalSpec

CSP_NAMES = (("alphabet", "Alphabet"), ("microsoft", "Microsoft"), ("meta", "Meta"))
_DOT = {"raise": "green", "maintain": "yellow", "slow": "red", "cut": "red"}
_LABEL = {"raise": "加碼", "maintain": "維持", "slow": "放緩", "cut": "削減"}


def _source(point: dict) -> dict:
    out = {"source": str(point.get("src") or "")}
    url = str(point.get("src_url") or "")
    if url.startswith(("https://", "http://")):
        out["source_url"] = url
    return out


def _latest_reports(reports: list[dict]) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    for report in reports:
        key = str(report.get("company") or "")
        if key not in {company for company, _ in CSP_NAMES}:
            continue
        if key not in latest or str(report.get("date") or "") > str(latest[key].get("date") or ""):
            latest[key] = report
    return latest


def _compute(inputs: dict) -> SignalResult:
    data = inputs.get("capex") or {}
    latest = _latest_reports(list(data.get("reports") or []))
    rows: list[dict] = []
    directions: list[str] = []
    sources: list[dict] = []

    for key, name in CSP_NAMES:
        report = latest.get(key)
        if not report:
            rows.append({"cells": [name, "待補正式指引", "—"], "dot": "gray", "spark": []})
            continue
        direction = str(report["direction"])
        directions.append(direction)
        source = _source(report)
        sources.append(source)
        row = {
            "cells": [name, str(report["guidance"]), _LABEL[direction]],
            "dot": _DOT[direction], "spark": [], "source": source["source"],
        }
        if source.get("source_url"):
            row["source_url"] = source["source_url"]
        rows.append(row)

    if not directions:
        return SignalResult(
            light="gray", rows=rows,
            extra={"columns": ["CSP", "最新 CapEx 指引", "方向", "燈", ""]},
        )

    red_count = sum(direction in {"slow", "cut"} for direction in directions)
    raise_count = directions.count("raise")
    if red_count:
        light = "red"
        value = f"{red_count} 家明確放緩/削減"
    elif len(directions) == len(CSP_NAMES) and raise_count == len(CSP_NAMES):
        light = "green"
        value = "3/3 仍加碼"
    else:
        light = "yellow"
        value = f"{raise_count}/3 仍加碼"

    as_of = max((str(report.get("date") or "") for report in latest.values()), default="")
    return SignalResult(
        light=light, value_label=value, rows=rows,
        extra={
            "columns": ["CSP", "最新 CapEx 指引", "方向", "燈", ""],
            "caption": "只判公司在正式法說明說的 CapEx 方向；任一家明確放緩/削減即紅。缺一家公司不偷補推論，維持黃。",
        },
        detail={"reported": len(directions), "raise": raise_count, "slow_or_cut": red_count,
                "as_of": str(data.get("as_of") or "")},
        data_as_of=as_of or str(data.get("as_of") or ""), sources=tuple(sources),
    )


SIGNAL = SignalSpec(
    id="csp_capex_guidance",
    name="CSP 巨頭資本支出指引",
    cluster="semi_memory_top",
    tags=("AI", "CSP", "CapEx", "Alphabet", "Microsoft", "Meta"),
    widget="table",
    bindings=(
        DataBinding(key="capex", source="manual_series", params={"key": "csp_capex_guidance"}),
    ),
    compute=_compute,
    interpretations={
        "green": "三家已追蹤 CSP 的最新正式指引都仍加碼，需求端未見本卡定義的踩煞車。",
        "yellow": "沒有明確削減，但至少一家維持或待補正式指引；不要把缺資料讀成樂觀。",
        "red": "至少一家 CSP 在正式法說明確放緩或削減 CapEx；需求端的第一手警訊出現。",
        "gray": "尚未有任何可溯源的 CSP 正式指引。",
    },
    cadence="manual",
    purpose="驗證 AI 基礎建設最大買家是否仍願意持續加碼需求。",
    track="Alphabet、Microsoft、Meta 在正式法說給出的下一期資本支出方向。大型買家若先踩煞車，通常比供應鏈營收更早顯示需求端轉折。",
    shape="每家公司只看最新一筆正式指引：三家皆加碼＝綠；有維持或缺資料＝黃；任一家明說放緩或削減＝紅。這張表不把推測、媒體轉述或缺資料當成公司指引。",
    order=8,
    in_master=False,
    featured=True,
    unit="",
)
