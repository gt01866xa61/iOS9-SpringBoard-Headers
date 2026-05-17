# PROGRESS

Commit 歷史。**新的放最上面（倒序）**，每次 commit 後在表頭下方插入新項目。
時間統一 Asia/Taipei (UTC+8)。Hash 取前 7 碼。

| 時間 (Asia/Taipei) | Hash | 描述 |
| --- | --- | --- |
| 2026-05-17 12:12 | 771be42 | docs(v2a): Round 1 三軸 review pass 全數通過、正式定案(雙 interface / output 形狀 / class+snapshot+strict schema 逐軸白話 walk-through、使用者 re-validate)|
| 2026-05-17 09:20 | b958963 | docs(v2a): Validation Standards 擴 M6/M7(M6 position sizing 必須 risk-based / M7 策略退役機制 — 對照 6 共識 gap 分析升級)+ 新增 domain_landscape.md 領域全景(6 共識 + 3 爭議 + 簡單派定調:策略數 anchor 在 3)|
| 2026-05-12 06:42 | c15bb75 | docs: V2-A glossary + CLAUDE.md section 6(表達規則跨 session 永久執行 — 新術語白話 inline 解釋 / 每輪日常話 summary / 一輪一 axis / glossary 維護 / skill check 停推機制;V2-A 進度從 3-6 週 → 5-9 週)|
| 2026-05-12 06:18 | ac1598a | docs(v2a): V2-A round 1 ledger — Strategy interface 三軸鎖板(axis 6 雙 interface SymbolStrategy+PortfolioStrategy / axis 4 long-only target [0,1] + per-symbol cap multiplier / axis 1 class+snapshot+strict dataclass schema)+ mean-reversion 換掉(候選 round 2 詳論)|
| 2026-05-12 04:59 | d7be050 | docs(readme): add V1-closed + V2-active status banner(避免新讀者誤以為 V1 還在跑)|
| 2026-05-12 04:59 | b20e380 | docs(claude): align root CLAUDE.md with V2 builder pivot(section 1 主讀切到 v2_roadmap,section 3 stale Stage 3/4 checkboxes → V2-A 當前 phase + 不寫 code 規則)|
| 2026-05-12 04:44 | 28afd9a | docs(research): add v2_roadmap.md — V2 builder long-term guide(專案定義 + 起步策略池 + 6 階段拆分 + M1-M5 validation + correlation-aware + V1-V2 關係) |
| 2026-05-12 04:43 | 6f8da72 | docs(research): archive v2_questions.md(V2-Q 三題框架被 builder pivot 取代,Q1 Pionex 盤點保留為 archive/ 歷史 snapshot) |
| 2026-05-12 04:43 | d2930e8 | docs(research): align data_sources.md with V2-A/B phases(V2-R 框架引用 → V2-A/B 架構 + 回測引擎) |
| 2026-05-12 04:42 | 720d458 | docs(research): rewrite CLAUDE.md for V2 builder framework(V2-Q 三題 → V2-A/B/S/T/E/D 蓋房子,移除儲蓄機 / baseline 描述) |
| 2026-05-12 04:42 | 45ba8f7 | docs(research): add 2026-05-09 V2 builder pivot decision entry(框架重寫 + V1 停止運行 + M1-M5 validation standards 寫死 + 5-step 預算 cascade) |
| 2026-05-09 20:20 | 2e400c9 | research(v2-q): fill Q1 — Pionex 罐頭可行性盤點(8 條 V2 存在空間) |
| 2026-05-09 18:41 | e2269fe | docs(research): scaffold V2 strategy research workspace(W0 落地,multi-CLI 工作流 + 三題答題本 + 策略 template) |
| 2026-05-08 23:50 | 346108e | docs(readme): Phase 4 → Validated,V1 結案(Stage 4 三日 trial 全綠 + 跨日 reset 5 次驗證 + failures 0/5) |
| 2026-05-04 22:13 | 6e45c71 | feat(main): add --deep-check flag (verifies _get_min_notional for each SYMBOLS_ROTATION symbol pre-flight) |
| 2026-05-04 09:31 | c40a389 | docs(claude): add section 5 — communication sense lessons (frame-respect, pre-condition surfacing, no cover-ass hedges) |
| 2026-05-04 07:09 | 907103c | fix(heartbeat): None sentinel for total_value (drops bogus +2 USDT inflation on partial fail) |
| 2026-05-04 07:07 | 40a7810 | docs(readme): align SYMBOLS_ROTATION order with config.py b28a871 (ETH first) |
| 2026-05-04 07:07 | deefeae | docs(readme): align MIN_SINGLE_BUY_USDT 10.0 → 5.0 with 3e45fe4 hotfix |
| 2026-05-04 07:07 | c763447 | fix(trader): RuntimeError instead of silent DAILY_CAP_USDT=50 fallback when config.py missing |
| 2026-05-04 07:06 | c379d77 | feat(config): add validate() + main() call for fail-fast on misconfig |
| 2026-05-04 00:02 | 3e45fe4 | fix(trader): lower MIN_SINGLE_BUY_USDT 10.0 → 5.0 to match Phase 4 DCA_AMOUNT_USDT=5.5 |
| 2026-05-03 11:51 | 777765f | docs: widen Stage 3 D2 buffer 00:05 → 00:15 (CLAUDE.md + README) |
| 2026-05-03 11:51 | 289d27f | fix(chaos): drop hardcoded chat_id fallback in [1/15] |
| 2026-05-03 07:08 | bb34de4 | docs(readme): expand Stage 3 pre-flight to 11-item checklist (host env + app sanity + chaos re-verify) |
| 2026-05-03 07:08 | a667aad | feat(main): --check now also queries USDT/BTC/ETH free balances |
| 2026-05-03 07:01 | 701eed4 | docs(readme): add Stage 3 pre-flight runbook + single-trade failure decision tree |
| 2026-05-03 07:01 | f2a19cd | feat(main): add --check pre-flight flag (no Telegram, no schedule) |
| 2026-05-03 06:48 | bf82dd1 | docs(claude): add meta-commit exemption to PROGRESS.md logging rule |
| 2026-05-02 23:15 | 9f35807 | docs: add lean CLAUDE.md and PROGRESS.md for session continuity |
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
