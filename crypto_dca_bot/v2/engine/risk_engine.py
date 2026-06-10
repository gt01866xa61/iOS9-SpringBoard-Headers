"""Risk Engine(framework 一級護欄,always-on,使用者不可關)。

ref: architecture.md §4.1 / R3-①(a + bc 拍板)。
三 sub-stage:vol-targeting sizing / portfolio-gross 上限 / stale 終責。
**Block 3 拍板**:gross 看 post-cap + post-vol-targeting 的數字
(已含守門員 #3C fail-safe 後果)。

V2-B 階段:
- vol-targeting:介面定好(輸入 target% 輸出 sized %),default = pass-through
  (架構決定要 vol-targeting,但**公式選型 V2-B 校準** — 留 hook 給策略期接)
- gross:sum > limit → 比例壓縮所有 symbol(數字 placeholder)
- stale 終責:**所有相關策略皆缺席**時強制砍到 conservative cap(避免空池+缺
  fail-safe 變裸奔;與 #3C 同方向)

數字全 placeholder,V2-B 校準。
"""
from __future__ import annotations

from typing import Protocol

# placeholders,V2-B 校準
GROSS_LIMIT_DEFAULT = 0.95         # 保留 5% cash buffer
TERMINAL_FALLBACK_CAP = 0.3        # 終責 fallback(全策略缺席時)


class VolEstimator(Protocol):
    """vol-targeting hook:策略期接 realized vol estimator。

    V2-B default = IdentityVolEstimator(不調整,pass-through)。
    """

    def scale(self, symbol: str) -> float: ...


class IdentityVolEstimator:
    """default:不做事(架構留 hook,公式 V2-B 校準)。"""

    def scale(self, symbol: str) -> float:
        return 1.0


def apply_risk_engine(
    target_pct: dict[str, float],
    *,
    all_strategies_absent: bool = False,
    vol_estimator: VolEstimator | None = None,
    gross_limit: float = GROSS_LIMIT_DEFAULT,
    terminal_fallback_cap: float = TERMINAL_FALLBACK_CAP,
) -> dict[str, float]:
    """三 sub-stage 套用,回 risk-adjusted target%。

    順序(architecture.md §2 / §4.1):vol-targeting → gross → stale 終責。
    Block 3:gross 看 vol-targeting 後的數字。
    """
    if not target_pct:
        return {}
    estimator = vol_estimator or IdentityVolEstimator()

    # sub-stage 1: vol-targeting sizing(逐 symbol)
    sized = {
        sym: max(0.0, min(1.0, pct * estimator.scale(sym)))
        for sym, pct in target_pct.items()
    }

    # sub-stage 2: gross 上限(看 vol-targeting 後總和)
    gross = sum(sized.values())
    if gross > gross_limit:
        scale = gross_limit / gross
        sized = {sym: pct * scale for sym, pct in sized.items()}

    # sub-stage 3: stale 終責(全策略集體缺席時的 last-resort)
    if all_strategies_absent:
        sized = {sym: min(pct, terminal_fallback_cap) for sym, pct in sized.items()}

    return sized
