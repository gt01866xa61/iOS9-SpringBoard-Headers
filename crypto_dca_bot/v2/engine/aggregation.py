"""Symbol target 加總 + Portfolio cap min 合併 + #3C fallback。

ref: architecture.md §2(pipeline 階段 2-3)/ §3.1(雙 interface 輸出形狀)
     / §6.4(#3C / #3D)。

Symbol 加總:多 SymbolStrategy 對同 symbol 的 target%,**per-strategy
capital weight** 加權平均(V2-B 階段 equal-weight default,V2-E meta-layer
才接 dynamic allocator)。Round 1 拍板輸出形狀沒指定加總方式,equal-weight
是合理 baseline。

Portfolio 合併(#3D min 取最狠):多 PortfolioStrategy 對同 symbol 的 cap
取 min(最保守者勝)。#3C 補釘:**缺席守門員的 fallback_cap 也丟進同一個
min 池**(非 min 算完後二次施加 — 後者會在「fallback 比現場 cap 寬鬆」時
反而放寬倉位、違反取最狠地基)。

空池(全部 symbol 沒任何守門員 vote)→ cap = 1.0。**注意這不是裸奔** —
Risk Engine 是 framework 護欄、always-on、不可關,後面還會把關。
"""
from __future__ import annotations

# #3C placeholder default,V2-B 校準
FALLBACK_CAP_DEFAULT = 0.5


def aggregate_symbol_targets(
    outputs: dict[str, dict[str, float]],
    weights: dict[str, float] | None = None,
) -> dict[str, float]:
    """{strategy_name: {symbol: target%}} → {symbol: combined_target%}.

    weights = per-strategy capital weight;None = equal-weight。
    缺席策略**不在 outputs 裡** → 不參與加總(從 weight 分母也消失)。
    某 symbol 在某策略沒輸出 → 該策略對它出 0(沒興趣)。
    """
    if not outputs:
        return {}
    if weights is None:
        weights = {name: 1.0 for name in outputs}
    total_w = sum(weights[name] for name in outputs)
    if total_w <= 0:
        return {}
    all_symbols = {s for out in outputs.values() for s in out}
    return {
        sym: sum(
            outputs[name].get(sym, 0.0) * weights[name] for name in outputs
        ) / total_w
        for sym in all_symbols
    }


def merge_portfolio_caps(
    outputs: dict[str, dict[str, float]],
    absent_portfolios: set[str],
    symbols: set[str],
    *,
    fallback_cap: float = FALLBACK_CAP_DEFAULT,
) -> dict[str, float]:
    """#3D min 合併 + #3C fallback 丟進同一個 min 池。

    outputs: 正常守門員的 cap 輸出 {name: {symbol: cap}}
    absent_portfolios: 因 stale/crash/disabled 而缺席的 PortfolioStrategy 名單
    symbols: 要算 cap 的 symbols(來自 combined_target keys)
    """
    if not symbols:
        return {}
    if not 0.0 <= fallback_cap <= 1.0:
        raise ValueError(f"fallback_cap out of [0,1]: {fallback_cap}")
    caps: dict[str, list[float]] = {s: [] for s in symbols}
    # 正常守門員
    for out in outputs.values():
        for sym in symbols:
            if sym in out:
                caps[sym].append(out[sym])
    # 缺席守門員:fallback_cap 進同一個 min 池(#3C 補釘)
    for _ in absent_portfolios:
        for sym in symbols:
            caps[sym].append(fallback_cap)
    # 空池 = 1.0(Risk Engine 後續把關,non-bypass 不算裸奔)
    return {sym: min(v) if v else 1.0 for sym, v in caps.items()}
