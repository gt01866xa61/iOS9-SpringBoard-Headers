"""V2-T 真資料三策略 demo runner(rejections baseline / 引擎精修對照用)。

ref: v2t_prereqs.md 前置 2。把 decisions.md 記的三場真資料回測固化成
可重跑腳本,讓「引擎精修前 vs 後」rejections 變化能 apples-to-apples 比。

跑法(在 crypto_dca_bot/ 底下):
    python3 -m v2.tools.real_demo

三場(配置對齊既有 real-data sanity test,擴成 BTC+ETH):
- S1 Donchian(entry=20/exit=10)BTC+ETH,default 執行政策(dead_band=0.02 / cooling=5m)
- S2 FundingSkew(lookback=21)BTC+ETH,default 執行政策(對齊 decisions 記錄的 demo)
- S3 Donchian BTC+ETH + MacroOverlay(VIX)

baseline(前置 2 動工前,2026-06-13):
  S1  958 rejections / 111 fills / equity $137,324
  S2  11206 rejections / 379 fills / equity $48,672
  S3  968 rejections / 177 fills / equity $197,854
  (三場 rejections 全為 insufficient_cash)

第 1 件(組合視角 sizing)後:
  S1  0 rejections / 111 fills / $137,324(純清帳,零真實交易變動)
  S2  0 rejections / 396 fills / $59,693(P&L 校正,曝險反而更緊)
  S3  0 rejections / 187 fills / $225,679

注:equity = cash + Σ 未平倉部位市值。早期版本誤用 field 名當 price key,
未平倉部位被估 0、只印現金,導致 S2 顯示 $3,041(其實只是 cash) — 已修。

輸出每場:fills(買/賣)/ rejections(分原因)/ 最終淨值。
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from ..data import BacktestReplayDriver, CsvFundingLoader, CsvLoader
from ..engine import Backtest
from ..interfaces import NoOpParams, NoOpPortfolioStrategy
from ..strategies import (
    DonchianBreakout,
    DonchianParams,
    FundingSkew,
    FundingSkewParams,
    MacroOverlay,
    MacroOverlayParams,
)

FIXTURES = Path(__file__).resolve().parents[1] / "data" / "fixtures"
PRICE_MAP = {"BTC": "BTC_kline_1d", "ETH": "ETH_kline_1d"}


def _btc_eth_kline() -> dict[str, list]:
    return {
        "BTC_kline_1d": CsvLoader(FIXTURES / "btc_usd_1d.csv", "BTC_kline_1d").fetch(),
        "ETH_kline_1d": CsvLoader(FIXTURES / "eth_usd_1d.csv", "ETH_kline_1d").fetch(),
    }


def _report(name: str, res) -> dict:
    buys = sum(1 for f in res.fills if f.delta_qty > 0)
    sells = sum(1 for f in res.fills if f.delta_qty < 0)
    reasons = Counter(r.reason for r in res.rejections)
    # mark price keyed by SYMBOL (PRICE_MAP maps symbol → kline field);
    # 不能直接用 _LAST_SERIES 的 field 名當 key,否則 positions(symbol 名)
    # 對不上 → 未平倉部位被估成 0、equity 變成「只算現金」。
    last_px: dict[str, float] = {}
    for sym, field_name in PRICE_MAP.items():
        s = _LAST_SERIES.get(field_name)
        if s and hasattr(s[-1][1], "close"):
            last_px[sym] = s[-1][1].close
    equity = res.final_state.equity(last_px) if last_px else float("nan")
    invested = equity - res.final_state.cash
    print(f"\n=== {name} ===")
    print(f"  fired_events : {res.fired_events}")
    print(f"  pipeline_runs: {res.pipeline_runs}")
    print(f"  fills        : {len(res.fills)}  ({buys} buy / {sells} sell)")
    print(f"  rejections   : {len(res.rejections)}")
    for reason, n in reasons.most_common():
        print(f"      - {reason:20s}: {n}")
    print(f"  final equity : ${equity:,.0f}  (cash ${res.final_state.cash:,.0f} "
          f"+ positions ${invested:,.0f})")
    return {
        "name": name,
        "fills": len(res.fills),
        "buys": buys,
        "sells": sells,
        "rejections": len(res.rejections),
        "reasons": dict(reasons),
        "equity": equity,
    }


# module-level so _report can mark-to-market with the same series it ran on
_LAST_SERIES: dict[str, list] = {}


def run_s1() -> dict:
    global _LAST_SERIES
    series = _btc_eth_kline()
    _LAST_SERIES = series
    bt = Backtest(initial_cash=10000, price_map=PRICE_MAP)
    bt.add_symbol(DonchianBreakout(DonchianParams(symbol="BTC", entry=20, exit=10)))
    bt.add_symbol(DonchianBreakout(DonchianParams(symbol="ETH", entry=20, exit=10)))
    bt.add_portfolio(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC", "ETH"])))
    return _report("S1 Donchian BTC+ETH (default exec policy)", bt.run(BacktestReplayDriver(series)))


def run_s2() -> dict:
    global _LAST_SERIES
    series = _btc_eth_kline()
    series["BTC_funding_8h"] = CsvFundingLoader(FIXTURES / "btc_funding_8h.csv", "BTC_funding_8h").fetch()
    series["ETH_funding_8h"] = CsvFundingLoader(FIXTURES / "eth_funding_8h.csv", "ETH_funding_8h").fetch()
    _LAST_SERIES = series
    bt = Backtest(initial_cash=10000, price_map=PRICE_MAP)
    bt.add_symbol(FundingSkew(FundingSkewParams(symbol="BTC", lookback_periods=21)))
    bt.add_symbol(FundingSkew(FundingSkewParams(symbol="ETH", lookback_periods=21)))
    bt.add_portfolio(NoOpPortfolioStrategy(NoOpParams(symbols=["BTC", "ETH"])))
    return _report("S2 FundingSkew BTC+ETH (default exec policy)", bt.run(BacktestReplayDriver(series)))


def run_s3() -> dict:
    global _LAST_SERIES
    series = _btc_eth_kline()
    series["vix_daily"] = CsvLoader(FIXTURES / "vix_daily.csv", "vix_daily").fetch()
    _LAST_SERIES = series
    bt = Backtest(initial_cash=10000, price_map=PRICE_MAP)
    bt.add_symbol(DonchianBreakout(DonchianParams(symbol="BTC", entry=20, exit=10)))
    bt.add_symbol(DonchianBreakout(DonchianParams(symbol="ETH", entry=20, exit=10)))
    bt.add_portfolio(MacroOverlay(MacroOverlayParams(symbols=["BTC", "ETH"])))
    return _report("S3 Donchian BTC+ETH + MacroOverlay(VIX)", bt.run(BacktestReplayDriver(series)))


def main() -> None:
    run_s1()
    run_s2()
    run_s3()


if __name__ == "__main__":
    main()
