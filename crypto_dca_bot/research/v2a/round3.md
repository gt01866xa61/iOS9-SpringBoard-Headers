# V2-A Round 3 — Risk Engine / 資料流 / 執行層 / V1 沿用整合

> 2026-05-26 起(Asia/Taipei)。Round 2 全段收官後進場(見 `round2.md` 末段「Round 2 全段收官」)。
> Round 3 主軸:把 Round 2 Strategy interface 層級的決定**升一層** — 平台底盤(engine / risk / data / execution / V1 整合)。
> Round 2 累積的 backlog #4(stale 權責 + portfolio-gross 約束)+ Round 1 review pass 留的執行層 over-trading 議題,都在此回收。

---

## 議程(R3-① ~ R3-④,來源 + 依賴關係)

| 議程 | 來源 | 依賴 |
|---|---|---|
| **R3-① Risk Engine 模組邊界** | Round 2 backlog #4(stale 權責)+ #3C review pass watch(portfolio-gross 約束)+ M6 risk-based sizing 落地位置 | 無依賴,先拍 |
| **R3-② 資料流 / event bus / snapshot 組裝** | Round 1 review pass line 131(資料流留 Round 3)+ Round 2 #2B event-driven 拍板後續細節(snapshot 組裝粒度 / event log 規格 / data source registry 實作層級) | 部分依賴 R3-① (Risk Engine 在資料流哪一層 hook) |
| **R3-③ 執行層 over-trading 冷卻機制** | Round 1 review pass line 131(over-trading 顧慮 → 執行層政策)| 依賴 R3-② event 模型 |
| **R3-④ V1 模組沿用整合點** | Round 2 #2D 開頭(circuit_breaker / exchange_api 留 V2-B 但 hook 位置該在架構期定)+ CLAUDE.md V2 邊界(V1 code 為技術資產) | 依賴 R3-①②③(知道整個架構長相才能定 hook 點) |

**建議拍板順序**:R3-① → R3-② → R3-③ → R3-④

---

## R3-① Risk Engine 模組邊界 — 待拍

**核心問題**:Round 2 #3C 拍 PortfolioStrategy 管 per-symbol cap、stale 失能時 fail-safe。但留下三個**整體性風險**沒人管:

1. **portfolio-gross 總曝險約束**(`#3C 補釘 watch`)— 「全組合 gross ≤ 50%」這種總量級,per-symbol min 裝不下
2. **Stale 權責切**(backlog #4)— 資料完整性責任歸 PortfolioStrategy 還是獨立的 Risk Engine?
3. **M6 risk-based sizing 落地位置**(roadmap M6)— volatility targeting / position sizing 放在 Strategy 內、PortfolioStrategy 內,還是獨立 Risk Engine?

**子題拆**(待 Round 3 推進時細化):
- R3-①-a:Risk Engine **要不要**獨立成 module?(與 PortfolioStrategy 邊界)
- R3-①-b:若要,Risk Engine **跑在哪一層**?(Symbol/Portfolio dispatch 之後 final 之前?)
- R3-①-c:portfolio-gross 約束的**輸入語意**(看 final target × cap 算 gross?還是看意圖階段?)

---

## R3-② 資料流 / event bus / snapshot 組裝 — 待拍

**核心問題**:Round 2 #2B 拍 event-driven + LKV + 統一 event log,但**「event 從哪裡生成 / 怎麼 fan-out 給策略 / snapshot 在哪一層組裝」**沒攤。

**子題拆**:
- R3-②-a:event 來源層(exchange websocket / 排程 / 內部 trigger)的統一抽象
- R3-②-b:snapshot 組裝是 **per-fire 重建** 還是 **incremental update**?
- R3-②-c:data source registry(Sub-Q3 拍的 `DATA_SOURCES`)實作層級(Python dict / YAML / DB)— 此題已標 Sub-Q3 留 P1 spec,Round 3 一併拍
- R3-②-d:event log 規格(stale 事件、跳過事件、crash 事件、Telegram 觸發事件統一格式)

---

## R3-③ 執行層 over-trading 冷卻機制 — 待拍

**核心問題**:Round 1 review pass 使用者 raise 川普推文 / TACO 類噪音洗手續費 → 結論「執行層」處理(target → 實際下單轉換)。Round 1 留 Round 3 攻。

**子題拆**:
- R3-③-a:**dead-band**(不動區)在 framework 哪一層?(全局 framework 強制 / 策略 param 各別宣告 / 混合)— 注意 funding skew 策略已自帶 `dead_band` param,框架層要不要再加一層?
- R3-③-b:**cooling period**(冷卻期)— 兩次調倉間最短間隔
- R3-③-c:**regime-aware 降頻**(macro 高 vol 時減少調倉頻率)
- R3-③-d:與 Round 2 #3D overlay 訊號「連續可衰退」紀律的關係(都是「降抖動」家族)

---

## R3-④ V1 模組沿用整合點 — 待拍

**核心問題**:CLAUDE.md V2 邊界明列 V1 code 為技術資產(`exchange_api.py` / `trader.py` / `notifier.py` / `circuit_breaker.py` / `heartbeat.py` / `price_recorder.py` / `chaos_test.py`)。Round 2 #2D 已宣告 API error / partial fill 沿用 V1,但**整體 hook 點地圖**沒定。

**子題拆**:
- R3-④-a:V1 → V2 模組對應(逐個 V1 模組對應 V2 哪一層 hook)
- R3-④-b:V1 `notifier`(Telegram)在 Round 2 累積的多處告警(stale alert / silent divergence / crash 永久停用 / fail-safe 觸發)統一 channel 設計
- R3-④-c:V1 `circuit_breaker` 在 Round 2 #2D 架構契約下的接點(跟「策略缺席」機制的關係)
- R3-④-d:V1 `chaos_test` 在 M1 stale-aware 規格下的角色(它是不是 M1 stress test 的 driver?)

---

## Round 2 carry over 速覽(背景參考)

來自 Round 2 全段收官「carry over」段:
- **架構層歸 Round 3**:R3-① ~ R3-④(本檔)
- **實測題歸 V2-B**:N 值校準 / counter 鋸齒評估 / whipsaw 量化 / trend × funding correlation / M1 stale-aware 驗
- **策略 codify 紀律歸 V2-S**:overlay 訊號連續可衰退禁 binary latch
- **核心拍板沿用至 Round 3** (Round 2 結論不翻盤,Round 3 在這個地基上蓋):
  - SymbolStrategy / PortfolioStrategy 雙 interface(Round 1)
  - event-driven + LKV + 統一 event log(#2B)
  - 「策略缺席」統一模型(stale + crash 共用,#2C2 + #2D)
  - Default + override pattern(Round 2 反覆 8 處)
  - Framework 不假設業務語意(Round 2 反覆否決所有 D 類 option)
  - cap 取最狠 + fail-safe 丟進 min 池(#3D + #3C)
  - always-on 鎖 + NoOp 假人(#3A)

---

## 維護

- 每個 R3-N 子題拍板後,本檔追加日期戳 + 拍板段落
- Round 3 結束後 prepend `decisions.md` + 更新 `glossary.md` + 視情況 review pass

---

## 下一步

R3-① Risk Engine 的 sub-Q 還未確認順序與 frame 細節,**等使用者開議**(按一輪一 axis 原則,frame 已立,實際進場前讓使用者消化議程 + 確認順序)。
