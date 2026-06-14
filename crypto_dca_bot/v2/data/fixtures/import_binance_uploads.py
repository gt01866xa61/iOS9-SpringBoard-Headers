"""把使用者本機 ccxt 抓的 Binance 正典資料轉成 V2 fixture 格式並 commit
(V2-T 真資料接入,2026-06-13)。

來源(本機 ccxt 跑,因容器 egress proxy 擋交易所):
- BTCUSDT_1d.csv / ETHUSDT_1d.csv:Binance spot 日線 OHLCV,2019-01-01~2026-06-13
- BTCUSDT_funding.csv:Binance USDT-M 永續 funding,2019-09~ (7405 筆)
- ETHUSDT_funding.csv:同上,2019-11~ (7171 筆)

格式:
- 日線 source:`timestamp(ms),open,high,low,close,volume`
- funding source:`timestamp(ms),fundingRate`

V2 fixture 既定格式(CsvLoader / CsvFundingLoader 讀的):
- 日線:`date(YYYY-MM-DD),open,high,low,close,volume`
- funding:`timestamp(ISO),funding_rate`

策略:純轉檔(ts 格式 + funding_rate 欄位名);ts unix-ms → datetime,
zero-padded YYYY-MM-DD;funding 全程 UTC,逐行轉。

provenance(committed 進 fixtures):
- 來源 = 使用者本機 ccxt 跑 Binance(V1 那套)→ to_csv → 上傳容器
- 取代既有 CoinMetrics close-only(close-only 退役、改用真 OHLCV)
- 啟用 S2 的 requires_funding_fixture 真資料 sanity

重跑:在容器內擺好上傳檔後 python -m v2.data.fixtures.import_binance_uploads
(實際使用者上傳路徑由本檔 CLI 參數帶入)
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent

KLINE_HEADER = [
    "# BTC/ETH daily OHLCV — V2-T canonical fixture (REAL OHLC)",
    "# source: Binance spot via ccxt, fetched on user's local machine (V1 stack)",
    "#         then uploaded to container (egress proxy blocks exchanges in container)",
    "# imported: 2026-06-13 by import_binance_uploads.py",
    "# 取代既有 CoinMetrics close-only fixture — Donchian 現在用真 high/low",
    "# (退役 close-only 變體,結果作廢、重跑)",
]

FUNDING_HEADER = [
    "# {sym} funding rate 8h — V2-T canonical fixture",
    "# source: Binance USDT-M perpetual via ccxt, fetched on user's local machine",
    "#         then uploaded to container",
    "# imported: 2026-06-13 by import_binance_uploads.py",
    "# 啟用 V2-S2 真資料 sanity(原本 requires_funding_fixture skip)",
]


def import_kline(src: Path, dst: Path) -> int:
    """ts(ms),open,high,low,close,volume → date(ISO),open,high,low,close,volume"""
    rows = list(csv.DictReader(src.open()))
    with dst.open("w", newline="") as f:
        for line in KLINE_HEADER:
            f.write(line + "\n")
        w = csv.writer(f)
        w.writerow(["date", "open", "high", "low", "close", "volume"])
        for r in rows:
            ts = datetime.fromtimestamp(int(r["timestamp"]) / 1000, tz=timezone.utc)
            w.writerow([
                ts.date().isoformat(),
                r["open"], r["high"], r["low"], r["close"], r["volume"],
            ])
    return len(rows)


def import_funding(src: Path, dst: Path, sym: str) -> int:
    """ts(ms),fundingRate → timestamp(ISO),funding_rate"""
    rows = list(csv.DictReader(src.open()))
    with dst.open("w", newline="") as f:
        for line in FUNDING_HEADER:
            f.write(line.format(sym=sym) + "\n")
        w = csv.writer(f)
        w.writerow(["timestamp", "funding_rate"])
        for r in rows:
            ts = datetime.fromtimestamp(int(r["timestamp"]) / 1000, tz=timezone.utc)
            w.writerow([ts.replace(tzinfo=None).isoformat(), r["fundingRate"]])
    return len(rows)


def main(uploads: list[Path]) -> None:
    """uploads 順序:BTC_kline, ETH_kline, BTC_funding, ETH_funding。"""
    btc_kline, eth_kline, btc_funding, eth_funding = uploads
    n = import_kline(btc_kline, HERE / "btc_usd_1d.csv")
    print(f"BTC 1d: {n} rows -> btc_usd_1d.csv (取代 CoinMetrics close-only)")
    n = import_kline(eth_kline, HERE / "eth_usd_1d.csv")
    print(f"ETH 1d: {n} rows -> eth_usd_1d.csv")
    n = import_funding(btc_funding, HERE / "btc_funding_8h.csv", "BTC")
    print(f"BTC funding: {n} rows -> btc_funding_8h.csv (新增,啟用 S2 真資料 sanity)")
    n = import_funding(eth_funding, HERE / "eth_funding_8h.csv", "ETH")
    print(f"ETH funding: {n} rows -> eth_funding_8h.csv")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(__doc__)
        print("\nUsage: python -m v2.data.fixtures.import_binance_uploads "
              "<BTC_1d.csv> <ETH_1d.csv> <BTC_funding.csv> <ETH_funding.csv>")
        sys.exit(2)
    main([Path(p) for p in sys.argv[1:]])
