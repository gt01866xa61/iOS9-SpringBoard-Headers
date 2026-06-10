# V2 — 多策略量化交易平台(code 工作區)

> **架構依據:`../research/v2a/architecture.md`(single source of truth,改 code 前先讀它)**
> V2-B 開發計畫 + 進度在本檔。工作節奏:Claude 寫、使用者驗收 milestone;碰到 §8 要拍的決定停下來 options。

## V2-B Milestones

| # | 內容 | 狀態 |
|---|---|---|
| **B1** | interface 層:策略 base class + lifecycle + NoOp + schema | **✅ DONE 2026-05-26**(19 tests)|
| B2 | 資料層:DATA_SOURCES registry + event bus + backtest replay driver + snapshot(LKV + no-lookahead)| **✅ DONE 2026-05-26**(17 tests)|
| B3 | dispatch core:event → fire → 收集 output + 策略缺席統一模型 + counter | **NEXT** |
| B4 | 風控管線:min 合併 + #3C fallback + Risk Engine + 算量站 + 執行政策層 | — |
| B5 | executor:sim 成交器(滑點/手續費模型 = Gap 4 拍板)| — |
| B6 | observability:統一 event log + alert sink | — |
| B7 | 整合驗收:dummy 策略全管線 + M1 五段崩盤 stress test | — |

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
