# Data fixtures

V2-S real-data sanity-check 資料。**committed(日線小、版控可重現回測)**。

## 現有

| 檔 | 內容 | 來源 | 定位 |
|---|---|---|---|
| `btc_usd_1d.csv` | BTC 日線 2019-01-01..2024-12-31(2192 天)| CoinMetrics community `PriceUSD` | sanity-only |
| `eth_usd_1d.csv` | ETH 日線 同範圍 | 同上 | sanity-only |

重建:`python -m v2.data.fixtures.build_fixture`(需 github 網路)。

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
