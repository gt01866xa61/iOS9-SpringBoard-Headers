# HANDOFF.md

多 agent（Claude Code、Codex、或任何其他 coding agent）交接「股癌訊號燈」專案用的固定
開場說明。任何新 session／新工具接手前，先讀這份，不用每次重新口述背景。

這份文件本身也是活的——交接規則有變動時直接改這份檔案，不用另外通知。

---

## 給接手 agent 的開場指示（可整段複製當 system/first prompt）

```
你正在接手一個進行中的專案：「股癌訊號燈」，repo 是
gt01866xa61/iOS9-SpringBoard-Headers，所有程式碼在 gooaye_signals/ 底下
（repo 根目錄的 System/、usr/ 是無關的 iOS dyld cache dump，不要動）。

開工前必讀（依序）：
1. gooaye_signals/README.md —— 專案全貌、Phase 進度、每個訊號的資料契約
2. CLAUDE.md（repo 根目錄）—— 協作規則
3. PROGRESS.md —— 逐 commit 完整歷史，最新的在最上面，看最上面 15-20 行
   就知道現在做到哪、上一個 agent 交接時的即時狀態

核心原則（凌駕一切，永遠遵守）：
- 第一性原理：先砍到最簡，再一點點把真正需要的部分補回來，不做沒意義的事
- 數據鐵律：所有呈現的數據必須同時滿足「真實×可規格×可溯源」三者，任何
  無法同時滿足的內容寧可不顯示，這是整個專案最核心的要求
- 分工鐵律：使用者口述訊號、agent 實作——交付到「訊號忠實呈現」為止；
  不提供投資判斷、不附下單建議或投資面免責叮嚀

工作流程鐵律：
- 開工先跑 git status + git log --oneline -10 對齊狀態，
  git pull --rebase origin master（CI bot 會自動 commit 燈號歷史，
  push 前後都要 rebase 一次避免衝突）
- 每完成一個邏輯單元（一個函式、一個 bug fix、一個小功能）立刻
  git add + commit，不累積
- 每次 commit 後在 PROGRESS.md 最上面補一行：
  YYYY-MM-DD HH:MM (Asia/Taipei) | commit hash 前 7 碼 | 一句話描述
- 改動 gooaye_signals/ 底下程式碼後，push 前先跑完 4 個 phase 測試
  （python tests/test_phase1_specs.py ~ test_phase4_frontend.py）
  + GOOAYE_DEMO=1 python build.py 確認能跑，再視改動範圍做視覺檢查
- 遇到 API 錯誤／context 爆炸／任何異常，立刻停手回報，不要硬跑或 retry

授權範圍（目前保守設定，見下方「push 權限」一節）：commit 可以自己做，
但 push 到 master 前，先跟使用者確認過。這跟本 repo 對 Claude Code 的既有
授權（全自動上線、直接 push）不同——是刻意給新加入的 agent 的較保守預設，
使用者確認過穩定之後可能會放寬。

即時狀態提醒：這幾天在修一套 GitHub Actions 接力機制（pacer.yml +
signals.yml），因為 GitHub 的 schedule cron 與 hosted runner 都不可靠
（會丟包、會佇列逾時被平台取消），做了一個 build↔pacer 雙向明確
workflow_dispatch 的自持環。細節都記在 PROGRESS.md 最上面幾行。接手第一件
事：去 repo 的 Actions 頁面確認 pacer 與 build-and-deploy-signals 兩個
workflow 最近有沒有正常在跑（沒有的話這是要優先處理的活問題，不是新任務）。

你的第一步：跑 git status + git log --oneline -15，讀完 PROGRESS.md 最上面
15-20 行，如果使用者訊息裡已經講了要做什麼就直接做；沒有的話跟使用者確認
接下來要做什麼。
```

---

## push 權限（目前狀態）

- **Claude Code（本 session 起）**：使用者已明確授權全自動上線——不需要每次改動都先問過使用者，
  直接 push 到 master（CI/CD 會自動測試、部署）。原話：「不用 改成全自動上線吧 基本上我手動按也是
  什麼都不會看 就直接按」。
- **Codex（或其他新加入的 agent）**：**先保守**——commit 可以自己做，但 **push 到 master 前要先跟
  使用者確認**。這是使用者刻意設的初始設定（怕多個 agent 同時全自動推 master 互相踩），不是能力
  限制。使用者觀察一段時間覺得穩定後，可能會把這條放寬成跟 Claude Code 一樣的全自動權限——放寬的話
  直接改這份檔案的這一段即可，不用整份重寫。

## 為什麼需要這份文件

- 這個 repo 用 5 小時 rate limit 的 Claude Code 在維護；額度用完的空檔想讓 Codex 接手繼續做，
  避免每次交接都要重新口述一大段背景。
- `CLAUDE.md`／`README.md`／`PROGRESS.md` 是純文字，任何 agent 都讀得懂，不是 Claude 專屬格式——
  真正需要額外講的只有「push 權限目前對不同 agent 不同」這種跨 agent 才會出現的協調問題，
  這正是本檔案存在的原因。
