# HANDOFF.md — 股癌訊號燈 多 agent 交接文件

最後更新：2026-08-09（新增每卡驗證目的副標，並把兩個 AI 外溢主題做 UI 分組）。
任何 agent（Codex、Claude、其他）接手前先讀完本檔。本檔是活文件——交接資訊變動時直接改這份。

---

## 0. 一分鐘定位

- **專案**：「股癌訊號燈」——把 Podcast《股癌》各集隨口提到的市場觀測訊號，量化成
  紅黃綠燈的網頁看板，全自動更新。
- **Repo**：`gt01866xa61/iOS9-SpringBoard-Headers`（**借殼**：根目錄 `System/`、`usr/`
  是 iOS dyld cache dump 不要動；`crypto_dca_bot/` 是另一個獨立專案不在範圍）。
- **工作分支**：`master`——就是 master，開發直接上 master，push 即自動測試部署
  （歷史開發分支 `claude/korea-semiconductor-investment-nb8cgk` 已合併退役，勿用）。
- **程式全部在** `gooaye_signals/` 底下。
- **正式網址**：https://gt01866xa61.github.io/iOS9-SpringBoard-Headers/
- **詳細架構與訊號清單**：讀 `gooaye_signals/README.md`；逐 commit 歷史：`PROGRESS.md`。

## 1. 核心原則（使用者明訂，凌駕一切）

1. **第一性原理**：先砍到最簡，再一點點把真正需要的補回來；不做沒意義的事。
2. **數據鐵律**：所有呈現的數據必須同時滿足「真實×可規格×可溯源」。無法同時滿足
   的內容，寧可不顯示。手動維護的數據也一樣——每個數據點必附出處（src 欄位）。
3. **分工鐵律**：使用者口述訊號、agent 實作——交付到「訊號忠實呈現（追什麼／怎麼看
   ／各燈含義）」為止。**不提供投資判斷、不附下單建議、不加投資免責叮嚀**。
4. 每個訊號必答四問：①驗證什麼 ②追什麼 ③變化長什麼樣 ④各燈分別什麼意思——
   都是 SignalSpec 的一等公民欄位（purpose / track / shape / interpretations）。`purpose`
   必須是一句固定可見的副標，不能只把目的藏在展開內容。

## 2. 目前進度（2026-07-18）

**平台**：Phase 1–5 全部完成上線，現在處於 Phase 6+（使用者口述新訊號→逐一擴充）。
**17 個訊號、3 個 cluster**：

| cluster | 主題 | 計主燈 | 佐證 |
|---|---|---|---|
| `semi_memory_top`（order 1）| 半導體/記憶體循環見頂 | 國巨月營收YoY、被動元件籃vs50MA、AI廣度 | 記憶體強弱表、鈀/銀、觀測名單、毛利率／CSP CapEx／現貨合約價差／CXMT量產 |
| `leadframe_osat`（order 2）| 導線架/封測供應鏈（EP678）| 四雄營收動能表、四雄籃vs50MA | 四雄+銅體檢表 |
| `onprem_hybrid`（order 3）| 地端/混合雲 AI（Satya 反向資訊悖論討論串）| DELL+HPE籃、HPE訂單動能（手動季更）| 事件簿、Menlo開源風向×體量 |

前端把 `leadframe_osat` 與 `onprem_hybrid` 共同包在「AI 榮景外溢驗證」區塊：前者驗證
供應鏈外溢，後者驗證客戶層外溢。**只合併 UI，不合併兩個 cluster 的主燈投票。**

**今日燈況（07-18，來源 data/history.json）**：總燈黃。cluster1 黃但**內含 AI 廣度紅**
（紅1黃2綠0，三主題中最接近轉紅＝主升段尾聲警示）；cluster2 黃（上週綠，基本面資金面
同步降溫）；cluster3 黃（預設「未驗證維持假設」，等 HPE 9 月財報）。

**懸而未決（等使用者拍板）**：
- 訂單卡綠燈門檻：目前「單季 +20% 即綠」，備選「連兩季增才綠」（快 vs 穩）。
- Menlo 年中報告（約 2026-07 底發布）公布後要補數據點。

## 3. 架構速覽（改東西前必懂）

- **一個訊號＝一個檔** `signals/<id>.py`，export `SIGNAL: SignalSpec`；`registry.py`
  自動探索（id 必須==檔名）。放進去就是註冊，無中央清單。新增訊號：複製最像的
  既有訊號檔改（`_template.py` 是空骨架）。
- **compute 是純函式**：不抓網路、不看時鐘、不寫檔（事件窗用資料檔內 as_of 錨定）。
- **資料源**（`fetchers/`，SOURCE_REGISTRY）：
  - `finmind_revenue`：台股月營收→YoY（匿名可用，FINMIND_TOKEN secret 未設）
  - `yf_close`：yfinance 收盤（.TW/.TWO/.KS/美股/期貨；threads=False＋單檔補抓；
    回傳 {"series", "asof"}——asof 給表格「資料至」標示）
  - `manual_series`：讀 repo 內 `data/manual/<key>.json`——給「無公開 API 但有公開
    出處」的季度/事件數據；每點必附 src
- **前端**：單檔 `web/index.html`，5 種 widget 泛型分派（light_card/bar_chart/gauge/
  sparkline/table），零函式庫零 CDN。新增用既有 widget 的訊號**不用碰前端**。
  內嵌 fallback 由 `web/build_embed.py` 重新產生。
- **說明層級**：每張卡收合時固定顯示 `purpose`；展開後才顯示較長的 `track`／`shape`／
  `interpretations`。`CLUSTER_GROUPS` 只控制共同 UI 外框，不改 cluster 或總燈計算。
- **韌性**：per-binding/per-signal 隔離、部分資料可降級續算、last-good+stale、原子寫、整輪保底；
  時區鎖死 fixed UTC+8（禁 IANA/ZoneInfo）。
- **資料狀態**：卡片分開標示 `ok`（本輪完整無錯）、`usable`（仍可判讀）、`degraded`
  （部分來源失敗）與 `data_as_of`／`sources`；灰燈或 stale 不寫入新燈史。
- **燈史**：`data/manual` 旁的 `data/history.json` 由 CI bot 每輪 commit 回 repo
  （`[skip ci]`），測試絕不可動它（phase3 已導向暫存檔）。

## 4. CI/CD——接力環（背景故事很重要，別亂改）

GitHub 免費基建三種故障都實測踩過：cron 大量丟包（尖峰 12 班發 1 班）、Pages 部署
暫時性失敗、hosted runner 佇列 15 分鐘拿不到機器被平台取消。現行架構：

- `signals.yml`：build→deploy（三段式重試 30s/60s）→最後一步 dispatch pacer（接力）。
- `pacer.yml`：睡 22 分→補發 build→**自派下一棒**（不依賴 build 有跑起來——佇列取消
  時 workflow_run 與 relay 都不會發生，自派是唯一活路）。
- cron（每 10 分離峰分鐘 + 每日 22:47Z 保底）＝**重啟票**不是節拍器；環是主保證。
- 防失控：窗外自動斷鏈（台北 09–22 平日）、發車前查重、concurrency 收斂多棒。
- 前端 stale 橫幅時段感知：平日盤中 90 分、夜間週末 26 小時才亮＝真異常才警報。
- **GITHUB_TOKEN 補發的 run 跑完不會觸發 workflow_run**（防遞迴的隱藏規則，
  三次斷鏈的根因）——所以兩條邊都是明確 dispatch，別「優化」回級聯。

## 5. 手動數據維護行事曆

| 檔案 | 更新時機 | 內容 |
|---|---|---|
| `data/manual/hpe_dell_ai_orders.json` | HPE 財報約 3/6/9/12 月；Dell 約 2/5/8/11 月 | 單季 AI 訂單、backlog（十億美元），附 SEC 8-K/新聞稿出處 |
| `data/manual/onprem_events.json` | 使用者口述或查證後隨時 | 事件必帶 date/camp/dir(+/-/0)/**type**(endorse/supply/data/narrative)/src；記得同步 as_of |
| `data/manual/menlo_opensource.json` | 年中約 7 月底、年末約 12 月 | pct（開源占比）＋ total_b（模型API總支出，分母）；缺分母會自動退回風向-only |
| `data/manual/memory_gross_margin.json` | 美光財報約 3/6/9/12 月 | 同一 **GAAP 合併**口徑的季毛利率；只是可連續代理，不能寫成產業平均 |
| `data/manual/csp_capex_guidance.json` | Alphabet／Microsoft／Meta 每次財報後 | 只收正式 IR／法說明說的 `raise/maintain/slow/cut`；缺公司留灰列，不能用媒體推測補 |
| `data/manual/memory_spot_contract_gap.json` | TrendForce/DRAMeXchange 每月更新後 | 只收同品項、同幣別快照；現貨與合約更新日都要原樣紀錄，至少兩筆才判趨勢 |
| `data/manual/cxmt_ramp.json` | 查證到實際里程碑時 | `stage` 必須是 plan/construction/volume/delay/restriction；**公告擴產不等於量產，小量量產也不等於大型供給已到** |

規則備忘：事件簿綠燈需「淨值≥+3 **且**窗內至少一筆 endorse」（雲廠自家 GA/擴國是
supply，蓋房子≠有人入住）；Menlo 卡是「風向×體量」雙變數（占比降但推算額升＝黃，
防分母效應誤讀——使用者親自抓過這個 bug，別改回單占比判燈）。

記憶體四張早期預警（`memory_gross_margin`、`csp_capex_guidance`、
`memory_spot_contract_gap`、`cxmt_ramp`）目前全是 **佐證面板**（`in_master=False`）：
它們同時設為 `featured=True`，所以會在主燈卡後直接顯示、**不可藏回補充面板**；但不能因為
單一公司代理、公司名單缺項、首筆價差快照或長週期施工新聞，就私自改變原本三支主燈的
cluster 主燈。來源優先：公司 IR／財報、監管／交易所文件；價格採 TrendForce／
DRAMeXchange；Reuters／AP 只做交叉核對。未達一手來源／連續資料門檻，留黃或灰，未來
要納入主燈，先取得使用者明確決定與足夠連續、多來源資料。

## 6. 工作流程鐵律

- 開工：`git status` + `git log --oneline -10` + `git pull --rebase origin master`
  （CI bot 會自己 commit 燈史，**push 前後都要 rebase**，衝突重試是常態）。
- 每完成一個邏輯單元立刻 commit；每次 commit 後在 `PROGRESS.md` 表頂加一行
  `YYYY-MM-DD HH:MM (Asia/Taipei) | hash前7碼 | 一句話`。
- **push 前 gate（不可跳過）**：`cd gooaye_signals` 跑
  `python -X utf8 tests/test_phase1_specs.py` ～ `test_phase4_frontend.py` 四個全過
  ＋ `GOOAYE_DEMO=1 python -X utf8 build.py`
  ＋ `GOOAYE_DEMO=1 python -X utf8 web/build_embed.py`
  ＋（改到版面時）目視檢查。
  PowerShell 先設 `$env:GOOAYE_DEMO='1'`；`-X utf8` 防 Windows CP950 終端輸出失敗。
- 遇到 API 錯誤/異常立刻停手回報，不硬 retry。
- 新增台股代號**必先查證上市/上櫃**（.TW vs .TWO）——威剛 3260.TWO、長科 6548.TWO、
  界霖 5285.TW 都是踩過或差點踩的坑，勿憑直覺。

## 7. push 權限（目前狀態）

- **Claude Code**：使用者已授權全自動——直接 push master，不用問。
- **Codex（保守模式，使用者明訂）**：commit 可以自己做，**push 到 master 前先跟
  使用者確認**。觀察穩定後使用者可能放寬——放寬時改本節即可。

## 8. 給接手 agent 的開場（使用者只需貼這段）

```
你正在接手「股癌訊號燈」專案。第一件事：讀 repo 根目錄的 HANDOFF.md 全文，
然後讀 gooaye_signals/README.md 與 PROGRESS.md 最上面 20 行。
接著跑 git status + git log --oneline -15 + git pull --rebase origin master 對齊。
規矩都在 HANDOFF.md（核心三鐵律、測試 gate、push 權限=保守模式）。
讀完後：使用者訊息裡有任務就直接做；沒有就簡短回報你理解的現狀並等指示。
```
