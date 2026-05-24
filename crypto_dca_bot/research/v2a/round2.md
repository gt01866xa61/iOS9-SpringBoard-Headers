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

## #3 PortfolioStrategy always-on 鎖 + 多 PortfolioStrategy 疊合 — TODO

也是 round 1 open question:
- **always-on**:macro overlay 是 risk-layer,直覺 always-on,但會限制 V2-E meta-layer 設計空間
- **疊合演算法**:`min` / `mul` / `sum` 各有道理(min 最保守、mul 對應獨立 risk score 累積、sum 較少用)

---

## 維護

- 每個 #N 子題拍板後,本檔追加日期戳 + 拍板段落
- 全 round 結束時更新 `decisions.md`(prepend 新條目)
- 新術語追加進 `glossary.md`
