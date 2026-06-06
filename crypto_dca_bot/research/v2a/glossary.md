# V2-A Glossary(專有名詞白話辭典)

> 給使用者隨時查的詞彙表。Round 1 起涉及的所有專有名詞集中在這。
> 後續每 round 新出現的術語追加進來。
> **找詞:Ctrl+F 搜中文或英文都行。**

---

## 1. 平台架構 / 軟工概念

### Interface(介面)
規定「某類東西應該長什麼樣」的合約。例如「凡是策略,都必須有 `on_bar()` 方法」。Interface 不寫實際邏輯,只定形狀。實際邏輯由 implement(實作)那邊寫。

### Class(類別) vs Function(函式)
- **Class**:有「自己的記性」的物件。例如 `class TrendBTC` 可以記住「我上次進場價是 100」、「我目前 EMA 值是 50000」這類資訊在自己身上。
- **Function**:純粹輸入 → 輸出,沒有記性。每次叫它都是新的。

### Stateful(有狀態) / Stateless(無狀態)
- **有狀態**:策略自己記住內部變數(例:過去 20 根 K 線的移動均值、上次進場價、目前 trailing stop 位置)
- **無狀態**:策略每次決策都從零開始,所有需要的東西都從外部餵進來

Round 1 拍板用 Class + 有狀態(但 state 可以被外部 snapshot 抓走存檔)。

### State(狀態) vs Params(參數)
- **State**:策略 run 起來之後內部變化的東西。例:目前 EMA 值、目前持倉成本、trailing stop 位置。每根 K 線可能變。
- **Params**:策略邏輯設定。例:EMA 用 20 還是 50 根?stop loss 設 2% 還是 5%?Initialize 時注入、跑起來不變。

簡單說:**Params 是設定,State 是運行中的變數**。

### Dataclass / Pydantic
Python 寫「結構化資料」的兩種工具。可以強迫每個欄位都有指定型別。例:
```
@dataclass
class TrendState:
    ema: float           # 必須是浮點數
    entry: float | None  # 浮點數或 None
```
這樣 engine 可以檢查 state 結構正不正確。Round 1 拍板用嚴格 dataclass / pydantic 來定 state schema(state 結構規格)。

### Schema(結構規格)
描述「資料結構長什麼樣」的定義。例:`StateSchema` 規定「state 必須有 ema (float) + entry (float|None) + trailing_stop (float|None) 三個欄位」。Engine 用 schema 來驗證、序列化、版本控制。

### Serialize(序列化) / Snapshot(快照)
把 strategy 內部狀態存到檔案 / 資料庫的動作。後續可以再 restore(還原)回來。M3 backtest lock 需要這個能力 — 才能事後驗證「當時的 state 是什麼」。

### Event-driven(事件驅動) vs Bar-based(K 線驅動)
策略什麼時候做決策:
- **Bar-based**:每根 K 線結束時做一次決策。例:每根 4h K 線收盤後檢查訊號。最常見。
- **Event-driven**:任何事件發生都觸發決策(每個 tick、每筆訂單變化)。更靈活但複雜,給 market-making / arbitrage 用。

V2 預設 bar-based,event-driven 留 round 2/3 視需要再開。

### Lifecycle method(生命週期方法)
策略 class 必須(或可選)實作的方法,engine 在固定時機呼叫。Round 2 #2A 拍板 **4 必 + 1 可選**:

| Method | 必要? | 何時被叫 | 用途 |
|---|---|---|---|
| `__init__(params)` | 必 | 建立時,只一次 | 接 params + 合法性檢查 |
| `required_data()` | 必 | 註冊時,只一次 | 跟 engine 宣告需要什麼資料 |
| `initialize(snapshot)` | 必(可空 `pass`) | 第一根 bar 前,只一次 | 暖機:prime indicators |
| `on_bar(snapshot)` | 必 | 每根 bar | 核心邏輯 → 回 target |
| `reset()` | 可選 | walk-forward 切窗口前 | 清空狀態 |

類比:React 元件規定 `render()` 必要、`componentDidMount()` 可選。Engine 負責叫,你負責寫內容。

### No-op(空實作)
方法明寫但內容空,只有 `pass`。例:無狀態策略不需要暖機,但 lifecycle 鎖 `initialize` 必要 → 明寫 `def initialize(self, snapshot): pass`。代價極小,換 contract 明確 + framework 可插 instrumentation。

### Boilerplate(樣板碼)
為了滿足 framework / 介面而要重複寫的固定樣板程式碼。例如:每個策略都要寫 `def __init__(self, params): self.params = params`。Boilerplate 多 = 開發負擔大,framework 設計要在「規範明確」跟「樣板量少」之間 trade-off。

### Instrumentation(儀器化 / 插樁)
在程式關鍵點插入記錄程式碼(計時、log state、發 metric),讓系統可以被觀察與診斷。例:Framework 在每個策略的 `initialize` 前後計時、log state snapshot → 可看出哪個策略暖機特別慢、哪個 state 不正常。Lifecycle 必要 method 越明確,插 instrumentation 越容易。

### Prime indicators(暖機指標)
策略要算的技術指標(EMA / 滾動平均 / RSI 等)通常需要 N 根歷史資料才能算出第一個值。例:rolling_21 funding 平均要 21 個 funding 期間才有第一個輸出。暖機(prime)= 在策略開始決策前,先把歷史餵進去算到指標就緒狀態。

### Walk-forward window(walk-forward 窗口)
M2 walk-forward 驗證每次切到下個 IS(訓練)/ OOS(測試)窗口時,需要把策略 state 清掉(因為新窗口可能是不同 regime,舊 state 帶過去會洩漏)。這就是 `reset()` 存在的時機。

### Event-driven(事件驅動)
Engine 等「事件」(新資料到達)發生時才行動,而非按固定時鐘輪詢所有策略。Round 2 #2B 拍板:V2 engine event-driven、每筆新資料只 fire 有 subscribe 的策略。相對概念是 polling(輪詢)/ synchronous bar tick(同步打點)— 每最細粒度 bar 觸發所有策略,V2 不採用。

### Dispatch table(派發表)
Engine 內部一張表,記錄「哪個 data source 來新資料 → 該 fire 哪些策略」。策略註冊時透過 `required_data()` 宣告需要什麼資料 + 哪些事件作觸發,engine 寫進 dispatch table。Event-driven 架構的核心資料結構。

### Last known value(最新已知值)
策略被 fire 時 snapshot 中的非主觸發 field,一律取「最新已知值」(可能來自前一個事件、可能是幾分鐘前的 last close)。不等資料同步、不空缺、可能 stale。每個 field 帶 `timestamp` 讓策略自己判斷 staleness 容忍度。

### Stale data(過時資料)
資料雖有值但時戳太舊,不一定可信。例:macro overlay 用 VIX 但 VIX feed 死了 3 天,snapshot 仍能拿到 last known value(3 天前的 VIX),但策略要決定是否信任。每個策略對 staleness 的容忍門檻不同 — 由策略內部或 framework convention 處理。

### Event log(事件記錄)
Engine 把所有 lifecycle event(initialize / on_bar / reset)+ 跨策略觸發時序寫進一條統一的時間序記錄。Debug / 回放 / paper-vs-backtest 對照都靠它當 single source of truth(單一真實來源)。V2 把它掛在 `initialize` 的 instrumentation hook(#2A 鎖板的副產品)。

### Subscribe(訂閱)
策略宣告「我關心哪些 data event 作觸發」的動作。Pub/sub(發布-訂閱)模式裡的訂閱端。Funding skew subscribe `funding_rate_8h`,trend subscribe `kline_1h`,macro overlay subscribe `vix_daily` + `dxy_daily`。Engine 是 publisher,策略是 subscriber。

### is_ready() — 就緒檢查(暖機完了沒)
Round 2 #2C1 拍板新增的 lifecycle 方法。策略告訴 engine「我準備好開始下決策了嗎?」回 `True` / `False`。
- 必要性:**可選**(default = framework 提供 buffer-based 實作 — 暖機 buffer 滿到 `min_history` 即 ready)
- 三條硬約束(寫進 lifecycle 規格):
  1. Framework 強制 log `is_ready` 每次回傳;連續 N 次 false 告警
  2. `is_ready()` **只能看歷史 buffer**(暫存區),不能看當前最新值 → 鎖 backtest/paper/live 三模式同 timestamp 結果必相同
  3. M5 paper-vs-backtest 對照納入 `is_ready` 觸發次數比對

### Override(覆寫)
子類別重寫父類別已有的 method。例:framework 提供 default `is_ready()`(看 buffer 是否滿),特殊策略可覆寫自己的版本(例如:同時要 BTC trend + ETH trend 都暖完才回 true)。

### on_stale() — stale 通知鉤子
Round 2 #2C2-B Sub-Q1 拍板新增的 lifecycle 方法。Framework 偵測到 critical data stale → 跳過 `on_bar` 之後,呼叫 `on_stale(stale_fields)` 通知策略「這次被跳了、是因為這幾個 field 過時」。
- 必要性:**可選**(base class default = no-op,寫了等於沒寫)
- 主要用途:風控策略(stale 時主動降部位)、fallback 策略(切備援資料源)、ensemble(re-weight 其他資料)
- 多數策略(long-only DCA、單純 trend)不需要 override

### Hook(鉤子)
Framework 預留給策略 / 外部 code「插入自訂行為」的接點。例:`initialize` 是 instrumentation hook(掛 event log),`on_stale` 是 stale 通知 hook。Hook 通常 default 是 no-op,需要的人才 override。

### Alert(警報) vs Log(記錄) vs Hook(鉤子)
三種「事情發生了要通知誰」的機制,目標不同:
- **Log**:寫進 event log,**被動等人查**。例:每次 dispatch 寫一行 `is_ready` 回傳值、每次 stale 跳過寫一行記錄。沒人關注時不打擾。
- **Alert**:**主動推播** 給使用者(走 V1 notifier / Telegram)。例:連續 stale N 次、連續 is_ready false N 次。代表「現在就要看一下」。
- **Hook**:給**策略**(程式自己)插入處理邏輯的接點。例:`on_stale` 讓風控策略 stale 時降部位。代表「策略要不要做點什麼」。
心智:Log = 給 debug,Alert = 給人,Hook = 給策略。

### Counter + 門檻 pattern(連續觀察累積)
Framework 通用模式:某事件連續發生時 counter++、發生「相反事件」時 counter 重設為 0、counter 達門檻 N 時觸發行為(通常是 alert)。
- #2C1 防呆 #1:`is_ready` 連續 N 次 false → alert
- #2C2-B Sub-Q2:某 field 連續 N 次 stale → alert
心智模型統一 — 兩處共用同一個 framework primitive,使用者只記一個 pattern。N 值通常 V2-B 實測校準。

### max_staleness(過時門檻)
某 field 的「資料超過多久未更新就算 stale」設定值。例:BTC 1h K 線 `max_staleness=2h`(超過 2h 沒新資料 → snapshot 中該 field 被判 stale)。Round 2 #2C2-B Sub-Q3 拍板,寫在 framework data source registry per-source 作 default,策略 `required_data()` 可 override 寫嚴格門檻(風控用)。

### Data source registry(資料源登錄表)
Framework 維護的 single source of truth(單一真實來源),集中宣告每個資料源的 `cadence`(預期 fire 頻率)、`max_staleness_default`(預設過時門檻)、`alert_N_default`(預設連續 stale 警報次數)。新增資料源改一處、不污染策略 code。Round 2 #2C2-B Sub-Q3 拍板,跟「default + 策略可 override」雙層機制配合。

### Default + override pattern(預設可特化)
Framework 普遍採用的設計模式:framework 提供一個合理 default(覆蓋多數情境)+ 策略可在自己內部 override(處理特殊需求)。心智:**多數人無感、特殊人有 hook**。Round 2 反覆出現:
- #2C1 `is_ready()`:framework 給 buffer-based default、策略可 override
- Sub-Q1 `on_stale()`:base class no-op default、策略可 override
- Sub-Q3 `max_staleness` / `alert_N`:registry per-source default、策略可 override
跟 boilerplate(每人重複寫)+ 強耦合(framework 寫死)兩個極端對立的折衷。

### Boilerplate vs API 統一(設計 trade-off)
- Boilerplate:策略開發者要重複寫的樣板(壞,愈少愈好)
- API 統一:framework 提供 default + 策略可特化(好,大家走同一條路)

Round 2 #2C1 選 γ 混合派:framework default 覆蓋多數情境(0 boilerplate),策略可 override(API 統一不破),防呆機制保證 override 不會炸。是這條 trade-off 的標準解。

### Pipeline(管線)
資料 / 訊號從一頭流到另一頭的處理鏈。V2 執行管線(per bar)=
SymbolStrategy 出 target → 加總 → PortfolioStrategy 出 cap → 合併 → engine 算下單。

### Meta-layer(元層 / 上層)
管理多策略的上層邏輯。決定「現在哪個策略該活躍、哪個該休眠、各分配多少資金」。V2-E ensemble 階段做。

---

## 2. 策略 / 交易基本概念

### Symbol(交易對)
要交易的標的代號。例:BTC、ETH、BTC/USDT。

### Bar(K 線)
一段時間內的價格資訊整合成的一根棒。包含開盤價 / 最高價 / 最低價 / 收盤價 / 成交量(OHLCV)。例:4h bar = 4 小時內的這 5 個數字。

### Long(做多) / Short(做空)
- **Long**:買進、賭漲。賺價差。
- **Short**:賣空、賭跌。先借幣賣出、之後低價買回還。**V2 邊界鎖了不允許**(因為涉及借貸 / 衍生品)。

### Spot(現貨) / Spot margin(現貨保證金) / Derivatives(衍生品)
- **Spot**:直接買賣現貨。買 1 BTC 就真的有 1 BTC。沒有借貸、沒有合約。
- **Spot margin**:跟交易所借幣後做交易。算現貨但有借貸成本 + 可被強制平倉。
- **Derivatives**:期貨、永續合約、選擇權等。能放大 leverage(槓桿)。

V2 邊界:**只玩 spot,不上 spot margin / derivatives**。所以「short」實質做不了。

### Long-only(只能做多)
V2 鎖定 long-only,意思是策略輸出**不能是負數**(不能表達「賣空」)。target 範圍 `[0, 1]` = 0% 到 100% 滿倉,不能 -50%(空頭部位)。

### Trend-following(趨勢追蹤)
「漲了再跟漲、跌了再跟跌」的策略風格。例:價格突破 50 日高 → 進場。等趨勢結束才出場。**起步策略池 #1**。

### Mean-reversion(均值回歸)
「偏離歷史均值的東西會回歸」的策略風格。例:BTC/ETH 比值正常 15,衝到 18,賭它會跌回 15。
**Long-only 限制下變弱**:原版要 long BTC + short ETH 賭 ratio 收斂;現貨只能做變體「ratio 偏高就減 BTC 配重加 ETH」,效果不如真 spread trade。Round 1 決議換掉,round 2 找替代。

### Macro overlay(宏觀風控層)
不是真策略,是**減倉保險**。例:VIX 恐慌指數飆高 → 全 risk asset 部位乘 0.5(砍半)。在 V2 對應 `PortfolioStrategy`,輸出是 per-symbol cap multiplier(上限乘數)。**起步策略池 #3**。

### Spread trade(價差交易)
兩個相關標的反向同時做:long A + short B,賭它們之間的價差收斂或擴大。長期 hedge 掉市場大方向的風險。**現貨 long-only 做不了**。

### Rebalance(重新配重)
不開新部位、只調整現有部位之間的比例。例:原本 BTC 60% + ETH 40%,改成 BTC 40% + ETH 60%。需要先有兩邊部位才有空間調。

### Target position(目標部位) / Target weight(目標權重)
策略告訴 engine「我想要這個 symbol 占資金 X%」。Round 1 拍板 SymbolStrategy 輸出這個。例:`{"BTC": 0.6, "ETH": 0.3}` = BTC 占 60%、ETH 占 30%。

### Allocated capital(配置資金)
Meta-layer 給每個策略分到的資金。例:策略 A 拿到 1000 USDT、策略 B 拿到 500 USDT。策略內部的 target % 是相對於自己的 allocated capital,不是總資金。

### Signal(訊號)
策略輸出的「該怎麼動」的簡短指示。最常見三種:BUY / SELL / HOLD。Round 1 沒選這種形狀(選 target position,語意更精確)。

### Order(下單指令)
最具體的形式:「以市價買 0.05 BTC」這種能直接送到交易所執行的指令。

### Cap / cap multiplier(上限 / 上限乘數)
PortfolioStrategy 的輸出。每個 symbol 一個介於 0-1 的數,表示「最多允許達意圖的多少%」。例:`{"BTC": 1.0, "ETH": 0.3}` = BTC 不限、ETH 上限 30%。

### Slippage(滑點)
下單時實際成交價跟你預期成交價的差。例:你以為市價買得到 50000,實際成交 50050。市場越動、單越大、滑點越多。M5 paper-vs-backtest 驗證會看這個。

### Fill rate(成交率)
下的單裡實際成交的比例。Limit order(限價單)可能掛了沒成交。M5 paper-vs-backtest 容忍門檻 ≤ 10%。

### Fee(手續費)
交易所抽的手續費。Binance 現貨約 0.1% per trade。Backtest 必須算進去否則績效虛胖。

### Sizing(下單量計算)
從「target %」算到「實際下單量(USDT 或 BTC 數)」的過程。要考慮現有部位、可用資金、最小下單量、手續費。Engine 負責,不是策略的事。

### Perpetual futures(永續合約)
沒有到期日的衍生品合約。為了讓永續價格不偏離現貨價,交易所每 8 小時收一筆「funding rate(資金費率)」讓多空互付。**V2 邊界鎖不交易永續**,但可以**只把永續的資料當訊號用**(funding rate skew 策略就是這樣)。

### Funding rate(資金費率)
永續合約每 8 小時(Binance 是 00 / 08 / 16 UTC 結算)多空互付的費率,單位是「每 8h 的 %」。
- 永續價 > 現貨價(多頭擁擠)→ funding 是正 → 多方付給空方
- 永續價 < 現貨價(空頭擁擠)→ funding 是負 → 空方付給多方

例:funding = 0.01% / 8h ≈ 年化 11% carry。

### Funding rate skew(資金費率偏度)
持續高 funding(例如連 7 天滾動平均 > 0.03% / 8h)≈ 多頭部位過度擁擠,歷史上常出現在動能末端、修正前。**Round 2 拍板策略池 #2**:funding 持續高 → 縮 BTC/ETH 現貨多單;funding 持續低/負 → 滿倉。

### Short squeeze(空頭擠壓)
價格急漲時空頭被迫平倉(買回標的)→ 推升價格 → 更多空頭被迫平倉的連鎖。期間 funding 通常極端負。

### BTC halving(BTC 減半) / Halving cycle(減半週期)
BTC 每挖 21 萬個區塊(約 4 年)區塊獎勵減半,歷史四次:2012-11-28 / 2016-07-09 / 2020-05-11 / 2024-04-19。歷史上減半後 12-24 個月通常出現週期高點。**這是 BTC 特有結構,ETH 無此事**(但市場常把 BTC 拉著 ETH 同步動)。Round 2 評估後,calendar 策略不當主策略(N=2 樣本問題),保留 PortfolioStrategy 子訊號候選。

### Rolling average(滾動平均)
固定窗口長度的移動平均。例:過去 21 個 8h funding 期間的平均 = 過去 7 天 funding 平均。每多一筆新資料,窗口往前推一格、最舊那筆掉出去。常用來把雜訊濾掉、看趨勢。

### Linear interpolation(線性插值)
兩端有固定值、中間按比例算。例:funding 在 `low_threshold` (0.005%) 時 target = 1.0,在 `high_threshold` (0.03%) 時 target = 0.0,中間 funding 0.02% 時 target = (0.03 - 0.02) / (0.03 - 0.005) = 0.4。比 if-else 階梯式平滑,部位變動較連續、訊號雜訊較不易引爆下單。

### Dead band(不動區)
訊號變動小於某門檻時部位不動,只有跨過門檻才調整。例:`dead_band = 0.002%`,funding 從 0.010% 漂到 0.011% 不動,漂到 0.013% 才動。用來防止訊號雜訊頻繁觸發下單(over-trade、燒手續費)。Round 1 review pass 衍生的「執行層 cooling tool」雛形之一。

### Catch a falling knife(抓刀)
標的急跌時進場,結果跌勢延續被套牢的情境。中文交易俗語「接刀」。Funding rate skew 在崩盤期極端負 funding 滿倉時就有抓刀風險。

---

## 3. 統計 / 驗證 / 績效

### Backtest(回測)
用歷史資料模擬策略 — 假裝時光倒流,如果當時跑這個策略結果會怎樣?V2-B 階段做。**輸出**:歷史績效曲線。**陷阱**:容易 overfitting(下面解釋)。

### Walk-forward(滾動樣本外驗證)
比純 backtest 嚴格的方法。把歷史切成 IS(訓練段)+ OOS(驗證段)交替滾動。
- **IS (In-Sample)**:用這段訓練 / 調參。V2-A 設定 30 個月。
- **OOS (Out-of-Sample)**:用 IS 學到的東西在這段測,看績效。V2-A 設定 3 個月。
- **重訓**:每 3 個月把 IS 視窗往前推、重新訓練。
- **WFE (Walk-Forward Efficiency,樣本外效率)**:OOS 績效 ÷ IS 績效。> 50% 才算過關。低於 50% = 模型只記住歷史、不會泛化。

### Overfit / Overfitting(過度擬合)
模型「死背」歷史資料的細節 → 在歷史上表現超好、在新資料表現崩潰。量化界第一大陷阱。Walk-forward 是對付這個的工具。

### Retrofit(事後改邏輯)
跑完 backtest 看結果不好,**回頭改策略參數讓歷史看起來綠**。M3 lock 機制就是防這個 — backtest 結果用 timestamp + commit hash 釘死,策略邏輯改了必須換新編號(strategy_v1 → strategy_v2)。

### Alpha(超額報酬)
策略相對於「無腦持有(buy-and-hold)」多賺到的部分。沒 alpha = 不如直接買著放。

### Sharpe ratio(夏普比率)
報酬除以波動度。越高表示「賺得平穩」。> 1 還行、> 2 不錯、> 3 罕見且通常可疑(可能有 overfit)。

### Drawdown(回撤)
從歷史高點到後續低點的跌幅。例:從 10000 跌到 7000,drawdown 30%。
- **Max drawdown**:歷史最大回撤
- **High water mark(高水位線)**:策略歷史最高淨值,drawdown brake 用這個算

### Stress-test(壓力測試)
拿歷史最爛幾段時期(崩盤 / 危機 / 黑天鵝)強迫策略跑一遍,看撐不撐得住。V2 M1 鎖了 5 段:COVID 2020-03 / China crackdown 2021-05 / LUNA 2022-05 / FTX 2022-11 / 日圓 carry unwind 2024-08-05。

### Crisis correlation(危機共振)
平常 risk asset 之間相關性可能 0.3-0.5,但崩盤時所有 risk asset 一起跌 → 相關性 → 1。意思是「分散投資在危機時失效」。設計策略池要避免崩盤期所有策略同向虧。

### Pearson correlation(皮爾遜相關係數)
兩個東西同向動的程度。+1 = 完全同向、0 = 無關、-1 = 完全反向。V2 設計目標:策略兩兩 PnL 相關性 ≤ 0.5。

### Regime(市況) / Regime shift(市況轉換) / Regime detection(市況辨識)
市場處於哪種「氣候」:牛市 / 熊市 / 盤整 / 高波動 / 低波動 / 危機。Regime 變了同一個策略可能從賺變賠。**V2-E ensemble 就是做這個** — 偵測目前是哪種 regime、切到適合該 regime 的策略。

### Ensemble(集成)
多策略加總 / 切換。V2-E 階段做。目標:整體 Sharpe 比最強單一策略還高。

### Paper trading(紙上交易)
用即時資料模擬下單,但不真的下單。M4 要求 ≥ 60 個交易日(不是自然日)。
**為什麼要做**:backtest 用歷史資料、paper trading 用即時資料 — 兩者有結構性差異(資料延遲、流動性、心理測試)。

### Paper vs Backtest(紙上 vs 回測對照)
M5 規定:策略過 paper trading 後跟 backtest 結果並排比,Sharpe 差距 ≤ 30%、Fill rate 差距 ≤ 10%。差太大 = backtest 不貼近實盤,reject。

---

## 4. V2 框架專有

### V2-A / V2-B / V2-S / V2-T / V2-E / V2-D
V2 builder 階段代號(蓋房子比喻):
- **V2-A** = Architecture 架構(畫設計圖)← 現在
- **V2-B** = Backtest 回測引擎(蓋廚房)
- **V2-S1..N** = Strategy 1..N codify(蓋房間)
- **V2-T1..N** = Test 1..N(試住房間)
- **V2-E** = Ensemble 集成(中央管控)
- **V2-D** = Deploy 部署(正式入住)

### M1 / M2 / M3 / M4 / M5
V2 寫死的 5 條 validation 標準:
- **M1**:V2-B 內建 5 段崩盤 stress-test。**規格補註(2026-05-24)**:M1 必須 **stale-aware** — LUNA / FTX 那種行情 exchange API 大量 timeout 會觸發 framework stale 機制(Round 2 #2C2-A/B 拍板),M1 stress test 不只測策略邏輯,**framework 對 stale 的反應(跳過 / `on_stale` hook / counter alert)本身也要被涵蓋**
- **M2**:Walk-forward 規格(IS 30 個月 / OOS 3 個月 / WFE > 50%)
- **M3**:Backtest 結果 lock(timestamp + commit hash,策略改 = 新編號)
- **M4**:Paper trading ≥ 60 交易日
- **M5**:Paper vs backtest 容忍門檻(Sharpe 差 ≤ 30%、Fill 差 ≤ 10%)

### SymbolStrategy / PortfolioStrategy
Round 1 拍板的雙 interface:
- **SymbolStrategy**:處理 per-symbol 或 pair 的部位意圖。輸出 `{symbol: target%}`。
- **PortfolioStrategy**:處理 portfolio-level 風控。輸出 `{symbol: cap multiplier}`。

### cap multiplier(上限放大器)
PortfolioStrategy 對每個 symbol 輸出的 0-1 之間倍率,乘上 SymbolStrategy 的 target%,得到最後下單目標。**日常比喻**:SymbolStrategy 是「想買多少」、cap multiplier 是「全局看盤的人允許你買多少比例」。
- `cap=1.0` = 放行不限制
- `cap=0.5` = 砍半(SymbolStrategy 想 60% → 實際 30%)
- `cap=0.0` = 強制清倉
Round 1 拍板,Round 2 #3A 用 NoOp 配套(NoOp 永遠 cap=1.0)。

### NoOpPortfolioStrategy(NoOp 假人領班)
Framework 內建的「明確不做事」版本的 PortfolioStrategy,行為:永遠對所有 symbol 回 `cap=1.0`(不限制)。**日常比喻**:擺一個假人坐在「全局看盤的人」那張椅子上 — 椅子有人占著,但那個人什麼都不做、所有交易都放行。
- **存在目的**:Round 2 #3A 拍 framework 硬鎖 ≥1 個 PortfolioStrategy。使用者若**真的不想要** portfolio 級風控,必須**明確 register NoOpPortfolioStrategy**(等於簽字「我選擇不做」),而不是默默裸奔
- **log 透明**:系統 log 顯示 `[NoOpPortfolio] cap=1.0 all symbols`,debug 時一眼看到「設計如此」
- 跟「framework 內建 baseline 替使用者預設風控」(被否決的 Option D)區別:NoOp **不假設業務邏輯**,只是占位

### Risk Engine(保全總管,組合級風控一級元件)
Round 3 R3-①-a 拍板的新一級架構元件,跟 SymbolStrategy / PortfolioStrategy 並列。職責:**組合級風控三件事**(portfolio-gross 總曝險上限 / M6 vol-targeting sizing / 資料完整性最終把關 stale 終責)。**跟守門員(PortfolioStrategy)的分工**:守門員管「逐幣打折」(per-symbol cap),Risk Engine 管「整桌總帳」(看全局)。**日常比喻**:守門員=每道菜的份量控制;Risk Engine=整桌總預算上限 + 出事應變總管。對齊團隊頭號共識「風險管理 > 預測」— 風控值得一級架構公民地位。內部結構 / 跟現有 sizing stage 合併與否 / 看什麼算 gross / 是否可插拔留 R3-①-bc 一併拍。

### framework 級護欄 vs 策略級風控(安全底線 vs 業務判斷)
Round 3 R3-①-bc Block 1 拍板確立的分層:
- **策略級風控**(PortfolioStrategy / 守門員):**業務判斷**,使用者可選不做(擺 NoOp 假人)。framework 不假設業務 → 允許關掉
- **framework 級護欄**(Risk Engine):**安全底線**,使用者**不可關不可換不可 NoOp**,類比 V1 `circuit_breaker`。always-on
**關鍵哲學區分**(解「framework 不假設業務」表面衝突):framework 不假設**業務語意**(gross 上限定 50% 還 70% 留使用者),但**可寫死安全機制的存在性**(有沒有「總曝險上限」這個概念 framework 說了算:一定有)。**日常比喻**:餐廳可以自己決定菜單口味(業務),但「廚房一定要有滅火器」是法規寫死的(安全底線),老闆不能說「我選擇不裝」。

### portfolio-gross exposure(總曝險,組合級風險)
「你帳戶裡所有部位**加起來**占總資金多少 %」這個數字。例:BTC 40% + ETH 40% = gross 80%。跟 per-symbol cap(每個幣各自的份量)是**兩個不同維度** — 守門員逐幣 min 模型裝不下總帳。**日常比喻**:gross=整桌菜總共上了多少分量(看全局);per-symbol=每道菜的份量(看單道)。Round 2 #3C 補釘 watch 標記 → Round 3 R3-①-a 拍歸 Risk Engine 管。確切門檻數字(如 ≤ 50%)留 V2-B 校準。

### vol-targeting(波動目標 / 按市場晃動調倉)
Roadmap M6 規格:**部位大小不准用固定比例,要按市場晃動程度調**。市場越晃 → 單一部位放越小,讓**整體風險水位穩定**(而不是固定下注 60%、平靜時 OK 但亂世會爆)。**日常比喻**:開車時雨天車距拉開、晴天可以縮短 — 不是固定車距,是「按路況調」讓**事故風險穩定**。Round 3 R3-①-a 拍歸 Risk Engine 落地(實際公式選型 V2-B 校準)。對應團隊共識「風險管理 > 預測」。

### 雜物抽屜 anti-pattern(萬能間反設計)
一個模組塞太多不相關的職責,變誰都看不懂的萬能間。Round 3 R3-①-a 否決 Option B(把 gross + sizing + vol-targeting + stale 把關全塞進現有 sizing stage)的核心理由 — 「算量站」本來只做 USDT 換算,塞進 4 件不相關的事會變雜物抽屜,違反 Round 1 拍的「每個元件內部簡單、一句話講得清」簡單派。**日常比喻**:那個家裡什麼都塞的「雜物間」,要找東西永遠翻不到。設計哲學:**寧可多開一個專責盒子,也不讓任何盒子變雜物抽屜**。

### 策略缺席統一模型(stale + crash 共用)
Round 2 #2D 拍板的設計哲學:策略「不能用」這件事,framework **不分原因**,統一當「這輪缺席」處理。原因可以是資料 stale(#2C2)、可以是程式 crash(#2D),framework 走**同一條路徑**:出價策略缺席就跳過、守門員缺席就 fail-safe 降風險。**日常比喻**:不管員工生病、家裡有事、還是手機沒電,公司排班系統一律當「今天請假」,不用為每種理由各寫一套規矩。**好處**:零新 framework primitive,#2C2 + #3C 已蓋好的機制 #2D 直接複用。**配套**:crash 是 persistent(每輪會再爆,不像 stale 是 transient I/O),所以**靠 crash counter 連續 N 次永久停用收尾**,counter 跟 #2C2-B Sub-Q2 的 stale alert counter 共用同 framework primitive。

### Crash counter + 永久停用(supervision pattern)
Round 2 #2D 拍板:策略連續 crash 達 N 次 → framework 永久停用該策略 + Telegram 告警。**復用 #2C2-B Sub-Q2 的 Counter + 門檻 pattern**(連續觀察 N 次累積觸發升級)。N 走 default + override 老路,per-strategy 可設(守門員可設 N=1 一次就停)。**日常比喻**:員工連續曠職達上限就開除,不問理由。**漂亮的湧現(emergent)**:守門員被永久停用後若數量降到 0,撞 #3A always-on 鎖 → framework 自動停機。「守門員壞了最終會停整台」**不是顯式規則,是 B + #3A 組合自然長出來的**,比顯式寫一條「守門員 crash 立刻停整台」更溫和 + 更不脆。

### Supervision(故障隔離 + 限度內容忍 + 達閾值升級)
工業界常見的容錯模式:單元出錯時隔離(不全停)、給一定次數重試 / 容忍機會、達閾值才升級到永久停用 / 停機。Round 2 #2D 拍板採此模式,但**零新 primitive** — 全靠 #2C2 + #3C + #2C2-B Sub-Q2 既有機制組裝。Round 2 反覆出現的 framework 哲學:**機制盡量少 + 組合自然湧現複雜行為**。

### silent divergence(沉默的歧異)
Round 2 #2C2 watch #1 + #3C 落地處理的危險場景:**風控失能,但別的策略繼續滿倉跑 → 整體曝險悄悄飆高 → 沒人察覺**。**日常比喻**:守門員突然不見了(被資料 stale 跳過),其他人沒注意到、繼續正常工作,結果守不住的時候才發現。「沉默」= 沒有任何明顯訊號告訴你風控失能。Round 2 #3C 拍 Option C 補:守門員瞎時 framework 強制降倉 + 大聲告警(讓它不再 silent)。

### fail-safe(往安全倒)
設計哲學:當系統處於不確定狀態(資料壞、訊號缺、決策者瞎)時,**預設往最保守 / 最安全的方向倒**,而不是裝沒事繼續跑。**日常比喻**:電梯感應器壞了 → 寧可停在原樓不開門(可能讓人等),也不要打開可能在井道半空中的門。Round 2 #3C 拍板的核心 — 守門員瞎了主動降倉(寧可白殺低 whipsaw)而非裸著穿越崩盤。

### whipsaw(殺低又買回的鋸齒)
資料短暫斷線觸發 fail-safe 降倉,但其實沒事 → 資料恢復後又買回 → 來回交易但實際沒受益,只付了**交易成本 + 滑價**。**日常比喻**:虛驚一場下車又上車,車費白付兩趟。Round 2 #3C 承認這是 fail-safe 不可避免的副作用(保費),理由:真崩盤裸著穿越的代價遠大於假警報 whipsaw + 資料常因崩盤才斷(LUNA/FTX 期間 API timeout)→ 相關性決定哪邊賠得大。V2-B M1 五段崩盤實測量化。

### fallback_cap_default(守門員瞎時的兜底折扣)
Round 2 #3C 拍板的 framework 預設值:PortfolioStrategy 因 stale 缺席時,framework 主動把受影響 symbol 的 cap 壓到此預設(候選 0.3-0.5 保守區,V2-B 校準)。策略可在 `on_stale()` hook 內 override(策略自知語意,自己交代降多少)。沿用 Round 2 反覆出現的 default + override pattern,framework 不假設業務語意。

### 連續可衰退訊號 vs binary latch(overlay 訊號紀律)
Round 2 #3D watch(使用者 2026-05-26 補,留 V2-S codify 時驗):PortfolioStrategy 的 cap 訊號設計紀律。
- **連續可衰退(continuous & decaying)**:cap 隨風險升降平滑變化,風險事件淡化後 cap **自動鬆回** 1.0。要的。
- **binary latch(二元卡死)**:風險一觸發 cap 鎖在低點不放(像跳閘的開關卡住)。**禁止**。
**日常比喻**:守門員攔人後要會「看情況放行」,不能攔了就**僵在那裡永遠不讓過**。**為什麼重要**:#3D 取最狠(min)會忠實放大任何一個卡死的訊號 — 地緣衝突那種事件型風險過了之後,若某 overlay 的 cap 還卡在低點,min 就被這個過時訊號綁架、持續誤殺正常倉位。**這是訊號層紀律不是合併規則問題**(min 本身正確),framework 管不到(不懂訊號語意),歸 V2-S 各策略 codify 時逐個驗 decay 機制。

### cap 合併規則 — 取最狠(min)
Round 2 #3D 拍板:多個 PortfolioStrategy 對同一 symbol 各給 cap multiplier(打折比例)時,framework 取**最小值**(最保守者勝)合併成一個。**日常比喻**:好幾個守門員,聽**最擔心的那個**說了算。否決平均(會稀釋緊急訊號)、否決連乘(對相關風險重複計算 + 多策略爆縮)。四大支柱:守門員天職任一可單獨剎車 / 可究責(指得出誰最狠)/ 單調不爆炸 / 不重複計算相關風險。NoOp(永遠 1.0)在 min 下天然不干擾。

### fail-safe cap 的合併位置 — 丟進 min 池 vs 二次施加(#3C × #3D 補釘)
Round 2 #3C review pass 撞點(2026-05-26 拍):守門員因 stale 缺席時的 fail-safe 值,架構上**當成 cap 候選丟進 #3D 的 min 池**(`final = min(正常 cap..., 缺席者 fallback)`),**不是 min 算完後 framework 二次施加(override)**。兩者**只在 fail-safe 值比現場 cap 寬鬆時分岔** — 那時 override 會讓「瞎掉守門員的通用兜底」蓋掉「明眼守門員看到危險喊的緊 cap」、反而**放寬**倉位,違反取最狠地基。**日常比喻**:瞎子的萬用預設,不准蓋過明眼人的真實警報。拍 min 池 = fail-safe **只能往緊、永遠不能放寬**(單調性)。實作後果:#3C 不是獨立的「事後補刀層」,stale 守門員就只是「這輪改用 fallback_cap 當它的產出」,走同一條 min 合併線。**告警與數值效果解耦** — 就算 fallback 在 min 裡沒起作用(別人更狠),告警照發(綁「守門員瞎掉」事件)。

### portfolio-gross cap(總曝險約束,#3D per-symbol 模型裝不下)
「守門員瞎 → 砍**整體總曝險**(不分幣,例全組合 gross ≤ 50%)」這種**總量級**約束,跟 #3D 的 **per-symbol cap**(逐幣各自打折)是兩種不同維度。#3D 的 per-symbol min 模型**裝不下**總量級約束。**日常比喻**:per-symbol 是「每道菜各自限量」,gross 是「整桌總預算上限」,兩個不是同一回事。Round 2 #3C review pass 標記為 **Round 3 Risk Engine 未模型化維度**,歸 backlog #4 一併處理。

### 雙層節流(策略訊號級 + framework 執行政策層)
Round 3 R3-③ 拍板的過度交易防線設計:過度交易有**兩種抖**,要兩個地方各擋一種:
- **策略訊號級節流**(funding `dead_band` / overlay 連續可衰退 #3D 等):擋「**訊號自己抖**」— 策略最懂自己訊號該多鈍,屬訊號語意
- **framework 執行政策層**(新元件,位於算量站後、送單前):擋「**聚合後才冒出的抖**」— 守門員 cap + Risk Engine vol-targeting + 多策略 capital 權重每 bar 都在變,加總後的最終 order 會抖,只有 framework 看得到。能力含 dead-band(差幅<threshold 不送單)/ cooling(剛調過冷卻一段)/ regime hook(預留 V2-E)
**日常比喻**:策略級擋的是「溫度該不該變」(冷氣判斷),framework 執行層擋的是「就算溫度該變也別每 0.1 度開關一次」(開關紀律)。兩種抖不同地方產生,要兩個地方擋:純策略級漏聚合後抖(真漏洞)、純 framework 抹掉策略訊號語意。對齊精簡第 ② 層(元件內部簡單) + #3D 連續可衰退紀律自然落策略層。

### framework 執行政策層(execution policy layer)
Round 3 R3-③ 新增架構元件,位於算量站後、實際送單前。職責:**比對 current 持倉 vs 算出來的 target,套執行紀律決定送不送單**。能力三件套:
- **dead-band**:差幅 < threshold → 不送單(擋幅度小到不值得動)
- **cooling**:距上次成單 < 間隔 → 不送單(擋頻率太密)
- **regime hook**:預留 V2-E regime detection 接入(市場特別瘋時降頻)
**日常比喻**:廚房門口的「出菜檢查站」— 算量算出來的菜不是直接送,先看「跟客人現在桌上的差多少」「上次送菜過多久了」決定要不要送。Risk Engine 是保全護欄(風險判斷),執行政策層是出菜紀律(訊號雜訊過濾)。具體數值(threshold / 間隔)V2-B 校準,regime hook 啟用 V2-E。

### executor 抽象 + 雙 driver(輸出側 parity)
Round 3 R3-④ 拍板的訂單執行架構,R3-② event bus 的**輸出側鏡像**。一個 **executor 介面**,底下兩個 driver:**backtest driver**(模擬成交器:歷史價成交+滑點/手續費估)/ **live driver**(V1 `trader.py` + `exchange_api` 真下單)。引擎算完 order 後**完全不知道是模擬還是真送**,丟介面就完事。**日常比喻**:餐廳的「出菜口」,底下廚房可接「演習用模型」(回測)或「真廚房」(實盤),服務生只認出菜口、不關心後面是誰做的。好處:輸出側 parity by construction,跟 R3-② 輸入側對稱形成完整 backtest/live parity 結構,M5 paper-vs-backtest 從根堵死。

### I/O 兩側對稱 parity(設計哲學)
Round 3 R3-② + R3-④ 累積的核心設計哲學:**資料進來(輸入)+ 訂單出去(輸出)兩側都用「同一介面 + 雙 driver」抽象**,讓 backtest 跟 live 從頭到尾用同一套 code,**結構上根本沒有「悄悄分岔」的空間**。**日常比喻**:管線兩端的水龍頭都做成同規格接口 — 不管接水塔還是自來水都對得上、接模擬下水道還是真的下水道也都對得上。對比 by discipline(靠人不犯錯維持兩條線一致):by construction(結構保證)更安全,**安全的東西要 by construction**。M5「paper-vs-backtest 一致」這條 milestone 因此**架構層已預防**,不必靠事後比對抓。

### Framework 一級護欄(non-bypassable framework primitive)
Round 3 累積的概念:某些 framework 元件**使用者不可關不可換不可 NoOp**(類比 V1 `circuit_breaker`)。對比策略級風控(`PortfolioStrategy` 可換 NoOp)。Round 3 拍的兩個 framework 一級護欄:
- `Risk Engine`(R3-① 拍)— 管組合級風控(總曝險 + vol-targeting + stale 終責)
- `framework 執行政策層`(R3-③ 拍)— 管最終 order 紀律(dead-band + cooling + regime hook)
**哲學區分**:framework 不假設**業務語意**(門檻數值留使用者),但**可寫死安全機制存在性**(有沒有這層 framework 說了算)。

### backtest/live parity(回測—實盤一致性)
策略先用歷史資料**回測**(看過去會不會賺)、過關才用真錢**實盤**。parity = 回測跟實盤**用同一套 code 餵資料、行為一致**。**怕的反面**:「考試一套題、上場一套題」— 回測賺翻、實盤一上線就走樣。是量化**最常見死法之一**(M5 paper-vs-backtest 專門抓這個)。Round 3 R3-② 拍 Option A(統一 event bus + 雙 driver)讓 parity **結構性內建**(同一個 event 介面,backtest/live 無從分岔)。

### no-lookahead(不偷看未來 / lookahead bias)
回測鐵律:時間 T 的市場快照**只能含 T 當下已知的資料**。若策略看到「未來」資料來決定當下的單 = **lookahead bias(偷看未來偏差)**,回測會**假賺**(作弊)、實盤現形。是回測**頭號作弊源**。Round 3 R3-② 拍 Option A 讓 no-lookahead **結構性內建**(引擎只處理「已發生的 event」,結構上碰不到未來)。**日常比喻**:考試只能用考前學的,不能翻到後面看答案 — 而且這個考場設計成「後面的題根本還沒發下來」,想翻都翻不到。

### event bus + 雙 driver(統一資料管線)
Round 3 R3-② 拍板的資料流架構:一個 **event 介面**(event bus),底下兩個 driver —— **backtest driver**(讀歷史按時間順序吐 events)/ **live driver**(接交易所 feed 即時吐 events)。引擎 + 策略消費同一介面、**完全不知資料來源**。**日常比喻**:同一個水龍頭,底下可接「水塔」(歷史)或「自來水」(即時),用水的人不需知道水從哪來、開法都一樣。好處:backtest/live parity + no-lookahead 都 by construction(結構性內建,不靠人自律)。前向連結 R3-④:live driver↔V1 `exchange_api`、backtest driver↔V1 `price_recorder`。

### by construction vs by discipline(結構性保證 vs 靠自律)
設計品味:讓正確性**由結構本身保證**(想犯錯都難),而非**靠人遵守紀律**(沒人犯錯才對)。Round 3 R3-② 選 Option A 而非 B 的核心 —— A 的 parity / no-lookahead 是「根本只有一套 code、根本碰不到未來」(by construction);B 的「兩套 code 講好要一致」是 by discipline(哪天有人寫錯就漏)。**日常比喻**:防止跌落,by construction = 把洞封起來(想掉都掉不下去),by discipline = 貼個「小心地洞」告示牌(靠你看到 + 記得閃)。Round 2 #3C「fail-safe 丟 min 池而非事後檢查」同一個品味。**安全的東西要 by construction。**

### dispatch(派工 / 叫策略起來算)
每次「市場有新資料」響鈴(framework fire 一次),framework 把所有策略叫起來、餵市場快照、收集它們算出的倉位 — 這整個「叫起來算」的動作叫 dispatch。**日常比喻**:像餐廳出餐鈴一響,廚房把所有廚師叫起來開始做菜。

### dispatch 順序(誰先算)
Round 2 #3B 拍板:一次 fire 裡 SymbolStrategy(出價的人)跟 PortfolioStrategy(全局看盤的人)誰先算。拍 **Option A — Symbol 先算 target → Portfolio 看完所有 target 後算 cap → 相乘**。理由:全局風控的價值就在「看完所有意圖再整體調度」,反過來讓 Portfolio 先算就失去全局視角。詳見 round2.md #3B。

### always-on 鎖(全局風控強制就位)
Round 2 #3A 拍板的 framework 行為:**系統啟動時強制至少有 1 個 PortfolioStrategy**(可以是真的、也可以是 NoOp),0 個 → refuse to start。**日常比喻**:像便利商店規定「至少要有一個店員在櫃檯」— 可以是真店員(做事的)、可以是假人模型(占位的),但不能空櫃。目的是**強迫使用者表態**(要做風控 / 明確選擇不做),不允許默默裸奔。

### Default + override pattern + framework 不假設業務(設計哲學)
Round 2 反覆出現的 framework 哲學:**framework 提供工具但不替使用者預設業務決定**。對比 Round 2 否決的設計:
- ❌ Sub-Q3 Option Δ 取最嚴 max_staleness — framework 假設「最嚴是合理」
- ❌ #3A Option D framework 內建 baseline — framework 假設「100% 曝險合理」
- ✅ 統一採:**framework default 處理 boilerplate + 策略可 override 處理特殊 + 強制使用者表態核心業務**(NoOp / required_data / on_stale 都這 pattern)

### Round 1 / Round 2 / ...
V2-A 階段內部的討論輪次。每輪鎖一些 axis(維度)的決定。

### Axis(維度 / 軸)
Round 1 用「axis」指 strategy interface 的設計維度。例:axis 6 = instrument 模型、axis 4 = output 形狀、axis 1 = 抽象層次。編號就是討論順序的代號,沒特別意義。

### Frame / Frame-level(框架級別)
最根本的設計決定,影響後面所有東西。例:「雙 interface」是 frame-level 決定 — 改它整個架構就要重畫。

### P0 / P1
優先級:
- **P0**:鎖死才能繼續(blocking)。Round 1 三個 axis 都是 P0。
- **P1**:重要但可延後(non-blocking)。Round 2/3 處理。

### Stub(占位符)
先放個空殼、晚點補實際內容。例:「策略池第二格留 stub `TBD`,等 V2-T1 再決定」。

---

## 5. 資安 / 維運(M8 backlog #8)

完整規格見 `v2a/m8_security.md`。這裡只收白話詞條。

### operational risk(維運風險)
跟「策略押對押錯」無關的風險 — 金鑰外洩、主機被駭、手滑打錯網。M1–M7 防市場風險(會不會虧),M8 防維運風險(會不會被偷 / 被駭)。**日常比喻**:開店,M1–M7 是「進的貨好不好賣」,M8 是「店門鎖牢不牢、收銀機會不會被整台搬走」。

### 2FA(雙因素驗證,two-factor authentication)
登入要過兩關:密碼(你知道的)+ 第二道(你有的東西,如手機動態碼或實體鑰匙)。光偷到密碼進不來。

### TOTP / authenticator app(動態碼 app)
手機 app 每 30 秒換一次的 6 位數動態碼(Google Authenticator / Authy)。2FA 第二道的中等強度選項。

### 硬體金鑰 / FIDO2 / passkey(實體鑰匙)
一把實體小鑰匙(如 YubiKey)或裝置綁定的登入憑證。2FA 第二道**最強**選項 — 對方沒實體拿到就是進不來。**日常比喻**:保險箱要插實體鑰匙,光知道密碼沒用。

### SIM swap(換卡攻擊)
攻擊者社工電信商把你的門號補發到他的 SIM 卡,你的簡訊驗證碼就送到他手機。**所以簡訊 2FA 等於沒有,M8 禁用 SMS OTP。**

### IP whitelist(IP 白名單)
API key 綁定指定 IP,非白名單 IP 拿這把 key 直接被交易所拒絕。**日常比喻**:這把鑰匙只認自家門口,別人拿去別處插不動。

### key rotate(金鑰輪換)
定期(M8 訂 90 天)產新 key、換掉、刪舊 key。鑰匙用久暴露機率累積,定期換新、作廢舊的。疑似外洩立即 rotate。

### 提現權限(withdrawal permission)
能把幣轉出帳戶的權限。bot 下單根本用不到,M8 規定 trading key 一律**關掉** — 就算 key 被偷,對方也搬不走幣。

### read-only key vs trading key
唯讀 key 只能看(抓資料 / 對帳),trading key 能下單。M8 規定兩者分離,看數字的程式只拿唯讀,降低下單 key 的暴露面。

### testnet vs mainnet(測試網 vs 實盤)
testnet = 交易所提供的假錢練習場,mainnet = 真錢。M8 規定兩邊 key 完全分開,防測試程式手滑打到真錢。

### UFW(簡易防火牆)
Ubuntu 內建防火牆。設「對內全擋、對外放行、只開 SSH」。**日常比喻**:給主機加一道牆,只留一扇你管理用的門。

### SSH 金鑰登入(key-based auth)
SSH 遠端登入只認「金鑰檔」不認密碼。密碼會被全網機器人 24h 爆破,金鑰幾乎猜不中。

### redact(遮蔽)
把敏感字串換成 `[REDACTED]` 或只留末 4 碼。M8 規定 log / 告警絕不印完整 secret。V1 `notifier.py` 已實作。

### pre-commit hook(提交前掛鉤)
每次 `git commit` 前自動跑的檢查。M8 用它掛 detect-secrets,commit 前掃到疑似金鑰直接擋下。**日常比喻**:出門前自動檢查「鑰匙有沒有不小心夾在要寄出的信封裡」。

### detect-secrets / gitleaks / trufflehog
掃 git 內容 / 歷史有沒有金鑰的工具。M8 用來掃全歷史 + 掛 pre-commit。

### secret scanning + push protection(GitHub 平台層)
GitHub 內建:有人 push 含金鑰的 commit 直接被平台擋住。M8 的第三道防線(hook 在本機擋、push protection 在平台擋、掃歷史事後稽核)。

---

## 維護規則

- 每 round 新出現的術語追加進對應分類
- 解釋以「使用者買菜阿姨也聽得懂」為標準
- 例子優先於定義 — 抽象解釋一定配一個具體例子
