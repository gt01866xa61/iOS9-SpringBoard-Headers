"""Fixture 建置腳本(provenance + 可重現)。

來源:CoinMetrics community data(reputable)
  https://raw.githubusercontent.com/coinmetrics/data/master/csv/{btc,eth}.csv
欄位:time + PriceUSD(CoinMetrics 日參考價)
範圍:2019-01-01 ~ 2024-12-31(涵蓋 M1 五段崩盤 + 暖機)

⚠️ 重要定位(close-only):
  CoinMetrics community data 是**單一日參考價**(PriceUSD),**沒有 OHLC high/low**。
  本 fixture 把 open=high=low=close=PriceUSD、volume=0 → Donchian 在此資料上
  退化成「**Donchian-on-close**」(通道 = 過去 N 日最高/最低**收盤**,而非最高/最低價)。
  這是合法的 Donchian 常見變體,**足夠 sanity check**(驗策略在真價格形狀上會不會
  爆、進出場形狀對不對),但**不是正典**。
  正典 OHLCV(真 high/low)= Binance via ccxt(CcxtLoader),使用者本機環境抓、
  V2-T 正式驗證用。

重跑:python -m v2.data.fixtures.build_fixture(需 github 網路)
"""
from __future__ import annotations

import csv
import io
import urllib.request
from pathlib import Path

SOURCES = {
    "BTC": "https://raw.githubusercontent.com/coinmetrics/data/master/csv/btc.csv",
    "ETH": "https://raw.githubusercontent.com/coinmetrics/data/master/csv/eth.csv",
}
START, END = "2019-01-01", "2024-12-31"
PRICE_COL = "PriceUSD"
HERE = Path(__file__).resolve().parent

HEADER_COMMENT = [
    "# BTC/ETH daily — sanity-check fixture (NOT canonical)",
    "# source: CoinMetrics community data (PriceUSD, close-only reference rate)",
    "# OHLC are degenerate: open=high=low=close=PriceUSD, volume=0",
    "#   => Donchian here is Donchian-on-CLOSE, not high/low. Sanity only.",
    "# canonical OHLCV = Binance via ccxt (CcxtLoader), V2-T validation.",
    f"# range: {START}..{END}  built by build_fixture.py",
]


def _grab(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")


def build(symbol: str, url: str) -> Path:
    rows = list(csv.DictReader(io.StringIO(_grab(url))))
    out_path = HERE / f"{symbol.lower()}_usd_1d.csv"
    n = 0
    with out_path.open("w", newline="") as f:
        for line in HEADER_COMMENT:
            f.write(line + "\n")
        w = csv.writer(f)
        w.writerow(["date", "open", "high", "low", "close", "volume"])
        for r in rows:
            d = r["time"][:10]
            px = r.get(PRICE_COL, "")
            if not (START <= d <= END) or not px:
                continue
            w.writerow([d, px, px, px, px, "0"])
            n += 1
    print(f"{symbol}: wrote {n} rows -> {out_path.name}")
    return out_path


if __name__ == "__main__":
    for sym, url in SOURCES.items():
        build(sym, url)
