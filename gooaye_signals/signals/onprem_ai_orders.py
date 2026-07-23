"""Signal 11 — 企業 AI 伺服器訂單動能（基本面：有人真的掏錢了嗎）。

追什麼：「企業掏錢買地端 AI」最可溯源的公開數字。三大雲都不公布盒子賣幾台，
        但盒子是實體硬體，錢一定流過必須公開記帳的地方——伺服器商的季報。
        HPE 每季披露 AI 系統新訂單且官方明講 backlog「primarily enterprise and
        sovereign」＝主軸；Dell 量體大十倍但混 neocloud（xAI、CoreWeave）＝對照列。
長相　：表格——每列一家：最新單季訂單、backlog、動能燈、backlog 迷你走勢。
狀態　：卡片燈＝HPE 列的動能燈（主軸）：🟢 最新披露訂單較上一已知披露期 +20% 以上＝放量；
        🟡 ±20% 內＝有生意沒放量（預設＝「吃力不討好」假設成立中）；
        🔴 -20% 以上，或資料為連續財季且連兩季縮＝反向。Dell 列同規則給點但不計卡燈。
資料　：data/manual/hpe_dell_ai_orders.json——每季財報後手動補一筆，逐點附出處
        （SEC 8-K／官方新聞稿）。手動＝季更，是「確認器」不是搶跑器。
"""
from __future__ import annotations

import re

from core.spec import DataBinding, SignalResult, SignalSpec

# === 門檻常數 ===
SURGE_PCT = 20.0     # 最新披露較上一已知披露期增/減超過此% 視為放量/反向
COMPANIES = (("hpe", "HPE", "企業+主權為主"), ("dell", "Dell", "混 neocloud，對照"))


def _order_series(entries: list) -> list[tuple[str, float]]:
    return [(str(e["q"]), float(e["orders_b"])) for e in entries if e.get("orders_b") is not None]


def _backlog_series(entries: list) -> list[float]:
    return [float(e["backlog_b"]) for e in entries if e.get("backlog_b") is not None]


def _quarter_index(label: str) -> int | None:
    """FY25Q4 / FY2025Q4 → 可比較的季度序號；其他標籤只保留上一已知期比較。"""
    match = re.fullmatch(r"FY(\d{2}|\d{4})Q([1-4])", label)
    if not match:
        return None
    year = int(match.group(1))
    return year * 4 + int(match.group(2)) - 1


def _dot(orders: list[tuple[str, float]]) -> str:
    """最新披露 vs 上一已知披露期；連續三季皆縮時另判紅。"""
    if len(orders) < 2:
        return "gray"
    if len(orders) >= 3:
        q0, q1, q2 = (_quarter_index(q) for q, _ in orders[-3:])
        v0, v1, v2 = (v for _, v in orders[-3:])
        if (q0 is not None and q1 == q0 + 1 and q2 == q1 + 1
                and v0 > v1 > v2):
            return "red"
    prev, last = orders[-2][1], orders[-1][1]
    if prev <= 0:
        return "gray"
    chg = (last / prev - 1) * 100
    if chg >= SURGE_PCT:
        return "green"
    if chg <= -SURGE_PCT:
        return "red"
    return "yellow"


def _compute(inputs: dict) -> SignalResult:
    data = inputs.get("orders") or {}
    rows: list[dict] = []
    light = "gray"
    hpe_latest = ""

    for key, name, note in COMPANIES:
        entries = list(data.get(key) or [])
        orders = _order_series(entries)
        backlog = _backlog_series(entries)
        if not entries or (not orders and not backlog):
            rows.append({"cells": [f"{name}（{note}）", "—", "—"], "dot": "gray", "spark": []})
            continue
        dot = _dot(orders)
        o_txt = f"${orders[-1][1]:.1f}B/{orders[-1][0]}" if orders else "—"
        b_txt = f"${backlog[-1]:.1f}B" if backlog else "—"
        shown_sources: list[str] = []
        shown_urls: list[str] = []
        for field in ("orders_b", "backlog_b"):
            shown = next((e for e in reversed(entries) if e.get(field) is not None), None)
            if shown:
                src = str(shown.get("src") or "")
                if src and src not in shown_sources:
                    shown_sources.append(src)
                src_url = str(shown.get("src_url") or "")
                if src_url.startswith(("https://", "http://")) and src_url not in shown_urls:
                    shown_urls.append(src_url)
        row = {
            "cells": [f"{name}（{note}）", o_txt, b_txt],
            "dot": dot,
            "spark": backlog if len(backlog) >= 2 else [],
            "source": "；".join(shown_sources),
        }
        if shown_urls:
            row["source_url"] = shown_urls[0]
        rows.append(row)
        if key == "hpe":                     # 卡片燈＝主軸 HPE 的動能燈
            light = dot if dot != "gray" else "gray"
            hpe_latest = o_txt

    if all(r["dot"] == "gray" for r in rows):
        return SignalResult(light="gray", rows=rows,
                            extra={"columns": ["公司", "單季AI訂單", "backlog", "動能", "backlog走勢"]})

    return SignalResult(
        light=light,
        value_label=f"HPE {hpe_latest}" if hpe_latest else "資料不足",
        rows=rows,
        extra={
            "columns": ["公司", "單季AI訂單", "backlog", "動能", "backlog走勢"],
            "caption": (f"卡燈＝HPE 列（企業+主權最純）・動能：較上一已知披露期 ±{SURGE_PCT:.0f}% 為界"
                        "；連續財季連縮兩季亦紅"
                        f"・資料至 {data.get('as_of', '—')}・每季財報後手動更新，逐點附出處於 data/manual"),
        },
        detail={"rule": f"較上一已知披露期 ±{SURGE_PCT}%；連續兩季縮則紅",
                "as_of": str(data.get("as_of", ""))},
        data_as_of=str(data.get("as_of", "")),
        sources=tuple({"source": str(e["src"]),
                       **({"source_url": str(e["src_url"])}
                          if str(e.get("src_url") or "").startswith(("https://", "http://")) else {})}
                      for key, _, _ in COMPANIES for e in data.get(key, []) if e.get("src")),
    )


SIGNAL = SignalSpec(
    id="onprem_ai_orders",
    name="企業 AI 伺服器訂單動能",
    cluster="onprem_hybrid",
    tags=("地端AI", "混合雲", "HPE", "Dell", "訂單"),
    widget="table",
    bindings=(
        DataBinding(key="orders", source="manual_series",
                    params={"key": "hpe_dell_ai_orders"}),
    ),
    compute=_compute,
    interpretations={
        "green": "HPE 最新披露 AI 訂單較上一已知披露期放量（+20% 以上）——企業用錢投票，地端劇本從敘事變訂單。",
        "yellow": "訂單有生意但未放量——維持「吃力不討好」假設，敘事再響也還沒變成錢。",
        "red": "訂單明顯收縮，劇本反向。",
        "gray": "訂單資料尚未更新。",
    },
    cadence="manual",
    track="HPE 每季 AI 系統新訂單（官方：backlog 主要來自企業與主權政府）＝「企業掏錢買地端 AI」最可溯源的公開數字；Dell 為對照列（量體大但混 neocloud）。三大雲不公布盒子數字，錢的痕跡在幫它們裝機的伺服器商季報裡。",
    shape="看 HPE 列的動能燈：最新披露訂單較上一已知披露期明顯變大（+20%↑）＝拉貨放量；連續財季連縮兩季或單次明顯縮＝反向。缺季比較不稱 QoQ。季更，是確認器。",
    order=11,
    in_master=True,
    unit="",
)
