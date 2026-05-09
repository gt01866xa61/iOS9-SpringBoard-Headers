# Data Sources(資料來源)清單

> 這份等到 V2-R 階段(策略決定後)再認真填。先建空檔當 placeholder(預留位置)。
> Day 1-2 期間 Gemini 有提到的資料來源也可以順便先記在這邊。

## 待評估的來源(供策略選用)

- [ ] **Binance API**(via ccxt)— 歷史 K 線、即時市場資料、現在 V1 已用
- [ ] **CoinGecko API** — 跨交易所市場 metrics、免費 tier 夠用
- [ ] **Glassnode** — 鏈上指標(MVRV、SOPR、Realized Cap 等),付費月費高
- [ ] **IntoTheBlock** — 鏈上 + 機器學習指標,部分免費
- [ ] **Etherscan / Tronscan** — whale 轉帳追蹤、合約事件
- [ ] **FRED** — 宏觀經濟資料(免費)
- [ ] **Twitter / Reddit** — 情緒資料(取得難、品質爭議)
- [ ] (你或 Gemini 想加的)

## 評估維度

| 維度 | 內容 |
|---|---|
| 成本 | 免費 / 付費(月費多少) |
| 頻率限制 | rate limit(每秒可呼叫幾次) |
| 歷史深度 | 能拿到多久前的資料 |
| 資料品質 | 缺漏率、時間延遲、可信度 |

(各 source 填上)
