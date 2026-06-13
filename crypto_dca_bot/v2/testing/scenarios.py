"""M1 壓測合成序列產生器(B7,stale-aware)。

ref: architecture.md §8(M1 stress test 必須 stale-aware)/ glossary M1。
拍板(B7,2026-05-26):**合成序列 + 預留真資料接點** — 不抓真歷史
(那是 V2-S 開工的事),用合成價格 + 故意製造的資料斷流(data gap)壓測
framework 對 stale 的反應(跳過 / on_stale / counter alert / fail-safe)。

關鍵:LUNA/FTX 那種行情交易所 API 大量 timeout → 大量 stale。M1 不只測
策略邏輯,**stale 機制本身**要被壓測。合成 gap 正是模擬這個。

真資料接點:replace make_*_series 的價格產生即可,event 介面不變。
"""
from __future__ import annotations

from datetime import datetime, timedelta

from ..data.events import DataEvent
from ..interfaces.types import Bar


def make_bar_series(
    field: str,
    start: datetime,
    closes: list[float],
    *,
    step: timedelta = timedelta(days=1),
    hl_spread: float = 0.0,
) -> list[tuple[datetime, Bar]]:
    """從 close 序列合成 OHLCV Bar 序列(high/low = close ± spread)。

    hl_spread=0 → high=low=close(純突破測試,通道 = 過去 close 高低)。
    供真策略(Donchian 等)的合成測試用。
    """
    out: list[tuple[datetime, Bar]] = []
    prev = closes[0] if closes else 0.0
    for i, c in enumerate(closes):
        out.append(
            (
                start + i * step,
                Bar(
                    open=prev,
                    high=c + hl_spread,
                    low=c - hl_spread,
                    close=c,
                    volume=1.0,
                ),
            )
        )
        prev = c
    return out


def make_kline_series(
    field: str,
    start: datetime,
    n: int,
    *,
    start_price: float = 50000.0,
    step: timedelta = timedelta(hours=1),
    drift: float = 0.0,
    crash_at: int | None = None,
    crash_pct: float = -0.5,
    gap_range: tuple[int, int] | None = None,
) -> list[tuple[datetime, float]]:
    """合成 K 線收盤序列。

    crash_at: 第 i 根突然 crash_pct(模擬崩盤)。
    gap_range: (start_idx, end_idx) 這段**不產生資料**(模擬 API timeout
               → 後續 fire 會判 stale)。
    """
    out: list[tuple[datetime, float]] = []
    price = start_price
    for i in range(n):
        if gap_range is not None and gap_range[0] <= i < gap_range[1]:
            price *= 1.0 + drift  # 價格內部仍動,但「不發出」(資料斷流)
            continue
        if crash_at is not None and i == crash_at:
            price *= 1.0 + crash_pct
        else:
            price *= 1.0 + drift
        out.append((start + i * step, round(price, 2)))
    return out


def make_macro_series(
    field: str,
    start: datetime,
    n: int,
    *,
    value: float = 18.0,
    spike_at: int | None = None,
    spike_value: float = 45.0,
    step: timedelta = timedelta(days=1),
    gap_range: tuple[int, int] | None = None,
) -> list[tuple[datetime, float]]:
    """合成 macro 指標(VIX 類)序列,可注入 spike + gap。"""
    out: list[tuple[datetime, float]] = []
    for i in range(n):
        if gap_range is not None and gap_range[0] <= i < gap_range[1]:
            continue
        v = spike_value if (spike_at is not None and i == spike_at) else value
        out.append((start + i * step, v))
    return out


# M1 五段崩盤的 placeholder anchor(真日期,合成價格;V2-S 換真資料)
M1_CRASHES = {
    "covid_2020_03": datetime(2020, 3, 9),
    "china_2021_05": datetime(2021, 5, 19),
    "luna_2022_05": datetime(2022, 5, 9),
    "ftx_2022_11": datetime(2022, 11, 8),
    "jpy_carry_2024_08": datetime(2024, 8, 5),
}


def make_crash_scenario(
    anchor: datetime,
    *,
    pre_bars: int = 30,
    post_bars: int = 30,
    api_gap_bars: int = 6,
) -> dict[str, list[tuple[datetime, float]]]:
    """一段崩盤情境:崩盤點 + 緊接著一段 API gap(stale 觸發)。

    模擬「崩盤當下交易所 API timeout → kline 斷流 api_gap_bars 根」。
    回 series dict 可直接餵 BacktestReplayDriver。
    """
    n = pre_bars + post_bars
    crash_idx = pre_bars
    return {
        "BTC_kline_1h": make_kline_series(
            "BTC_kline_1h", anchor, n,
            crash_at=crash_idx, crash_pct=-0.4,
            gap_range=(crash_idx + 1, crash_idx + 1 + api_gap_bars),
        ),
        "ETH_kline_1h": make_kline_series(
            "ETH_kline_1h", anchor, n, start_price=3000.0,
            crash_at=crash_idx, crash_pct=-0.45,
            gap_range=(crash_idx + 1, crash_idx + 1 + api_gap_bars),
        ),
    }
