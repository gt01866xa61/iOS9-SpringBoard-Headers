"""Regime 診斷:把 OOS 視窗按行情(上升趨勢 / 下跌趨勢 / 盤整)分類,檢查策略
表現是不是 regime-dependent(只靠某一種天氣)。

ref: 2026-06-14 「2024-2026 為什麼垮」診斷固化成資產。**每個新策略都要過這關**:
證明它的 edge 不是只在某一種行情才有,否則策略池 DNA 太單一 → 盤整一起垮。

regime 用**策略無關**的市場度量(避免循環論證 — 不能用策略自己的 P&L 定義 regime):
- net return:視窗內價格淨變動(方向 + 幅度)
- Kaufman efficiency ratio (ER):|淨變動| / Σ|逐日變動|,∈[0,1]。
  ER=1 乾淨單邊、ER→0 來回震盪。衡量趨勢「乾不乾淨」。
分類(以 net 為主、ER 佐證):
  net > +T  → up_trend
  net < −T  → down_trend
  |net| ≤ T → chop(盤整 / 震盪)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import mean
from typing import Protocol

TREND_THRESHOLD_DEFAULT = 0.15  # ±15% / 視窗 視為趨勢盤;否則盤整

UP, DOWN, CHOP = "up_trend", "down_trend", "chop"


def efficiency_ratio(closes: list[float]) -> float:
    """Kaufman ER = |淨變動| / Σ|逐日變動|,∈[0,1]。空/單點 → 0。"""
    if len(closes) < 2:
        return 0.0
    path = sum(abs(closes[i] - closes[i - 1]) for i in range(1, len(closes)))
    return abs(closes[-1] - closes[0]) / path if path > 0 else 0.0


def net_return(closes: list[float]) -> float:
    """視窗淨報酬 = close[-1]/close[0] − 1。"""
    return (closes[-1] / closes[0] - 1.0) if len(closes) >= 2 and closes[0] > 0 else 0.0


def classify(net: float, *, trend_threshold: float = TREND_THRESHOLD_DEFAULT) -> str:
    """net 淨報酬 → regime 標籤。"""
    if net > trend_threshold:
        return UP
    if net < -trend_threshold:
        return DOWN
    return CHOP


class _HasClose(Protocol):
    close: float


def closes_in_range(
    series: list[tuple[datetime, object]], start: datetime, end: datetime
) -> list[float]:
    """切 [start, end) 的收盤序列。value 可為 Bar(取 .close)或 float。"""
    out: list[float] = []
    for ts, v in series:
        if start <= ts < end:
            out.append(v.close if hasattr(v, "close") else float(v))
    return out


@dataclass(frozen=True)
class RegimeBucket:
    regime: str
    n_windows: int
    mean_oos_return: float   # 策略在此 regime 視窗的平均 OOS 報酬
    win_rate: float          # OOS 報酬 > 0 的視窗比例
    window_returns: list[float]
    mean_efficiency: float   # 此 regime 視窗的平均 ER(市場乾淨度)


class _Window(Protocol):
    oos_start: datetime
    oos_end: datetime
    oos_return: float


def bucket_windows(
    windows: list[_Window],
    regime_series: list[tuple[datetime, object]],
    *,
    trend_threshold: float = TREND_THRESHOLD_DEFAULT,
) -> dict[str, RegimeBucket]:
    """把 walk-forward 的 OOS 視窗按 regime 分桶,回每桶的策略表現彙總。

    windows: 任何有 oos_start/oos_end/oos_return 的物件(WalkForwardResult.windows)。
    regime_series: 定義 regime 的市場價格序列(策略無關,如 BTC 日線)。
    """
    grouped: dict[str, list[tuple[float, float]]] = {UP: [], DOWN: [], CHOP: []}
    for w in windows:
        closes = closes_in_range(regime_series, w.oos_start, w.oos_end)
        r = classify(net_return(closes), trend_threshold=trend_threshold)
        grouped[r].append((w.oos_return, efficiency_ratio(closes)))

    out: dict[str, RegimeBucket] = {}
    for regime, rows in grouped.items():
        rets = [ret for ret, _ in rows]
        ers = [er for _, er in rows]
        out[regime] = RegimeBucket(
            regime=regime,
            n_windows=len(rows),
            mean_oos_return=mean(rets) if rets else 0.0,
            win_rate=(sum(1 for x in rets if x > 0) / len(rets)) if rets else 0.0,
            window_returns=rets,
            mean_efficiency=mean(ers) if ers else 0.0,
        )
    return out
