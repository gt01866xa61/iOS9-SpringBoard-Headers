# V2 Decisions Log(決策日誌)

> 重要決策記錄,每個決定一段:日期 + 決定 + 理由。
> 這是 V2 旅程的 ledger(分類帳)— 寫下來才不會忘記當時為什麼這樣決定。
> **新的放最上面**(倒序)。

---

## 2026-05-17 — V2-A Round 1 review pass:Validation Standards 擴 M6/M7 + 簡單派定調

Round 1 review pass(用白話 walk-through 三軸讓使用者 re-validate)過程中浮現的結構性決策:

**Validation Standards 從 M1-M5 擴成 M1-M7**(寫進 `v2_roadmap.md`):
- **M6:Position sizing 必須 risk-based** — 對應核心共識「風險管理 > 預測」。部位大小不得用固定比例,預設 volatility targeting;V2-B/T 階段須證明 risk-based 版 max drawdown 優於 naive 版。
- **M7:策略退役機制** — 對應核心共識「edge 會衰退」。M1-M6 是上線前關卡,M7 是上線後持續監控:滾動 Sharpe 連續 2 窗低於 backtest 50%、或 live 回撤超 backtest 1.5 倍 → 退役。
- 來源:對照量化交易 6 條核心共識做 gap 分析,Gap 1(sizing)/ Gap 2(退役)被判定跟 M1-M5 同級重要,升級進 roadmap。M6/M7 門檻數字為初版,V2-D 前校準。

**簡單 vs 複雜爭議定調:簡單派**(使用者委託 Claude 專業判斷):
- V2 實際策略數目標 anchor 在 **3 個**,roadmap 的「3-7」中 7 當理論上限不當目標
- 「簡單」不只指策略數量,每個策略內部也要簡單:參數理想 < 5 個、邏輯一句話講得清
- 理由:複雜派玩法需規模才成立(文藝復興等級資源),個人玩家頭號死因是複雜度爆炸而非分散不足

完整領域脈絡(6 共識 + 3 爭議 + 雙方論據)見 `v2a/domain_landscape.md`。Round 1 衍生事項(over-trading 執行層政策、Gap 3/4)見 `v2a/round1.md`。

---

## 2026-05-12 — V2-A Round 1(Strategy Interface 規範)

V2-A 第一輪鎖死 Strategy interface frame-level 三件事:

- **Axis 6 Instrument 模型**:雙 interface — `SymbolStrategy`(per-symbol / pair 部位意圖)+ `PortfolioStrategy`(portfolio-level risk overlay)。Per bar 執行順序鎖死 SymbolStrategy → PortfolioStrategy。
- **Axis 4 Output 形狀**:SymbolStrategy = target % long-only `[0, 1]` per symbol(% of strategy's allocated capital);PortfolioStrategy = per-symbol cap multiplier `[0, 1]`。
- **Axis 1 抽象層次**:Class + 外部可 snapshot state + 嚴格 dataclass / pydantic state schema。params(策略邏輯參數)跟 state(run-time 內部變數)分離。

V2 邊界 implication:SymbolStrategy output domain `[0, 1]` spot-only long-only 鎖死 → **Mean-reversion(BTC/ETH ratio)自動降級成 rebalance flavor**(ratio 偏高 → 減 BTC 配重加 ETH,非真 spread trade)。Round 1 拍板**起步策略池中 Mean-reversion 換掉**,候選名單 round 2 詳論(volatility regime / on-chain / calendar / funding skew / cross-exchange premium 等)。Trend-following 跟 Macro overlay 不受影響。

Round 1 完整 ledger 見 `v2a/round1.md`(P0 拍板 + interface 骨架預覽 + 執行管線 + 範圍外 P1 子題 + open questions)。

下一輪 V2-A Round 2 重點:策略池候選 finalize、P1 子題(lifecycle methods / param schema / data spec)、PortfolioStrategy always-on 鎖 + 疊合演算法。

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
