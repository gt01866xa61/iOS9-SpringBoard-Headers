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

## ⭐ 設計原則（永遠遵守，凌駕一切）

1. **第一性原理**：先把所有東西砍到剩本質，再一點一點把「真正需要」的補回來。
   **不做沒意義的事**（例：不為了「有出處欄位」而補假集數——那對數據真實性零貢獻）。
2. **所有呈現的數據必須同時滿足【真實 × 可規格 × 可溯源】**——這是本專案存在的理由：
   - **真實**：來自真實資料源（FinMind／yfinance…），絕不用假造／示範數字充當正式內容。
   - **可規格**：每個數字有精確、可重現的定義（公式寫在該 signal 的 `compute` 與「怎麼看」）。
   - **可溯源**：能追回原始來源（哪個代碼、哪個資料源、哪個時間點）。
   
   **任何無法同時滿足這三點的內容，寧可不顯示，也不掛上去。** 新增訊號前先問自己這三題。

## 🔑 新增一個訊號（最重要的日常操作）

平台的第一設計原則：**加一個訊號 = 複製一個檔、改它、完成**。零中央清單、零前端、
零 schema 改動（90% 情況）。

1. `cp signals/_template.py signals/<你的id>.py`（或複製最接近的既有訊號檔）。
2. 編輯那一個檔：`id`(=檔名)、門檻常數、`bindings`(資料源)、純函式 `_compute`、
   四個 `interpretations`、`track`/`shape`/`order`/`cluster`/`widget`/`tags`/`in_master`。
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

## 訊號清單

### cluster 1：半導體 / 記憶體循環見頂觀察

計入主燈（名稱一律中性，「轉弱與否」由燈色判定）：
- `yageo_rev_yoy`（bar_chart）國巨(2327) 月營收 YoY。
- `mlcc_basket_ma`（sparkline）被動四雄籃 vs 50MA。
- `ai_breadth`（gauge）AI 類股廣度（站上 50MA 比例）。

佐證面板（`in_master=False`）：記憶體相對強度、原物料(鈀/銀)、觀測名單。

### cluster 2：導線架 / 封測供應鏈觀察（EP678，Phase 6 首個擴充）

核心觀點：導線架是傳統封裝的上游瓶頸、封測獲利行情能否延續的先行溫度計；
但「產業缺貨（基本面）與股價表現（資金面）是兩條線」——所以拆成兩條線各一個訊號。

計入主燈：
- `leadframe_rev_yoy`（table）導線架四雄營收動能——基本面線：每家 YoY 動能燈
  （綠＝未連降且 YoY>0、黃＝連降1月/年減中、紅＝連降≥2月），真值表彙總；
  四家並列可辨「全面延續 vs 一家獨撐」。
- `leadframe_basket_ma`（sparkline）導線架四雄籃 vs 50MA——資金面線：最缺不一定最漲。

佐證面板：`leadframe_watch` 四雄逐檔體檢＋銅(HG=F，成本推力參考、不計入燈號)。
四雄代號已逐檔查證交易所：順德 2351.TW、長科 6548.TWO（上櫃）、界霖 5285.TW、一詮 2486.TW。

### cluster 3：地端 / 混合雲 AI 觀察（Satya 反向資訊悖論文後的討論串）

核心問題：「企業自建/地端 AI 這條路燒不燒得起來」——拆成「有人真的掏錢了嗎」
（訂單）與「有人敢具名站台嗎」（名單），加一支提前聞味道的股價溫度計。

計入主燈：
- `onprem_basket_ma`（sparkline）DELL＋HPE 等權籃 vs 50MA——資金面即時溫度計。
- `onprem_ai_orders`（table，手動季更）HPE 單季 AI 訂單為主軸（官方：backlog 主要
  企業+主權）、Dell 對照；±20% QoQ 三態，預設黃＝「未驗證，維持吃力不討好假設」。

佐證面板：`onprem_events` 事件簿（近 180 天正負淨值給燈，逐筆附出處）、
`menlo_opensource` Menlo 開源占比（半年更，19→13→11 敘事照妖鏡）。

新資料源 `manual_series`：讀 repo 內 `data/manual/<key>.json`——給「無公開 API 但有
公開出處」的季度/事件型數據用，每點必附 src，財報後手動補一筆。

主燈真值表（各 cluster 共用）：🔴 ≥2 紅｜🟡 任一紅/黃｜🟢 全綠；總燈取各 cluster 最高嚴重度。

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
   觸發是「接力環」：build 最後一步發車 `pacer.yml`，pacer 交易時段內睡 22 分鐘再發車
   build，兩條邊都走明確 workflow_dispatch（GITHUB_TOKEN 補發的班次跑完不會觸發
   workflow_run——實測三次鏈全斷在這，所以不能靠級聯）。此外每棒 pacer 睡醒後
   一律自派下一棒——build 可能在佇列階段就被平台取消（2026-07-09 實測 runner 供應
   異常，排 15 分鐘被砍、零 step 執行），鏈的存活不能依賴 build 有跑起來。cron
   （17/47 離峰分鐘）與 push 是環的重啟入口；GitHub cron 實測大量丟班（2026-07-06
   上午 14 班只發 1 班），環是主保證、cron 是冗餘。
6. **加到手機主畫面**：iPhone Safari → 分享 → 加入主畫面；Android Chrome → ⋮ → 加到主畫面。
   之後點圖示打開就是雲端最後一次跑出來的最新燈號，不用開電腦。

常見卡點：Pages 剛開會先 404，等第一次 workflow 部署完才有；某個 symbol（尤其韓股 `.KS`、
期貨 `PA=F`）偶爾抓空 → 那張卡會顯示「資料較舊」沿用上一版，屬正常，下輪通常補回。
