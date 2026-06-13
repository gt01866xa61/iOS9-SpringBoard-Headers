# V2-T 開工前置 + 完整 frame

> 建立 2026-06-13(V2-S 收官 session 結尾)。**最後更新 2026-06-13(真資料
> 到位 + V2-T 完整 T1-T9frame + 前置 2 拍板)。** 下個 session 開頭讀這份。

---

## 進度標記

| 項 | 狀態 |
|---|---|
| **前置 1 真資料接入** | ✅ **DONE 2026-06-13** |
| **前置 2 引擎精修(3 件全做)** | ⬜ **NEXT — 下個 session 動工** |
| T1 績效指標層 | ⬜ |
| T2 Walk-forward runner(M2) | ⬜ |
| T3 M1 真資料壓測 | ⬜ |
| T4 M3 lock(commit-hash)| ⬜ |
| T5 M6 vol-targeting 真公式 | ⬜ |
| T6 LiveDriver(輸入側)| ⬜ |
| T7 M4 paper trading ≥ 60 交易日 | ⬜ |
| T8 M5 paper-vs-backtest | ⬜ |
| T9 M7 退役監控 | ⬜ |

---

## 前置 1 — 正典真資料接入 ✅ DONE(2026-06-13)

使用者本機 Windows + ccxt(V1 那套)抓 Binance 正典資料、上傳容器、轉檔
覆蓋 fixtures(`v2/data/fixtures/import_binance_uploads.py`):

| 檔 | 內容 |
|---|---|
| `btc_usd_1d.csv` | BTC 日線 2019-01-01~2026-06-13(2721 天真 OHLCV)|
| `eth_usd_1d.csv` | ETH 同範圍 |
| `btc_funding_8h.csv` | BTC 永續 funding 8h(7405 筆,2019-09 起)|
| `eth_funding_8h.csv` | ETH 同(7171 筆,2019-11 起)|

**close-only sanity 退役數字佐證**(同 Donchian 20/10 BTC+ETH $10k 2019-2024):
- close-only(CoinMetrics PriceUSD,Donchian-on-CLOSE):**$171k**
- 真 OHLCV(Binance 真 high/low):**$137k**(差 -$34k,close-only 通道窄訊號偏多)
- → V2-S 期 close-only 數字**作廢**,以真 OHLCV 為準

**正典版實跑全範圍**(2019-01-01 ~ 2026-06-13,**7.5 年**):
- S1 Donchian:111 fills(53 買/58 賣)/ 958 rejections / $137k
- S2 Funding skew:379 fills / **11206 rejections** / $48k
- S1 + S3 MacroOverlay(VIX):177 fills / 968 rejections / $197k

196 tests 全綠**零 skip**(S2 `requires_funding_fixture` 自動啟用)。

工作流固化:容器擋交易所 → 使用者本機 ccxt 抓 → `to_csv()` → 上傳 →
`import_binance_uploads.py` 轉檔(ms ts → ISO date,fundingRate → funding_rate)→
覆蓋 fixtures → `requires_fixtures` 偵測啟用 sanity test。**未來更新走同流程。**

---

## 前置 2 — 引擎精修(使用者 2026-06-13 拍板)

**Rejections 從 V2-S 的 752 → 真資料 11206,引擎精修不是可選、是 V2-T
其他閘的硬前置**。被拒絕的單沒成交 → P&L 是錯的 → walk-forward 拿到的
數字也是錯的 → 後面所有 M2-M7 建在沙上。

### ★ 拍板:三個全做,順序 + 哲學

| # | 動作 | 為什麼 |
|---|---|---|
| **(1) delta-aware sizing** | sizing 算「target − current 的差額」(`B5 sizing.py` 在算絕對 target)| 從**源頭**省去無意義單(想加倉但其實差不多)|
| **(2) sell-before-buy ordering** | 同一 fire 內先處理賣單釋放現金、再處理買單(改 `pipeline.py` order 排序)| 真實交易者就是這樣做 |
| **(3) partial fill** | 限價單可部分成交;市場單看交易所實際行為(Binance spot market 若 notional > 餘額 = reject 整單,不切)| 對齊真實交易所 |

### ★ 拍板哲學(使用者明文)

> **「目的是像真實交易所、不准作弊式讓 rejections 歸零」**

- ✅ **可以**:減少不必要的單(delta-aware)、改下單順序(sell-before-buy)、
  支援交易所**真的支援**的 partial fill
- ❌ **不可以**:「餘額不足就自動裁切到能買的量」之類**真實交易所不會做**
  的事。Binance spot market order 餘額不足就是被拒,我們的 sim executor
  必須**忠實反映**這個行為,不准巧妙藏起來
- **判定:每個 reject 路徑要對得上「Binance 同情境會怎樣」**。對不上 → 我們
  改錯了

### 影響面

- `v2/engine/sizing.py`:absolute target → delta
- `v2/engine/pipeline.py`:order 產出排序(sells first)
- `v2/execution/executor.py`:Rejection 路徑 audit(對齊 Binance 行為)
- 既有 `test_pipeline.py` / `test_execution.py` 部分數字會跳,要更新
- 重跑三策略真資料 demo,看 11206 rejections 降到合理水位(但**不是歸零**;
  真實交易也會有 reject,看的是「降到符合策略合理頻率 × 真實交易所拒絕率」)

---

## V2-T T1-T9 完整 frame

### T1 — 績效指標層

V2-B 只算最終淨值,V2-T 需要的指標(M2-M7 拍閘要):
- **Sharpe**(年化 risk-adjusted return)
- **Sortino**(下行波動 risk-adjusted)
- **max DD**(最大回撤)
- **Calmar**(年化報酬 / max DD)
- **WFE**(Walk-Forward Efficiency)= OOS Sharpe / IS Sharpe(M2 要求 > 50%)
- **滾動 Sharpe**(window-by-window,M7 退役監控用)

新元件:`v2/analysis/metrics.py`(從 fills + equity curve 算)。要 test 釘死
(用已知曲線驗證計算正確)。

### T2 — Walk-forward runner(M2)

V2-B 的 `Backtest` 是單次跑全段。M2 規格:**IS 30 個月訓練 / OOS 3 個月驗證,
滾動切窗**(每 3 個月推一窗)。

新元件:`v2/analysis/walk_forward.py`:
- 多窗 runner,每窗呼叫 `strategy.reset()`(Round 1 拍 lifecycle 已留 hook)
- 重訓 boundary:IS 內訓練(此 V2-T 階段「訓練」= 暖機 + 跑 IS)→ OOS 跑出來
- WFE 計算 = mean(OOS Sharpe) / mean(IS Sharpe)
- M2 閘:WFE > 50% 才過

**會撞**:暖機通則(`min_history=0` + 策略自管)在 reset 後仍適用,但 OOS
第一段的暖機要從 IS 末段 fill。設計時釐清。

### T3 — M1 真資料壓測

V2-B M1 用合成 stale 序列。V2-T 改用真資料壓測五段崩盤:
- 2020-03 COVID
- 2021-05 China crackdown
- 2022-05 LUNA
- 2022-11 FTX
- 2024-08-05 JPY carry unwind

每段切出 ±30 天 fixture,跑 3 策略 + S3 overlay,驗證:
- 不爆(framework 不 crash)
- max DD 在可接受範圍(策略級閾值)
- overlay 在這些期間真的 risk-off

### T4 — M3 lock(commit-hash)

`fingerprint`(B6)已有 SHA-256。M3 完整 spec 加:
- 鎖檔含 `(timestamp, git_commit_hash, fingerprint, strategy_params, fixture_hashes)`
- 任一改動 → 新鎖檔 → 策略編號 +1
- 鎖檔 immutable

新元件:`v2/analysis/lock.py`。

### T5 — M6 vol-targeting 真公式

`Risk Engine` 留了 `VolEstimator` hook(`IdentityVolEstimator` 是 pass-through)。
M6 規格:**部位大小按市場晃動程度調**(volatility targeting)。真公式選型:
- **realized vol**(過去 N 根 std)/ **EWMA vol** / **GARCH** — V2-T 開議拍
- target_vol(年化,例 15%)/ realized_vol → scale 倍率
- 寫進 `v2/engine/risk_engine.py` 的 `VolEstimator` 實作

### T6 — LiveDriver(輸入側)

V2-B R3-② 拍了「同介面、雙 driver」,只蓋了 backtest driver。LiveDriver 是
**第一次 paper trading 真實上場的元件**:
- 接 Binance websocket(spot kline + perp funding stream)
- 容器跑不了(egress 擋)→ **使用者本機 / VPS 跑**
- 介面對齊 `EventSource` Protocol(B2)
- 沿用 V1 `exchange_api.py` 為基礎(architecture.md §6.4 落點)

**這是 V2-T 工作環境第一次跨出容器** — 規劃時要先想好跑在哪、怎麼 deploy。

### T7 — M4 paper trading ≥ 60 交易日

LiveDriver 接 Binance websocket(真即時資料)→ 引擎照常跑 → 但 executor
換成 `BacktestSimExecutor`(模擬成交,不真下單)。觀察:
- 跑滿 60 個交易日
- websocket 不斷線(或斷線後 framework 處理對)
- 累積 fills / P&L log

跑在 VPS(或長開電腦)。

### T8 — M5 paper-vs-backtest 對照

paper trading 期間用 backtest 跑同期歷史 → 比對:
- **Sharpe 差 ≤ 30%**
- **Fill 差 ≤ 10%**
- 不過 → 表示**回測沒抓到的東西**(滑點 / 延遲 / 真實 spread / 訂單衝擊)→ 調 cost
  model 直到對得上

這是 R3-②/④「I/O parity by construction」的真實驗證。

### T9 — M7 退役監控

策略上線後持續跑:
- 滾動 Sharpe 連 2 窗 < backtest 50% → **自動退役**
- live max DD > backtest 1.5 倍 → **自動退役**
- 觸發退役 = stop 該策略 + Telegram alert(走 V1 notifier,M8 已規劃)

實際是 cron + monitoring;V2-D 才真正部署,V2-T 階段把監控規則寫好。

---

## ⚠️ 4 個真風險(寫死 — V2-T 跑時必須意識到)

### 1. 引擎精修不修,後面全錯

11206 rejections **扭曲所有後續驗證**。被 reject 的單 P&L 沒記到,walk-forward
拿到的 Sharpe 是假的,M2 閘形同虛設。**前置 2 不解,T1+ 全部建在沙上。**

### 2. M4 paper trading 必須離開容器

LiveDriver 接 Binance websocket,容器 egress 擋。**T6/T7 要先想清楚跑在哪**
(使用者本機 / VPS / 雲端 VM)。M8 規格(VPS / 2FA / SSH 鎖死)就是為這準備。

### 3. 多次測試會汙染樣本外可信度

你會想試 Donchian (20,10) / (10,5) / (40,20)、Funding 不同 thresholds、VIX 不同
門檻 ... **每試一次就汙染 OOS 的可信度**(p-hacking / 過擬合)。

T1 要記**完整 testing protocol**:Deflated Sharpe / PBO(Probability of Backtest
Overfitting)/ purged-embargoed CV — López de Prado 的工作流。**不是「再
試一個參數看看」這麼簡單。**

### 4. 數字會繼續變(心理準備)

| 階段 | Donchian BTC+ETH |
|---|---|
| V2-S close-only sanity | $171k |
| V2-T 真資料 in-sample | $137k |
| V2-T 前置 2 修完(P&L 校正)| 會跳(待測)|
| V2-T M2 walk-forward(OOS)| 通常**再降**(in-sample 高估)|
| V2-T M6 vol-targeting + 成本校準 | 通常**再降** |
| V2-T M4 paper trading | 通常**再降一次**(真實滑點 + 延遲)|

**「數字一路縮小」就是逼近真實的過程**。**這不是壞消息,是健康的訊號**(策略
做不到、被排除掉,是 V2-T 該做的事 — 把不真實的期望剃掉)。**如果跑完
M2-M7 還有正數字 + 通過所有閘,那才是真的能放錢的東西**。

---

## 下個 session 開頭 checklist

1. `git status` + `git log --oneline -10` 對齊
2. 讀 CLAUDE.md 4 必讀 + 掃 glossary
3. **讀本檔**(進度標記 / 前置 2 拍板 / T1-T9 frame / 4 個真風險)
4. 確認真資料 fixture 還在(`v2/data/fixtures/btc_usd_1d.csv` 等 4 檔)
5. **開前置 2 第 1 件(delta-aware sizing)動工**:
   - 看 `v2/engine/sizing.py`(absolute target)
   - 看 `v2/engine/pipeline.py`(order 產出)
   - 設計 delta 計算:`delta_pct = target_pct − current_pct`(current_pct 從
     `PortfolioState.position_pct()` 拿)
   - 既有「dead-band」在 `execution_policy.py` 已用差額判定,可參考
   - 寫 test、跑、看 rejections 從 11206 降到多少
6. 第 1 件落地 + push 後接第 2 件(sell-before-buy)
7. 第 2 件落地 + push 後接第 3 件(partial fill)
8. 三件做完重跑 3 策略真資料 demo,update 數字到 decisions log
9. 第 3 件結束 = 前置 2 ✅,可進 T1 績效指標層

**節奏**:每件獨立 commit + push,中間 test 跑綠才推下一件。三件之間有依賴
但**不耦合**,可以乾淨拆。
