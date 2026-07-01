# 股癌訊號燈 (Gooaye Signal Board)

一個從《股癌》(謝孟恭) 節目延伸出來的**可擴充訊號觀測平台**：把孟恭每集隨口提到、
他在盯的市場／總經／供應鏈訊號，系統化蒐集、量化成**紅黃綠燈號**，做成手機／電腦
隨時隨地可看的網頁儀表板。

- **後端**：`build.py` 抓資料、算每個訊號的燈號，原子寫出 `data/signals.json`（由
  GitHub Actions 排程跑）。
- **前端**：單一 `web/index.html`（深色、手機優先）同源讀 `signals.json`，內嵌 fallback
  讓頁面永不空白，自動刷新。
- **零伺服器、零資料庫、零 CORS。**

> 借殼提醒：本 repo 根目錄的 `System/`、`usr/` 是 iOS dyld cache dump，與本專案無關；
> `crypto_dca_bot/` 是另一個獨立專案。本專案全部在 `gooaye_signals/` 底下。

## 🔑 新增一個訊號（最重要的日常操作）

平台的第一設計原則：**加一個訊號 = 複製一個檔、改它、完成**。零中央清單、零前端、
零 schema 改動（90% 情況）。

1. `cp signals/_template.py signals/<你的id>.py`（或複製最接近的既有訊號檔）。
2. 編輯那一個檔：`id`(=檔名)、門檻常數、`bindings`(資料源)、純函式 `_compute`、
   四個 `interpretations`、`episode_ref`/`episode_date`/`cluster`/`widget`/`tags`/`in_master`。
3. `GOOAYE_DEMO=1 python build.py` → 開 `web/index.html` 確認卡片出現 → 加一條
   `tests/test_phase2_compute.py` 斷言 → commit + push。cron 下輪自動接手。

- 新主題（cluster）：另在 `core/clusters.py` 的 `CLUSTERS` append 一行 `ClusterSpec`。
- 全新視覺化（罕見）：在 `web/index.html` 的 `WIDGETS` 表加一個 render 函式，並在
  `core/spec.py` 的 `Widget` literal 加一個名稱。

## 每個訊號都回答「三個問題」

這是使用者的核心需求，也是資料模型與卡片的一等公民：

1. **追什麼 (track)**：白話定義在盯什麼、為什麼重要 → 模組 docstring + `name`/`tags`。
2. **變化的長相 (shape)**：實際圖表 + 一句「動起來長什麼樣」→ `widget` + `widget_data`。
3. **各狀態含義 (states)**：🟢🟡🔴🩶 各代表什麼 + 目前解讀 → `interpretations` + `light`。

## Phase 進度

| Phase | 範圍 | 狀態 |
| ----- | ---- | ---- |
| 1 | 契約 + registry 完整性（`core/`、`registry.py`、`config.py`、`logger.py` + 3 個種子 spec，stub compute） | ✅ Done |
| 2 | 運算引擎 + demo 模式（`fetchers/cache.py`、`demo/fixtures/`、六訊號真 `_compute`） | ⬜ 待做 |
| 3 | 實接資料源 + 全流程（`finmind.py`、`yfinance_src.py`、`build.py` 端到端 + 失敗隔離） | ⬜ 待做 |
| 4 | 前端（`web/index.html` 泛型渲染 + 5 widget + 內嵌 fallback + 自動刷新） | ⬜ 待做 |
| 5 | 部署（`.github/workflows/signals.yml` + GitHub Pages） | ⬜ 待做 |
| 6+ | 擴充驗證（口述新訊號逐一加，如 `rates_macro` cluster） | ⬜ 持續 |

## 首版種子訊號（cluster：半導體 / 記憶體循環見頂觀察）

計入主燈：
- `yageo_rev_yoy`（bar_chart）國巨(2327) 月營收 YoY 轉弱。
- `mlcc_basket_ma`（sparkline）被動四雄籃 vs 50MA。
- `ai_breadth`（gauge）AI 類股站上 50MA 的廣度。

主燈：🔴 ≥2 紅＝主升段尾聲警示｜🟡 任一紅/黃＝留意轉弱｜🟢 全綠＝循環健康。

佐證面板（`in_master=False`，Phase 2 加）：記憶體相對強度、原物料(鈀/銀)、觀測名單。

## 開發與驗證

```bash
cd gooaye_signals

# Phase 1：契約 + registry 完整性
python tests/test_phase1_specs.py       # 印「Phase 1 驗證通過」

# 之後（Phase 2+）：離線 demo 跑整條 pipeline，不需任何金鑰
GOOAYE_DEMO=1 python build.py
python -m http.server                    # 開 http://localhost:8000/web/ 看儀表板
```

慣例沿用 `crypto_dca_bot/`：`from __future__ import annotations` + type hints、設定常數
集中檔頭、繁中註解、每 phase 一個驗證測試、時區鎖 Asia/Taipei (fixed UTC+8)。
