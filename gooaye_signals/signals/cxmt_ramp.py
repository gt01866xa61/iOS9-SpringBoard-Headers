"""支援面板 — 中國長鑫存儲（CXMT）量產進度（供給側長週期追蹤，不計主燈）。

追什麼：CXMT 對一般 DRAM 的新增供給何時從「計畫」跨到「施工」再到「實際量產」。
        三者不可混為一談；只有可溯源的實際量產才算供給已落地。
長相　：事件表，逐列列出計畫／施工／量產／延後或設備限制，以及目標年份與最低產能。
狀態　：黃＝仍在計畫、施工或小量量產驗證；紅＝可溯源的大型量產里程碑落地；綠＝近期
        只見延後/限制；灰＝尚無事件。計畫本身不亮紅。
資料　：data/manual/cxmt_ramp.json——公司披露、IPO 文件或可信來源查證後逐筆補入。
"""
from __future__ import annotations

from datetime import date, timedelta

from core.spec import DataBinding, SignalResult, SignalSpec

WINDOW_DAYS = 540
MATERIAL_VOLUME_WSPM = 100_000
_DOT = {"plan": "yellow", "construction": "yellow", "volume": "red",
        "delay": "green", "restriction": "green"}
_LABEL = {"plan": "計畫", "construction": "施工", "volume": "量產",
          "delay": "延後", "restriction": "設備限制"}


def _source(point: dict) -> dict:
    out = {"source": str(point.get("src") or "")}
    url = str(point.get("src_url") or "")
    if url.startswith(("https://", "http://")):
        out["source_url"] = url
    return out


def _target(point: dict) -> str:
    year = point.get("target_year")
    wspm = point.get("target_wspm_min")
    parts: list[str] = []
    if year is not None:
        parts.append(f"{year} 年")
    if wspm is not None:
        parts.append(f"至少 {float(wspm) / 1000:.0f}k 片/月")
    return "・".join(parts) or "—"


def _compute(inputs: dict) -> SignalResult:
    data = inputs.get("ramp") or {}
    milestones = list(data.get("milestones") or [])
    if not milestones:
        return SignalResult(light="gray")

    as_of = str(data.get("as_of") or "")
    try:
        anchor = date.fromisoformat(as_of)
        dated = [(date.fromisoformat(str(point["date"])), point) for point in milestones]
    except (KeyError, TypeError, ValueError):
        return SignalResult(light="gray", value_label="事件日期格式錯誤", data_as_of=as_of)
    dated.sort(key=lambda pair: pair[0], reverse=True)
    recent = [point for event_date, point in dated if event_date >= anchor - timedelta(days=WINDOW_DAYS)]
    material_volume = [point for point in recent if point.get("stage") == "volume"
                       and float(point.get("target_wspm_min") or 0) >= MATERIAL_VOLUME_WSPM]
    small_volume = [point for point in recent if point.get("stage") == "volume"
                    and float(point.get("target_wspm_min") or 0) < MATERIAL_VOLUME_WSPM]
    active = [point for point in recent if point.get("stage") in {"plan", "construction"}]
    brakes = [point for point in recent if point.get("stage") in {"delay", "restriction"}]

    if material_volume:
        light, value = "red", f"大型量產 {len(material_volume)} 件"
    elif small_volume:
        light, value = "yellow", f"量產驗證中 {len(small_volume)} 件"
    elif active:
        light, value = "yellow", f"計畫／施工 {len(active)} 件"
    elif brakes:
        light, value = "green", f"延後／限制 {len(brakes)} 件"
    else:
        light, value = "gray", "近窗無可判讀里程碑"

    rows: list[dict] = []
    sources: list[dict] = []
    for _, point in dated[:6]:
        source = _source(point)
        sources.append(source)
        row = {
            "cells": [str(point.get("date") or ""), _LABEL.get(str(point.get("stage")), "—"),
                      str(point.get("what") or ""), _target(point)],
            "dot": _DOT.get(str(point.get("stage")), "gray"), "spark": [], "source": source["source"],
        }
        if source.get("source_url"):
            row["source_url"] = source["source_url"]
        rows.append(row)

    return SignalResult(
        light=light, value_label=value, rows=rows,
        extra={
            "columns": ["日期", "階段", "里程碑", "目標", "燈", ""],
            "caption": (f"近 {WINDOW_DAYS} 天（至 {as_of}）只把「可溯源的大型量產」判紅；"
                        "施工、計畫與未達門檻的小量量產仍是黃，不能把宣布擴產當供給已到。"),
        },
        detail={"volume": len(material_volume), "small_volume": len(small_volume),
                "active": len(active), "brakes": len(brakes),
                "as_of": as_of},
        data_as_of=as_of, sources=tuple(sources),
    )


SIGNAL = SignalSpec(
    id="cxmt_ramp",
    name="CXMT 一般 DRAM 量產進度",
    cluster="semi_memory_top",
    tags=("記憶體", "DRAM", "CXMT", "中國", "供給"),
    widget="table",
    bindings=(
        DataBinding(key="ramp", source="manual_series", params={"key": "cxmt_ramp"}),
    ),
    compute=_compute,
    interpretations={
        "green": "近期只見延後或設備限制，未見本卡定義的大型量產落地。",
        "yellow": "新增供給仍在計畫、施工或小量驗證；它是供給風險地圖，尚不是大量供給已到位。",
        "red": "可信來源確認大型一般 DRAM 量產里程碑落地，新增供給開始從計畫變現實。",
        "gray": "尚無可溯源的 CXMT 供給里程碑。",
    },
    cadence="manual",
    track="CXMT 對一般 DRAM 的新增供給，依序區分計畫、施工、量產、延後與設備限制。它追的是「產能何時真的落地」，不是把新聞裡的擴產計畫當成已量產。",
    shape="事件表由計畫/施工/小量驗證（黃）走到可溯源的大型量產（紅）；若近期只有延後或設備限制（綠），表示本卡尚未看到供給加速落地。",
    order=10,
    in_master=False,
    unit="",
)
