# V2 Strategy Research — Claude Context

> **⚠️ 目前進度(2026-06-13):V2-A/B/S 完成。下一步 V2-T,但卡在硬前置 —
> 開 V2-T 前必讀 `v2t_prereqs.md`(正典真資料接入 + 752 引擎精修)。**

## What this folder is

V2 量化交易平台研究工作區。**V1(Phase 4 DCA bot)2026-05-08 結案,Stage 4 後停止運行**(不繼續跑當儲蓄機 — 使用者已有手動長期部位,V1 重疊無意義)。

V2 = 多市場 / 多策略 / 動態切換 24h 量化交易平台(Builder mode 蓋房子模式)。完整 roadmap 見 `v2_roadmap.md`,2026-05-09 重大 pivot 決策見 `decisions.md`。

## V2 工作框架(取代舊的 V2-Q 三題)

V2 分 6 階段,依序執行:

| Phase | 做的事 |
|---|---|
| V2-A | Architecture(架構)— 畫設計圖,平台骨架 / 模組接口 / 資料流 |
| V2-B | Backtest 引擎 — 多策略可插拔回測 |
| V2-S1..N | Strategy 1..N codify(策略實作)|
| V2-T1..N | Strategy 驗證(walk-forward + paper trading)|
| V2-E | Ensemble 動態策略選擇 |
| V2-D | Deploy(真錢小額 → 漸進放大)|

每階段獨立 deliverable(可交付產出)。**V2-T 階段必跑 M1-M7 validation standards**(stress-test / walk-forward / lock / paper trade / paper-vs-backtest / risk-based sizing / 上線後退役監控,見 `v2_roadmap.md`)。

## 我(Claude)的角色

- 計畫制定、structured analysis(結構化分析)、code 實作
- 跟用戶對話磨策略想法
- 把對話結論結構化寫進 `strategies/<name>.md`
- **不**找漏洞(那是 Codex 的事,見 `role_codex.md`)
- **不**找學術背景(那是 Gemini 的事,見 `role_gemini.md`)

## 用戶角色

- 提供策略直覺(想法、市場觀察、風險偏好)
- 拍板每個策略 go / no-go
- 在 Codex / Gemini / Claude 之間 route(路由)任務

## V2 邊界(預設不變)

- 不充值,先用現有 ~13 USDT 緩衝(夠到 V2-D step 4 tiny live 50-100 USDT)
- 不上 leverage(槓桿)/ 衍生品
- V1 code 保留當技術資產(`exchange_api.py` / `trader.py` / `notifier.py` / `circuit_breaker.py` / `heartbeat.py` / `price_recorder.py` / `chaos_test.py` 將被 V2 沿用),但 V1 **不再運行**,**也不會被 wrap 成 V2 策略模組**
- 第一階段嚴格鎖 BTC/ETH,後續才擴 Gold / Oil / NDX

## 重要 reference

- **V2-A 平台架構總圖: `v2a/architecture.md`(★ 單一 source of truth,V2-B 開工只讀這份就夠)**
- V2 builder roadmap: `v2_roadmap.md`(長期指引)
- 重大決定 log: `decisions.md`(倒序)
- V2-A round-by-round ledger: `v2a/round1.md` / `round2.md` / `round3.md`(細節論證 / 否決理由 / options 對照)
- V2-A 白話詞彙表: `v2a/glossary.md`(non-quant 友善,Ctrl+F 查詞)
- V1 progress: `../README.md`(Phase 1-4 設計,歷史參考)
- V1 commit history: `../../PROGRESS.md`
- 工作流規則: `../../CLAUDE.md`(全局協作守則)
- 過時的 V2-Q 三題框架: `archive/v2_questions.md`(歷史 snapshot,僅供參考)
