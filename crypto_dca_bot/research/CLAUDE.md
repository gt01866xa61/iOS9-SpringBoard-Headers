# V2 Strategy Research — Claude Context

## What this folder is

V2 策略研究工作區。V1(Phase 4 DCA bot)2026-05-08 結案 — Stage 4 trial 全綠驗證完成。現在進入 V2-Q 階段(策略候選評估),決定是否要做 V2(有 edge 的策略)還是讓 V1 繼續當被動儲蓄機。

## V2 啟動三題(必答完才進 V2-R)

1. **Pionex 罐頭機器人能不能做你想的策略?** 能 → V2 取消,沒必要重造輪子。
2. **列 3 個具體策略構想**(進出場條件、頻率、預期 win rate)。
3. **每個策略的 edge 假設**(為什麼還在?為什麼別人沒吃光?)

不能答這 3 題 = V2 別開,V1 跑著當儲蓄機,完全可以接受。

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

## 工作節奏(W0 + V2-Q phase)

- Day 1-2:策略構想 + Codex/Gemini 第一輪反饋
- Day 3:整體評估,V2-R 是否啟動
- 每個重大決定寫進 `decisions.md`

## V2 邊界(預設不變)

- 不充值,先用現有 ~13 USDT 緩衝
- 不上 leverage(槓桿)/ 衍生品
- 不重寫 V1,V1 繼續當 baseline(基準)

## 重要 reference

- V1 progress: `../README.md`(Phase 1-4 設計)
- V1 commit history: `../../PROGRESS.md`
- 工作流規則: `../../CLAUDE.md`(全局協作守則)
