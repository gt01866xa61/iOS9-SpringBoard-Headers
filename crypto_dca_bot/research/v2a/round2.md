# V2-A Round 2 — 策略池 finalize + P1 細節 + PortfolioStrategy 疊合

> 2026-05-21 起(Asia/Taipei)。Round 1 三軸正式定案後(見 `round1.md`),進入 Round 2。
> Round 2 三個重點(按 `round1.md` open questions 排序,依賴關係 #1 → #2 → #3):
>   1. 策略池 #2 替代 mean-reversion 拍板 → **DONE 2026-05-21**(本檔下方)
>   2. P1 細節子題(lifecycle methods / param schema / data spec)→ pending
>   3. PortfolioStrategy always-on 鎖 + 多 PortfolioStrategy 疊合演算法 → pending

---

## #1 策略池 #2 — 替代 mean-reversion 拍板(2026-05-21)

### 拍板

**選 D:Funding rate skew(永續資金費率偏度)** 為起步策略池 #2。
**C(Calendar / BTC halving cycle)退為 PortfolioStrategy 子訊號候選**,V2-E ensemble 階段再評估。

### 起步策略池(round 2 後狀態)

| # | Style | 角色 | 來源 |
|---|---|---|---|
| 1 | Trend-following | SymbolStrategy | V1 既有合約系統 codify |
| 2 | **Funding rate skew** | SymbolStrategy | round 2 新選(本檔) |
| 3 | Macro overlay (VIX / DXY) | PortfolioStrategy | round 1 留 |

### 拍板理由

**不是「D 一定賺」,而是 D 通得過 M1-M7 驗證流程**,C 在 M2 / M4 / M5 結構性卡關(樣本 N = 2)。詳對照見 [§ D vs C 對照](#d-vs-c-對照濃縮)。

---

## D — Funding rate skew(完整 6 項分析)

### 1. 訊號定義(進場 / 出場)

```
每 8 小時觸發(對齊 Binance funding 結算時間 00 / 08 / 16 UTC):
  raw_funding = 過去 lookback_periods 個 funding 期間滾動平均
  IF raw_funding ≤ low_threshold  → target = 1.0   (滿倉)
  IF raw_funding ≥ high_threshold → target = 0.0   (出場)
  ELSE → 兩端線性插值 (linear interpolation)

per symbol 各自獨立 — BTC funding 對 BTC 部位、ETH funding 對 ETH 部位
```

核心 thesis:持續高 funding(永續多頭擁擠) → 縮 spot 多單;持續低/負 funding(空頭擁擠) → 滿倉。**不交易永續,只把 funding 當訊號用** — 符合 V2 邊界(只玩 spot)。

### 2. 參數清單(5 個,簡單派紀律 ≤ 5 ✓)

| # | param | 預設 | 意義 |
|---|---|---|---|
| 1 | `lookback_periods` | 21 | 滾動平均的 8h 期間數(7 天) |
| 2 | `low_threshold` | 0.005% / 8h | funding 低於此 → 全進(≈ 5.5% 年化 carry) |
| 3 | `high_threshold` | 0.03% / 8h | funding 高於此 → 全出(≈ 33% 年化 carry) |
| 4 | `dead_band` | 0.002% | 訊號變動小於此不動部位(防 over-trade) |
| 5 | `symbol_list` | `["BTC", "ETH"]` | 套用對象 |

`dead_band` 是 round 1 review pass 衍生的 over-trade 防制工具雛形(對應「執行層 cooling tools」note)。

### 3. 資料需求

| 項目 | 內容 |
|---|---|
| 來源 | Binance Futures REST `/fapi/v1/fundingRate` |
| 頻率 | 每 8h(00 / 08 / 16 UTC)by exchange |
| 成本 | $0,public endpoint,無 API key |
| 歷史可用度 | BTCUSDT perp 2019-09 起、ETHUSDT perp 2019-11 起 — M1 五段崩盤(2020-03 / 2021-05 / 2022-05 / 2022-11 / 2024-08)**全覆蓋** ✓ |
| 儲存 | ~1100 rows/年/symbol,既有 SQLite 可吸收 |
| 額外依賴 | 無新 lib,V1 `exchange_api.py` 改 endpoint 即可 |

### 4. 對 M1-M7 影響

| Std | 影響 / 風險 |
|---|---|
| M1 五段崩盤 | 資料全覆蓋 ✓。但 2020-03 永續市場規模小,funding 動態可能跟 2022+ 結構不同 — V2-B 階段需 sanity check |
| M2 walk-forward | IS 30m 從 2019-09 起足夠涵蓋多 regime,資料量充足 ✓ |
| M3 lock | 標準流程,無特殊處理 |
| M4 paper 60 交易日 | 訊號頻率 8h,60 日內訊號豐富 ✓ |
| M5 paper vs backtest | funding 由交易所定期推、訊號不是市價觸發 → fill rate 預期接近完美,paper-backtest 差距小 — 對 D 友善 |
| M6 risk-based sizing | D 本身就是 graduated target (0~1 連續),vol targeting 可疊在外層 |
| M7 退役監控 | **真實 concern**:funding skew 是知名 edge,2021 起被 funding arb fund 大量抹平,Sharpe 持續衰退風險高 — M7 上線後會密切觸發 |

### 5. 失效情境(什麼市況會虧)

1. **緩牛慢漲**:funding 持續中度正,策略長期半倉,trend 在賺、D 踏空 → 機會成本但不直虧
2. **快崩前 funding 沒先飆**(例 2022 LUNA):funding 沒明顯異常 → 策略沒提前縮,跟現貨一起虧
3. **Regime shift 後 threshold 過時**:2023+ 永續市場成熟,平均 funding 結構性下降,沿用舊 threshold → 訊號常駐「過熱」、策略長期空手
4. **Short squeeze 期間**:極端負 funding 時策略滿倉,但反彈失敗繼續下跌 → 抓刀(catch a falling knife)

### 6. 對 Trend-following 的 correlation 推導邏輯

**前提**:trend 賺「動能持續期」、D 在「動能過熱期」減倉。兩者在週期不同階段啟動。

| 週期階段 | trend 動作 | D 動作 | 同 / 反 |
|---|---|---|---|
| 動能起步(底部突破) | 加倉 | funding 中性,滿倉 | **同向** |
| 動能中段(穩升) | 滿倉 | funding 升,部位漸縮 | **半反向** |
| 動能頂部(過熱) | 還沒轉、滿倉 | funding 極高、撤了 | **強反向** |
| 急跌(崩盤) | 出場 | funding 暴跌負值、重滿倉 | **強反向** |
| 盤整 | 不動 | funding 來回小幅進出 | **近零** |

**全期混合 correlation 預估**:**-0.1 ~ +0.2**

**關鍵 caveat** — 數字是邏輯推導,**不是實測**。最大風險點:若 trend 訊號(EMA crossover)的 lag 跟 funding 升溫時間軸只差 1-2 週,實測 correlation 會比預估高(0.3+)。**M1 五段崩盤是這條 correlation 的 reality check 關鍵**,V2-B 跑出來看實際結果再校準。

---

## C 為何不選(但保留)

### C 的硬問題:N = 2

C(BTC halving cycle)邏輯吸引人 — 4 年週期歷史上減半後 12-24 個月是強勢期。但高品質 BTC/ETH 資料 2017+ 才齊,只覆蓋 **2020-05 + 2024-04 兩次 halving** = N = 2。

這違反多條驗證標準的前提:
- **M2 walk-forward**:訊號每 4 年才實質觸發,IS 30m / OOS 3m 視窗多數時間訊號靜止 → WFE > 50% 幾乎不可能達標
- **M4 paper trading 60 日**:60 天可能根本沒跨 halving window 邊界,訊號靜止 → 無實質驗證
- **M5 paper vs backtest**:訊號太稀,對照無統計意義

簡單說:**C 是「設計上邏輯不能被 M1-M7 驗證」的策略**。不是調參能解決,是樣本量問題。

### 為什麼仍保留?

C 在 PortfolioStrategy 子訊號角色(「decade 級週期過熱期降風險」)的 overlay 用法**不要求 walk-forward 過關**(overlay 是 risk-reduction 機制,不主張 alpha)。V2-E ensemble 階段再評估是否納入 PortfolioStrategy 子訊號集。

---

## D vs C 對照濃縮

| 維度 | D 資金費率 | C 減半週期 |
|---|---|---|
| 簡單度 | 5 params,邏輯一句話 ✓ | 5 params,邏輯一句話 ✓ |
| 跟 trend 邏輯互補性 | **強**(機制反向) | 弱(只是不相關) |
| 訊號頻率 | 每 8h | 每 4 年(實質) |
| 資料樣本量 | 充沛(M1-M2 都可滿足) | **N = 2,M2 / M4 / M5 結構性失敗** |
| Walk-forward 過關難度 | 中 | **極高(機制上很難)** |
| Edge 衰退風險 | 中-高(arb 抹平) | 中(N=2 無法判斷) |
| 失效時最壞情境 | 訊號鈍化、機會成本 | 黑天鵝撞 window、無防衛 |

---

## #2 P1 細節子題 — IN PROGRESS

> 子軸:A. 必要 vs 可選 → DONE 2026-05-22 / B. 觸發頻率粒度 → DONE 2026-05-22 / **C. 狀態 lifecycle 細節 → C1 DONE 2026-05-22(C2/C3 TODO)** / D. 錯誤路徑 → TODO

### #2A Lifecycle method 必要 vs 可選(2026-05-22)

**拍板:4 必要 + 1 可選**

| Method | 必要? | 何時被叫 | 用途 |
|---|---|---|---|
| `__init__(params)` | **必要** | 策略建立時,只一次 | 接 params + 合法性檢查 |
| `required_data() → DataSpec` | **必要** | 註冊時,只一次 | 跟 engine 宣告需要什麼資料(粒度 / 長度 / symbol) |
| `initialize(snapshot)` | **必要**(可空 `pass`) | 第一根 bar 前,只一次 | 暖機:load 歷史 prime indicators |
| `on_bar(snapshot) → output` | **必要** | 每根 bar | 核心邏輯:看快照 → 回 target |
| `reset()` | **可選**(default = framework 丟舊 instance、用同 params new 新的) | walk-forward 切窗口前 | 清空所有內部狀態 |

**為什麼 initialize 鎖為必要而非可選**:即使 no-op (`pass`),明寫的好處:
1. Framework 可在 initialize 前後關鍵點插 instrumentation(timing / state snapshot / telemetry)
2. Contract 對策略開發者更明確 — 「暖機」是一等公民概念,不藏在 `__init__` 裡偷做
3. 實際策略池 0 代價:funding skew 要 prime 21 期 rolling buffer、trend 要 prime EMA、macro overlay 要 load 30 天 VIX/DXY history,3 條都需要 initialize

**為什麼 reset 留可選**:多數策略不會在意 — engine 直接丟舊 instance、用同 params new 新的等價於 reset。只有特殊需求(例如:策略內部有 expensive cache 想保留結構但 reset 內容)才 override。

**下一子軸 #2B**:`on_bar` 的「bar」到底是什麼粒度?BTC K 線是 1h、funding 是 8h、macro 資料是日線,multi-timeframe 怎麼合進同一個 on_bar 觸發?

---

### #2B 觸發頻率粒度(2026-05-22)

**拍板:Event-driven + last known value 對齊 + 統一 event log**

**核心三元素**:

1. **Event-driven dispatch**:engine 不是「每根最細粒度 bar 觸發所有策略」,而是「每筆新資料來只 fire 對應 subscribe 的策略」。
   - BTC 1h close → 只 fire trend
   - 8h funding 結算 → 只 fire funding skew
   - 日線 VIX/DXY → 只 fire macro overlay

2. **Last known value 時序對齊**:策略被 fire 時,snapshot 中所有非主觸發 field 一律是「最新已知值」,不等同步、不空缺、但可能 stale。
   - 例:funding skew 在 08:00 UTC funding 結算被 fire,snapshot 中 BTC price = 最近一根 1h bar(07:00 UTC 收盤)。不會因為「下一根 1h bar 還沒收」而 block。

3. **統一 event log**:利用 #2A 鎖板的 `initialize` instrumentation hook,framework 把所有 lifecycle event(initialize / on_bar / reset)+ 跨策略觸發時序統一寫進 event log。Debug 時可看「先 fire trend(08:00:01)、再 fire funding(08:00:03)、snapshot 中 BTC price 是 67200(時戳 07:00:00)」這種完整時序。

**架構意涵**:

| 元件 | 設計需求 |
|---|---|
| Engine dispatch table | 註冊時 `required_data()` 不只宣告需要什麼資料、也宣告 subscribe 哪些 data event 作觸發 |
| Snapshot 組裝 | 永遠是「組裝最新 known values」的視圖 — 各 field 帶 `timestamp` 讓策略可查 staleness |
| Walk-forward / paper trading | event ordering 在三種模式(backtest / paper / live)下必須完全可重現,event log 是 single source of truth |

**為何不選「同步每 bar 觸發」**:
- 8h funding 跟 1h K 線之間沒有「最大公約 bar」(8h)能合理觸發 trend(trend 一天只 fire 3 次太少)
- 強制同步會讓策略相互等對方資料,但 funding 不會「等 BTC 1h 收盤再公布」,反之亦然 → 同步只是人為延遲

**未解伏筆**(往 #2C / #2D):
- 暖機期間(buffer 未填滿)on_bar 被 fire,策略應 emit 什麼?
- Last known value 多 stale 算「太舊不可用」?
- 多策略 emit 衝突的 target 給同一 symbol?(這偏 portfolio aggregation,V2-A 後段)

**下一子軸 #2C**:狀態 lifecycle 細節 — 暖機 / stale data / state 持久化的協議。

---

### #2C1 暖機期協議(2026-05-22)

**拍板:γ 混合派 — Framework 統一 `is_ready()` API + 策略可 override + 3 條防呆**

**基本機制(白話)**:
- 策略 class 多一個 method:`is_ready() -> bool`(白話:策略告訴 engine「我準備好開始決策了嗎?」回 true/false)
- Framework 在 fire `on_bar` 之前,先 call `is_ready()`;回 false 就跳過這次 fire(不執行 `on_bar`)
- Framework 提供 default 實作:「buffer 滿到 `required_data()` 宣告的 `min_history` 為止」— 覆蓋多數情境
- 策略可 override 寫自己版本(funding skew 用 default 就夠;特殊策略可特化)

**3 條防呆(寫進 lifecycle 規格,不是建議,是強制)**:

1. **強制 log `is_ready` 回傳結果 + 連續 N 次 false 告警**(N 預設待定,V2-B 時定數字)
   - Framework 不問策略要、直接記;每次 dispatch 自動掛
   - 連續 N 次 false → 告警「策略可能 buffer 餵不進來、或就緒條件設太嚴」
   - 解決盲點:策略默默不就緒、整個系統不知道

2. **`is_ready()` 只能看歷史 buffer,不能看當前最新值**
   - 寫進 lifecycle 規格作硬約束
   - 目的:鎖死 backtest / paper / live 三模式在同 timestamp 下 `is_ready` 結果必相同
   - 解決盲點:避免「回測算 ready 但 live 上線後變未 ready」這種模式差異 bug

3. **M5 paper-vs-backtest 對照納入 `is_ready` 觸發次數比對**
   - M5 既有對照項(訊號數、fill rate、target 軌跡)+ 新增「`is_ready` true 次數 / false 次數」
   - 兩模式差太多 → fail M5,設計有 bug
   - 解決盲點:防呆 #2 鎖時序、這條鎖數值;雙重保險

**為何選 γ 而非 α/β**:
- α(策略自報):每個策略都要寫 readiness 判斷,boilerplate ↑;且 framework 無法統一插 instrumentation
- β(framework 推遲):framework 必須懂每個策略的就緒邏輯,耦合度過高
- γ:default 覆蓋 80% 情境(buffer-based)、特殊策略可 override,且配上 3 防呆讓 override 不會炸

**對 #2A 邊界影響**:
- `is_ready()` 是新增的策略 method,需歸到「必要 / 可選」分類
- 拍:**可選**(default = framework 提供 buffer-based 實作),理由與 `reset()` 同 — 多數策略 default 就夠
- 但 default 實作本身是 framework 一級公民,不是「策略開發者忘了就空」

**未解伏筆**:
- 防呆 #1 的 N 值(連續幾次 false 告警):待 V2-B 實測訊號分佈後定
- 防呆 #2 「歷史 buffer」的精確邊界:`is_ready` 能讀 snapshot 嗎?還是只能讀策略內部 buffer?— 留 #2C2 stale data 子題一起處理

**下一子軸**:#2C2 stale data 容忍協議。但 user 觸發 skill check → 推進前先做 Round 2 全部已拍板的 review pass。

---

### #2C2-A Framework 對 stale data 的行為(2026-05-24)

**拍板:Option 3 — Framework 偵測 stale → 跳過 on_bar + 寫 event log,策略無感**

**核心機制**:
- Engine fire 策略前先掃 snapshot 各 field 的 `timestamp`,任何被 `required_data()` 宣告為 critical 的 field 超過 staleness 門檻 → **不 call `on_bar`**(直接跳過這次觸發)
- 跳過事件統一寫進 event log:`{strategy, timestamp, stale_fields: [...], action: "skipped"}`
- 策略本身**預設無感** — 它只是這次沒被叫到,跟「is_ready 回 false 被跳」結構一致

**為何 Option 3(framework 擋)而非「策略自己判斷 stale」**:
- 跟 #2C1 `is_ready()` 同精神 — framework 統一卡關、不勞煩每個策略自己重寫一份 stale 檢查 boilerplate
- backtest / paper / live 三模式 stale 判定走同一條 code path,確保結果可重現(M5 對照不會炸)
- staleness 門檻是 framework convention(由 `required_data()` 宣告每 field 的 `max_staleness`),不混進策略邏輯

**未解伏筆 → 拆成 3 個 Sub-Q**:
- Sub-Q1:策略要不要有 `on_stale` 鉤子?(事後通知)
- Sub-Q2:連續 stale N 次要不要升級成 alert?(類比 #2C1 防呆 #1)
- Sub-Q3:`max_staleness` 門檻在哪宣告 / 預設值?

---

### #2C2-B Sub-Q1 策略 stale 通知鉤子(2026-05-24)

**拍板:Option C — 可選 `on_stale(stale_fields)`,base class default no-op,策略可 override**

**機制**:
```python
class Strategy:
    def on_bar(self, snapshot): ...
    def is_ready(self, snapshot): ...
    def on_stale(self, stale_fields):  # default no-op
        pass

class MyRiskStrategy(Strategy):
    def on_stale(self, stale_fields):
        if "BTC_price" in stale_fields:
            self.reduce_position()
```

- 預設無感:多數策略(long-only DCA、單純 trend)用 default no-op,寫了等於沒寫
- 留 hook 點:風控 / fallback / ensemble 策略 override 處理 stale 後續(例:降部位、切備援源、re-weight)

**為何 Option C(可選 override)而非 A/B/D**:
- A(黑箱,不開鉤子):跟 Option 3「策略無感」一致到底,但風控 / fallback 策略沒地方寫 stale 處理 → 過度極端 minimalist
- B(強制 on_stale):統一介面但**多數策略不需要** = 強迫所有人寫 `def on_stale(self, fields): pass` boilerplate,違反「策略無感」精神
- D(event bus / pub-sub):為一個 on_stale 引入 event bus 架構複雜度爆炸,V2-A 階段過早優化
- C 同時滿足「不需要的策略無感」+「需要的策略有 hook 點」+ base class 多一個方法成本極低

**對 #2A 邊界影響**:
- `on_stale()` 是新增的策略 method,歸到「**可選**」分類(與 `reset()` / `is_ready()` 同),理由同上 — default 覆蓋多數策略

**對其他 Sub-Q 的影響**:
- 對 Sub-Q2(連續 stale 升 alert)幾乎無影響 — alert 是 framework 往 surveillance 發,跟策略 hook 解耦
- 對 Sub-Q3(`max_staleness` 宣告)無影響 — 門檻是 `required_data()` schema 的事

**未解伏筆**:
- 順序問題:同一輪 dispatch 內,`on_stale` 應在 `on_bar` 被跳之前 / 同時 / 之後呼叫?— 留 P1 lifecycle methods 規格章節定
- `stale_fields` payload schema:純 field name list?還是含每 field 的 timestamp + max_staleness?— 同上留 P1 規格章節

**下一子軸**:#2C2-B Sub-Q2 連續 stale N 次升 alert。

---

### #2C2-B Sub-Q2 連續 stale 升 alert 機制(2026-05-24)

**拍板:Option C — 連續 N 次 stale → alert + N 值 per-field + M5 對照納入 stale 次數比對**

**核心機制(完全平行 #2C1 防呆 #1)**:
- Framework 內建 **per-field counter**:某 critical field 連續被判 stale 時 counter++
- counter 達到 N → 升 alert(走 V1 沿用的 `notifier.py` / Telegram bot)
- counter 在「該 field fresh 一次」時 **reset 歸零**
- **N 值 per-field** 由 `required_data()` 宣告(預設值留 V2-B 實測校準)
  - 例:1h K 線 N=6(連續 6 小時容忍)、8h funding N=2(連續 16 小時容忍)
  - 把時間語義 pre-baked 進「次數 × 該 field cadence」,效果等同時長派但機制與 #2C1 共用

**為何 Option C 而非 A/B/D**:
- A(不 alert):資料源真死了沒人通知 → 災難場景沒覆蓋;且跟 #2C1 防呆 #1 心智模型分裂
- B(一次就 alert):網路抖一下即炸 → **alert 疲勞**,重要訊號被淹
- D(連續時長 X 分鐘):多時鐘策略更公平、但跟 #2C1 不同 pattern;C 用 per-field N 模擬時長**結果等價、機制統一**
- C 同時滿足:跟 #2C1 一致(framework 心智統一)+ 過濾雜訊 + 抓得到死

**配套防呆(類比 #2C1 防呆 #3)**:
- **M5 paper-vs-backtest 對照納入「stale 次數 / alert 觸發次數」比對**
- backtest 與 paper / live 的 stale 次數差太多 → 設計有 bug(可能 data lag 模擬不對、可能 `max_staleness` 門檻三模式不一致)
- 零額外成本、直接複用 M5 既有對照框架

**Alert destination 決議**:
- 沿用 V1 `notifier.py`(Telegram bot)— 不阻塞拍板
- V2 surveillance layer 設計時(後續 round)可再分級 critical / warning,V2-A 階段不超前設計

**對 #2C1 / #2C2-A / Sub-Q1 的關係**:
- 跟 #2C1 防呆 #1 / #3 結構完全平行(counter + 門檻 + alert / M5 對照)
- 跟 #2C2-A 解耦:framework 跳過 on_bar 是「該次行為」;Sub-Q2 alert 是「連續觀察累積行為」
- 跟 Sub-Q1 解耦:`on_stale` hook 是策略視角、alert 是 operator(使用者)視角

**未解伏筆**:
- N 值預設與 per-field 校準(`required_data()` schema):留 Sub-Q3(`max_staleness` 宣告)+ V2-B 實測
- Alert payload schema(包哪些 field?多 strategy 同時 stale 要不要 dedupe?):留 V2-D 部署階段細究
- counter reset 規則邊界:`fresh 一次即 reset` 是否會被「fresh 一筆又 stale」鋸齒重置綁架?— 留 V2-B 觀測

**下一子軸**:#2C2-B Sub-Q3 `max_staleness` 門檻宣告位置 + 預設值機制。

---

### #2C2-B Sub-Q3 max_staleness + N 值宣告位置與預設機制(2026-05-24)

**拍板:Option Γ+Ε — 雙層 default + 策略可 override + per-strategy 判定**

**整合解(3 個小維度同時拍)**:

| 維度 | 拍 |
|---|---|
| 1. 宣告位置 | **1C 雙層**:Framework data source registry per-source 給 default + 策略 `required_data()` 可 override |
| 2. 預設機制 | **per-data-source**(default 寫在 framework registry,跟 `cadence` 一起設) |
| 3. 多策略訂同 field 衝突 | **3-Ε per-strategy 判定**:snapshot 共享、stale 判定 / 跳過 per-strategy 各用自己門檻 |
| N 值機制 | **同 `max_staleness` 機制共生**(default + override + per-strategy 判定) |

**Framework data source registry 形狀**:
```python
DATA_SOURCES = {
    "BTC_kline_1h": {
        "cadence":               "1h",   # 預期 fire 頻率
        "max_staleness_default": "2h",   # 超過 2h 算 stale
        "alert_N_default":       6,      # 連續 6 次 stale → alert
    },
    "funding_rate_8h": {
        "cadence":               "8h",
        "max_staleness_default": "16h",
        "alert_N_default":       2,
    },
    "vix_daily": {
        "cadence":               "1d",
        "max_staleness_default": "3d",
        "alert_N_default":       3,
    },
}
```

**策略宣告兩種用法**:
```python
# 多數策略:用 default,完全不寫 staleness 欄位
def required_data(self):
    return {"BTC_kline_1h": {"min_history": 200}}

# 風控策略:override 寫嚴格門檻
def required_data(self):
    return {
        "BTC_kline_1h": {"min_history": 200, "max_staleness": "30m", "alert_N": 2},
    }
```

**為何 Γ+Ε 而非 Α / Β / Δ**:
- Α(純 per-strategy):多策略訂同 field 不一致(snapshot 共用、各家 max_staleness 不同 framework 無所適從)+ boilerplate 爆炸
- Β(純 framework registry):**風控 / fallback 策略沒地方寫嚴格門檻**;V2-A 雖未明列風控策略,但 PortfolioStrategy(macro overlay)即風控性質,未來「BTC 跌破 stop loss 清倉」這類策略需 ≈0 stale 容忍 — Γ 留 hook
- Δ(取最嚴 `min(max_staleness)`):trend 接受 2h、風控要 30m → framework 用 30m → **trend 也被頻繁跳過** = 寬鬆策略被嚴格策略綁架,行為不可預期
- Γ+Ε:default 解 boilerplate、override 解風控需求、per-strategy 判定解多策略衝突 — 三維度同解,且**跟 #2C1 / Sub-Q1 / Sub-Q2 同 pattern**(framework default + 策略可特化),framework 心智統一

**Framework 邏輯影響**:
- dispatch 前 per-strategy 算自己的 stale 判定(每次 fire 多一次 timestamp 比較,cost 微乎其微)
- snapshot 組裝**不變**(各 field 共享 last known value + timestamp,Sub-Q3 不動 snapshot 結構)
- alert counter **per-(strategy, field)** 累積:`{strategy_X}.{BTC_kline_1h}.stale_count`,因為各策略門檻不同

**配套防呆**:
- 無新增 — Sub-Q2 已加 M5 對照 stale 次數,Sub-Q3 拍 per-strategy 後 M5 對照自動覆蓋 per-strategy 視角(各策略各自比對)
- 未來資料源新增 → 改 registry 一處,不污染策略 code

**對其他事情的影響**:
- `required_data()` schema 多兩個可選欄位(`max_staleness` / `alert_N`),P1 lifecycle spec 章節要寫進去
- Framework 需維護 `DATA_SOURCES` registry 為一級結構,V2-B 引擎開發時建出

**未解伏筆**:
- Per-data-source 預設值(`max_staleness_default` / `alert_N_default`)實際數字 — 留 V2-B 實測校準(類比 #2C1 防呆 #1)
- Registry 是 Python dict / YAML / 資料庫 — 留 P1 規格實作細節
- `cadence` 不規律的 source(如 event-driven 但 timing 抖動)的 stale 判定精度問題 — 留 V2-B 觀測

**Round 2 #2C2-B 全套 Sub-Q 完成(Sub-Q1/2/3 都拍板)**。

---

### #2C2 全段收尾 — review pass 全綠 + 4 個 watch item 分流(2026-05-24)

#2C2 整段(A + B-1/2/3)用白話 walk-through review pass,8 個 checkpoint 全綠。使用者 carry over 4 個 watch item,分流如下:

**架構層(必處理,Round 2 #3 議題)**:
1. **Silent divergence(沉默歧異)— 進 #3**:PortfolioStrategy 領班要有 **cross-strategy stale override** — 風控策略被 stale 跳過時 framework 強制全策略降風險。防止「風控失能 + 其他策略繼續滿倉」這種沉默危險場景(整體曝險上升、無人察覺)。**Round 2 #3 必拍**,整合進 PortfolioStrategy 領班議題的 sub-Q。
2. **Stale 權責切 — 進 backlog #4**:資料完整性責任歸 PortfolioStrategy 還是獨立的 Risk Engine?**Round 3 拍 Risk Engine 時會撞**,先註記,Round 3 進場時 Risk Engine 邊界討論必處理。

**V2-B 必驗(實測題)**:
3. **Counter 鋸齒 reset 評估**:Sub-Q2 拍的「連續 N 次 reset」counter 模式,可能因資料偶爾恢復 1 次又斷 → counter 重置 → 永遠不觸發 alert。評估改 **滑動視窗 N-of-M**(過去 M 次裡有 N 次 stale 就 alert,不要求連續)— V2-B 觀測實際 stale 序列形狀再決定。
4. **N 值校準不收斂**:Sub-Q3 拍的 `alert_N_default`(預設 BTC 6 / funding 2 / VIX 3)+ `max_staleness_default` 數字屬於需 V2-B **實測校準** 的參數,可能跑過才知道太鬆或太緊。

**規格補註(已落地)**:
- **M1 stress test 必須 stale-aware**:LUNA / FTX 那種行情 exchange API 大量 timeout 會觸發 stale,**stale 機制本身(framework 跳過 / `on_stale` hook / counter alert)要被 stress test 涵蓋**。已寫入 `glossary.md` M1 條目補註,V2-B M1 實作必須遵守。

---

## #3 PortfolioStrategy 議題(Round 1 carry over,2026-05-24 開始 frame)

承自 Round 1 拍板「兩階層策略(SymbolStrategy + PortfolioStrategy)」遺留的 open question + Round 2 #2C2 watch #1 整合進來。Round 2 在此拍。

**子題清單(待拍板)**:

| 子題 | 內容 | 依賴 |
|---|---|---|
| **#3A** | **always-on 鎖** — Framework 是否強制至少有一個 PortfolioStrategy 在系統裡?(全 disable 是否合法?) | 無依賴,先拍 |
| **#3B** | **Dispatch 順序** — fire 時 PortfolioStrategy 跟 SymbolStrategy 誰先跑?(影響領班 override 時機) | 無依賴 |
| **#3C** | **Cross-strategy stale override**(#2C2 watch #1)— PortfolioStrategy 領班如何偵測旗下風控被 stale 跳過 + 強制全策略降風險的機制 | 依賴 #3B |
| **#3D** | **多 PortfolioStrategy 疊合** — 如果有 N 個 PortfolioStrategy(例 macro overlay + sentiment overlay),最終 cap multiplier 怎麼算? | 無依賴 |

**建議拍板順序**:#3A → #3B → #3D → #3C(把無依賴的先拍完、#3C 留最後因為要看 #3B 結果)。

子題清單 + 順序 2026-05-26 使用者拍板通過。

---

### #3A always-on 鎖 — 拍板 Option E(2026-05-26)

**拍板:Option E — Framework 硬鎖至少 1 個 PortfolioStrategy + 提供 `NoOpPortfolioStrategy` 讓使用者明確 register**

**機制**:
- 系統啟動時 framework 檢查 PortfolioStrategy 數量
- 0 個 → refuse to start(拒絕啟動)
- ≥1 個 → 正常啟動
- Framework 提供內建類別 `NoOpPortfolioStrategy`,行為:永遠回 `cap=1.0` 對所有 symbol(等於「不限制」)
- 使用者**必須明確選擇**:要 portfolio 風控 → 寫自己的 `PortfolioStrategy`;不要 → 明確 register `NoOpPortfolioStrategy`
- NoOp 在系統 log 透明顯示:`[NoOpPortfolio] cap=1.0 all symbols` — debug 時一眼看到「使用者選了不做風控」

**為何 E(非 A/B/C/D)**:
| 否決 option | 理由 |
|---|---|
| A 不鎖 | 新手裸奔風險,framework 沒保護 |
| B 軟鎖 warning | 警告會被忽略(dev 期 N 次後麻木),等於沒鎖 |
| C 硬鎖逼寫 | 沒 escape hatch,開發 / 測試階段煩 |
| D 硬鎖 + framework 內建 baseline | **Framework 替使用者預設業務邏輯**(「合理曝險 100%」是誰定義?),違反「framework 不假設業務」原則 + baseline 隱形 debug 困難 |
| **E**(拍) | Framework 不假設業務 + 強迫使用者表態 + NoOp 透明可 debug + 跟 Round 2 哲學一致(同 #2C1 framework 偵測要使用者 ack / 同 Sub-Q3 default + override pattern) |

**對其他事的影響**:
- **#3C 領班 stale override**:NoOp 模式下沒人當領班 → #3C 拍板時必處理「NoOp 場景 stale 機制」(已標 watch)
- **V2-B 實作**:`NoOpPortfolioStrategy` 是 framework 內建 first-class 類別

**Watch / 未解伏筆**:
- NoOp register 具體 API 形狀(`framework.register(NoOpPortfolioStrategy())` 之類)— V2-B 實作細節,Round 2 不拍

**拍板白話講(2026-05-26 起新規則:每個拍板都附這段)**:
你選了「framework 強迫你做風控選擇」。意思是:系統啟動的時候,framework 會檢查有沒有「全局看盤的人」(PortfolioStrategy)在崗位上。沒有的話 framework 不啟動、直接拒絕你跑。如果你真的不想要這種全局風控(例如只有一個策略、簡單 DCA、不需要 portfolio 級的兜底),那你要**明明白白寫一行**「我選擇不做」— framework 提供一個叫 NoOp 的假人讓你擺到那個位子(假人占著位置但什麼都不做、所有 symbol 都放行不砍倉位)。重點不是「強迫你寫一堆風控」,而是「強迫你做選擇 — 要做還是不要做、自己決定、但不能假裝沒這回事」。好處是以後 debug 翻 log 看到「NoOp 占位」就知道是設計如此、不是 bug 漏了東西。

**下一子軸**:#3B Dispatch 順序 — fire 時 PortfolioStrategy 跟 SymbolStrategy 誰先跑?

---

### #3B Dispatch 順序 — 拍板 Option A(2026-05-26)

**拍板:Option A — SymbolStrategy 先算 target → PortfolioStrategy 看完所有 target 後算 cap → framework 相乘**

**機制(一次 dispatch、單向資訊流)**:
```
fire 響鈴
  │
  ├─ 階段 1:所有 SymbolStrategy 算 target%
  │        (可從 snapshot 讀 macro 欄位:VIX / funding / regime,不盲跑)
  │        → {BTC: 60%, ETH: 30%, ...}
  │
  ├─ 階段 2:所有 PortfolioStrategy 看完「全部 target」後算 cap multiplier
  │        (有全局視角:看得到所有 Symbol 想要什麼 → 整體協調)
  │        → {BTC: 0.5, ETH: 0.5, ...}
  │
  └─ framework 相乘:target × cap = 最終下單目標
           BTC 60% × 0.5 = 30%
```

**為何 A(非 B/C/D/E)**:
| 否決 option | 理由 |
|---|---|
| B(Portfolio 先 → Symbol 後) | Portfolio 算 cap 時看不到 Symbol 想要什麼 → **失去全局視角**,只剩 macro signal(但 macro Symbol 自己從 snapshot 就能讀,B 沒多給東西) |
| C(Portfolio 給 context → Symbol → Portfolio final) | 兩階段 dispatch 心智複雜、framework 變重,收益微小(Symbol 從 snapshot 讀 macro 已達成「知道 context」目的) |
| D(iterative 來回迭代) | 實作惡夢、可能不收斂、不可預測 — 直接否決 |
| E(並行) | Portfolio 看不到 Symbol target → 同 B 失去全局意義 |
| **A**(拍) | Portfolio 級風控本質 = 「看完所有意圖後的整體決定」+ Symbol 從 snapshot 讀 macro 不盲跑 + 一次 dispatch framework 簡單 |

**對其他事的影響**:
- **#3C cross-strategy stale override**:A 下 Portfolio 是後算的 — 若 Portfolio 被 stale 跳過,Symbol 已算完。**#3C 必處理「framework 在 dispatch 前先預判 Portfolio 會不會 stale,是 → fail-safe 強制全策略降風險、不浪費 Symbol 結果」**。#3B 把這責任明確 surface 給 #3C
- **#3D 多 PortfolioStrategy 疊合**:多個 PortfolioStrategy 在「階段 2」並排跑,#3D 拍「各自 cap 怎麼合併」(取最嚴 / 平均 / 連乘)

**Watch / 未解伏筆**:
- Symbol 算時**不能依賴「上次 fire 的 Portfolio cap」**作提示 — 違反「每次 fire 獨立」原則(Portfolio 看新資料可能改變 cap,Symbol 用舊 cap 誤判)
- NoOp 模式:dispatch 順序仍是 A,Portfolio 階段 NoOp 永遠回 `cap=1.0` trivial 過,不阻擋 Symbol 結果

**拍板白話講**:
你選了「出價的人先講、看盤的人後拍板」這個順序。意思是:每次市場有新資料,framework 先讓每個出價策略講「我想要多少 BTC、多少 ETH」,**全部講完之後**,再讓那個全局看盤的人一次看到「大家總共想要什麼」,然後決定要不要打折(例如「欸大家都想重押 BTC,加起來太擠了,全部砍半」)。最後 framework 把「想要的量」乘上「打折比例」算出真正下單的量。

為什麼不反過來讓看盤的人先講?因為**全局看盤的價值就在於「看完大家的意圖再整體調度」** — 你如果讓他先講,他根本還不知道大家想幹嘛,只能看看天氣(macro 大環境)而已,而天氣這件事出價的人自己也看得到,等於白讓他先講。所以「先收集所有意圖、再讓看盤的人整體拍板」才是對的順序。

要注意一點:出價的人講價的時候,雖然還不知道最後會被打幾折,但他**看得到天氣**(從市場快照讀得到 VIX、資金費率這些大環境訊號),所以不是閉著眼睛亂喊,是看著大環境喊。

**下一子軸**:#3D 多 PortfolioStrategy 疊合 — N 個全局看盤的人,各自的打折比例怎麼合併成一個?

---

### #3D 多 PortfolioStrategy 疊合 — 拍板 Option A 取最狠(2026-05-26)

**拍板:Option A — 多個 PortfolioStrategy 對同一 symbol 的 cap multiplier 取最小值(最保守者勝)**

**機制**:
```
階段 2 多個 PortfolioStrategy 並排算:
  macro overlay   → BTC cap = 0.5
  sentiment overlay → BTC cap = 0.7
  ...
framework 合併:final_cap[BTC] = min(0.5, 0.7, ...) = 0.5
最後:target × final_cap = 下單目標
```

**為何 A(取最狠)非 B/C/D/E**:
| option | 規則 | 例(0.5,0.7) | 否決理由 |
|---|---|---|---|
| **A**(拍) | min 取最小 | 0.5 | 守門員天職 = 任一個都能單獨踩剎車 + 可究責 + 單調不爆炸 + 不重複計算相關風險 |
| B 連乘 | 全部相乘 | 0.35 | 對相關訊號重複計算(加密崩盤時 overlay 高度相關,同一事件算兩次)+ 多策略爆縮(三個 0.7 連乘→0.34)+ 究責困難。僅當 overlay 真獨立才合理,加密不成立 |
| C 平均 | mean | 0.6 | **稀釋尖叫** — 把「快逃 0.0」跟「沒事 1.0」混成「逃一半」,風控致命傷,直接否決 |
| D 加權/優先序 | 權重合併 | 視權重 | 誰定權重?framework 又要假設業務(違反 framework-不假設-業務)+ 權重要調參,過度設計 |
| E 取最寬鬆 | max 取最大 | 0.7 | 最樂觀者勝 = 反風控,純對照,否決 |

**A 的四大支柱**:
1. **守門員天職** — 任一 PortfolioStrategy 都能單獨完整踩剎車;C 平均會被淡定訊號稀釋掉緊急訊號
2. **可預測可究責** — 最終 cap 永遠指得出是哪個策略設的(最狠那個);B 連乘的 0.35 說不清誰造成
3. **單調不爆炸** — 多加守門員只會更保守或不變,絕不失控;B 連乘多策略指數爆縮
4. **不重複計算相關風險** — 加密崩盤時各 overlay 常反應同一事件,min 天然免疫;連乘會把同一風險算兩次

**NoOp 場景檢查**:取最狠對 NoOp 天然友善 — NoOp 永遠回 1.0,`min(0.5, 1.0)=0.5` 假人不干擾真守門員;全 NoOp 時 `min(1.0)=1.0` 不限制,與「使用者選擇不做風控」一致 ✓

**對其他事的影響 / Watch**:
- **加權 / 優先序留未來 hook**:現拍取最狠當 framework default,未來若真有「某看盤人該大聲點」需求,再循 Round 2「default + 可 override」老路加,不在 #3D 拍
- **#3C 接力**:#3D 是 #3 倒數第二塊。取最狠合併規則直接餵進 #3C — 「Portfolio 被 stale 跳過時 fail-safe 降風險」本質也往最保守靠,與 min 同向
- **⚠️ overlay 訊號設計紀律(使用者 2026-05-26 補,留 V2-S 各策略 codify 時驗)**:PortfolioStrategy 輸出的 cap 訊號**必須連續可衰退**(continuous & decaying),**禁止 binary latch**(二元卡死 — 風險事件觸發後 cap 鎖在低點不放)。理由:事件型風險(地緣衝突、單日黑天鵝那類)**淡化後 cap 必須能自動鬆回**,否則取最狠(min)會被**過時的高風險訊號綁架** → 持續誤殺正常倉位(明明事件過了還在砍)。**這是 overlay 訊號層的紀律,不是 #3D 合併規則的問題** — min 合併本身正確,但餵進來的訊號若卡死,min 會忠實放大這個卡死。歸屬:**V2-S 各 PortfolioStrategy codify 時逐個驗證其 cap 訊號有 decay 機制**,不是 framework 層能強制的(framework 不知道訊號語意)

**拍板白話講**:
你選了「最擔心的那個守門員說了算」。意思是:如果同時有好幾個全局看盤的人,對同一個 BTC 各喊了不同的打折(一個說打 5 折、一個說打 7 折),framework **聽最狠那個的**(打 5 折)。

為什麼不取平均、不把折扣連乘?

- **不取平均**:因為平均會把「快逃啊」跟「沒事啦」混成「逃一半」。風控最怕這個 — 萬一有個看盤人看到大事不妙喊「全部清倉(0 折)」,你絕不希望另一個淡定的人一句「沒事(不打折)」把這個救命的尖叫稀釋掉變成「賣一半」。守門員的天職就是**任何一個都能單獨把人攔下來**。
- **不連乘**:因為加密市場崩盤的時候,管總經的看盤人跟管情緒的看盤人**常常在看同一場崩盤**。連乘等於把同一個壞消息算兩次(5 折再打 7 折變 3.5 折),把倉位砍過頭。而且要是哪天看盤人變多,連乘會越乘越小、容易失控;取最狠就不會 — 多幾個守門員頂多更保守,不會突然爆掉。

還有個實際好處:以後你看帳本問「為什麼今天 BTC 被打 5 折?」,答案永遠指得出「是那個管總經的看盤人設的(因為他最狠)」。要是用連乘,3.5 折是誰造成的根本講不清。

**下一子軸**:#3C cross-strategy stale override — #3 最後一塊。Portfolio(後算的守門員)若被 stale 資料跳過,framework 怎麼 fail-safe 強制全策略降風險?

---

### #3C cross-strategy stale override — 拍板 Option C 強制降風險(2026-05-26)

**拍板:Option C — PortfolioStrategy 因 stale 缺席時,framework 強制把受影響 symbol 的 cap 壓到保守上限 + 大聲告警 + 套 default + override 老路讓策略自宣告 fallback**

**前提(不投票,地基)**:守門員因 stale 缺席 → **一定**走 V1 notifier Telegram 大聲告警。silent divergence 的觸發點最不能 silent。

**機制**:
```
Framework 偵測 PortfolioStrategy 將因 stale 被跳過
  ├─ 不 dispatch 它(同 #2C2-A)
  ├─ Telegram 大聲告警(地基,不投票)
  └─ 對受影響 symbol 主動壓 cap 到保守上限:
       ├─ 策略事先在 on_stale() hook override → 用策略宣告值
       └─ 沒 override → 用 framework `fallback_cap_default`(V2-B 校準)
     強制壓的 cap 進入 #3D 的 min 合併池 → 跟其他正常守門員取最狠
                                          ↓
                                   最終 final cap
```

**為何 C(非 A/B/D/E)**:
| Option | 否決理由 |
|---|---|
| A 沿用上次 cap | 過時訊號 = binary latch(#3D watch 剛否決過這種病)+ 違反「每次 fire 獨立」 |
| B 凍結加倉 | 只「不升」不「降」,不滿足 watch #1「強制全策略降風險」 |
| D 整輪凍結不交易 | 既有滿倉不解 + 資料常因崩盤才斷 → hold 穿越崩盤最危險(高相關性) |
| E 強制全平倉 | 一次斷線就清倉,whipsaw 致命 + 交易成本爆炸 |
| **C**(拍) | 寧可錯殺(假警報 whipsaw)也不裸著穿越崩盤 + 用 on_stale + min 合併池既有機制 + NoOp 天然豁免 |

**串接前三塊(#3C 是 #3 收官,所有前面拍的都在這裡 converge)**:
- **#3B(Portfolio 後算)** → 守門員缺席會留下沒人管的滿倉 → #3C 補洞
- **#3D(min 合併)** → 強制壓的 cap 進 min 池天然往最保守倒 → 同向
- **#2C2-B Sub-Q1(on_stale hook)** → 直接複用,不增 framework primitive
- **#2C2-B Sub-Q3(default + override)** → fallback_cap 沿用同 pattern
- **#3A(NoOp 假人)** → 無 required data → 不會 stale → **純 NoOp 系統天然豁免**(使用者明確選不做風控,framework 不偷塞降風險)
- **#2C2 watch #1 silent divergence** → 落地完成 ✓

**Watch(留 V2-B 實測 / 校準)**:
1. **`fallback_cap_default` 預設值** — V2-B 校準(同 Sub-Q3 N 值命運),候選範圍 0.3-0.5 保守區
2. **守門員可設更短的 max_staleness 容忍**(它是風控該更敏感)— 沿用 Sub-Q3 機制,自然支援
3. **whipsaw 量化** — 假警報殺低買回成本,V2-B 用 M1 五段崩盤實測(LUNA/FTX API timeout 大量觸發,正好驗這條)— 呼應 M1 stale-aware 規格(已寫進 glossary M1 條目)

**拍板白話講**:

你選了「守門員瞎了 = 假設最壞、主動往安全方向倒」。

當守門員(PortfolioStrategy)要看的資料壞掉了、他沒辦法上場拍板,framework **不裝沒事**(沿用舊折扣)、也**不原地凍住**(假裝沒發生),而是**主動把倉位降一點**到比較安全的水位,同時**打電話通知你**(Telegram)。

降多少?守門員可以**事先在自己程式裡交代**(「我這守門員要是瞎了,請把 BTC 壓到 30%」)。沒交代的話 framework 用一個保守預設值兜底(具體數字 V2-B 跑出來校準)。這跟 Round 2 一路用的 pattern 一樣 — **framework 給合理 default、策略想特別處理可以自己 override**。

這條為什麼必要:你前面拍守門員**後算**(#3B),要是他瞎了 = 整局沒人踩剎車;再加上前面拍**資料壞掉就跳過策略**(#2C2),兩條合起來會撞出「出價的人已經喊滿倉、守門員缺席」這種**沒人管的滿倉**。#3C 就是補這個洞,也是你最早 flag 的 silent divergence 落地。

副作用要承認:資料**只是短暫斷線**(其實沒事),framework 也會主動降倉,可能**白殺低又買回**(whipsaw)。但這是 fail-safe 該付的保費 — **寧可在假警報時白降一點,也不要在真崩盤時裸著穿越**。而且資料常常**就是因為崩盤才斷的**(交易所 API 在 LUNA/FTX 那種行情會大量 timeout),這時候裸著穿越的代價遠遠大於 whipsaw。

兩個豁免要記得:
1. **NoOp 假人模式天然豁免** — 假人沒有要看的資料、不會壞,所以你明確選了「不做風控」的話,framework 不會偷塞這條給你
2. **告警那條不投票** — 守門員瞎掉這件事正是 silent divergence 最危險的觸發點,所以一定 Telegram 大聲喊,它最不能 silent

---

## Round 2 #3 PortfolioStrategy 議題正式收官 ✓

| 子題 | 拍板 | 核心 |
|---|---|---|
| **#3A** always-on 鎖 | Option E | Framework 硬鎖至少 1 個 PortfolioStrategy + NoOp 明確 register |
| **#3B** Dispatch 順序 | Option A | Symbol 先算 → Portfolio 後算 → 相乘 |
| **#3D** 多 PortfolioStrategy 疊合 | Option A 取最狠 | min(cap1, cap2, ...) 最保守者勝 |
| **#3C** cross-strategy stale override | Option C 強制降風險 | 守門員 stale → 強制壓 cap + 告警 + on_stale 可 override |

**一條線拉通的哲學**:framework 強迫使用者表態(#3A)+ 看完所有意圖才拍板(#3B)+ 多守門員取最狠(#3D)+ 守門員瞎了主動降(#3C)= 整套 fail-safe 結構,每一步都往最保守倒、framework 不假設業務、使用者隨時可 override。

**下一子軸**:Round 2 #3 收官,確認 Round 2 範圍是否還有未拍項目,否則進 **Round 2 全段 review pass / 收官 + Round 3 frame**。

---

## #3 PortfolioStrategy always-on 鎖 + 多 PortfolioStrategy 疊合 — TODO

也是 round 1 open question:
- **always-on**:macro overlay 是 risk-layer,直覺 always-on,但會限制 V2-E meta-layer 設計空間
- **疊合演算法**:`min` / `mul` / `sum` 各有道理(min 最保守、mul 對應獨立 risk score 累積、sum 較少用)

---

## 維護

- 每個 #N 子題拍板後,本檔追加日期戳 + 拍板段落
- 全 round 結束時更新 `decisions.md`(prepend 新條目)
- 新術語追加進 `glossary.md`
