"""算量站(技術轉換):target% → USDT → 數量。

ref: architecture.md §2(pipeline 階段 5)/ §4.2(跟 Risk Engine 分 2 站,
     R3-① Block 2)。
**這站只做純數學換算**,不碰風控判斷(否則變雜物抽屜,R3-① 否決的反面)。
fee / slippage 精確模型 = B5 executor 的事(Round 1 Gap 4 拍板),
B4 階段這站只算「無摩擦下單量」。
"""
from __future__ import annotations


def size_to_quantity(
    target_pct: dict[str, float],
    prices: dict[str, float],
    equity: float,
) -> dict[str, float]:
    """{symbol: target%} × equity / price → {symbol: desired qty}.

    缺價格的 symbol 跳過(寧可不下單也不亂下);target_pct=0 也回 0.0
    (讓執行政策層比對 current 決定要不要清倉)。
    """
    out: dict[str, float] = {}
    if equity <= 0:
        return out
    for sym, pct in target_pct.items():
        price = prices.get(sym)
        if price is None or price <= 0:
            continue
        out[sym] = pct * equity / price
    return out
