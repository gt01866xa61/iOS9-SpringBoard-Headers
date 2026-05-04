# PROGRESS

Commit 歷史。**新的放最上面（倒序）**，每次 commit 後在表頭下方插入新項目。
時間統一 Asia/Taipei (UTC+8)。Hash 取前 7 碼。

| 時間 (Asia/Taipei) | Hash | 描述 |
| --- | --- | --- |
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
