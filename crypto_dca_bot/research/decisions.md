# V2 Decisions Log(決策日誌)

> 重要決策記錄,每個決定一段:日期 + 決定 + 理由。
> 這是 V2 旅程的 ledger(分類帳)— 寫下來才不會忘記當時為什麼這樣決定。
> **新的放最上面**(倒序)。

---

## 2026-06-06 — 法律邊界宣言:寫死「只管自己的錢」最高位階紅線(backlog #3)

獨立於主線架構的治理決策,但**位階凌駕所有策略 / 架構 option** — 任何後續決定都不得抵觸。完整聲明見 `research/legal_boundary.md`(commit `5e08a3d`)。

**紅線(寫死,不得繞過)**:本平台只用**使用者本人**的資金、為**使用者本人**下單,不替任何第三人服務、不碰任何第三人的錢。

**理由 — 一跨出「自己理財」就變成「對外經營金融服務」**:
- 踩線情境:代操 / 全權委託、收費投資建議、賣訊號、對外募資集資、分潤抽成、經常性對外買賣建議
- 在台灣會撞《證券投資信託及顧問法》第 4 條(證券投資顧問 = 為取得報酬提供分析意見 / 推介建議,須先經主管機關金管會核准許可,無牌即違法經營)
- **不限第 4 條**:代操 / 對外募資這類「碰別人的錢」的行為風險更高,可能另觸同法其他條文,甚至**銀行法非法吸金**(刑責重得多)。BTC/ETH 現貨在台一般不算有價證券,但保守起見維持紅線、不靠這點當逃生口

**規矩**:跨過上面任一條、擴大平台用途之前,**必須先諮詢執業律師 / 合規顧問,確認合法且取得必要許可才能動手**。本宣言為內部範圍提醒,非法律意見,實際適用以主管機關與律師解釋為準。

---

## 2026-05-26 — V2-A Round 2 全段收官:Strategy interface + PortfolioStrategy 完整契約鎖死

Round 2 全 13 個議程 / 子題拍板完成,Strategy interface 從骨架(Round 1)推進到**完整 framework 契約**。完整 ledger 見 `v2a/round2.md` 末段「Round 2 全段收官」總覽表。

**拍板總清單(13 條,本檔只列骨幹)**:
- #1 起步策略池 #2 → Funding rate skew(2026-05-21,已 prepend)
- #2A Lifecycle 4 必要 + 1 可選 / #2B Event-driven + LKV + 統一 event log / #2C1 暖機 is_ready buffer-based + 防呆 / #2C2-A Framework 偵測 stale 跳過策略無感 / #2C2-B Sub-Q1 on_stale 可選 hook / Sub-Q2 per-field counter + V1 notifier alert / Sub-Q3 max_staleness/N 寫 framework registry default + 策略可 override + per-strategy 判定 / #2D 錯誤路徑 = 復用「策略缺席」+ crash counter + #3A 湧現停機 / #3A always-on 鎖 + NoOpPortfolioStrategy 明確 register / #3B Dispatch 順序 Symbol → Portfolio → 相乘 / #3D 多 PortfolioStrategy min 取最狠 / #3C cross-strategy stale override fail-safe 丟進 min 池(非二次施加)

**Round 2 浮現的 6 條設計哲學(沿用至 Round 3)**:
1. Framework 不假設業務語意 — 否決所有「替使用者預設業務」option
2. Default + override 老路 — framework 給合理 default,策略可特化
3. Counter + 門檻 pattern — 連續 N 次累積觸發升級,框架統一 primitive,#2C1 / Sub-Q2 / #2D 共用
4. 單調往最保守倒 — fail-safe 只能往緊永不放寬(#3D min / #3C 丟 min 池而非二次施加)
5. 強迫表態 > 默默裸奔(#3A NoOp 明確 register / #2C1 ack 防呆)
6. 湧現 > 顯式條文(#2D crash + #3A 鎖 → 自動停機;比寫死規矩穩)

**Round 2 review pass 撞點處理**:
- #3C × #3D 合併位置(fail-safe 值丟進 min 池 vs 二次施加)→ 拍丟 min 池,保住單調性、保住明眼守門員警報、實作零新層
- silent divergence(風控失能其他策略繼續滿倉)→ 整套 #3 + #2C2 落地完成

**Round 3 議程(carry over)**:
- R3-① Risk Engine 模組邊界(吸收 backlog #4 + portfolio-gross 約束 + M6 sizing 落地)
- R3-② 資料流 / event bus / snapshot 組裝(Round 1 + Round 2 #2B 留)
- R3-③ 執行層 over-trading 冷卻機制(Round 1 review pass 留)
- R3-④ V1 模組沿用整合點(#2D 開頭,完整定 hook)

**V2-B 必驗清單(實測題)**:N 值校準 / counter 鋸齒評估 / whipsaw 量化 / trend × funding correlation / M1 stale-aware 受測

**V2-S 各策略 codify 紀律**:overlay 訊號連續可衰退禁 binary latch(使用者補)

Round 2 完整 ledger 見 `v2a/round2.md`,Round 3 議程 frame 見 `v2a/round3.md`。新增專有名詞已追加 `v2a/glossary.md`(共 Round 2 期間新增 20+ 條,以「故事 / 比喻」風格寫,使用者非 quant 背景可快速 reference)。

---

## 2026-05-21 — V2-A Round 2 (Part 1):策略池 #2 拍 Funding rate skew

Round 2 第一題(策略池 #2 替代 mean-reversion)拍板。

**選 D:Funding rate skew(永續資金費率偏度)** 為起步策略池 #2。
**C(BTC halving cycle / calendar)退為 PortfolioStrategy 子訊號候選**,V2-E ensemble 階段再評估。

**拍板理由 — 驗證流程可通,不是賺率高:**
- D vs C 6 維對照(訊號 / 參數 / 資料 / M1-M7 / 失效 / correlation 推導,見 `v2a/round2.md`)
- C 結構性問題:高品質 BTC/ETH 資料只覆蓋 2 次 halving(2020-05 / 2024-04),N=2 違反 M2 walk-forward + M4 paper 60 日 + M5 paper-vs-backtest 的「足夠樣本」前提 — 不是調參能解決
- D 資料 Binance Futures `/fapi/v1/fundingRate` 2019-09 起,M1 五段崩盤全覆蓋,M1-M7 結構性可驗

**核心設計**:funding 持續高(永續多頭擁擠) → 縮 spot 多單;funding 持續低/負 → 滿倉。5 個 params(`lookback_periods` / `low_threshold` / `high_threshold` / `dead_band` / `symbol_list`),邏輯一句話。**不交易永續、只把 funding 當訊號**,符合 V2 邊界(只玩 spot)。

**對 trend correlation 預估**:**-0.1 ~ +0.2**(邏輯反向 — trend 賺動能持續、D 在動能過熱時減倉)。**Caveat**:邏輯推導非實測,若 EMA crossover lag 跟 funding 升溫時間軸接近,實測可能 0.3+。**M1 五段崩盤是 reality check 關鍵**,V2-B 跑出結果再校準。

**起步策略池(round 2 後狀態):**

| # | Style | 角色 |
|---|---|---|
| 1 | Trend-following | SymbolStrategy |
| 2 | **Funding rate skew** | SymbolStrategy |
| 3 | Macro overlay | PortfolioStrategy |

Round 2 完整 ledger 見 `v2a/round2.md`。下一題:P1 細節(lifecycle methods / param schema / data spec)。

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

**Round 1 三軸正式定案:** 雙 interface / output 形狀 / class+snapshot+strict schema 三軸經白話 review pass(用買菜阿姨聽得懂的話逐軸 walk-through、使用者 re-validate)全數通過,Round 1 結束,進 Round 2。

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
