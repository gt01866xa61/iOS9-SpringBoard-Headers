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
- **M1**:V2-B 內建 5 段崩盤 stress-test
- **M2**:Walk-forward 規格(IS 30 個月 / OOS 3 個月 / WFE > 50%)
- **M3**:Backtest 結果 lock(timestamp + commit hash,策略改 = 新編號)
- **M4**:Paper trading ≥ 60 交易日
- **M5**:Paper vs backtest 容忍門檻(Sharpe 差 ≤ 30%、Fill 差 ≤ 10%)

### SymbolStrategy / PortfolioStrategy
Round 1 拍板的雙 interface:
- **SymbolStrategy**:處理 per-symbol 或 pair 的部位意圖。輸出 `{symbol: target%}`。
- **PortfolioStrategy**:處理 portfolio-level 風控。輸出 `{symbol: cap multiplier}`。

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

## 維護規則

- 每 round 新出現的術語追加進對應分類
- 解釋以「使用者買菜阿姨也聽得懂」為標準
- 例子優先於定義 — 抽象解釋一定配一個具體例子
