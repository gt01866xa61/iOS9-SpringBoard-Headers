# V2 — 多策略量化交易平台(code 工作區)

> **架構依據:`../research/v2a/architecture.md`(single source of truth,改 code 前先讀它)**
> V2-B 開發計畫 + 進度在本檔。工作節奏:Claude 寫、使用者驗收 milestone;碰到 §8 要拍的決定停下來 options。

## V2-B Milestones

| # | 內容 | 狀態 |
|---|---|---|
| **B1** | interface 層:策略 base class + lifecycle + NoOp + schema | **✅ DONE 2026-05-26**(19 tests)|
| B2 | 資料層:DATA_SOURCES registry + event bus + backtest replay driver + snapshot(LKV + no-lookahead)| **✅ DONE 2026-05-26**(17 tests)|
| B3 | dispatch core:event → fire → 收集 output + 策略缺席統一模型 + counter | **✅ DONE 2026-05-26**(21 tests)|
| B4 | 風控管線:min 合併 + #3C fallback + Risk Engine + 算量站 + 執行政策層 | **✅ DONE 2026-05-26**(29 tests)|
| B5 | executor:sim 成交器(滑點/手續費模型 = Gap 4 拍板)| **✅ DONE 2026-05-26**(17 tests)|
| B6 | observability:統一 event log + alert sink | **✅ DONE 2026-05-26**(30 tests)|
| B7 | 整合驗收:dummy 策略全管線 + M1 五段崩盤 stress test | **✅ DONE 2026-05-26**(11 tests)|

**V2-B 全段完成** — 7 milestones / 144 tests 全綠。Backtest 引擎可端到端跑、M3 fingerprint 可重現、M1 stale-aware 合成壓測通過。

## V2-S Milestones(策略實作)

| # | 策略 | 狀態 |
|---|---|---|
| **S1** | Donchian breakout(海龜經典,日線,entry=20/exit=10,long-only,BTC+ETH)| **✅ DONE 2026-06-13**(15 tests)— codify + 真資料接入(CsvLoader/CcxtLoader 雙軌)+ 真資料 sanity(BTC/ETH 2019-2024)|
| **S2** | Funding rate skew(Round 2 #1,5 params 簡單派)| **✅ DONE 2026-06-13**(22 tests,1 skipped 等真資料 fixture)— codify + 合成 sanity + CcxtFundingLoader/CsvFundingLoader 雙軌 |
| **S3** | Macro overlay(VIX/DXY,第一個真守門員 PortfolioStrategy)| **✅ DONE 2026-06-13**(15 tests)— codify + 真 VIX 資料(datahub OHLC)sanity + cap 套到 S1/S2 下單驗證;DXY 留 optional hook |

**V2-S 起步策略池 3 個全 codify 完成**(S1 Donchian / S2 Funding skew / S3 Macro overlay)。真資料:BTC/ETH(CoinMetrics close-only)+ VIX(datahub OHLC)已接;funding + DXY 等本機 ccxt 帶回。M1-M7 正式驗證(walk-forward/paper)= V2-T。

> 真策略在 `v2/strategies/`(donchian.py 等);dummy(SmaCross/ThresholdOverlay)留作 reference + engine smoke。
> M1-M7 真驗證(walk-forward / paper)= V2-T,V2-S 不碰。

## 目錄

```
v2/
├── interfaces/        B1:策略 interface + base class + types
├── data/              B2:event bus + driver + registry
├── engine/            B3-B4:dispatch + 風控管線
├── execution/         B5:executor + sim 成交器
├── observability/     B6:event log + alert sink
└── tests/             pytest(全程伴隨)
```

## 環境

- Python 3.11+
- deps 見 `requirements.txt`(V1 四件套之上加 pydantic / pytest / pandas+numpy)
- 跑測試:`cd crypto_dca_bot && python -m pytest v2/tests/ -v`

## V1 資產沿用(落點表,ref architecture.md §6.4)

V1 flat 檔(`../*.py`)**不搬不改**,V2 需要時 import。資料側接 B2(`exchange_api` 取數 / `price_recorder` 歷史),下單側接 B5(`trader`),`chaos_test` 接 B7,其餘(notifier channel / circuit_breaker 實盤 / heartbeat)V2-D 才接。
