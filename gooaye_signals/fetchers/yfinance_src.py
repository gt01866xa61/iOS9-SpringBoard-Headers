"""yf_close — 用 yfinance 抓收盤序列。支援 .TW/.TWO/.KS/US/期貨(如 PA=F)。

回傳形狀（與 demo shaper 一致）：{symbol: [close, ...]}（舊→新），缺的 symbol 給空 list。
yfinance 為非官方套件、偶爾因 Yahoo 改版失效——單一 symbol 抓失敗只給空 list，不拖垮整批。
lazy import：只有真的呼叫時才 import yfinance，demo/測試無需安裝。
"""
from __future__ import annotations

from typing import Mapping

from fetchers._http import call_with_retry
from logger import get_logger

log = get_logger()


def fetch_close(params: Mapping[str, object]) -> dict:
    import yfinance as yf  # lazy

    symbols = list(params.get("symbols", []))
    days = int(params.get("days", 120))
    if not symbols:
        return {}

    # 多抓一些天數當 50MA + 斜率的緩衝
    period = f"{max(days, 60) + 60}d"

    def _dl():
        return yf.download(symbols, period=period, interval="1d",
                           progress=False, group_by="ticker", threads=True, auto_adjust=True)

    data = call_with_retry(_dl, desc="yf.download")

    out: dict[str, list[float]] = {}
    for s in symbols:
        try:
            if len(symbols) > 1:
                ser = data[s]["Close"]
            else:
                ser = data["Close"]
            closes = [float(x) for x in ser.dropna().tolist()]
            out[s] = closes[-days:] if days else closes
        except Exception as exc:  # noqa: BLE001 — 單檔失敗隔離
            log.warning("yf_close 取不到 %s：%s", s, exc)
            out[s] = []
    return out
