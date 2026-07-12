# PROGRESS

Commit 歷史。**新的放最上面（倒序）**，每次 commit 後在表頭下方插入新項目。
時間統一 Asia/Taipei (UTC+8)。Hash 取前 7 碼。

| 時間 (Asia/Taipei) | Hash | 描述 |
| --- | --- | --- |
| 2026-07-12 20:00 | 6ca622a | feat：新 cluster「導線架/封測供應鏈」（EP678）——順德YoY基本面線＋四雄籃資金面線＋銅參考列；四雄代號逐檔查證（長科=6548.TWO）；master reason 泛化 |
| 2026-07-11 21:05 | d46c359 | docs：新增 HANDOFF.md——多 agent（Codex 等）交接用固定 prompt；Codex push master 前先保守確認過使用者 |
| 2026-07-11 20:30 | 772fd68 | feat(web)：標的名稱掛抓價代號「名稱 (代號)」——列列可溯源；空格＝手機斷行點，390px 實測無溢出 |
| 2026-07-11 15:10 | 5daf99c | fix(web)：過期橫幅時段感知——平日盤中 90 分、夜間/週末 26 小時才亮，週末休市不再假警報 |
| 2026-07-09 22:55 | 9e11a9f | ci：cron 重啟票加密至每 10 分一張（78 張/日）——7/9 下午 GitHub runner 斷供數小時，連 pacer 都拿不到機器；票越密復原後自癒越快 |
| 2026-07-09 19:35 | b5a69ce | ci：pacer 每棒自派下一棒——7/9 三班 build 佇列 15 分鐘拿不到 runner 被平台取消（零 step）致鏈死，存活不再依賴 build 有跑起來 |
| 2026-07-07 12:55 | e09d678 | ci：接力環閉合——證實 GITHUB_TOKEN 補發班跑完不觸發 workflow_run（3/3 斷鏈），改 build↔pacer 雙向明確 dispatch |
| 2026-07-06 16:45 | b91fa66 | ci：新增 pacer 接力節拍器（cron 改離峰後仍連三班丟包→build 完成後自補下一班，三道閘防失控） |
| 2026-07-06 15:11 | fc8e2de | ci：Pages 部署重試三段式 30s/60s 退避（run #17 兩發連撞 "try again later"） |
| 2026-07-06 15:05 | c7bdc4c | 時效審查：yfinance threads 鎖掉檔修復＋補抓、表格列「資料至」標示（休市凍結自我說明）、籃子缺料揭露 |
| 2026-07-06 15:04 | 488f530 | ci：cron 分鐘改離峰 17,47——GitHub 尖峰丟包（7/6 上午 12 班只發 1 班＝stale 根因） |
| 2026-07-04 17:55 | 77b306e | ci：artifact 帶 run_attempt 唯一命名，修 Re-run 同名相撞（count is 2） |
| 2026-07-04 17:40 | 2e9f551 | ci：Pages 部署加自動重試（防 GitHub "try again later" 暫時性失敗）；PR#4 已合併上線 |
| 2026-07-04 13:05 | b307045 | ci：修燈史持久化（stash 髒工作區＋rebase 重試）；bot 首筆燈史 commit 已落地 |
| 2026-07-04 12:58 | a12adea | 再審修正：sparkline 圖內文字爆版改圖下註記、孤兒日期隱藏；燈帶方向實測確認正確 |
| 2026-07-04 12:45 | 6a26d61 | 邏輯審查修正：原物料語義矛盾、命名去偏見、主數值加量綱、儀表刻度、燈帶30格 |
| 2026-07-04 12:35 | f5fa850 | 三層式改版：掃視窄卡＋展開說明＋30日燈帶＋今日變化置頂＋燈史 CI 持久化 |
| 2026-07-04 00:30 | e4f15e6 | UX 驗收回饋：sparkline 加 50MA 虛線、月更標「資料至」、表格加點/線讀法 |
| 2026-07-04 00:10 | 4021bd0 | 🚀 正式上線：Pages 部署成功（run#4 全綠、真實資料 0 errors），gt01866xa61.github.io/iOS9-SpringBoard-Headers |
| 2026-07-03 22:50 | d008ef2 | fix：威剛 3260.TW→3260.TWO（首次雲端實測抓到）；CI 改 dev 分支 push 觸發部署 |
| 2026-07-02 23:20 | 4f9f7aa | gooaye_signals：track/shape/order 升格必填、卡片直接顯示三個必答問題＋三燈對照 |
| 2026-07-02 00:22 | 87086c6 | gooaye_signals：Phase 4 測試改為跑完還原 index.html，不弄髒工作區 |
| 2026-07-02 00:17 | 0c12b81 | gooaye_signals Phase 5：GitHub Actions 排程 build + Pages 部署 + 上線教學 |
| 2026-07-02 00:15 | 0f83d84 | gooaye_signals Phase 4：深色手機優先前端 + 泛型 widget 渲染 + 內嵌 fallback + 測試 |
| 2026-07-02 00:08 | e115d7e | gooaye_signals Phase 3：實接 yfinance/FinMind + build.py 全流程 + 失敗隔離 + 測試 |
| 2026-07-02 00:03 | 880e3d7 | gooaye_signals Phase 2：運算引擎 + DayCache + demo 模式 + 六訊號 compute + 測試 |
| 2026-07-01 23:53 | 90b720d | gooaye_signals Phase 1：訊號契約 + 自動探索 registry + 3 種子 spec + 測試 |
| 2026-05-02 22:17 | b28a871 | Phase 4 polish: align rotation with plan D3 + heartbeat cross-day guard |
| 2026-05-02 13:37 | ff4c2dc | Phase 4: main loop with circuit breaker, heartbeat, dry-run, atomic state |
| 2026-05-02 08:32 | 078118a | Phase 3 chaos: back up + restore real daily_state.json in [11/11] |
| 2026-05-02 08:28 | e646683 | Phase 3 hotfix 2: drop ZoneInfo for fixed UTC+8 (Windows tzdata-free) |
| 2026-05-02 08:24 | 37643d7 | Phase 3 hotfix: load_markets() before client.market(), [11/11] amount |
| 2026-05-02 07:18 | dbc7d3c | Phase 3: trader.py with multi-layer safety + atomic daily cap |
| 2026-05-02 06:42 | d961d16 | Phase 2 chaos fixes: isolate [5/7] from env keys, [7/7] expects AuthenticationError |
| 2026-05-01 19:00 | 2b85bcb | Phase 2: Binance market data + balance via ccxt (read-only) |
| 2026-05-01 18:04 | 653cd30 | Phase 1 hardening: pin logger to Asia/Taipei, add chaos_test.py |
| 2026-05-01 17:32 | fcb6976 | Phase 1: drop parse_mode=HTML, log Telegram description, redact token |
| 2026-04-24 06:03 | af626eb | Phase 1: bootstrap crypto_dca_bot with logger and Telegram notifier |
| 2015-11-23 12:19 | a11be52 | Dump Entire dyld-shared-cache (pre-bot, repo 借殼前的歷史殘留) |
| 2015-09-23 16:36 | 7b62aab | iOS9 SpringBoard Headers (pre-bot, repo 借殼前的歷史殘留) |
