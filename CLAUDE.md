# CLAUDE.md

## 1. 先讀 README

開始任何工作前，請先讀 `crypto_dca_bot/README.md` 取得完整專案脈絡與 Phase 進度。本檔只補 README 沒涵蓋的協作規則，不重複內容。

## 2. 工作流程鐵律

- 每完成一個邏輯單元（一個函式、一個 bug fix、一個小功能）立刻 `git add` + `git commit` + `git push`，**不累積**。
- 每次 commit 後在 `PROGRESS.md` 追加一行：`YYYY-MM-DD HH:MM (Asia/Taipei) | <commit hash 前 7 碼> | <一句話描述>`，新項目放表格頂端（倒序）。
- **例外**：`PROGRESS.md` 維護類 commit（backfill、排版修正等 meta-commit）不自記，避免無限遞迴。只有純功能 commit 才記。
- 每個 session 開始先跑 `git status` + `git log --oneline -10` 對齊狀態。
- 每個 session 結束前確認所有改動已 push。
- 遇到 API 400 / context error / 任何異常**立刻停手回報**，不要硬跑或 retry。

## 3. 當前 live 驗證進度

- [ ] Stage 3 跨日驗證：Day1 23:55 BTC 5.5 USDT + Day2 00:15 ETH 5.5 USDT
- [ ] Stage 4 三天 production trial：每天 12:00 一筆，總計 ~16.5 USDT
- 預計 5/3 23:25 開工

## 4. Repo 借殼提示

本 repo 名為 `iOS9-SpringBoard-Headers`，根目錄的 `System/` 與 `usr/` 是 iOS dyld cache dump，**與 bot 無關，不要動**。所有 bot code 都在 `crypto_dca_bot/` 底下。

## 5. 溝通的 sense（2026-05-04 被訓斥後加，違者 = 浪費使用者的錢）

這節記錄反覆犯的低級錯誤，未來 session 啟動就讀，不要再犯同一招。

- **使用者已 bracket 掉的範圍不要偷渡回答案裡**。例：他明確說「#1 是 runtime（只能等時間到）、#2 是 deterministic（可預先驗）」之後問「#2 能不能保證」，答案就只談 #2。硬加「但 runtime 也可能 fail」是把 #1 的東西塞回 #2 — 暗示「我覺得你沒想到」，既不尊重也浪費他的 token。**先解析使用者怎麼分類，再進去那個格子裡作答**。
- **timing-critical pre-condition 從工作清單拆出來單獨 surface，不要混在同層 step 裡**。「23:55 host 上的舊 bot 先殺」（P0 阻塞前置）跟「寫 validate() 函式」（P3 work）差三個數量級，並列成 plan 第 0/1/2/3 步等於沒提示。Pre-condition 用「**先做這個，否則後面整包白做 + deadline 是 X**」的格式單獨寫。
- **不要用罐頭 hedge cover ass**。「但 X 也可能 Y」這類保守話如果使用者已知 = 浪費 token + 損他對我的信任。要嘛 raise 他**真的不知**的點，要嘛閉嘴直接答。Disclaimer 機器不值錢。
- **使用者付錢用我，期待 partner 等級的 sense**。partner 會抓 frame、會主動 surface 真風險、不會把對方當白癡重複講已知事項。每次想加 caveat 之前停 1 秒問自己：「他知道嗎？」知道就刪。
