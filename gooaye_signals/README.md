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

## 每個訊號都回答「三個問題」——直接顯示在卡片上

這是使用者的核心需求，是 `SignalSpec` 的**必填欄位**（Phase 1 測試強制檢查），且**全部渲染在網頁卡片上**：

1. **追什麼 (`track`)**：白話「在盯什麼、為什麼重要」→ 卡片名稱下方的〔追什麼〕列。
2. **變化的長相 (`shape`)**：實際圖表 + 白話「動起來長什麼樣」→ 圖表本體 + 圖下方的〔怎麼看〕列。
3. **各狀態含義 (`interpretations`)**：🟢🟡🔴 三燈對照**全部列出**、當前燈高亮並標〔現在〕→ 卡片底部燈號對照區。

另有 `order` 欄位＝**擴充順序**（先加的訊號排前面），同 cluster 內卡片依此排序，非檔名字母序。

## Phase 進度

| Phase | 範圍 | 狀態 |
| ----- | ---- | ---- |
| 1 | 契約 + registry 完整性（`core/`、`registry.py`、`config.py`、`logger.py` + 3 個種子 spec，stub compute） | ✅ Done |
| 2 | 運算引擎 + demo 模式（`fetchers/cache.py`、`demo/fixtures/`、六訊號真 `_compute`） | ✅ Done |
| 3 | 實接資料源 + 全流程（`finmind.py`、`yfinance_src.py`、`build.py` 端到端 + 失敗隔離） | ✅ Done |
| 4 | 前端（`web/index.html` 泛型渲染 + 5 widget + 內嵌 fallback + 自動刷新） | ✅ Done |
| 5 | 部署（`.github/workflows/signals.yml` + GitHub Pages） | ✅ 已上線；**每30分自動更新需合併 master**（cron 只在預設分支生效），開發分支目前為 push 即部署 |
| 6+ | 擴充驗證（口述新訊號逐一加，如 `rates_macro` cluster） | ⬜ 持續 |

## 首版種子訊號（cluster：半導體 / 記憶體循環見頂觀察）

計入主燈（名稱一律中性，「轉弱與否」由燈色判定）：
- `yageo_rev_yoy`（bar_chart）國巨(2327) 月營收 YoY。
- `mlcc_basket_ma`（sparkline）被動四雄籃 vs 50MA。
- `ai_breadth`（gauge）AI 類股廣度（站上 50MA 比例）。

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

## 🚀 上線（Phase 5，一步一步）

架構：**GitHub Actions 排程算訊號 → 把 `web/` 當 Pages artifact 部署**。程式都寫好了，
剩下幾個只能在 GitHub 網頁點的設定。網址會是
`https://gt01866xa61.github.io/iOS9-SpringBoard-Headers/`。

1. **拿 FinMind token**（免費）：到 [finmindtrade.com](https://finmindtrade.com) 註冊登入 →
   後台產生 API token 複製。（不加也能跑，只是額度低、月營收可能抓不到。）
2. **加 Secret**：repo → Settings → Secrets and variables → Actions → New repository secret →
   Name `FINMIND_TOKEN`、Value 貼 token → Add。（`FRED_API_KEY` 選配，暫時不用。）
3. **開 Pages（來源選 Actions）**：repo → Settings → Pages → Build and deployment →
   Source 選 **GitHub Actions**（不是 Deploy from a branch）。
4. **先手動跑一次測試**：repo → Actions → 左邊選 `build-and-deploy-signals` → 右邊
   **Run workflow**（可先選 `claude/korea-semiconductor-investment-nb8cgk` 這個分支測）→
   等綠勾。完成後點出現的 `page_url`，或直接開上面的網址。
5. **讓它自動定時更新**：把這個分支合併到 `master`（開 PR → 核准合併）。**排程 (cron) 只在
   master 生效**，合併後才會平日每 30 分、每日再補跑一次自動更新。
6. **加到手機主畫面**：iPhone Safari → 分享 → 加入主畫面；Android Chrome → ⋮ → 加到主畫面。
   之後點圖示打開就是雲端最後一次跑出來的最新燈號，不用開電腦。

常見卡點：Pages 剛開會先 404，等第一次 workflow 部署完才有；某個 symbol（尤其韓股 `.KS`、
期貨 `PA=F`）偶爾抓空 → 那張卡會顯示「資料較舊」沿用上一版，屬正常，下輪通常補回。
