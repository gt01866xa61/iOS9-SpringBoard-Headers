# CLAUDE.md

## 1. 先讀 V2 roadmap + research context

開始任何工作前，請按順序讀：

1. `crypto_dca_bot/research/v2_roadmap.md` — V2 builder roadmap（**目前主動工作區**）
2. `crypto_dca_bot/research/CLAUDE.md` — V2 研究脈絡 + multi-CLI（Claude / Codex / Gemini）分工
3. `crypto_dca_bot/research/decisions.md` — 重大決策紀錄（倒序，最新在最上）
4. `crypto_dca_bot/README.md` — V1 Phase 1-4 歷史紀錄（**V1 已結案**，V2 沿用模組參考用）

本檔只補上述沒涵蓋的協作規則，不重複內容。

## 2. 工作流程鐵律

- 每完成一個邏輯單元（一個函式、一個 bug fix、一個小功能）立刻 `git add` + `git commit` + `git push`，**不累積**。
- 每次 commit 後在 `PROGRESS.md` 追加一行：`YYYY-MM-DD HH:MM (Asia/Taipei) | <commit hash 前 7 碼> | <一句話描述>`，新項目放表格頂端（倒序）。
- **例外**：`PROGRESS.md` 維護類 commit（backfill、排版修正等 meta-commit）不自記，避免無限遞迴。只有純功能 commit 才記。
- 每個 session 開始先跑 `git status` + `git log --oneline -10` 對齊狀態。
- 每個 session 結束前確認所有改動已 push。
- 遇到 API 400 / context error / 任何異常**立刻停手回報**，不要硬跑或 retry。

## 3. 當前 phase

- **V1（Phase 4 DCA bot）2026-05-08 結案，已停止運行**（Stage 4 trial 全綠驗證完成，commit `346108e`；不重啟、不當儲蓄機）
- **V2 builder pivot 2026-05-09**：framework 從 V2-Q/R/D（問題驅動）改成 V2-A/B/S/T/E/D（builder 蓋房子模式，詳見 `crypto_dca_bot/research/v2_roadmap.md`）
- **目前位置:V2-A 架構設計第一輪**（**不寫 code**，先把平台骨架討論清楚）

## 4. Repo 借殼提示

本 repo 名為 `iOS9-SpringBoard-Headers`，根目錄的 `System/` 與 `usr/` 是 iOS dyld cache dump，**與 bot 無關，不要動**。所有 bot code 都在 `crypto_dca_bot/` 底下。

## 5. 溝通的 sense（2026-05-04 被訓斥後加，違者 = 浪費使用者的錢）

這節記錄反覆犯的低級錯誤，未來 session 啟動就讀，不要再犯同一招。

- **使用者已 bracket 掉的範圍不要偷渡回答案裡**。例：他明確說「#1 是 runtime（只能等時間到）、#2 是 deterministic（可預先驗）」之後問「#2 能不能保證」，答案就只談 #2。硬加「但 runtime 也可能 fail」是把 #1 的東西塞回 #2 — 暗示「我覺得你沒想到」，既不尊重也浪費他的 token。**先解析使用者怎麼分類，再進去那個格子裡作答**。
- **timing-critical pre-condition 從工作清單拆出來單獨 surface，不要混在同層 step 裡**。「23:55 host 上的舊 bot 先殺」（P0 阻塞前置）跟「寫 validate() 函式」（P3 work）差三個數量級，並列成 plan 第 0/1/2/3 步等於沒提示。Pre-condition 用「**先做這個，否則後面整包白做 + deadline 是 X**」的格式單獨寫。
- **不要用罐頭 hedge cover ass**。「但 X 也可能 Y」這類保守話如果使用者已知 = 浪費 token + 損他對我的信任。要嘛 raise 他**真的不知**的點，要嘛閉嘴直接答。Disclaimer 機器不值錢。
- **使用者付錢用我，期待 partner 等級的 sense**。partner 會抓 frame、會主動 surface 真風險、不會把對方當白癡重複講已知事項。每次想加 caveat 之前停 1 秒問自己：「他知道嗎？」知道就刪。
