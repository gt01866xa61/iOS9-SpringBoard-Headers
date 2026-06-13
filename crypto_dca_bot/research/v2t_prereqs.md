# V2-T 開工前置 — BLOCKERS(下個 session 開 V2-T 前先清)

> 建立 2026-06-13(V2-S 收官 session 結尾)。**V2-T(驗證階段:walk-forward /
> M1-M7 / paper trading)開工前,以下硬前置必須先解。** 下個 session 開頭讀這份。

---

## 為什麼有這份

V2-S 把起步策略池 3 個全 codify 完成(195 tests),但 V2-T 是**嚴格樣本外
驗證**階段,而嚴格驗證**不能用 V2-S 的 sanity 資料**(close-only / 合成 /
缺 funding)。V2-T 開工 = 必須先有正典資料 + 引擎精修。

---

## 前置 1 — 正典真資料接入(使用者本機,硬 blocker)

V2-S 的真資料是 **sanity 級**,V2-T 要 **正典級**:

| 資料 | V2-S 現況 | V2-T 需要 |
|---|---|---|
| BTC/ETH 日線 | CoinMetrics `PriceUSD`(**close-only** → Donchian-on-CLOSE)| **Binance OHLCV**(真 high/low)|
| BTC/ETH funding | **無**(容器內合成 sanity)| **Binance funding history**(8h)|
| VIX | datahub 真 OHLC ✅(夠用)| 沿用(或本機補更新)|
| DXY | **無**(optional)| optional,有更好 |

**動作(使用者本機 Windows + ccxt,即 V1 那套;容器擋交易所不能硬連)**:
1. OHLCV:
   ```python
   from datetime import datetime
   from v2.data import CcxtLoader
   for sym, field in [("BTC/USDT", "BTC_kline_1d"), ("ETH/USDT", "ETH_kline_1d")]:
       s = CcxtLoader(sym, field, timeframe="1d", since=datetime(2019, 1, 1)).fetch()
       CcxtLoader.to_csv(s, f"{field}.csv")  # 命名對齊 CsvLoader 預期
   ```
2. funding:
   ```python
   from v2.data import CcxtFundingLoader
   for sym, field in [("BTC/USDT:USDT", "BTC_funding_8h"), ("ETH/USDT:USDT", "ETH_funding_8h")]:
       s = CcxtFundingLoader(sym, field, since=datetime(2019, 1, 1)).fetch()
       CcxtFundingLoader.to_csv(s, f"{field}.csv")
   ```
3. 帶回容器 commit 進 `crypto_dca_bot/v2/data/fixtures/`(覆蓋 close-only BTC/ETH、
   新增 funding)。檔頭標來源 + 「正典 OHLCV from Binance」定位。
4. 既有 `requires_fixtures` / `requires_funding_fixture` 機制 → 真資料 sanity
   test 自動切換到正典(現有 close-only fixture 若覆蓋,Donchian 改用真 high/low)。

**注意**:Donchian 用 close-only 跟真 OHLCV 的 entry/exit 訊號**會不同**(通道用
high/low vs close)→ 正典資料進來後,Donchian 訊號才算數,V2-S 的回測數字
($171k 那些)**作廢、重跑**。

---

## 前置 2 — 752 rejections 引擎精修(使用者 V2-S1 拍板留 V2-T)

V2-S1 真資料 sanity 發現:Donchian BTC+ETH 跑 2019-2024 出 **752 rejections**。

**根因**:多 symbol near-fully-invested 時,`sizing-to-absolute-target` ×
`executor reject-whole`(B5 簡化:餘額不足整單拒絕、不部分成交)互動 →
想加倉但現金被既有倉位占住 → insufficient_cash 拒絕。**非策略 bug,是引擎簡化
在真資料多 symbol 場景現形。**

**精修選項(V2-T 開工時 options 拍板)**:
- **sell-before-buy ordering**:同一 fire 內先處理賣單釋放現金、再處理買單(最小改動、最直接)
- **partial fill**:餘額不足時成交買得起的部分(更真實,沿用 V1 trader 對帳邏輯)
- **delta-aware sizing**:sizing 算「target − current 的差額」而非絕對 target(從源頭減少不必要單)

影響檔:`v2/execution/executor.py`(`BacktestSimExecutor`)+ 可能 `v2/engine/
pipeline.py`(order 排序)。會動 fingerprint → 既有 tests 數字要更新。

---

## V2-T 本體(前置清完才開,frame 用)

roadmap / architecture.md §8 carry over:
- **M2 walk-forward**:IS 30 個月 / OOS 3 個月 / WFE > 50%,滾動
- **M1 五段崩盤 stress-test**:接正典資料(現有 M1 合成壓測骨架 → 換真資料)
- **M3 backtest lock**:fingerprint 鎖檔(B6 已有機制)
- **M4 paper trading** ≥ 60 交易日(接 live websocket、模擬下單)— 這步要 LiveDriver(輸入側 live driver,V2-B 只做了 backtest driver）
- **M5 paper-vs-backtest**:Sharpe 差 ≤ 30% / Fill 差 ≤ 10%
- **M6 risk-based sizing**:vol-targeting 落地(Risk Engine 已留 hook,IdentityVolEstimator → 真公式)
- **M7 退役監控**:滾動 Sharpe 連 2 窗 < backtest 50% → 退役

**V2-T 也會撞**:平台還沒有「績效指標計算層」(Sharpe / max drawdown / WFE)+
walk-forward 切窗 runner。這些是 V2-T 要蓋的(B7 的 Backtest runner 是單次跑,
walk-forward 要多窗 + 重訓 boundary 用 reset()）。

---

## 下個 session 開頭 checklist

1. `git status` + `git log --oneline -10` 對齊
2. 讀 CLAUDE.md 4 必讀 + 掃 glossary
3. **讀本檔**(V2-T 前置)
4. 確認前置 1(正典資料)使用者帶回了沒 → 沒有則 V2-T 不能真開,先處理資料 or 做前置 2(引擎精修,不依賴真資料可先做)
5. 前置 2(引擎精修)可不等資料先做 — options 拍板 → 精修 → 重跑既有 sanity
