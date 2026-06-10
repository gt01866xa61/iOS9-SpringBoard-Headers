"""Framework 執行政策層(framework 一級護欄,使用者不可關)。

ref: architecture.md §4.2 / R3-③ 雙層節流。
位於算量站後、送單前。能力三件套:
- **dead-band**:|current% − desired%| < threshold → 不送單(幅度太小)
- **cooling**:距上次成單 < interval → 不送單(頻率太密)
- **regime hook**:預留 V2-E regime-aware 降頻(架構留 hook,V2-E 接)

擋的是「聚合後才冒出的抖」(守門員 cap + vol-targeting + capital weight
每 bar 都在動,加總後的最終 order 會抖,只有 framework 看得到)。
策略訊號級節流由策略自帶(funding 自帶 dead_band 等),雙層各擋一種。

數字 placeholder,V2-B 校準。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

# placeholders,V2-B 校準
DEAD_BAND_DEFAULT = 0.02         # 差 2% 以下不送單
COOLING_DEFAULT = timedelta(minutes=5)


class RegimeHook(Protocol):
    """V2-E regime-aware 降頻接點。default = no-op(允許所有 order)。"""

    def allow(self, symbol: str, now: datetime) -> bool: ...


class _NoopRegimeHook:
    def allow(self, symbol: str, now: datetime) -> bool:
        return True


@dataclass
class OrderIntent:
    """通過執行政策層的下單意圖(交 B5 executor)。"""

    symbol: str
    target_qty: float
    current_qty: float
    delta_qty: float  # 正 = 買、負 = 賣
    reason: str       # 為何放行(rebalance / open / close)


@dataclass
class FilteredOut:
    """被執行政策層擋下的 candidate(進 event log,debug 用)。"""

    symbol: str
    reason: str       # dead_band / cooling / regime
    delta_pct: float


def apply_execution_policy(
    desired_pct: dict[str, float],
    desired_qty: dict[str, float],
    current_qty: dict[str, float],
    current_pct: dict[str, float],
    last_trade_ts: dict[str, datetime],
    now: datetime,
    *,
    dead_band: float = DEAD_BAND_DEFAULT,
    cooling: timedelta = COOLING_DEFAULT,
    regime_hook: RegimeHook | None = None,
) -> tuple[list[OrderIntent], list[FilteredOut]]:
    """三能力套用 → (放行的 OrderIntents, 擋下的 FilteredOut)。

    順序:dead-band → cooling → regime hook(逐 symbol,獨立判斷)。
    任一擋下 = 不送單,但記 FilteredOut 進 log(B6 觀察用)。
    """
    hook = regime_hook or _NoopRegimeHook()
    sent: list[OrderIntent] = []
    blocked: list[FilteredOut] = []

    for symbol, target_q in desired_qty.items():
        cur_q = current_qty.get(symbol, 0.0)
        cur_p = current_pct.get(symbol, 0.0)
        des_p = desired_pct.get(symbol, 0.0)
        delta_p = des_p - cur_p

        # dead-band
        if abs(delta_p) < dead_band:
            blocked.append(FilteredOut(symbol, "dead_band", delta_p))
            continue
        # cooling
        last = last_trade_ts.get(symbol)
        if last is not None and (now - last) < cooling:
            blocked.append(FilteredOut(symbol, "cooling", delta_p))
            continue
        # regime hook
        if not hook.allow(symbol, now):
            blocked.append(FilteredOut(symbol, "regime", delta_p))
            continue

        delta_q = target_q - cur_q
        reason = "open" if cur_q == 0 else ("close" if target_q == 0 else "rebalance")
        sent.append(
            OrderIntent(
                symbol=symbol,
                target_qty=target_q,
                current_qty=cur_q,
                delta_qty=delta_q,
                reason=reason,
            )
        )

    return sent, blocked
