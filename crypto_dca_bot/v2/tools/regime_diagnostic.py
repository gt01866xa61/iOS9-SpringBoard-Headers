"""Regime 診斷 runner:每個新策略都要過這關 — 證明 edge 不是只靠某一種天氣。

跑法(crypto_dca_bot/ 底下):  python3 -m v2.tools.regime_diagnostic

輸出三段(2026-06-14「為什麼垮」診斷固化):
1. 年度行情(net% + ER):看 in-sample 期是不是剛好大牛市(策略好看 = 天時?)
2. 每策略 OOS 視窗按 regime 分桶:上升趨勢有沒有 edge、盤整盤是不是一起垮
3. Buy&Hold 對照:策略的 OOS 表現是「策略爛」還是「整體市場難做」(edge vs beta)

新策略接法:寫一個 factory()(回 (symbols, portfolios))+ 對應 series,呼叫
`regime_report(name, series, factory, price_map)`。
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ..analysis import (
    CHOP,
    DOWN,
    UP,
    bucket_windows,
    closes_in_range,
    efficiency_ratio,
    equity_returns,
    net_return,
    sharpe,
    single_split,
    walk_forward,
)
from ..analysis.walk_forward import StrategyFactory, Series
from ..data import CsvFundingLoader, CsvLoader
from ..interfaces import NoOpParams, NoOpPortfolioStrategy
from ..strategies import (
    DonchianBreakout,
    DonchianParams,
    FundingSkew,
    FundingSkewParams,
    MacroOverlay,
    MacroOverlayParams,
)

FIX = Path(__file__).resolve().parents[1] / "data" / "fixtures"
PM = {"BTC": "BTC_kline_1d", "ETH": "ETH_kline_1d"}
_LABEL = {UP: "上升趨勢", DOWN: "下跌趨勢", CHOP: "盤整/震盪"}


def regime_report(
    name: str,
    series: Series,
    factory: StrategyFactory,
    *,
    regime_field: str = "BTC_kline_1d",
    price_map: dict[str, str] | None = None,
) -> dict:
    """跑 walk-forward + 按 regime 分桶,印表並回 buckets(供測試 / 後續分析)。"""
    pm = price_map or PM
    wf = walk_forward(series, factory, price_map=pm)
    buckets = bucket_windows(wf.windows, series[regime_field])
    print(f"\n=== {name} — OOS regime 分桶({wf.n_windows} 視窗)===")
    print(f"  {'regime':10s} {'視窗':>4} {'平均OOS報酬':>11} {'勝率':>6} {'市場ER':>7}")
    for r in (UP, CHOP, DOWN):
        b = buckets[r]
        print(f"  {_LABEL[r]:8s} {b.n_windows:>4} {b.mean_oos_return*100:>+10.1f}% "
              f"{b.win_rate*100:>5.0f}% {b.mean_efficiency:>7.2f}")
    up, chop = buckets[UP], buckets[CHOP]
    verdict = ("edge 集中在上升趨勢、盤整盤垮 → 趨勢類(看天吃飯)"
               if up.mean_oos_return > 0 and chop.mean_oos_return <= 0
               else "非典型趨勢型 — 看分桶細節")
    print(f"  → {verdict}")
    return buckets


def _annual_regime(btc, eth) -> None:
    print("=== 年度行情(BTC / ETH net% + BTC ER)— in-sample 是不是大牛市? ===")
    for y in range(btc[0][0].year, btc[-1][0].year + 1):
        a, b = datetime(y, 1, 1), datetime(y + 1, 1, 1)
        bp, ep = closes_in_range(btc, a, b), closes_in_range(eth, a, b)
        if len(bp) < 2:
            continue
        print(f"  {y}: BTC {net_return(bp)*100:>+7.1f}%  ETH {net_return(ep)*100:>+7.1f}%  "
              f"BTC_ER {efficiency_ratio(bp):.2f}")


def _buy_and_hold_oos(btc, eth, split_ts: datetime) -> None:
    bo = closes_in_range(btc, split_ts, datetime(9999, 1, 1))
    eo = closes_in_range(eth, split_ts, datetime(9999, 1, 1))
    n = min(len(bo), len(eo))
    if n < 2:
        return
    bh = [(bo[i] / bo[0] + eo[i] / eo[0]) / 2 for i in range(n)]
    print(f"\n=== Buy&Hold 50/50 對照(OOS {split_ts.date()}→末)— edge vs 只是吃 beta ===")
    print(f"  Buy&Hold 報酬 {(bh[-1]-1)*100:+.1f}%  Sharpe {sharpe(equity_returns(bh)):.2f}")
    print("  (B&H 也低 → 該段市場整體難做,非策略獨有;B&H 高但策略低 → 策略真的爛)")


def _kline():
    return {"BTC_kline_1d": CsvLoader(FIX / "btc_usd_1d.csv", "BTC_kline_1d").fetch(),
            "ETH_kline_1d": CsvLoader(FIX / "eth_usd_1d.csv", "ETH_kline_1d").fetch()}


def _f_donchian():
    return ([DonchianBreakout(DonchianParams(symbol="BTC", entry=20, exit=10)),
             DonchianBreakout(DonchianParams(symbol="ETH", entry=20, exit=10))],
            [NoOpPortfolioStrategy(NoOpParams(symbols=["BTC", "ETH"]))])


def _f_funding():
    return ([FundingSkew(FundingSkewParams(symbol="BTC", lookback_periods=21)),
             FundingSkew(FundingSkewParams(symbol="ETH", lookback_periods=21))],
            [NoOpPortfolioStrategy(NoOpParams(symbols=["BTC", "ETH"]))])


def _f_overlay():
    return ([DonchianBreakout(DonchianParams(symbol="BTC", entry=20, exit=10)),
             DonchianBreakout(DonchianParams(symbol="ETH", entry=20, exit=10))],
            [MacroOverlay(MacroOverlayParams(symbols=["BTC", "ETH"]))])


def main() -> None:
    kl = _kline()
    btc, eth = kl["BTC_kline_1d"], kl["ETH_kline_1d"]
    _annual_regime(btc, eth)

    regime_report("S1 Donchian BTC+ETH", dict(kl), _f_donchian)

    s2 = dict(kl)
    s2["BTC_funding_8h"] = CsvFundingLoader(FIX / "btc_funding_8h.csv", "BTC_funding_8h").fetch()
    s2["ETH_funding_8h"] = CsvFundingLoader(FIX / "eth_funding_8h.csv", "ETH_funding_8h").fetch()
    regime_report("S2 FundingSkew BTC+ETH", s2, _f_funding)

    s3 = dict(kl)
    s3["vix_daily"] = CsvLoader(FIX / "vix_daily.csv", "vix_daily").fetch()
    regime_report("S3 Donchian + MacroOverlay(VIX)", s3, _f_overlay)

    sp = single_split(kl, _f_donchian, price_map=PM)
    _buy_and_hold_oos(btc, eth, sp.split_ts)


if __name__ == "__main__":
    main()
