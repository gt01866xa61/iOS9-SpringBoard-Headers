"""demo 模式 shaper：把 demo/fixtures/<source>.json 依 params 整形成「fetcher 會回傳的形狀」。

真正的 live fetcher（Phase 3 的 finmind.py / yfinance_src.py）必須回傳與這裡一致的形狀，
這樣 compute 不必分辨 demo/live。
"""
from __future__ import annotations

from typing import Mapping


def _finmind_revenue(params: Mapping[str, object], fixture: dict) -> list:
    """回傳 [[month, yoy%], ...]（舊→新）。"""
    return fixture.get(str(params["stock_id"]), [])


def _yf_close(params: Mapping[str, object], fixture: dict) -> dict:
    """回傳 {"series": {symbol: [close, ...]}, "asof": {}}（舊→新），缺的 symbol 給空 list。

    fixtures 是合成數列、沒有真實日期，asof 一律留空（不捏造日期）——「資料至」標示只在
    live 模式出現。
    """
    symbols = params.get("symbols", [])
    return {"series": {s: fixture.get(s, []) for s in symbols}, "asof": {}}


def _manual_series(params: Mapping[str, object], fixture: dict) -> object:
    """回傳 fixtures 裡以 key 為鍵的整包 payload（與 live 讀 data/manual/<key>.json 同構）。"""
    return fixture.get(str(params["key"]), {})


DEMO_SHAPERS = {
    "finmind_revenue": _finmind_revenue,
    "yf_close": _yf_close,
    "manual_series": _manual_series,
}
