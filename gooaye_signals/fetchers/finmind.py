"""finmind_revenue — 用 FinMind 抓台股月營收並換算 YoY。

回傳形狀（與 demo shaper 一致）：[[month "YYYY-MM", yoy%], ...]（舊→新）。
YoY = 該月營收 / 去年同月營收 - 1。需要至少 months+12 個月的資料。
FINMIND_TOKEN 從環境變數讀（免費註冊）；沒 token 也能跑，只是額度較低。
lazy import：只有真的呼叫時才 import FinMind，demo/測試無需安裝。
"""
from __future__ import annotations

import os
from datetime import date
from typing import Mapping

from fetchers._http import call_with_retry
from logger import get_logger

log = get_logger()


def fetch_revenue(params: Mapping[str, object]) -> list:
    from FinMind.data import DataLoader  # lazy

    stock_id = str(params["stock_id"])
    months = int(params.get("months", 14))
    # 為了算 YoY，往前多抓 ~13 個月的緩衝
    lookback_days = (months + 14) * 31
    start = (date.today().toordinal() - lookback_days)
    start_date = date.fromordinal(max(start, 1)).isoformat()

    api = DataLoader()
    token = os.environ.get("FINMIND_TOKEN")
    if token:
        try:
            api.login_by_token(api_token=token)
        except Exception as exc:  # noqa: BLE001
            log.warning("FinMind token 登入失敗，改用匿名額度：%s", exc)

    def _q():
        return api.taiwan_stock_month_revenue(stock_id=stock_id, start_date=start_date)

    df = call_with_retry(_q, desc=f"finmind_revenue {stock_id}")
    if df is None or df.empty:
        return []

    # 建 (year, month) -> revenue
    rev_by_ym: dict[tuple[int, int], float] = {}
    for _, row in df.iterrows():
        y = int(row["revenue_year"])
        m = int(row["revenue_month"])
        rev_by_ym[(y, m)] = float(row["revenue"])

    out: list[list] = []
    for (y, m) in sorted(rev_by_ym):
        prev = rev_by_ym.get((y - 1, m))
        if not prev:
            continue
        yoy = (rev_by_ym[(y, m)] / prev - 1) * 100
        out.append([f"{y:04d}-{m:02d}", round(yoy, 2)])

    return out[-months:]
