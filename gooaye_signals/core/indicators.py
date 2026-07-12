"""純技術指標小工具。全部是 pure function，給各 signal 的 compute 共用、可離線單測。

不抓網路、不看時鐘、不寫檔——輸入數列、輸出數字。
"""
from __future__ import annotations

from typing import Optional, Sequence


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)


def sma(series: Sequence[float], window: int) -> Optional[float]:
    """最後 window 根的簡單移動平均；資料不足回 None。"""
    if len(series) < window:
        return None
    return mean(series[-window:])


def above_ma(series: Sequence[float], window: int) -> Optional[bool]:
    """最新值是否站上 window-SMA；資料不足回 None。"""
    m = sma(series, window)
    if m is None:
        return None
    return series[-1] > m


def pct_change(series: Sequence[float]) -> Optional[float]:
    """最新一根相對前一根的漲跌 %；資料不足或前值為 0 回 None。"""
    if len(series) < 2 or series[-2] == 0:
        return None
    return (series[-1] / series[-2] - 1) * 100


def ma_slope_pct(series: Sequence[float], window: int, lookback: int) -> Optional[float]:
    """window-SMA 在 lookback 根之間的斜率（以 %）；資料不足回 None。"""
    if len(series) < window + lookback:
        return None
    ma_now = mean(series[-window:])
    ma_prev = mean(series[-window - lookback:-lookback])
    if ma_prev == 0:
        return None
    return (ma_now / ma_prev - 1) * 100


def basket_index(series_list: Sequence[Sequence[float]]) -> list[float]:
    """把多檔價格序列做「各自歸一到 100、再等權平均」的籃子指數。

    自動丟掉空序列、對齊到最短長度。回傳空 list 代表無可用資料。
    """
    valid = [list(s) for s in series_list if s]
    if not valid:
        return []
    n = min(len(s) for s in valid)
    if n == 0:
        return []
    trimmed = [s[-n:] for s in valid]
    norm = []
    for s in trimmed:
        base = s[0] if s[0] else 1.0
        norm.append([x / base * 100.0 for x in s])
    return [mean(col) for col in zip(*norm)]


def consec_declines(seq: Sequence[float], eps: float = 0.0) -> int:
    """序列尾端「連續下滑」的期數（後值 − 前值 < eps 視為下滑）。

    月營收 YoY 類訊號的共用核心：連降幾個月決定燈色。
    """
    n = 0
    for i in range(len(seq) - 1, 0, -1):
        if seq[i] - seq[i - 1] < eps:
            n += 1
        else:
            break
    return n


def unpack_closes(data: object) -> tuple[dict, dict]:
    """把 yf_close 的回傳拆成 (series, asof)，新舊兩種形狀都吃。

    新：{"series": {sym: [...]}, "asof": {sym: "YYYY-MM-DD"}}
    舊：{sym: [...]}（相容改版前的 last-good 快取與手寫測資）→ asof 給空 dict。
    """
    if not isinstance(data, dict) or not data:
        return {}, {}
    if isinstance(data.get("series"), dict):
        return data["series"], data.get("asof") or {}
    return data, {}


def breadth_light(above: int, counted: int,
                  red_below: float = 40.0, yellow_below: float = 60.0) -> str:
    """站上均線比例 → 燈號（廣度邏輯，也給支援面板當概況燈用）。"""
    if counted == 0:
        return "gray"
    pct = 100.0 * above / counted
    return "red" if pct < red_below else "yellow" if pct < yellow_below else "green"


def quote_row(name: str, series: Sequence[float],
              window: int = 50, spark_n: int = 24, asof: str = "",
              symbol: str = "") -> dict:
    """把一檔的價格序列轉成 table widget 的一列：名稱／價格／漲跌%／站上均線點／迷你走勢。

    asof＝該檔最後收盤日（yf_close 提供）。前端把落後於全表最新日的列標「資料至 MM-DD」，
    休市中的市場（如美股假日）報價凍結時使用者能一眼看出是市場沒開、不是系統沒更新。
    symbol＝抓價用的真實代號（yfinance ticker），顯示成「名稱 (代號)」——每一列都能
    直接溯源到報價來源。名稱與代號之間留空格，窄螢幕（手機）可在此自然斷行，
    避免長代號把表格撐出畫面。
    """
    label = f"{name} ({symbol})" if symbol else name
    if not series:
        return {"cells": [label, "—", "—"], "dot": "gray", "spark": [], "asof": asof}
    price = series[-1]
    chg = pct_change(series)
    amv = above_ma(series, window)
    dot = "gray" if amv is None else ("green" if amv else "red")
    return {
        "cells": [label, f"{price:.2f}", "—" if chg is None else f"{chg:+.1f}%"],
        "dot": dot,
        "spark": [round(float(x), 3) for x in series[-spark_n:]],
        "asof": asof,
    }
