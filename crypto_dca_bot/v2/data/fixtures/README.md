# Data fixtures

V2 真資料 fixture。**committed(日線/funding 小、版控可重現回測)**。

## 現有(V2-T 正典資料,2026-06-13)

| 檔 | 內容 | 來源 | 定位 |
|---|---|---|---|
| `btc_usd_1d.csv` | BTC 日線 2019-01-01~2026-06-13(2721 天)| **Binance spot via ccxt(本機抓)** | **canonical 真 OHLCV** |
| `eth_usd_1d.csv` | ETH 日線 同範圍 | 同上 | **canonical 真 OHLCV** |
| `btc_funding_8h.csv` | BTC 永續 funding(7405 筆,2019-09~)| **Binance USDT-M via ccxt(本機抓)** | **canonical** |
| `eth_funding_8h.csv` | ETH 永續 funding(7171 筆,2019-11~)| 同上 | **canonical** |
| `vix_daily.csv` | VIX 日線 2019-2024(1529 交易日)| datahub.io core/finance-vix(CBOE 官方)| sanity,**真 OHLC**(本機抓更新待補)|

## 工作流(已固化)

容器內 egress proxy 擋所有交易所 API。**正典資料路徑**:
1. **使用者本機**(Windows + ccxt,即 V1 那套)跑 `CcxtLoader` / `CcxtFundingLoader`
   抓 Binance OHLCV / funding → `to_csv()` 存檔。
2. 上傳容器 → `python -m v2.data.fixtures.import_binance_uploads <4 個 csv 路徑>`
   把使用者格式(`timestamp(ms),...`)轉成 V2 fixture 既定格式
   (`date,...` / `timestamp(ISO),funding_rate`)→ 覆蓋本資料夾。
3. 既有 `requires_fixtures` / `requires_funding_fixture` 機制 → V2-S 真資料
   sanity test 自動啟用正典版本。

## 歷史(close-only sanity 退役,2026-06-13)

V2-S 開發期用 CoinMetrics community `PriceUSD`(close-only)當 BTC/ETH
sanity fixture(`build_fixture.py` 拉的)。V2-T 開工真資料接入後**已取代**:
- close-only 版的 Donchian 退化成 Donchian-on-CLOSE(收盤通道,非 high/low
  通道)
- 真 OHLCV 跑出來 Donchian 進出場時點不同:close-only $171k → 真 OHLCV
  $137k(同參數 / 同期間 / 同初始資金,**差 $34k**)
- V2-S 期間的 close-only 數字**作廢**;V2-T 起以真 OHLCV 為準

`build_fixture.py` 保留(VIX 部分仍 active);BTC/ETH 部分已退役,新流程
走 `import_binance_uploads.py`。

## DXY(仍缺,留 optional)

`MacroOverlay` 預設 VIX-only。DXY 等使用者本機 ccxt 抓 → 同 funding 流程
帶回 → commit `dxy_daily.csv` → 加進 `MacroOverlayParams(indicators=...)`。

## DXY 缺口(V2-S3 MacroOverlay 第二指標,等本機帶回)

MacroOverlay 預設 **VIX-only**(VIX > 30 → cap 0.5)。**DXY 找不到 reputable
公開源**(FRED 403、datahub 無 dollar-index、stooq/yahoo 403)。DXY 作為
**optional 第二 indicator** 留 hook:本機抓 `dxy_daily` → commit `dxy_daily.csv`
→ `MacroOverlayParams(indicators=[VIX..., MacroIndicator(field="dxy_daily",
risk_off_above=..., cap=...)])` 即生效(multi-indicator min 取最狠)。

## 缺口 — funding rate fixture(V2-S2 等使用者本機帶回)

V2-S2 funding skew **暫無真資料 sanity fixture**。系統性探勘 GitHub 結論
(2026-06-13,decisions log + V2-S2 開工訊息):**無可達 reputable 公開歷史
funding 資料集**(haozhu18 發 Kaggle 容器擋、leepacific 只有 README、其他
低星/code-only)。Kaggle/HuggingFace egress 也擋。

容器內 sanity = **合成 funding 序列**(`v2/testing/scenarios.py
make_funding_series`),驗策略邏輯,**非真資料**。

正典路徑(同 BTC OHLCV pipeline 對稱):
1. 使用者本機 Windows + ccxt 跑 `CcxtFundingLoader`:
   ```python
   from datetime import datetime
   from v2.data import CcxtFundingLoader
   ld = CcxtFundingLoader(
       symbol="BTC/USDT:USDT",          # ccxt 統一 swap 格式
       field="BTC_funding_8h",
       since=datetime(2022, 1, 1),
   )
   series = ld.fetch()
   CcxtFundingLoader.to_csv(series, "btc_funding_8h.csv")
   ```
2. 帶回容器 commit 進本資料夾:`btc_funding_8h.csv` / `eth_funding_8h.csv`
3. `v2/tests/test_funding_skew.py::test_funding_skew_real_data_sanity` 的
   `requires_funding_fixture` 自動偵測啟用(同 BTC `requires_fixtures` 機制)。

## ⚠️ close-only 限制(重要)

CoinMetrics community data 是**單一日參考價**,**沒有 OHLC high/low** →
fixture 的 `open=high=low=close=PriceUSD`、`volume=0`。

後果:**Donchian 在此資料上是 Donchian-on-CLOSE**(通道 = 過去 N 日最高/最低
**收盤**,非最高/最低**價**)。合法常見變體,**足夠 sanity check**,但**不是正典**。

## 正典資料路徑(production)

**正典 OHLCV = Binance via ccxt。**

工作流(2026-06-13 記):
- 容器內 egress proxy 擋所有交易所 API(Binance/Coinbase/... 全 403)→
  **不在容器硬連交易所**。
- 正式抓真資料:**使用者本機環境**(Windows + ccxt,即 V1 那套)用
  `CcxtLoader` 抓 → `CcxtLoader.to_csv()` 存檔 → 帶回容器用 `CsvLoader` 餵。
- M1-M7 正式驗證(V2-T)用這條正典 OHLCV,非本 sanity fixture。

## 規則

- **日線**(小)→ commit 進 repo(本資料夾)。
- **intraday**(之後,大)→ 不 commit,另存 + gitignore。
