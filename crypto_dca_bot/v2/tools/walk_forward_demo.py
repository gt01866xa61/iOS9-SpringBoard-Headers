"""T2 walk-forward demo:三策略 OOS 驗證,pooled WFE + 單一 split 對照。

跑法(crypto_dca_bot/ 底下):  python3 -m v2.tools.walk_forward_demo

兩個算法都印(2026-06-14 拍板):
- pooled OOS WFE(主):30/3 滑窗,全部 OOS 段日報酬拼一條 Sharpe ÷ mean IS Sharpe
- single 70/30 split(對照):一段連續跑,boundary 切
兩者一致才信;打架 = 警訊。per-window 數字(含 OOS 交易筆數)印出當診斷。

M2 閘:WFE > 50%。低頻策略每窗 <30 筆,**per-window WFE 不當閘門**,看 pooled +
split 兩個 aggregate。
"""
from __future__ import annotations

from pathlib import Path

from ..analysis import single_split, walk_forward
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


def _kline():
    return {
        "BTC_kline_1d": CsvLoader(FIX / "btc_usd_1d.csv", "BTC_kline_1d").fetch(),
        "ETH_kline_1d": CsvLoader(FIX / "eth_usd_1d.csv", "ETH_kline_1d").fetch(),
    }


def _donchian_factory():
    return (
        [DonchianBreakout(DonchianParams(symbol="BTC", entry=20, exit=10)),
         DonchianBreakout(DonchianParams(symbol="ETH", entry=20, exit=10))],
        [NoOpPortfolioStrategy(NoOpParams(symbols=["BTC", "ETH"]))],
    )


def _funding_factory():
    return (
        [FundingSkew(FundingSkewParams(symbol="BTC", lookback_periods=21)),
         FundingSkew(FundingSkewParams(symbol="ETH", lookback_periods=21))],
        [NoOpPortfolioStrategy(NoOpParams(symbols=["BTC", "ETH"]))],
    )


def _overlay_factory():
    return (
        [DonchianBreakout(DonchianParams(symbol="BTC", entry=20, exit=10)),
         DonchianBreakout(DonchianParams(symbol="ETH", entry=20, exit=10))],
        [MacroOverlay(MacroOverlayParams(symbols=["BTC", "ETH"]))],
    )


def _gate(wfe: float) -> str:
    if wfe != wfe:  # NaN
        return "N/A (IS Sharpe<=0)"
    return "PASS ✓" if wfe > 0.50 else "FAIL ✗"


def report(name: str, series, factory) -> None:
    wf = walk_forward(series, factory, price_map=PM)
    sp = single_split(series, factory, price_map=PM)
    print(f"\n=== {name} ===")
    print(f"  walk-forward windows : {wf.n_windows}  (IS=30mo / OOS=3mo / step=3mo)")
    print(f"  total OOS trades     : {wf.total_oos_trades}  "
          f"(median/window {_median([w.oos_trades for w in wf.windows])})")
    print(f"  [pooled]  OOS Sharpe {wf.pooled_oos_sharpe:6.3f}  / mean IS Sharpe "
          f"{wf.mean_is_sharpe:6.3f}  → WFE {wf.wfe_pooled:7.1%}  {_gate(wf.wfe_pooled)}")
    print(f"  [split ]  OOS Sharpe {sp.oos_sharpe:6.3f}  / IS Sharpe "
          f"{sp.is_sharpe:6.3f}  → WFE {sp.wfe:7.1%}  {_gate(sp.wfe)}  "
          f"(split {sp.split_ts.date()}, OOS trades {sp.oos_trades})")
    agree = (wf.wfe_pooled > 0.5) == (sp.wfe > 0.5)
    print(f"  → 兩法結論{'一致' if agree else '★打架(警訊,要查)'}")
    print("  per-window 診斷 (is_sh / oos_sh / oos_trades):")
    for w in wf.windows:
        print(f"      {w.oos_start.date()}→{w.oos_end.date()}: "
              f"IS {w.is_sharpe:5.2f}  OOS {w.oos_sharpe:6.2f}  trades {w.oos_trades:3d}")


def _median(xs):
    if not xs:
        return 0
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def main() -> None:
    kl = _kline()
    report("S1 Donchian BTC+ETH", dict(kl), _donchian_factory)

    s2 = dict(kl)
    s2["BTC_funding_8h"] = CsvFundingLoader(FIX / "btc_funding_8h.csv", "BTC_funding_8h").fetch()
    s2["ETH_funding_8h"] = CsvFundingLoader(FIX / "eth_funding_8h.csv", "ETH_funding_8h").fetch()
    report("S2 FundingSkew BTC+ETH", s2, _funding_factory)

    s3 = dict(kl)
    s3["vix_daily"] = CsvLoader(FIX / "vix_daily.csv", "vix_daily").fetch()
    report("S3 Donchian + MacroOverlay(VIX)", s3, _overlay_factory)


if __name__ == "__main__":
    main()
