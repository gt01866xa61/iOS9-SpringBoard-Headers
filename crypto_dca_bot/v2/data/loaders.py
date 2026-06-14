"""OHLCV / funding loader 雙軌(V2-S1+S2,A 拍板)。

ref: 跟引擎 I/O 兩側「同介面、可換 driver」同一招。一個 DataLoader 介面,
多種後端(Csv*/Ccxt*)— OHLCV 跟 funding 各一對:

- CsvLoader / CcxtLoader           : OHLCV(Bar)
- CsvFundingLoader / CcxtFundingLoader: funding rate(float per 8h)

兩種 Csv*  → committed CSV fixture → **這個容器能跑**
兩種 Ccxt* → 從 Binance 抓 → **使用者本機 env**(Windows + ccxt,即 V1 那套)
              跑、`to_csv()` 存檔帶回容器餵。**不在容器硬連交易所。**

所有 loader 都吐 list[(datetime, value)],可用 build_replay_series() 組成
{field: series} 餵 BacktestReplayDriver。
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from ..interfaces.types import Bar


class DataLoader(Protocol):
    """通用 loader 介面;value 型別由實作決定(Bar / float / ...)。"""

    field: str

    def fetch(self) -> list[tuple[datetime, object]]: ...


# backward-compat alias(V2-S1 OHLCV-only 時期的命名)
OhlcvLoader = DataLoader


# ============================================================================
# OHLCV(Bar)
# ============================================================================

class CsvLoader:
    """讀 OHLCV CSV(date,open,high,low,close,volume;# 開頭為註解略過)。"""

    def __init__(self, path: str | Path, field: str) -> None:
        self.path = Path(path)
        self.field = field

    def fetch(self) -> list[tuple[datetime, Bar]]:
        out: list[tuple[datetime, Bar]] = []
        with self.path.open() as f:
            lines = [ln for ln in f if not ln.lstrip().startswith("#")]
        reader = csv.DictReader(lines)
        for row in reader:
            ts = datetime.fromisoformat(row["date"])
            out.append(
                (
                    ts,
                    Bar(
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row.get("volume", 0) or 0),
                    ),
                )
            )
        out.sort(key=lambda t: t[0])  # 保證時間序(replay no-lookahead 前提)
        return out


class CcxtLoader:
    """從交易所抓 OHLCV(production / 正典路徑)。

    在使用者本機(ccxt 已裝、有交易所網路)跑;容器內交易所被 proxy 擋。
    ccxt 為 lazy import — 沒裝也能 import 本模組(容器只用 CsvLoader)。
    抓完可用 to_csv() 存檔,再用 CsvLoader 餵回容器。
    """

    def __init__(
        self,
        symbol: str,             # ccxt 格式,如 "BTC/USDT"
        field: str,              # 平台 field 名,如 "BTC_kline_1d"
        *,
        timeframe: str = "1d",
        since: datetime | None = None,
        exchange: str = "binance",
        limit: int = 1000,
    ) -> None:
        self.symbol = symbol
        self.field = field
        self.timeframe = timeframe
        self.since = since
        self.exchange = exchange
        self.limit = limit

    def fetch(self) -> list[tuple[datetime, Bar]]:
        import ccxt  # lazy:容器沒裝也不影響 import

        ex = getattr(ccxt, self.exchange)({"enableRateLimit": True})
        since_ms = int(self.since.timestamp() * 1000) if self.since else None
        out: list[tuple[datetime, Bar]] = []
        while True:
            batch = ex.fetch_ohlcv(self.symbol, self.timeframe, since=since_ms, limit=self.limit)
            if not batch:
                break
            for ts_ms, o, h, l, c, v in batch:
                ts = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).replace(tzinfo=None)
                out.append((ts, Bar(open=o, high=h, low=l, close=c, volume=v)))
            if len(batch) < self.limit:
                break
            since_ms = batch[-1][0] + 1
        out.sort(key=lambda t: t[0])
        return out

    @staticmethod
    def to_csv(series: list[tuple[datetime, Bar]], path: str | Path) -> None:
        """抓完存 CSV(本機跑完 → 帶回容器用 CsvLoader 餵)。"""
        with Path(path).open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["date", "open", "high", "low", "close", "volume"])
            for ts, b in series:
                w.writerow([ts.date().isoformat(), b.open, b.high, b.low, b.close, b.volume])


# ============================================================================
# Funding rate(float per 8h period)
# ============================================================================

class CsvFundingLoader:
    """讀 funding rate CSV(timestamp, funding_rate;# 註解略過)。

    格式跟 CcxtFundingLoader.to_csv() 對稱 — 使用者本機 ccxt 抓 → to_csv() →
    帶回容器 commit 進 fixtures → 本 loader 讀。容器內 ccxt 擋,只走本 loader。
    """

    def __init__(self, path: str | Path, field: str) -> None:
        self.path = Path(path)
        self.field = field

    def fetch(self) -> list[tuple[datetime, float]]:
        out: list[tuple[datetime, float]] = []
        with self.path.open() as f:
            lines = [ln for ln in f if not ln.lstrip().startswith("#")]
        reader = csv.DictReader(lines)
        for row in reader:
            ts = datetime.fromisoformat(row["timestamp"])
            out.append((ts, float(row["funding_rate"])))
        out.sort(key=lambda t: t[0])
        return out


class CcxtFundingLoader:
    """從交易所抓 funding rate history(production / 正典路徑)。

    使用者本機 env 跑;容器擋。Binance USDT-M 永續用 ccxt 統一 swap 格式
    (symbol 例 "BTC/USDT:USDT")。fetch_funding_rate_history 對應
    /fapi/v1/fundingRate(8h 結算)。

    ccxt lazy import(容器無 ccxt 也能 import 本模組)。
    """

    def __init__(
        self,
        symbol: str,            # ccxt 統一格式,例 "BTC/USDT:USDT"
        field: str,             # 平台 field 名,例 "BTC_funding_8h"
        *,
        since: datetime | None = None,
        exchange: str = "binance",
        limit: int = 1000,
    ) -> None:
        self.symbol = symbol
        self.field = field
        self.since = since
        self.exchange = exchange
        self.limit = limit

    def fetch(self) -> list[tuple[datetime, float]]:
        import ccxt  # lazy

        ex = getattr(ccxt, self.exchange)(
            {"enableRateLimit": True, "options": {"defaultType": "swap"}}
        )
        since_ms = int(self.since.timestamp() * 1000) if self.since else None
        out: list[tuple[datetime, float]] = []
        while True:
            batch = ex.fetch_funding_rate_history(self.symbol, since=since_ms, limit=self.limit)
            if not batch:
                break
            for entry in batch:
                ts_ms = entry["timestamp"]
                ts = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).replace(tzinfo=None)
                out.append((ts, float(entry["fundingRate"])))
            if len(batch) < self.limit:
                break
            since_ms = batch[-1]["timestamp"] + 1
        out.sort(key=lambda t: t[0])
        return out

    @staticmethod
    def to_csv(series: list[tuple[datetime, float]], path: str | Path) -> None:
        """抓完存 CSV(本機跑完 → 帶回容器用 CsvFundingLoader 餵)。"""
        with Path(path).open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["timestamp", "funding_rate"])
            for ts, rate in series:
                w.writerow([ts.isoformat(), rate])


# ============================================================================
# 組合
# ============================================================================

def build_replay_series(
    *loaders: DataLoader,
) -> dict[str, list[tuple[datetime, object]]]:
    """多個 loader → {field: [(ts, value)]},直接餵 BacktestReplayDriver。
    value 型別異質(Bar / float)— BacktestReplayDriver 不在意,Snapshot
    消費端(策略 / runner mark_prices)各自處理。
    """
    return {ld.field: ld.fetch() for ld in loaders}

