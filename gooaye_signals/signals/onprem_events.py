"""支援面板 — 地端盒子事件簿（不計入主燈，佐證用）。

追什麼：「誰敢把名字借給這個方案」。雲廠自吹不算數，算數的是可溯源事件：
        具名企業背書（LSEG/Nasdaq 等級）、產品里程碑（GA、供應國擴張）、
        反向事件（專案取消、調查數據反向）。
長相　：表格——每列一事件：日期、陣營、事件內容、方向點（＋綠／−紅／敘事灰）。
狀態　：近半年（180 天，以檔案 as_of 為準）正負事件淨值＋背書門檻：
        🟢 淨值 ≥ +3「且」窗內至少一筆具名背書（type=endorse）——雲廠自家里程碑
        （GA、擴國）是供應側，蓋房子不等於有人入住，湊不出綠燈；
        🟡 -2～+2、或淨值達標但無背書（預設）；🔴 淨值 ≤ -3＝反向證據占優。
資料　：data/manual/onprem_events.json——使用者口述或查證後新增，逐筆附出處。
判讀　：名單加速變長且出現「普通產業」名字＝擴散成立；清一色政府金融＝管制行業
        剛需，不是擴散。
"""
from __future__ import annotations

from datetime import date, timedelta

from core.spec import DataBinding, SignalResult, SignalSpec

# === 門檻常數 ===
WINDOW_DAYS = 180        # 淨值統計窗（相對檔案 as_of，不看系統時鐘、compute 保持純函式）
GREEN_NET = 3            # 窗內 (+) - (-) ≥ 此值 → 綠
RED_NET = -3             # ≤ 此值 → 紅
SHOWN = 8                # 表格顯示最新幾筆

_DOT = {"+": "green", "-": "red", "0": "gray"}


def _compute(inputs: dict) -> SignalResult:
    data = inputs.get("events") or {}
    events = list(data.get("events") or [])
    if not events:
        return SignalResult(light="gray")

    as_of = str(data.get("as_of") or "")
    try:
        anchor = date.fromisoformat(as_of)
        dated = [(date.fromisoformat(str(e.get("date") or "")), e) for e in events]
    except (TypeError, ValueError):
        return SignalResult(light="gray", value_label="事件日期格式錯誤",
                            detail={"as_of": as_of, "invalid_dates": True}, data_as_of=as_of)
    dated.sort(key=lambda pair: pair[0], reverse=True)
    events = [e for _, e in dated]
    cutoff = anchor - timedelta(days=WINDOW_DAYS)

    # 同時設上下界：人工誤植的未來事件不得提前污染目前燈號。
    in_win = [e for event_date, e in dated if cutoff <= event_date <= anchor]
    pos = sum(1 for e in in_win if e.get("dir") == "+")
    neg = sum(1 for e in in_win if e.get("dir") == "-")
    net = pos - neg
    # 綠燈的背書門檻：需求側證據（具名客戶）至少一筆——供應側里程碑湊不出綠
    has_endorse = any(e.get("dir") == "+" and e.get("type") == "endorse" for e in in_win)
    if net >= GREEN_NET and has_endorse:
        light = "green"
    elif net <= RED_NET:
        light = "red"
    else:
        light = "yellow"

    rows = []
    for e in events[:SHOWN]:
        row = {
            "cells": [str(e.get("date", ""))[2:], str(e.get("camp", "")), str(e.get("what", ""))],
            "dot": _DOT.get(str(e.get("dir")), "gray"),
            "spark": [],
            "source": str(e.get("src") or ""),
        }
        src_url = str(e.get("src_url") or "")
        if src_url.startswith(("https://", "http://")):
            row["source_url"] = src_url
        rows.append(row)

    return SignalResult(
        light=light,
        value_label=f"近半年 +{pos}／−{neg}",
        rows=rows,
        extra={
            "columns": ["日期", "陣營", "事件", "向", ""],
            "caption": (f"點＝方向（綠 正向・紅 反向・灰 敘事）・近 {WINDOW_DAYS} 天淨值"
                        f"（至 {as_of}）給燈，綠須含具名背書・逐筆出處在 data/manual/onprem_events.json"),
        },
        detail={"pos": pos, "neg": neg, "net": net, "as_of": as_of,
                "has_endorse": has_endorse},
        data_as_of=as_of,
        sources=tuple({"source": str(e["src"]),
                       **({"source_url": str(e["src_url"])}
                          if str(e.get("src_url") or "").startswith(("https://", "http://")) else {})}
                      for e in events if e.get("src")),
    )


SIGNAL = SignalSpec(
    id="onprem_events",
    name="地端盒子事件簿",
    cluster="onprem_hybrid",
    tags=("地端AI", "混合雲", "背書", "事件"),
    widget="table",
    bindings=(
        DataBinding(key="events", source="manual_series",
                    params={"key": "onprem_events"}),
    ),
    compute=_compute,
    interpretations={
        "green": "正向事件加速累積且含具名客戶背書——名單在變長，留意是否出現非政府金融的普通產業名字（擴散）。",
        "yellow": "事件零星混雜、或只有雲廠自家里程碑而無客戶背書——蓋房子不等於有人入住。",
        "red": "反向事件占優（取消、砍單、數據反向），劇本退潮。",
        "gray": "事件簿尚無資料。",
    },
    cadence="manual",
    track="「誰敢把名字借給這個方案」——三大雲盒子的可溯源事件簿：具名企業背書、產品 GA、供應國擴張、反向事件。雲廠自吹不算數，具名站台才算。",
    shape="名單加速變長、且出現普通產業（零售/製造）名字＝從管制行業剛需擴散到一般企業；只有雲廠自家 GA/擴國而無客戶具名＝供應側自嗨，亮不了綠；取消案例變多＝反向。",
    order=12,
    in_master=False,
    unit="",
)
