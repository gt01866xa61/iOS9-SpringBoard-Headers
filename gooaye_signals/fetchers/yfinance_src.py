"""yf_close — 用 yfinance 抓收盤序列。支援 .TW/.TWO/.KS/US/期貨(如 PA=F)。

回傳形狀（與 demo shaper 一致）：
    {"series": {symbol: [close, ...]}, "asof": {symbol: "YYYY-MM-DD"}}
series 舊→新、缺的 symbol 給空 list；asof 是該檔最後一根 K 棒的日期（休市中的市場
會停在最後交易日，前端據此標示「資料至」，凍結的報價不會被誤讀成沒更新）。

yfinance 為非官方套件、偶爾因 Yahoo 改版失效——單一 symbol 抓失敗只給空 list，不拖垮整批。
threads=False：yfinance 多執行緒會撞自己的 SQLite 快取鎖（實測 CI 出現
OperationalError('database is locked') 掉檔），序列抓慢幾秒但不掉料。
lazy import：只有真的呼叫時才 import yfinance，demo/測試無需安裝。
"""
from __future__ import annotations

from typing import Mapping

from fetchers._http import call_with_retry
from logger import get_logger

log = get_logger()


def _extract(data, sym: str, multi: bool) -> tuple[list[float], str]:
    """從 yf.download 結果取出單檔 (closes, 最後日期)。任何形狀不符丟給呼叫端隔離。"""
    try:
        ser = data[sym]["Close"]
    except Exception:  # noqa: BLE001 — 單檔下載時 yfinance 可能不分層
        if multi:
            raise
        ser = data["Close"]
    ser = ser.dropna()
    closes = [float(x) for x in ser.tolist()]
    asof = ser.index[-1].strftime("%Y-%m-%d") if closes else ""
    return closes, asof


def fetch_close(params: Mapping[str, object]) -> dict:
    import yfinance as yf  # lazy

    symbols = list(params.get("symbols", []))
    days = int(params.get("days", 120))
    if not symbols:
        return {"series": {}, "asof": {}}

    # 多抓一些天數當 50MA + 斜率的緩衝
    period = f"{max(days, 60) + 60}d"

    def _dl():
        return yf.download(symbols, period=period, interval="1d",
                           progress=False, group_by="ticker", threads=False, auto_adjust=True)

    data = call_with_retry(_dl, desc="yf.download")

    series: dict[str, list[float]] = {}
    asof: dict[str, str] = {}
    for s in symbols:
        try:
            closes, last = _extract(data, s, multi=len(symbols) > 1)
            series[s] = closes[-days:] if days else closes
            asof[s] = last
        except Exception as exc:  # noqa: BLE001 — 單檔失敗隔離
            log.warning("yf_close 取不到 %s：%s", s, exc)
            series[s], asof[s] = [], ""

    # 批次漏掉的單檔補抓一次（yfinance 偶發單檔失敗），仍失敗才回空 list
    for s in [k for k, v in series.items() if not v]:
        try:
            retry = yf.download([s], period=period, interval="1d",
                                progress=False, group_by="ticker", threads=False,
                                auto_adjust=True)
            closes, last = _extract(retry, s, multi=False)
            if closes:
                series[s] = closes[-days:] if days else closes
                asof[s] = last
                log.info("yf_close 補抓成功 %s", s)
        except Exception as exc:  # noqa: BLE001
            log.warning("yf_close 補抓仍失敗 %s：%s", s, exc)

    return {"series": series, "asof": asof}
