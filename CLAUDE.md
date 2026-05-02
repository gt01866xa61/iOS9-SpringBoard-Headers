# CLAUDE.md

## 1. 先讀 README

開始任何工作前，請先讀 `crypto_dca_bot/README.md` 取得完整專案脈絡與 Phase 進度。本檔只補 README 沒涵蓋的協作規則，不重複內容。

## 2. 工作流程鐵律

- 每完成一個邏輯單元（一個函式、一個 bug fix、一個小功能）立刻 `git add` + `git commit` + `git push`，**不累積**。
- 每次 commit 後在 `PROGRESS.md` 追加一行：`YYYY-MM-DD HH:MM (Asia/Taipei) | <commit hash 前 7 碼> | <一句話描述>`，新項目放表格頂端（倒序）。
- 每個 session 開始先跑 `git status` + `git log --oneline -10` 對齊狀態。
- 每個 session 結束前確認所有改動已 push。
- 遇到 API 400 / context error / 任何異常**立刻停手回報**，不要硬跑或 retry。

## 3. 當前 live 驗證進度

- [ ] Stage 3 跨日驗證：Day1 23:55 BTC 5.5 USDT + Day2 00:05 ETH 5.5 USDT
- [ ] Stage 4 三天 production trial：每天 12:00 一筆，總計 ~16.5 USDT
- 預計 5/3 23:25 開工

## 4. Repo 借殼提示

本 repo 名為 `iOS9-SpringBoard-Headers`，根目錄的 `System/` 與 `usr/` 是 iOS dyld cache dump，**與 bot 無關，不要動**。所有 bot code 都在 `crypto_dca_bot/` 底下。
