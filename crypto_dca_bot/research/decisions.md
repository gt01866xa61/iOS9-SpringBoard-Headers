# V2 Decisions Log(決策日誌)

> 重要決策記錄,每個決定一段:日期 + 決定 + 理由。
> 這是 V2 旅程的 ledger(分類帳)— 寫下來才不會忘記當時為什麼這樣決定。
> **新的放最上面**(倒序)。

---

## 2026-05-09 — V2 Builder Pivot(框架重寫)

V1 結案後使用者揭露真實意圖:**不是 problem-solver 模式**(沒明確痛點),而是 **builder 模式**(想創造大型量化平台)。原本的 V2-Q/R/D(問題驅動)框架不適用,**整套重寫成 V2-A/B/S/T/E/D**(蓋房子模式)。

關鍵決定:

- **V1 停止運行**,不當儲蓄機(使用者已有手動長期部位,V1 重疊無意義)
- V1 code 保留當技術資產,V2 沿用 `exchange_api.py` / `trader.py` / `notifier.py` / `circuit_breaker.py` / `heartbeat.py` / `price_recorder.py` / `chaos_test.py`
- V1 **不會被 wrap 成 V2 策略模組**(原 plan 該段刪除)
- V2 框架:V2-A(架構)→ V2-B(回測引擎)→ V2-S1..N(策略 codify)→ V2-T1..N(策略驗證)→ V2-E(集成)→ V2-D(部署)
- 起步策略池:trend-following + mean-reversion + macro overlay(3 個業界 style,V2-A 可調)
- Validation Standards 寫死 M1-M5:
  - M1:V2-B 內建 5 段歷史崩盤 stress-test(COVID 2020-03 / China crackdown 2021-05 / LUNA 2022-05 / FTX 2022-11 / 日圓 carry unwind 2024-08-05)
  - M2:walk-forward 規格 — IS 30 個月 / OOS 3 個月 / retrain 每 3 個月 / WFE > 50% / OOS 每視窗 ≥ 30 trades
  - M3:backtest 結果 lock — 自動 timestamp + commit hash,策略邏輯改 = 新編號(避免 retrofit)
  - M4:paper trading 最少 60 個交易日(不是自然日)
  - M5:paper vs backtest 並排 — Sharpe 差 ≤ 30%、Fill rate 差 ≤ 10%,超過 = reject
- 預算策略:simulation-first 5-step cascade(backtest → walk-forward → paper → tiny live 50-100 USDT → scale up)
- 第一階段嚴格鎖 BTC/ETH,Gold / Oil / NDX 是後續

V2-Q 框架已過時:`v2_questions.md` 已 archive 到 `archive/`。完整 builder roadmap 見 `v2_roadmap.md`。

下一步:V2-A 架構設計(我跟使用者來回討論平台骨架,**不寫 code**,產出架構文件)。

---

## 2026-05-08 — V1 結案,V2-Q 啟動

V1 Stage 4 trial 全綠(3 trades + 5 次跨日 reset 驗證 + failures 0/5)。
Phase 4 status → Validated(commit `346108e`)。
進入 V2-Q 階段(用戶思考三題,Claude + Codex + Gemini 平行協助)。

決定:
- 不充值,V1 不重寫
- V2 邊界保持(無 leverage / 衍生品)
- 用 multi-CLI 工作流(Claude / Codex / Gemini),角色分工見各 role_*.md

下一個 milestone:V2-D(48h 後評估三策略 go/no-go)
