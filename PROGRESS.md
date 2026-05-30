# PROGRESS

Commit 歷史。**新的放最上面（倒序）**，每次 commit 後在表頭下方插入新項目。
時間統一 Asia/Taipei (UTC+8)。Hash 取前 7 碼。

| 時間 (Asia/Taipei) | Hash | 描述 |
| --- | --- | --- |
| 2026-05-26 | 761166a | docs(v2a): #3C cross-strategy stale override 拍板 Option C — #3 議題收官(PortfolioStrategy 因 stale 缺席時 framework 強制壓 cap 到保守上限+大聲告警+on_stale() 可 override)+ 前提地基不投票守門員瞎掉一定 Telegram 告警 silent divergence 觸發點最不能 silent + 機制(framework 偵測→不 dispatch→告警→對受影響 symbol 主動壓 cap 進入 #3D min 合併池跟其他正常守門員取最狠→最終 cap)+ 降多少策略事先 on_stale() override(策略自知語意)否則 fallback_cap_default 兜底 V2-B 校準沿用 default+override 老路 + 否決 A 沿用上次=binary latch / B 凍結加倉只「不升」不「降」/ D 整輪凍結資料常因崩盤才斷 hold 穿越最危險 / E 全平倉 whipsaw 致命 + 串接前三塊 #3C 是 #3 收官 converge 點(#3B 後算留滿倉洞 / #3D min 合併同向 / #2C2-B Sub-Q1 on_stale 複用 / #2C2-B Sub-Q3 default+override 沿用 / #3A NoOp 天然豁免 / #2C2 watch #1 silent divergence 落地 ✓)+ Watch V2-B 實測校準 fallback_cap_default 預設值 / 守門員可設更短 max_staleness / whipsaw 量化 M1 五段崩盤實測呼應 stale-aware 規格 + Round 2 #3 PortfolioStrategy 議題正式收官 #3A/B/C/D 全拍完一條線拉通哲學 framework 強迫使用者表態+看完所有意圖才拍板+多守門員取最狠+守門員瞎了主動降=整套 fail-safe 結構 + Glossary 追加 4 新詞 silent divergence 沉默歧異守門員不見了比喻 / fail-safe 電梯感應器壞比喻 / whipsaw 虛驚下車又上車比喻 / fallback_cap_default 守門員瞎時兜底折扣 |
| 2026-05-26 | cd1123b | docs(v2a): #3D 補 watch — overlay 訊號紀律(使用者補,留 V2-S 各策略 codify 時驗:PortfolioStrategy 的 cap 訊號必須連續可衰退 continuous & decaying、禁 binary latch 二元卡死風險觸發後 cap 鎖低點不放 / 事件型風險地緣衝突黑天鵝淡化後 cap 必須自動鬆回否則取最狠 min 會被過時高風險訊號綁架持續誤殺正常倉位 / 這是 overlay 訊號層紀律不是 #3D 合併規則問題 min 本身正確但會忠實放大餵進來的卡死訊號 / 歸屬 V2-S 各策略 codify 逐個驗 decay 機制 framework 不懂訊號語意管不到)+ Glossary 追加 1 新詞 連續可衰退訊號 vs binary latch 守門員攔人後要會看情況放行不能僵住比喻 |
| 2026-05-26 | bbc60bc | docs(v2a): #3D 多 PortfolioStrategy 疊合拍板 Option A 取最狠(多個 PortfolioStrategy 對同一 symbol 的 cap multiplier 取最小值最保守者勝 final_cap=min(0.5,0.7,...)=0.5)+ 四大支柱(① 守門員天職任一可單獨踩剎車 / ② 可究責最終 cap 指得出哪個策略設的 / ③ 單調不爆炸多加守門員只會更保守 / ④ 不重複計算相關風險加密崩盤各 overlay 常反應同一事件 min 免疫)+ 否決 B 連乘(相關訊號重複計算+多策略指數爆縮+究責困難)/ C 平均(稀釋尖叫把快逃 0.0 跟沒事 1.0 混成逃一半風控致命傷直接否決)/ D 加權(誰定權重 framework 又假設業務+要調參過度設計)/ E 取最寬鬆(反風控否決)+ NoOp 場景 min(0.5,1.0)=0.5 假人不干擾真守門員全 NoOp min(1.0)=1.0 不限制 + 加權/優先序留未來 hook 循 default+override 老路 + #3C 接力取最狠規則直接餵進 fail-safe 降風險與 min 同向 + Glossary 追加 1 新詞 cap 合併規則-取最狠守門員比喻 |
| 2026-05-26 | ea78c38 | docs(v2a): #3B Dispatch 順序拍板 Option A(SymbolStrategy 先算 target → PortfolioStrategy 看完所有 target 後算 cap → framework 相乘 / 一次 dispatch 單向資訊流 / Symbol 算時可從 snapshot 讀 macro 欄位 VIX/funding/regime 不盲跑 / Portfolio 後算有全局視角看得到所有 Symbol 意圖後整體協調)+ 否決 B Portfolio 先 / E 並行(失去全局視角只剩 macro 而 Symbol 自己讀得到)/ C 兩階段(心智複雜收益微小)/ D iterative(不收斂直接否決)+ 對其他事影響 #3C 必處理 dispatch 前預判 Portfolio stale → fail-safe 強制降風險(#3B surface 給 #3C)/ #3D 多 PortfolioStrategy 在階段 2 並排跑拍 cap 怎麼合併 + Watch Symbol 不能依賴上次 fire 的 Portfolio cap 作提示 + Glossary 追加 2 新詞 dispatch 派工出餐鈴比喻 / dispatch 順序誰先算 |
| 2026-05-26 | df73833 | docs(v2a): #3A always-on 鎖拍板 Option E(Framework 硬鎖至少 1 個 PortfolioStrategy + 提供 NoOpPortfolioStrategy 讓使用者明確 register / 0 個 → refuse to start / 不想做風控必須明確 register NoOp 假人永遠 cap=1.0 all symbols / NoOp 在 log 透明顯示 debug 時一眼看到設計如此 / 否決 D framework 內建 baseline 因不該假設業務邏輯「100% 曝險合理」是誰定義違反 framework-不假設-業務 哲學)+ 對其他事影響 #3C 領班 stale override 在 NoOp 模式無領班 → #3C 必處理 NoOp 場景(已標 watch)+ CLAUDE.md section 6 新增永久條目「拍板必附白話 walk-through 段」(2026-05-26 使用者明確要求跨 session 永久執行:架構討論段可用術語但拍板後單獨給「這個拍板實際是什麼意思」段純人話用比喻不堆英文符號表格,第一次出現專有名詞用比喻或日常情境不只是括號直譯)+ Glossary 追加 4 新詞(cap multiplier 上限放大器 / NoOpPortfolioStrategy NoOp 假人領班 / always-on 鎖便利商店至少有店員的比喻 / Default+override pattern+framework 不假設業務 設計哲學) |
| 2026-05-24 | 91ef1bd | docs(v2a): #2C2 全段 review pass 8 checkpoint 全綠通過 + 4 watch item 分流落地(① Silent divergence — PortfolioStrategy 領班 cross-strategy stale override 風控被跳時強制全策略降風險 防「風控失能其他策略繼續滿倉」沉默危險 → 整合進 Round 2 #3 sub-Q / ② Stale 權責切 PortfolioStrategy vs Risk Engine → 進 backlog #4 Round 3 必撞 / ③ Counter 鋸齒 reset 評估改滑動視窗 N-of-M / ④ N 值校準不收斂)+ M1 規格補註寫入 glossary stale-aware(LUNA/FTX API timeout 大量觸發 stale framework 對 stale 反應本身要被 M1 涵蓋)+ 開 #3 PortfolioStrategy 議題 frame(Round 1 carry over,4 sub-Q:#3A always-on 鎖 / #3B Dispatch 順序 / #3C Cross-strategy stale override #2C2 watch #1 整合 / #3D 多 PortfolioStrategy 疊合,建議順序 #3A → #3B → #3D → #3C,這輪只 frame 不拍守一輪一 axis 原則) |
| 2026-05-24 | 2db3b88 | docs(v2a): Round 2 #2C2-B Sub-Q3 拍板 — max_staleness + N 值宣告與預設 = Option Γ+Ε(3 維度同解:① 雙層 — framework data source registry per-source 給 max_staleness_default / alert_N_default + 策略 required_data() 可 override / ② 預設 per-data-source 寫在 registry 跟 cadence 一起設 / ③ 多策略訂同 field 衝突 per-strategy 判定 snapshot 共享但 stale 判定各用自己門檻 不取最嚴避免寬鬆策略被嚴格策略綁架)+ alert counter 改 per-(strategy, field) 累積 + 跟 #2C1 / Sub-Q1 / Sub-Q2 同 Default+override pattern + glossary 追加 3 新詞(max_staleness / Data source registry / Default+override pattern)+ Round 2 #2C2-B 全套 Sub-Q1/2/3 拍完 |
| 2026-05-24 | 8c5de98 | docs(v2a): Round 2 #2C2-B Sub-Q2 拍板 — 連續 stale 升 alert = Option C(per-field counter 連續 N 次 stale → alert 走 V1 notifier、counter 在 field fresh 時 reset、N 值 per-field 由 required_data() 宣告 V2-B 校準、把時長語義 pre-baked 進「次數 × cadence」與 #2C1 防呆 #1 共用 pattern)+ 配套防呆(M5 paper-vs-backtest 對照納入 stale 次數比對,類比 #2C1 防呆 #3,零額外成本)+ glossary 追加 2 新詞(Alert vs Log vs Hook 三機制區別 / Counter+門檻 pattern 通用 primitive) |
| 2026-05-24 | 22f14ff | docs(v2a): Round 2 #2C2-A + #2C2-B Sub-Q1 拍板 — #2C2-A stale 行為 = Option 3(framework 偵測 stale → 跳過 on_bar + 寫 event log,策略無感,跟 #2C1 同精神鎖 backtest/paper/live 三模式同一條 path)+ #2C2-B Sub-Q1 策略 stale 通知鉤子 = Option C 可選 on_stale(base class default no-op、策略可 override,多數策略無感、風控/fallback/ensemble 有 hook 點)+ on_stale 歸「可選」lifecycle method(與 reset/is_ready 同級)+ glossary 追加 2 新詞(on_stale / Hook)+ 未解伏筆:dispatch 內順序 + stale_fields payload schema 留 P1 規格章節 |
| 2026-05-22 | a750fb8 | docs(v2a): Round 2 #2C1 拍板 — 暖機期協議 = γ 混合派 is_ready() (framework 提供 buffer-based default + 策略可 override) + 3 條硬約束防呆 (強制 log + 連續 N 次 false 告警 / is_ready 只能看歷史 buffer 鎖三模式時序一致 / M5 對照納入 is_ready 觸發次數比對) + glossary 追加 3 詞 |
| 2026-05-22 | 95e9568 | docs(v2a): Round 2 #2B 拍板 — 觸發頻率粒度 = event-driven + last known value 對齊 + 統一 event log(掛 initialize instrumentation hook;不採每最細粒度 bar 同步觸發 — 多時鐘策略合理觸發頻率衝突;snapshot 各 field 帶 timestamp 給策略查 staleness;event log 為 backtest/paper/live 三模式 single source of truth)+ glossary 追加 6 新詞 |
| 2026-05-22 | 23ab83f | docs(v2a): Round 2 #2A 拍板 — Lifecycle method 4 必 + 1 可選(__init__/required_data/initialize/on_bar 必 + reset 可選;initialize 鎖必要即使 no-op 也明寫 → contract 明確 + framework 可插 instrumentation;實際策略池 0 boilerplate 代價)+ glossary 擴 lifecycle 條目 + 5 新詞 |
| 2026-05-21 | 089100e | docs(v2a): Round 2 Part 1 拍板 — 策略池 #2 選 funding rate skew(D)、calendar(C)退為 PortfolioStrategy 子訊號候選(D vs C 6 維對照:訊號 / 5-param / 資料 / M1-M7 / 失效 / vs-trend correlation 推導;C 因 N=2 樣本違反 M2/M4/M5 前提卡關)+ glossary 追加 8 詞 |
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
