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
    """回傳 {symbol: [close, ...]}（舊→新），缺的 symbol 給空 list。"""
    symbols = params.get("symbols", [])
    return {s: fixture.get(s, []) for s in symbols}


DEMO_SHAPERS = {
    "finmind_revenue": _finmind_revenue,
    "yf_close": _yf_close,
}
