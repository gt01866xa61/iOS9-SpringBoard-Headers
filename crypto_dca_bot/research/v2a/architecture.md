# V2-A 平台架構總圖(Architecture)

> **單一 source of truth**。V2-A 三輪(Round 1 interface / Round 2 contract / Round 3 平台底盤)拍板的收斂成品。
> **V2-B 開工只讀這份就夠** — 不必爬 `round1/2/3.md`。細節論證 / 否決理由 / options 對照仍在各 round 檔。
> 風格:每節含「**白話 summary**」(non-quant 友善)。每個拍板帶「**是什麼 + 為什麼 + ref**」。
> 狀態:2026-05-26 收斂。V2-A 階段(畫設計圖、不寫 code)完成。
>
> **閱讀順序建議**:§0 邊界 → §2 pipeline 全圖(先看一眼資料怎麼流)→ §1 元件清單 → §3-6 各元件細節 → §7 哲學 → §8 carry over。

---

## § 0. 平台目標 + 邊界

**V2 是什麼**:多市場 / 多策略 / 動態切換的 24h 量化交易平台(builder 模式蓋房子)。V2-A 畫的是這棟房子的**設計圖**。

**V2 不是什麼**(邊界,預設不變,ref CLAUDE.md):
- **只玩 spot(現貨)**,不上 leverage(槓桿)/ 衍生品
- **只做 long(做多)**,不做 short(SymbolStrategy output domain 鎖 `[0,1]`)
- **起步嚴格鎖 BTC + ETH**,後續才擴 Gold / Oil / NDX
- **不充值**,先用現有 ~13 USDT 緩衝(夠到 V2-D tiny live 50-100 USDT)
- **V1 不再運行**,但 V1 code 為技術資產沿用(見 §6 落點表)

**起步策略池**(Round 2 後狀態,實際 codify 在 V2-S):
| # | Style | 角色 |
|---|---|---|
| 1 | Trend-following | SymbolStrategy |
| 2 | Funding rate skew | SymbolStrategy(Round 2 #1 拍,替代 mean-reversion)|
| 3 | Macro overlay (VIX/DXY) | PortfolioStrategy |

簡單派定調(ref decisions 2026-05-17):**策略數 anchor 3 個**(roadmap「3-7」的 7 是理論上限不是目標)、**每策略內部也要簡單**(參數理想 < 5、邏輯一句話講得清)。

**白話 summary**:這是一個自動幫你在 BTC/ETH 上**只買不賣空、不開槓桿**的量化平台設計圖。先求穩、求簡單(3 個策略),別貪多貪複雜 —— 個人玩家頭號死因是複雜度爆炸。

---

## § 1. 完整元件清單(7 元件 + 3 政策)

### 策略層(使用者寫,你的業務邏輯)
| 元件 | 一句話 | ref |
|---|---|---|
| `SymbolStrategy` | 出價的人:看單一資產 → 出 target%(我想要多少 BTC)| Round 1 |
| `PortfolioStrategy` | 策略級守門員:看全局 → 出 per-symbol cap(每幣打幾折)。**可換 NoOp** | Round 1 + #3A |

### Framework 一級護欄(framework 寫死,使用者不可關不可換不可 NoOp)
| 元件 | 一句話 | ref |
|---|---|---|
| `Risk Engine` | 保全總管:組合級風控(總曝險上限 + 按波動調倉 + 資料終責)| R3-① |
| `framework 執行政策層` | 出菜檢查站:最終 order 紀律(dead-band + cooling + regime hook)| R3-③ |

### Framework 管線基建(framework 提供的水電)
| 元件 | 一句話 | ref |
|---|---|---|
| `算量站` | 純技術換算:target% → USDT → 數量(含 fee/slippage 估)| Round 1 + R3-① Block 2 |
| `event bus + 雙 driver` | 資料**輸入**:backtest replay driver / live driver,同一介面 | R3-② |
| `executor 抽象 + 雙 driver` | 訂單**輸出**:sim 成交器 / live trader,同一介面 | R3-④ |
| `統一 event log + alert sink` | 全程旁路記錄 + 告警匯流(Telegram)| #2B + R3-④ |
| `DATA_SOURCES registry` | 資料源登錄表(cadence / max_staleness / alert_N 的 default)| #2C2-B Sub-Q3 |

### Framework 政策(全鏈路強制,non-bypass)
| 政策 | 一句話 | ref |
|---|---|---|
| `always-on 鎖` | 啟動時強制 ≥1 PortfolioStrategy(不做也要明擺 NoOp)| #3A |
| `策略缺席統一模型` | 策略 stale / crash 一律當「這輪缺席」,不分原因統一處理 | #2C2 + #2D |
| `crash counter 永久停用` | 連續 crash N 次永久停用 + 告警(復用 counter+門檻)| #2D |

**白話 summary**:這棟樓有 **3 種角色**。**你寫的策略**(出價的人 + 守門員)是住戶,可以換、可以不做。**保全護欄**(保全總管 + 出菜檢查站)是 framework 寫死的安全底線,你**不能拆**。**水電基建 + 政策**是 framework 自動跑的後勤。

---

## § 2. per-fire pipeline 全圖

每次「市場有新資料」響鈴(event-driven,ref #2B),走這條生產線:

```
┌─────────────────────────────────────────────────────────────────┐
│ event bus(輸入 driver:backtest 歷史播放器 / live 即時接收器)  │  R3-②
│   → 組裝 snapshot(LKV 對齊 + no-lookahead 保證)                 │  #2B
└─────────────────────────────────────────────────────────────────┘
        ↓ snapshot(point-in-time,只含已發生資料)
┌─────────────────────────────────────────────────────────────────┐
│ SymbolStrategy_1..N . on_bar(snapshot) → target%                 │  Round 1
│   [策略訊號級節流在策略內:funding dead_band / #3D 連續可衰退]   │  R3-③
│   stale/crash → 這輪缺席跳過(策略缺席統一模型)                 │  #2C2/#2D
└─────────────────────────────────────────────────────────────────┘
        ↓ engine aggregate(per-strategy capital 加權)
   combined_target = {BTC: .., ETH: ..}
        ↓
┌─────────────────────────────────────────────────────────────────┐
│ PortfolioStrategy_1..M . on_bar → cap(per-symbol multiplier)    │  Round 1 / #3B
│   多個 → min 取最狠(最保守者勝)                                │  #3D
│   stale 缺席 → fallback_cap 丟進同一個 min 池(非二次施加)+告警 │  #3C
│   全 NoOp → 不觸發(使用者明確選不做策略級風控)                 │  #3A
└─────────────────────────────────────────────────────────────────┘
        ↓ final_target = combined_target × effective_cap(min 後)
┌─────────────────────────────────────────────────────────────────┐
│ ★ Risk Engine(framework 護欄,always-on,不可關)              │  R3-①
│   1. vol-targeting sizing(按波動調該佔幾%,M6 規格)            │
│   2. gross 總曝險上限(看 post-cap + 調倉後的真實水位)         │  Block 3
│   3. stale 最終把關(資料完整性終責)                           │
└─────────────────────────────────────────────────────────────────┘
        ↓ risk-adjusted target%
┌─────────────────────────────────────────────────────────────────┐
│ 算量站:target% → USDT → 數量(fee / slippage 估)               │  Round 1 / Block 2
└─────────────────────────────────────────────────────────────────┘
        ↓ desired order qty
┌─────────────────────────────────────────────────────────────────┐
│ ★ framework 執行政策層(護欄)                                   │  R3-③
│   dead-band:|current − desired| < threshold → 不送單            │
│   cooling:距上次成單 < 間隔 → 不送單                            │
│   regime hook(預留 V2-E)                                       │
└─────────────────────────────────────────────────────────────────┘
        ↓ 確定要送的 order
┌─────────────────────────────────────────────────────────────────┐
│ executor 抽象(輸出 driver:backtest sim 成交器 / live trader)  │  R3-④
└─────────────────────────────────────────────────────────────────┘
        ↓
   orders / fills

══ 全程旁路:統一 event log(每步寫一行)+ alert sink(critical → Telegram)══  #2B / R3-④
══ 全鏈路政策:always-on 鎖 / 策略缺席統一模型 / crash counter ══              #3A / #2C2 / #2D
```

**為什麼是這個順序**:
- **Symbol 先 → Portfolio 後**(#3B):守門員要「看完所有出價意圖才能整體協調」,先算就失去全局視角
- **Portfolio → Risk Engine**(R3-①):守門員管逐幣、Risk Engine 管整體,先逐幣再整體
- **Risk Engine → 算量站**(R3-① Block 2):Risk Engine 算「該佔幾%」(風險語意),算量站算「換成幾顆」(技術語意),分開不混
- **算量站 → 執行政策層**(R3-③):dead-band 要比對「真實下單量 vs 現有持倉」,所以在換算成量之後
- **執行政策層 → executor**(R3-④):確定要送才送

**白話 summary**:資料從上面進來,經過「出價的人 → 守門員打折 → 保全總管管總量 → 算量員換算 → 出菜檢查站過濾雜訊 → 真的送單」一條龍。每一站為什麼排這個位置都有理由:先個別後整體、先風險判斷後技術換算、先過濾再送。旁邊還有「記錄員」(event log)全程寫筆記、「保全政策」全鏈路盯著。

---

## § 3. 策略 interface 規格

### 3.1 雙 interface(ref Round 1)

| Interface | 職責 | output | 白話 |
|---|---|---|---|
| `SymbolStrategy` | per-symbol / pair 部位意圖 | `{symbol: target% ∈ [0,1]}` | 「我這個策略想要 BTC 60% / ETH 30%」 |
| `PortfolioStrategy` | portfolio-level 風控 overlay | `{symbol: cap_multiplier ∈ [0,1]}` | 「全局看,BTC 放行、ETH 砍到 30%」 |

**為什麼雙 interface**:per-symbol「想要多少」跟 portfolio「整體該不該收」是兩種不同職責,分開讓策略各自單純。最終 `下單目標 = target% × cap`。

**為什麼 long-only `[0,1]`**:V2 邊界鎖 spot/no-leverage → 真 short 不允許。後果:mean-reversion 自動降級成 rebalance flavor(ratio 偏高 → 減 BTC 加 ETH,非真 spread trade),Round 1 決定起步池換掉 mean-reversion。

### 3.2 抽象層次(ref Round 1)

- **Class + 有狀態**(策略自己記內部變數,如過去 20 根均值)
- **state 可外部 snapshot**:`get_state()` / `set_state()` — M3 backtest lock + walk-forward 重訓 boundary 序列化用
- **params vs state 分離**:params = 設定(initialize 注入、跑起來不變);state = 運行中變數(每 bar 可變)
- **嚴格 dataclass / pydantic schema**:framework 可驗證 / 序列化 / 版本控制

### 3.3 Lifecycle methods(ref #2A + #2C1 + #2C2-B Sub-Q1)

| Method | 必要? | 何時被叫 | 用途 |
|---|---|---|---|
| `__init__(params)` | **必** | 建立時,只一次 | 接 params + 合法性檢查 |
| `required_data() → DataSpec` | **必** | 註冊時,只一次 | 宣告需要什麼資料(粒度/長度/symbol)+ subscribe 哪些 event + 可 override `max_staleness`/`alert_N` |
| `initialize(snapshot)` | **必**(可空 `pass`) | 第一根 bar 前,只一次 | 暖機:prime indicators(load 歷史算到指標就緒)|
| `on_bar(snapshot) → output` | **必** | 每根 bar | 核心邏輯:看快照 → 回 target / cap |
| `is_ready() → bool` | 可選 | dispatch 前 | 暖機完了沒。default = framework buffer-based(buffer 滿 `min_history` 即 ready)|
| `on_stale(stale_fields)` | 可選 | 被 stale 跳過後 | 通知策略「這輪被跳、因這幾個 field 過時」。base = no-op |
| `reset()` | 可選 | walk-forward 切窗口前 | 清空狀態。default = framework 丟舊 instance 用同 params new |
| `get_state()` / `set_state()` | framework 提供 | M3 lock / WF boundary | 序列化 state |

**為什麼 initialize 鎖必要(即使 no-op)**:framework 可在前後插 instrumentation(計時/telemetry);contract 明確(暖機是一等公民,不藏 `__init__` 偷做);實際 3 條起步策略都要暖機。

**is_ready() 三條硬約束**(ref #2C1):
1. framework 強制 log 每次回傳;連續 N 次 false 告警
2. **只能看歷史 buffer**(暫存區),不能看當前最新值 → 鎖 backtest/paper/live 三模式同 timestamp 結果必相同
3. M5 paper-vs-backtest 對照納入 `is_ready` 觸發次數比對

**白話 summary**:每個策略是個「有記性的物件」,記得自己的內部狀態(可被存檔還原,回測鎖檔用)。它必須會 4 件事(出生設定 / 宣告要什麼資料 / 暖機 / 每根 K 線做決策),另外 3 件可做可不做(說準備好沒 / 被跳過時通知我 / 重置)。framework 給每個可選的都備好「預設動作」,多數策略不用管、特殊策略才自己改 —— 這就是反覆出現的 **default + override**。

### 3.4 觸發機制(ref #2B)

- **Event-driven**:有新資料(event)才 fire 有 subscribe 的策略,不是固定時鐘輪詢所有
- **Last known value(LKV)對齊**:策略 fire 時 snapshot 的非主觸發 field 取「最新已知值」(可能幾分鐘前的 last close),每 field 帶 timestamp 讓策略判 staleness
- **multi-timeframe**:BTC 1h / funding 8h / VIX daily 各自 cadence,LKV 對齊進同一 snapshot
- **統一 event log**:所有 lifecycle event + 跨策略觸發時序寫一條時間序記錄,debug / 回放 / M5 對照的 single source of truth

**白話 summary**:不是死板每隔固定時間叫策略,而是「**有新東西來才叫相關的策略**」。叫的時候給它一張市場快照,慢頻率的資料(像每天才更新的 VIX)就用「最後一次知道的值」填,並標上時間讓策略自己判斷新不新。

---

## § 4. Framework 一級護欄(non-bypass)

兩個護欄是 framework 寫死、使用者不可關的安全底線。**哲學區分**(ref R3-① Block 1):framework 不假設**業務語意**(門檻數值留使用者調),但**可寫死安全機制的存在性**(有沒有這層 framework 說了算)。類比:餐廳可決定菜單口味(業務),但「廚房一定要有滅火器」是法規寫死(安全)。

### 4.1 Risk Engine(ref R3-①)

**是什麼**:組合級風控,管守門員(per-symbol)管不到的整體性風險。三個 sub-stage:
1. **vol-targeting sizing**:部位大小按市場晃動調(越晃放越小,讓整體風險穩),M6 規格
2. **gross 總曝險上限**:所有部位加總別超過上限。看 **post-cap + vol-targeting 算完**的真實水位(ref Block 3)
3. **stale 最終把關**:資料完整性的最終責任歸這

**為什麼獨立成一級元件(非塞 PortfolioStrategy / 算量站)**:
- 塞 PortfolioStrategy:per-symbol min 模型**裝不下 gross**(總量 ≠ 逐幣,Round 2 #3C 補釘已證)
- 塞算量站:那站變「算量+gross+vol-target+stale」**雜物抽屜**,違反「每元件內部簡單」
- 獨立:職責單一 + gross 有正確的家 + 對齊頭號共識「風險管理 > 預測」應為一級公民

**為什麼寫死 + always-on(非可插拔 NoOp)**:M6 是 roadmap 硬規格,NoOp = 合法繞過;「風險 > 預測」給逃生口 = 動搖根基。即使 PortfolioStrategy 全 NoOp,Risk Engine 仍 always-on(無逃生口)。

**sub-stage 順序**(vol-target → gross → stale?)→ V2-B 細化(僅 gross 看 post-vol-targeting 這條已鎖)。

### 4.2 framework 執行政策層(ref R3-③)

**是什麼**:最終 order 紀律,位於算量站後、送單前。三能力:
- **dead-band**:`|current − desired| < threshold` → 不送單(幅度太小不值得動)
- **cooling**:距上次成單 < 間隔 → 不送單(頻率太密)
- **regime hook**:預留 V2-E regime-aware 降頻

**為什麼要它 + 為什麼跟策略級節流並存(雙層)**:過度交易有**兩種抖**,不同地方產生:
- **訊號自抖**(funding 小波動)→ **策略級**擋(funding 自帶 `dead_band`,策略最懂自己訊號該多鈍)
- **聚合後抖**(守門員 cap 每 bar 變 + vol-targeting 隨波動變 + 多策略 capital 權重挪)→ **framework 執行層**擋(只有它看得到最終 order,策略看不到)
- 純策略級漏聚合後抖(真漏洞);純 framework 抹掉策略訊號語意 → 故雙層

**白話 summary**:兩個護欄是 framework 焊死的安全底線。**保全總管**管「整桌總共下多少注、按市場晃動調倉、資料壞了最終把關」—— 因為這些守門員管不到、又是團隊第一順位的事,所以給它自己的家、還不准關。**出菜檢查站**管「就算要調倉,也別為了雞毛蒜皮的小變動或太頻繁地下單浪費手續費」。為什麼不塞進別的站?因為會變成「什麼都做的萬能間」,沒人看得懂。

---

## § 5. Framework 政策(全鏈路強制)

### 5.1 always-on 鎖(ref #3A)
**是什麼**:啟動時 framework 檢查 ≥1 PortfolioStrategy,0 個 → refuse to start。不想做風控 → 必須明確 register `NoOpPortfolioStrategy`(永遠 cap=1.0,log 透明顯示)。
**為什麼**:強迫使用者**表態**(要做/明確選不做),不允許默默裸奔。framework 不替你決定要不要風控,但逼你**做這個選擇**。

### 5.2 策略缺席統一模型(ref #2C2 + #2D)
**是什麼**:策略「不能用」這件事,framework **不分原因**統一當「這輪缺席」:
- 原因可以是資料 **stale**(#2C2-A:framework 偵測 → 跳過 on_bar,策略無感)
- 也可以是程式 **crash**(#2D:on_bar 拋例外 → catch + 當缺席)
- 缺席處理:**SymbolStrategy** → 跳過;**PortfolioStrategy** → fail-safe(fallback_cap 丟進 #3D min 池)+ 告警
**為什麼**:零新 framework primitive,#2C2 + #3C 機制 #2D 直接複用。心智統一(不為每種理由各寫一套)。

### 5.3 crash counter 永久停用(ref #2D)
**是什麼**:策略連續 crash 達 N 次 → 永久停用 + Telegram 告警。復用 #2C2-B Sub-Q2 的 **counter + 門檻 pattern**。N 走 default + override(守門員可設 N=1)。
**漂亮的湧現**:守門員被永久停用 → 數量降到 0 → 撞 §5.1 always-on 鎖 → framework 自動停機。「守門員壞了會停整台」**不是顯式規則,是 #2D + #3A 組合自然長出**,比寫死規矩更溫和(transient glitch 有機會)+ 更不脆。

### 5.4 stale 處理細節(ref #2C2-B)
- **Sub-Q1** `on_stale()`:可選 hook 通知策略被跳(風控用),base no-op
- **Sub-Q2** alert 升級:per-field counter 連續 N 次 stale → V1 notifier 告警 + M5 對照 stale 次數
- **Sub-Q3** 門檻宣告:`max_staleness` / `alert_N` 寫 `DATA_SOURCES` registry 作 default,策略 `required_data()` 可 override,**per-strategy 判定**(snapshot 共享、stale 判定各用自己門檻,寬鬆策略不被嚴格策略綁架)

**白話 summary**:三條政策全鏈路盯著。**第一條**:啟動一定要有守門員在崗位(真的或假人),不准空櫃。**第二條**:策略不管是資料壞了還程式爆了,一律當「今天請假」統一處理,不為每種理由各寫規矩。**第三條**:請假太多次就開除,而且要是開除到「最後一個守門員」也沒了,系統會自動撞上「一定要有守門員」那條鎖而停機 —— 這個保護是前兩條組合**自動長出來的**,沒人特別寫。

---

## § 6. I/O 兩側對稱 parity 架構

V2-A 最關鍵的結構性保證 —— **回測跟實盤從頭到尾用同一套 code**,結構上沒有「悄悄分岔」的空間。

### 6.1 輸入側:event bus + 雙 driver(ref R3-②)
```
              ┌─ backtest driver:讀歷史,按時間順序吐 events
event 介面 ───┤                                          → 引擎 + 策略(不知來源)
              └─ live driver:接交易所 feed,即時吐 events
```
- **parity by construction**:同一 event 介面 → 同一套 code,無從分岔
- **no-lookahead by construction**:引擎只處理「已發生的 event」→ 結構上碰不到未來資料

### 6.2 輸出側:executor 抽象 + 雙 driver(ref R3-④)
```
                 ┌─ backtest driver:sim 成交器(歷史價成交 + 滑點/手續費估)
executor 介面 ───┤                                          ← 引擎輸出 order(不知去向)
                 └─ live driver:V1 trader.py + exchange_api 真下單
```
- **輸出側 parity by construction**:同一 executor 介面 → 同一套下單 code

### 6.3 為什麼 I/O 都要(M5 從根堵死)
backtest/live 分岔是量化頭號死法之一(M5 paper-vs-backtest 專門抓)。輸入(R3-②)堵了資料側、輸出(R3-④)堵了訂單側 → **I/O 兩側皆 by construction** → M5 那條病**架構層已預防**,不必靠事後比對抓。設計品味:**安全的東西要 by construction(結構保證),不要 by discipline(靠人不犯錯)** —— 同 #3C「fail-safe 丟 min 池而非事後檢查」。

### 6.4 V1 模組落點表(ref R3-④,使用者確認 OK)
| V1 模組 | 落點 | 狀態 |
|---|---|---|
| `exchange_api` | R3-② live driver(資料IN)+ R3-④ live executor(下單OUT)| 已決 |
| `price_recorder` | R3-② backtest 歷史資料源 | 已決 |
| `trader` | R3-④ live executor driver | 已決 |
| `notifier` | 統一 alert sink(stale/silent divergence/crash/fail-safe 匯流)| 接縫定,channel 細節 → V2-D |
| `circuit_breaker` | #2D 框架級 crash 處理(架構已決)+ 實盤安全層 | 架構已決,實作 → V2-D |
| `heartbeat` | 維運 liveness 監控 | → V2-D(回測用不到)|
| `chaos_test` | M1 五段崩盤壓測注錯驅動 | V2-B 測試基建 |

**白話 summary**:這是整個架構**最值錢的一招**。資料「進來」跟訂單「出去」兩側,都做成「同一條管線 + 兩個插頭」 —— 回測插模擬的、實盤插真的,中間那套 code 一模一樣。所以「考試會、上場走樣」這種量化最常見的暗虧,在架構層**根本沒有發生的空間**,不用靠事後對帳去抓。你舊的 V1 工具則照「資料的接 R3-②、下單的接 R3-④、上場才用的留 V2-D」歸位。

---

## § 7. 設計哲學 10 條

整個 V2 framework 反覆出現的設計品味。看到新問題先套這 10 條,多半能推出答案。

**Round 2 浮現(1-6)**:
1. **Framework 不假設業務語意** — 否決所有「替使用者預設業務」的 option(Sub-Q3 取最嚴 / #3A 內建 baseline / #3D 平均加權)
2. **Default + override 老路** — framework 給合理 default 處理 boilerplate,策略可特化(is_ready / on_stale / max_staleness / fallback_cap 全套)
3. **Counter + 門檻 pattern** — 連續觀察 N 次累積觸發升級,統一 primitive(is_ready 防呆 / stale alert / crash 永久停用 共用)
4. **單調往最保守倒** — fail-safe 只能往緊永不放寬(#3D min / #3C fallback 丟 min 池非二次施加)
5. **強迫表態 > 默默裸奔** — #3A NoOp 明確 register / #2C1 ack 防呆
6. **湧現 > 顯式條文** — #2D crash + #3A 鎖 → 自動停機,組合長出比寫死穩

**Round 3 新增(7-10)**:
7. **精簡尺反覆作用** — litmus「不拍 V2-B 引擎骨架會卡嗎?」,4 議題 3 個塌成一刀(R3-②/③/④)。super-題前先評估拆法很值錢
8. **I/O 兩側對稱 parity** — R3-② 輸入 + R3-④ 輸出 by construction,backtest/live 從根堵死
9. **framework 級護欄 vs 策略級風控分層** — 區分「業務語意」(留使用者)vs「安全機制存在性」(framework 寫死),解「framework 不假設業務」的表面衝突
10. **雙層職責對抗雜物抽屜** — 寧多開盒子不變萬能間(Risk Engine vs 算量站、訊號層 vs 執行層)

**白話 summary**:這 10 條是整個平台的「性格」。最核心兩條:**framework 給你預設、但把真正的選擇逼你自己做**(1/2/5),和**安全的東西用結構保證、不靠人自律**(4/8)。以後遇到新設計題,先問「這 10 條會怎麼說」,通常答案就出來了。

---

## § 8. Carry over(V2-B / V2-D / V2-E / V2-S)

V2-A 不拍的東西,明確分流到後續階段。

### → V2-B 必驗 / 必拍(寫引擎時)
- 模擬成交器演算法 / 滑點 + 手續費模型(= Round 1 Gap 4 回測成本模型)
- Risk Engine 三 sub-stage 順序選型
- snapshot rebuild vs incremental 效能選型
- DATA_SOURCES registry 格式(dict/YAML/DB)+ event log 確切 schema
- 數值校準:`max_staleness` / `alert_N` / `fallback_cap` / dead-band / cooling 間隔 / crash N
- counter 鋸齒 reset 評估(連續 vs 滑動視窗 N-of-M)
- whipsaw 量化(M1 五段崩盤 stale-aware 實測)
- trend × funding correlation 實測(Round 2 #1 預估 -0.1~+0.2,M1 reality check)
- 最低 edge 門檻數字(Round 1 Gap 3)

### → V2-D 順延(實盤上場才需要)
- notifier channel 分流(critical / warning / info)
- circuit_breaker 實盤層整合
- heartbeat liveness 監控頻率 / 告警

### → V2-E 順延(依賴 regime detection)
- regime-aware 降頻(framework 執行政策層已預留 hook)
- ensemble 動態策略選擇 / allocation meta-layer

### → V2-S 各策略 codify 紀律
- overlay 訊號**連續可衰退、禁 binary latch**(事件型風險淡化後 cap 要自動鬆回,否則 min 被過時訊號綁架誤殺;framework 管不到訊號語意,逐策略驗)

### Validation Standards 對照(ref roadmap)
- **M1-M7** = 策略上線閘門(市場風險):M1 五段崩盤壓測 / M2 walk-forward / M3 lock / M4 paper ≥60 日 / M5 paper-vs-backtest / M6 risk-based sizing / M7 退役機制
- **M8** = 系統運行閘門(維運風險,**獨立 track**,見 `m8_security.md`,非本架構文件範圍)

**白話 summary**:V2-A 只畫架構、不碰「實際數字」跟「實盤工具」。所有「要跑過真資料才知道的數字」(門檻、公式、相關性)留給 V2-B 校準;所有「真錢上場才用到的」(通知、斷路、心跳)留給 V2-D;市場狀態偵測那種進階的留給 V2-E。各策略寫的時候要守一條紀律:風控訊號別卡死、事件過了要會鬆手。

---

## § 9. V2-A 階段收官狀態

| Round | 主題 | 狀態 |
|---|---|---|
| Round 1 | Strategy interface 骨架(雙 interface / output / 抽象層次)| ✅ 定案 2026-05-17 |
| Round 2 | 完整 framework 契約(lifecycle / 觸發 / 暖機 / stale / 錯誤 / PortfolioStrategy)| ✅ 收官 2026-05-26(13 拍板)|
| Round 3 | 平台底盤(Risk Engine / 資料流 / 執行層 / V1 整合)| ✅ 收官 2026-05-26(6 拍板)|
| 收斂 | 本文件(architecture.md)| ✅ 2026-05-26 |

**V2-A(畫設計圖、不寫 code)階段完成。** 下一步:V2-A officially 收官 → 進 **V2-B**(寫第一行回測引擎 code,依本文件 + carry over 清單)。

**白話 summary**:房子的設計圖**畫完了**。三輪討論(策略長什麼樣 → 策略的完整規矩 → 整棟樓的公共系統)全部拍板、收斂成這一份。接下來就是拿這份圖**真的開始蓋**(V2-B 寫第一行 code)。
