# V2 Builder Roadmap(長期指引)

> 2026-05-09 pivot — V1 結案後 builder mode 啟動。V2 = 多市場 / 多策略 / 動態切換 24h 量化交易平台。
> 完整 pivot 決策紀錄見 `decisions.md` 2026-05-09 條目。

---

## V2 專案定義

**多市場 / 多策略 / 動態切換 24h 量化交易平台**

| 維度 | 內容 |
|---|---|
| 市場 | 第一階段 BTC/ETH,後續擴 Gold(黃金)/ Oil(石油)/ NDX(那指)|
| 策略 | 起步 3 個業界 style,sweet spot 3-7 個 |
| 動態 | meta-layer(元層)依市況選策略 |
| 24h | 全自動執行,人睡覺也跑 |

工程量:V1 的 50-100 倍。**強制分階段建,不能一次蓋到位**。

---

## 起步策略池(starting point,V2-A 階段可調)

3 個業界標準 style 的組合(correlation-designed,設計階段避免共振):

| # | Style | 例子 | 對應使用者既有 |
|---|---|---|---|
| 1 | **Trend-following**(趨勢追蹤)| BTC/ETH 永續合約 setup | ✅ 直接 codify 既有合約系統 |
| 2 | **Mean-reversion**(均值回歸)| ETH/BTC ratio 偏離歷史均值反向交易 | 補沒在做的 style |
| 3 | **Macro overlay**(宏觀風控)| DXY 美元指數 / VIX 波動率指數 上升時減倉 | 補沒在做的風控層 |

**這是合理起點,不是經過驗證的最佳組合**。V2-A 階段 review 是否要換,V2-B 階段用真實資料 backtest 驗證 correlation。

---

## 預算策略(simulation-first 5-step cascade)

| 階段 | 資金 | 目的 |
|---|---|---|
| 1. Backtest(回測)| $0 | 跑歷史資料看績效 |
| 2. Walk-forward(滾動樣本外)| $0 | 用歷史前段訓練、後段驗證,避免 overfit |
| 3. Paper trading(紙上交易)| $0 | 即時資料模擬下單 2-3 個月 |
| 4. Tiny live(小資金實單)| 50-100 USDT | 真實 slippage(滑點)+ fee + 心理測試 |
| 5. Scale up(放大)| TBD | 視 step 4 結果 |

V2 開發過程主要消耗時間,**不是金錢**(直到 step 4)。

---

## 階段拆分(V2-A → V2-D,蓋房子比喻)

| Phase | 字母代表 | 房子比喻 | 實際做的事 | 預估時間 |
|---|---|---|---|---|
| V2-A | **A**rchitecture(架構)| 畫設計圖 | 平台骨架 / 模組接口 / 資料流 | 3-6 週(地基要穩,允許走久)|
| V2-B | **B**acktest(回測引擎)| 蓋廚房 | 多策略可插拔回測引擎 | 2-3 週 |
| V2-S1..N | **S**trategy 1..N | 蓋房間 | 各策略 codify | 各 2-3 週 |
| V2-T1..N | **T**est 1..N | 試住房間 | Walk-forward + paper trading | 各 2 週 |
| V2-E | **E**nsemble(集成)| 中央管控系統 | 動態策略選擇 / regime detection | 4-6 週 |
| V2-D | **D**eploy(部署)| 正式入住 | Tiny live 50-100 USDT → 漸進放大 | 1-2 週 |

**每階段獨立 deliverable**(可交付產出)— 不等全部做完才看到成果。

---

## Validation Standards(M1-M5,V2-B / V2-T 必跑)

V2-B / V2-T 階段必須遵循的硬規格 — 規格鬆 → backtest 看起來綠但實單翻車。

### M1:V2-B 內建 5 段歷史崩盤 stress-test

| 期間 | 事件 | 為什麼 |
|---|---|---|
| 2020-03(2-3 週)| COVID crash | risk-asset 同步崩,測 crisis correlation |
| 2021-05(1-2 週)| China crackdown / Bitcoin -30% | 政策風險衝擊 |
| 2022-05(1-2 週)| LUNA / Terra 崩盤 | 系統性流動性危機 |
| 2022-11(1-2 週)| FTX 倒閉 | 中心化交易所信用危機 |
| 2024-08-05(數日)| 日圓 carry trade unwind | 跨資產 deleveraging |

任何策略過不了這關 = reject。

### M2:Walk-forward 規格寫死

- **IS**(In-Sample 樣本內訓練):**30 個月**
- **OOS**(Out-of-Sample 樣本外驗證):**3 個月**
- **重訓週期**:**每 3 個月**
- **WFE**(Walk-Forward Efficiency,樣本外效率):**> 50%**(= OOS 績效 ÷ IS 績效)
- **OOS 每視窗 trade 數**:**≥ 30 筆**(統計顯著性下限)

### M3:Backtest 結果 lock(避免事後改數)

- 自動帶 timestamp(時間戳)+ commit hash(版本雜湊)
- 結果寫進固定 log 檔,事後不能改
- **策略邏輯改 = 新編號**(strategy_v1 / strategy_v2),不能用同名字蓋掉舊紀錄

避免 retrofit(事後改邏輯讓績效變好看)— 量化界最常見的自欺。

### M4:Paper trading 最少 60 個交易日

- **60 個 trading day(交易日,週末 / 假日不算)**,不是自然日
- 為了讓策略遇到至少 1-2 次月度 regime shift(市場狀態變化)

### M5:Paper vs Backtest 並排比較門檻

| 指標 | 容忍門檻 | 超過 = reject |
|---|---|---|
| **Sharpe ratio 差距** | ≤ 30% | 模型有結構性誤差 |
| **Fill rate(成交率)差距** | ≤ 10% | backtest 假設不貼近實盤 |

reject 的策略**不上 V2-D**(真錢 deploy)。

---

## Correlation-aware 設計

避免「5 策略 = 1 策略 + 5 倍工程量」的陷阱。

### 相關性的來源(設計時要避免)

- 同邏輯類型(都是趨勢、或都是均值回歸)
- 同輸入資料(都吃 BTC 4h K 線)
- 同時間尺度(都是日內 1h)
- 同市場(BTC + ETH 本就 0.85+ 相關)
- **危機共振(crisis correlation)**:崩盤期所有 risk asset → 1

### 驗證方法(V2-T 階段)

1. **Pearson correlation**(皮爾遜相關係數):兩兩 pair PnL ≤ 0.5
2. **Position correlation**:部位重疊度
3. **Stress-period correlation**:歷史崩盤期(May 2021、Nov 2022 FTX、Mar 2020)是否一起虧
4. **Regime conditional correlation**:牛 / 熊 / 盤整 三市況的相關性

### Sweet spot

3-7 個策略。少於 3 = 不夠分散。多於 7 = 過度分散傷 alpha + 工程複雜度爆炸。

---

## V1 與 V2 關係

- **V1 已結案,停止運行**(不當儲蓄機 — 使用者已有手動長期部位,V1 重疊無意義)
- V1 code 保留當技術資產,V2 沿用以下模組:
  - `exchange_api.py`(ccxt wrapper)
  - `trader.py`(market buy + safety + daily cap atomic state)
  - `notifier.py`(Telegram)
  - `circuit_breaker.py`(連敗保護)
  - `heartbeat.py`(6h 存活訊號)
  - `price_recorder.py`(SQLite 歷史價,V2-B 會擴充)
  - `chaos_test.py`(失敗注入測試)
- V1 不會被改寫,**也不會被 wrap 成 V2 策略模組**

---

## 範圍鎖

- 第一階段嚴格鎖 BTC/ETH,Gold / Oil / NDX 是後續
- 不上 leverage(槓桿)/ 衍生品
- 不充值,現有 ~13 USDT 緩衝足夠到 V2-D step 4(tiny live 50-100 USDT 從用戶獨立資金供應)

---

## 資源需求(目前不需用戶額外準備)

| 資源 | 用途 | 取得 |
|---|---|---|
| 歷史 K 線 | Backtest 訓練 | Binance API 免費(2017 起)|
| 股 / 商品歷史 | Gold/Oil/NDX 階段 | Yahoo Finance API 免費 |
| Backtest 引擎 | 跑模擬 | vectorbt(向量化回測 lib)或自寫輕量版 |
| 資料庫 | 歷史 + trade log | SQLite(V1 已用)|
| 圖表 | 視覺化績效 | matplotlib / plotly |
| (選用)On-chain API | 鏈上策略 | Glassnode / IntoTheBlock 免費 tier |

→ Windows host + Python + git 已夠用。需新工具會明說。

---

## Honest reality check

| 風險 | 程度 | 對應 |
|---|---|---|
| Alpha 不保證 | 高 | Process 驗證:沒 alpha 的策略丟掉 |
| Overfitting 陷阱 | 高 | Walk-forward + paper trading 雙重驗證 |
| Crisis correlation 危機共振 | 高 | 設計階段強制 stress-test(M1)|
| 「業界 3-style」對使用者未驗證 work | 中 | V2-A/B 檢驗,可調整 |
| 工程複雜度爆炸 | 中 | 階段性 milestone + 每階段獨立 deliverable |
| 範圍蔓延(BTC 還沒做就想擴黃金)| 中 | **第一階段嚴格鎖 BTC/ETH** |

---

## 決策點(每階段結束 review)

- **V2-A 結束**:架構評審,可 pivot
- **V2-T1 結束**:第一策略 backtest 失敗 → 重新評估方向
- **V2-E 結束**:集成 Sharpe(夏普比率)沒顯著優於最強單策略 → 簡化掉 ensemble 層
- **每 2 個月 sunk-cost(沉沒成本)review**:有偏離初衷嗎?要 pivot 嗎?

---

## Verification(每階段 exit criteria 離場標準)

| Phase | Exit criteria |
|---|---|
| V2-A | 架構文件 review 通過 |
| V2-B | 回測引擎能重現 V1 trades(sanity check 健全性檢查)|
| V2-S1 | 第一策略在歷史資料產生 non-trivial(非平凡)PnL |
| V2-T1 | (1) Walk-forward 多視窗 WFE > 50%<br>(2) Paper trading ≥ 60 個交易日<br>(3) Paper vs backtest:Sharpe 差 ≤ 30%、Fill rate 差 ≤ 10%<br>(4) OOS 每視窗 trade ≥ 30 筆 |
| V2-E | Ensemble 績效 > 最強單策略(用 Sharpe ratio 比較)|
| V2-D | Tiny live 小資金交易順利執行,無 unexpected(預期外)行為 |

---

## 下一步

進入 **V2-A 架構設計** — 跟使用者來回討論平台骨架(**不寫 code**),產出架構文件。V2-A 結束 review 通過後才進 V2-B 寫第一行 code。
