"""Signal 7 — 導線架四雄營收動能（產業級的先行溫度計）。

追什麼：導線架四雄各自的月營收年增率(YoY)動能。缺貨與漲價最終都要灌進營收——
        這是「交期還緊不緊」最可溯源的硬數據。四家並列而非只看龍頭：單一公司的
        轉單、基期、副業雜訊（順德含文具、一詮多 LED 支架）騙不了整排，
        「全面延續還是一家獨撐」一眼可辨。
長相　：表格——每列一家：最新 YoY、連降月數、動能燈點、近 12 月 YoY 迷你走勢。
狀態　：每家依「連降幾月」給動能燈（綠 0／黃 1／紅 ≥2），整卡照主燈真值表彙總：
        🟢 全綠＝全面延續；🟡 任一黃/紅＝開始鈍化；🔴 ≥2 家紅＝產業級轉弱。
資料　：FinMind 月營收（各家 (month, yoy%)，舊→新）。約每月 10 號更新，
        各家公布有先後，晚報的列會標「至X月」。
來源　：股癌 EP678——導線架可當封測強度的先行指標。
"""
from __future__ import annotations

from core.indicators import consec_declines
from core.spec import DataBinding, SignalResult, SignalSpec

# === 門檻常數（single source of truth）===
# (FinMind stock_id, 顯示名)——id 即 FinMind 查詢代號，列列可溯源
COMPANIES = (("2351", "順德"), ("6548", "長科"), ("5285", "界霖"), ("2486", "一詮"))
BARS = 12                # 迷你走勢顯示月數
RED_CONSEC = 2           # 單家 YoY 連降幾月 = 該家紅點


def _compute(inputs: dict) -> SignalResult:
    rows: list[dict] = []
    reds = yellows = greens = 0
    latest_months: list[str] = []

    parsed: dict[str, list] = {}
    for sid, _ in COMPANIES:
        rev = list(inputs.get(f"r{sid}") or [])[-BARS:]
        parsed[sid] = rev
        if len(rev) >= 2:
            latest_months.append(str(rev[-1][0]))
    max_month = max(latest_months) if latest_months else ""

    for sid, name in COMPANIES:
        rev = parsed[sid]
        if len(rev) < 2:
            rows.append({"cells": [f"{name} ({sid})", "—", "—"], "dot": "gray", "spark": []})
            continue
        yoy = [float(v) for _, v in rev]
        consec = consec_declines(yoy)
        dot = "red" if consec >= RED_CONSEC else "yellow" if consec == 1 else "green"
        reds += int(dot == "red")
        yellows += int(dot == "yellow")
        greens += int(dot == "green")
        # 各家公布有先後：資料月份落後於同表最新月的，明講「至X月」
        month = str(rev[-1][0])
        lag = f"（至{int(month[-2:])}月）" if month < max_month else ""
        rows.append({
            "cells": [f"{name} ({sid})", f"{yoy[-1]:+.1f}%{lag}",
                      f"連降{consec}月" if consec else "未連降"],
            "dot": dot,
            "spark": [round(v, 2) for v in yoy],
        })

    counted = reds + yellows + greens
    if counted == 0:
        return SignalResult(light="gray", rows=rows,
                            extra={"columns": ["公司", "最新YoY", "動能", "燈", "近12月"]})

    # 與主燈同一張真值表：≥2 紅→紅；任一紅/黃→黃；全綠→綠
    light = "red" if reds >= 2 else ("yellow" if (reds or yellows) else "green")
    caption = "點＝動能燈（綠 未連降・黃 連降1月・紅 連降≥2月）・線＝近12月YoY走勢"
    if counted < len(COMPANIES):
        caption += f"・{len(COMPANIES) - counted} 家暫缺料"
    return SignalResult(
        light=light,
        value_label=f"{greens}/{counted} 擴張中",
        rows=rows,
        extra={"columns": ["公司", "最新YoY", "動能", "燈", "近12月"], "caption": caption},
        detail={"greens": greens, "yellows": yellows, "reds": reds, "counted": counted},
    )


SIGNAL = SignalSpec(
    id="leadframe_rev_yoy",
    name="導線架四雄營收動能",
    cluster="leadframe_osat",
    tags=("導線架", "封測", "功率元件", "月營收"),
    widget="table",
    bindings=tuple(
        DataBinding(key=f"r{sid}", source="finmind_revenue",
                    params={"stock_id": sid, "months": BARS + 2})
        for sid, _ in COMPANIES
    ),
    compute=_compute,
    interpretations={
        "green": "四家營收年增全數延續，缺貨/漲價全面灌進財報，封測行情有基本面支撐。",
        "yellow": "部分公司營收動能鈍化——觀察是全面轉弱的起點，還是單一公司的雜訊。",
        "red": "兩家以上 YoY 連降 2 個月，產業級動能轉弱，封測先行指標轉負。",
        "gray": "月營收資料尚未更新或抓取失敗。",
    },
    cadence="monthly",
    track="導線架四雄（順德(2351)、長科(6548)、界霖(5285)、一詮(2486)）各自的月營收 YoY 動能——缺貨與漲價最終都要灌進營收；四家並列看「全面延續還是一家獨撐」，單一公司的轉單、基期、副業雜訊（順德含文具、一詮多 LED 支架）騙不了整排。",
    shape="每列一家：點＝動能燈（綠 未連降／黃 連降1月／紅 連降≥2月），線＝近12月 YoY 走勢；紅點變多＝產業級轉弱，只有一家紅＝公司個案。",
    order=7,
    in_master=True,
    unit="% YoY",
)
