# V2-A Round 3 — Risk Engine / 資料流 / 執行層 / V1 沿用整合

> 2026-05-26 起(Asia/Taipei)。Round 2 全段收官後進場(見 `round2.md` 末段「Round 2 全段收官」)。
> Round 3 主軸:把 Round 2 Strategy interface 層級的決定**升一層** — 平台底盤(engine / risk / data / execution / V1 整合)。
> Round 2 累積的 backlog #4(stale 權責 + portfolio-gross 約束)+ Round 1 review pass 留的執行層 over-trading 議題,都在此回收。

---

## Round 3 運作原則:精簡(2026-05-26 使用者拍)

**只拍「進 V2-B 前非拍不可的架構題」** — pipeline 形狀 / 模組存在性 / 責任歸屬 / hook 點。實測校準(門檻數字 / 公式選型 / 參數)+ 實作細節(資料結構選型 / API 重試)**一律降級 V2-B**。

**litmus test(每個子題進場前先問)**:
> 「這題**不拍**,V2-B 寫引擎骨架會**卡住**嗎?」
> - 卡 → 架構題,Round 3 拍
> - 不卡(只是數字 / 公式 / 細節沒定)→ 降級 V2-B

**配套節奏**:super-題(如 R3-①)**先評估拆 sub-Q,不一次吞**。每個 sub-Q 過 litmus test,過不了的當場降級,避免 Round 3 肥大。

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

**子題拆(2026-05-26 評估 — 精簡原則下拆 3 個,但只 ①-a 是 hard fork)**:

| sub-Q | 內容 | litmus(非拍不可?) | 依賴 |
|---|---|---|---|
| **①-a〔hard fork〕** | Round 2 留的 3 個整體性風險(總曝險約束 / 資料完整性最終責任 / 部位大小 M6),要一個**獨立 Risk Engine 層**裝,還是**塞現有層**(PortfolioStrategy / framework sizing stage)? | ✅ **非拍** — V2-B 引擎骨架的 pipeline 形狀(有沒有 Risk Engine 這一段)非知道不可 | 無,先拍 |
| **①-b** | 若 ①-a = 獨立,Risk Engine 跑 pipeline 哪一段(round1 已有的 "engine sizing" 之前 / 之後 / 合併)+ 看什麼算 gross(final target×cap?意圖階段?) | ✅ 非拍(若 a=獨立)/ ⛔ **若 ①-a ≠ 獨立本題塌縮** | 依賴 ①-a |
| **①-c** | 三個關切各歸哪層(總曝險 → ? / stale 最終責任 → ? / M6 vol-targeting sizing 是否獨立 stage) | ⚠️ 部分非拍(架構落點)— 但 **stale 權責很可能被 ①-a 自動決定**(Risk Engine 存在且管總體 → stale 最終責任歸它;否則維持 #3C)| 依賴 ①-a(部分被 a 吸收) |

**精簡 deferrals(明確降級 V2-B,本輪不拍)**:
- gross 約束**確切門檻數字**(如 ≤ 50%)— V2-B 校準
- vol-targeting **公式選型**(M6 sizing 實際算法)— V2-B 校準
- stale **偵測參數** — 同 Round 2 N 值命運

**評估結論**:**①-a 是唯一 hard fork**,①-b/①-c 大概率在 ①-a 落地後**快速收斂或自動塌縮**(①-a 若選「不獨立」→ ①-b 消失、①-c 退化成「散進現有層」;①-a 若選「獨立」→ ①-b/①-c 變填空)。所以 R3-① 這個 super-題**實質重量集中在 ①-a**,先拍 ①-a、再看殘量。

---

### R3-①-a Risk Engine 存在性 — 拍板 Option C 獨立成一級元件層(2026-05-26)

**拍板:Option C — Risk Engine 獨立成一級元件層**

**機制(管線新增一站)**:
```
Symbol target → 加總 → PortfolioStrategy per-symbol cap
                       → 【Risk Engine】← 新一級元件
                            ├─ portfolio-gross 總曝險上限
                            ├─ M6 vol-targeting sizing
                            └─ 資料完整性最終把關(stale 終責)
                       → 下單構造 → 下單
```

**職責切分定案**:
| 層 | 職責 | 一句話 |
|---|---|---|
| SymbolStrategy | per-symbol target % | 「我想要多少 BTC」 |
| PortfolioStrategy | per-symbol cap multiplier | 「每個幣各自打幾折」 |
| **Risk Engine**(新) | 組合級風控 | 「整桌總預算 + 按波動調倉 + 資料責任」 |

**為何 C(非 A/B)**:
| Option | 否決 / 拍板理由 |
|---|---|
| A 塞 PortfolioStrategy | Round 2 #3C 補釘已證 per-symbol min 模型裝不下 gross,硬塞扭曲語意 + sizing / stale 責任更不搭 |
| B 塞現有 sizing stage | 那一站變雜物抽屜(算量 + gross + vol-target + stale 把關 4 件不相關),違反簡單派「每個元件內部簡單」+ stale 把關塞進「算量」語意不搭 |
| **C**(拍) | 職責單一 / gross 有正確的家 / M6 sizing 有明確落點 / stale 最終責任歸一處 / 對齊頭號共識「風險管理 > 預測」風控應為一級架構公民 |

**精簡原則對齊(關鍵說明)**:
「精簡」分兩層:
1. **元件數量少**(B 贏 — 不加新元件)
2. **每個元件內部簡單**(C 贏 — 每個元件一句話講得清)

Round 1 拍的**簡單派定的是 ②**(每策略內部一句話講得清,參數 < 5 個)。Round 2 已證**一定要有新東西裝 gross**(守門員裝不下) → 爭點不是「要不要加東西」,而是「加的東西要不要**正名**」。C 給它招牌,B 把它藏進別人家變雜物抽屜。**→ C 服務簡單派的 ②,不違反精簡。**

**對 ①-b / ①-c 殘量影響(評估收斂)**:
- ①-b 殘量:**Risk Engine 跟現有 sizing stage 合併還是分開兩站** + **看什麼算 gross**(final target × cap?還是意圖階段?)— 仍需拍
- ①-c 殘量:**部分被 ①-a 自動回答** —— gross 歸 Risk Engine ✓、stale 最終責任歸 Risk Engine ✓。**剩**:M6 sizing 是 Risk Engine 內部 sub-stage 還是另立 stage — 仍需拍
- **建議**:①-b 殘量(2 題)+ ①-c 殘量(1 題)= 3 個小題, **併成一輪「R3-①-bc」一次快收**,符合精簡原則 + 不違反「一輪一 axis」(都是同一個 Risk Engine 的內部結構)

**Watch(留 ①-bc 一併處理)**:
- Risk Engine 是**可插拔策略**(像 PortfolioStrategy 可換 NoOp)還是 **framework 寫死的安全護欄**(像 V1 `circuit_breaker` 不可移除)?直覺後者(風控不該允許「明確選不做」逃生口),但留 ①-bc 拍
- NoOp 模式下 Risk Engine 是否仍 always-on?直覺是(framework-level 護欄不該被使用者關掉),但留 ①-bc 確認

**拍板白話講**:

你選了「**給保全總管一個自己的辦公室**」。

意思是:整體性的風險(整桌總共下多少注、資料壞了誰最終扛責、部位按市場晃動調多大)不會塞進守門員的辦公桌(他桌子小、裝不下整桌總帳),也不會塞進「算量員」的辦公桌(他本來只做 USDT 換算、塞進去會變誰都看不懂的萬能間),而是**多開一間辦公室**叫 Risk Engine,**專門管這三件事**。

雖然「多一間辦公室」聽起來不精簡,但你 Round 1 拍的「簡單」其實是指「**每間辦公室裡的事一句話講得清**」—— 守門員管「逐幣打折」、算量員管「換 USDT 數量」、Risk Engine 管「整體風控」,各做各的、邊界乾淨。這比「省一間辦公室、但其中一間變成什麼都做的萬能間」更好懂、更好維護、出 bug 也好查(知道找誰)。

而且重點:風控是你們團隊一致認定的**第一順位**(「風險管理 > 預測」是 Round 0 就寫死的共識),它**值得自己的家、自己的招牌**,不該寄人籬下。

至於「保全總管實際看什麼數字、跟算量員怎麼分工、能不能被使用者關掉」這些**辦公室內部細節**,留下一輪 R3-①-bc 一次快收。

**下一子軸**:R3-①-bc(併成一題)— Risk Engine 內部結構 + 看什麼算 gross + 是否 framework-level 護欄(可插拔 vs always-on)。3 個小題同質性高,精簡原則下併輪。

---

### R3-①-bc Risk Engine 內部裝修 — 拍板 A / B / B(2026-05-26)

3 個 Block 一輪快收,拍 **Block 1 = A(寫死護欄)/ Block 2 = B(分 2 站)/ Block 3 = B(post-cap)**。

#### Block 1:護欄性質 — 拍 A 寫死護欄 + always-on

**拍板**:Risk Engine 是 **framework 寫死的安全護欄**(類比 V1 `circuit_breaker`),**使用者不能換不能關,連 NoOp 都不給**。

**關鍵哲學區分**(解「framework 不假設業務」表面衝突):
| 維度 | framework 該不該假設? |
|---|---|
| 業務語意(gross 上限 % / vol-target 公式 / stale 閾值)| ❌ 不假設 — 參數化 + V2-B 校準 |
| 安全機制**存在性**(有沒有「總曝險上限」概念、有沒有 Risk Engine 站)| ✅ 可寫死 — 任何系統都有底線 |

**為何 A(非 B 可插拔)**:
1. **M6 是 roadmap 寫死硬規格**(不准固定比例 / 必須 vol-targeting)。NoOp 等於合法繞過 M6 → 規格虛設
2. **「風險管理 > 預測」是 Round 0 頭號共識**,給逃生口 = 動搖根基
3. **與 #3A 不衝突**:#3A 是**策略級**風控(PortfolioStrategy 可選 NoOp,因它是業務判斷);Risk Engine 是 **framework 級**護欄,跟 circuit_breaker 同階。框架有底線、業務有選擇,兩件事

**對 #3A NoOp 模式的影響**:即使使用者把 PortfolioStrategy 全設 NoOp(明確選不做策略級風控),**Risk Engine 仍 always-on**(framework 級護欄不可關)。⇒ 系統**永遠**有總曝險上限 + vol-targeting + stale 終責把關,無逃生口。

#### Block 2:站數 — 拍 B 分 2 站

**拍板**:Risk Engine(風控 3 件事)跟「算量站」(純 USDT 換算)**分 2 站**。

```
... PortfolioStrategy cap
    → 【Risk Engine】 風控:vol-target sizing + gross 上限 + stale 把關
    → 【算量站】     技術轉換:% → USDT → 數量(含 fee / slippage 預估)
    → 下單
```

**為何 B(非 A 合站 / C 4 站)**:
1. **跟 ①-a 同精神** — ①-a 才否決「雜物抽屜」(4 件事塞 sizing stage),A 把算量塞 Risk Engine = 同病換間復發
2. **語意內聚** — Risk Engine 3 sub-stage 都是**組合級風控**(高內聚);算量站是**技術轉換**(不同概念)
3. **vol-targeting vs USDT 換算本質不同**:
   - vol-targeting:算「BTC 該佔帳戶 X%」(風險語意,看波動)
   - USDT 換算:算「X% × 總資金 ÷ 價 = 數量」(技術語意,純數學)
4. C 4 站獨立 = 過切分,否決

**Risk Engine 內部 3 sub-stage 順序** → 精簡原則**降級 V2-B**(引擎骨架知道「Risk Engine 一站 + 算量站一站」即可畫管線)

#### Block 3:gross 看什麼階段 — 拍 B post-cap

**拍板**:Risk Engine 算 gross 約束時,看 **守門員打折後 → Risk Engine 內 vol-targeting 算完** 的總和(post-cap + Risk Engine 內部處理後)。

**為何 B(非 A intent / C post-sizing)**:
1. **gross 本質 = 實際曝險上限**,intent(SymbolStrategy 原意)不是實際 — Symbol 想 100% 但守門員打折後 50%,卡 intent 等於否決有效策略
2. **守門員存在目的** = 全局協調 → Risk Engine 接守門員結果合邏輯
3. **vol-targeting 在 Risk Engine 內先發生** → gross 在它之後算最有意義(看按波動調過後的真實水位)
4. C post-sizing 時序不可能 — Block 2 拍 B 後 Risk Engine 在算量站**之前**,要看 post-sizing 等於 Risk Engine 跑兩次,過工程,否決

**與 Round 2 #3C fail-safe 自然對齊**:Risk Engine 看 post-cap = 看守門員 fail-safe 後的數字。守門員 stale 缺席時 fallback_cap 已進 #3D min 池 → post-cap 已含 fail-safe 降風險結果 → Risk Engine 接到的就是「已往保守倒」的數字,**同方向、無需特別處理** ✓

**完整管線(R3-① 收官後定形)**:
```
SymbolStrategy target % → 加總(per-strategy capital 加權)
  → PortfolioStrategy per-symbol cap → final_target = 加總 × cap
  → 【Risk Engine】(framework 護欄,always-on,不可關):
       vol-targeting sizing → gross 總曝險上限 → stale 最終把關
  → 【算量站】% → USDT → 數量(fee / slippage 預估)
  → orders
```

**整輪 Watch(留 V2-B)**:
- Risk Engine 3 sub-stage 具體順序(vol-target → gross → stale?)
- gross 上限 / vol-targeting 公式 / stale 終責閾值(全 V2-B 校準)
- 算量站滑點 / 手續費演算法(= Round 1 Gap 4 回測成本模型規格題)

**拍板白話講**:

這輪是「保全總管辦公室的內部裝修」,拍了三件事:

1. **這間辦公室不能拆、不能換成空殼**(Block 1 = A)。守門員(策略級風控)你可以選擇不要(擺 NoOp 假人),但**保全總管不行** —— 它是整棟樓的安全底線,跟「斷路器」同一級,framework 寫死、永遠在。為什麼?因為「部位要按波動調大小」(M6)跟「風險第一」是你們開案就釘死的規矩,要是允許關掉,規矩就形同虛設。**注意這跟「framework 不替你決定業務」不衝突** —— framework 不會替你決定「總曝險上限是 50% 還是 70%」(那是你的業務、留給你調),但「**有沒有上限這個概念**」framework 說了算:一定有。

2. **保全總管跟算量員分兩間辦公室**(Block 2 = B)。保全總管管「風險判斷」(按波動定該佔幾 %、總共別超過多少、資料壞了把關),算量員管「純數學換算」(% 換成幾顆 BTC、估手續費)。不把兩個混一間 —— 不然又變成上一輪我們才否決的「什麼都做的萬能間」。

3. **保全總管看「打折後」的數字算總帳**(Block 3 = B)。算「整桌總共下多少注」的時候,看的是**守門員已經打過折**的實際數字,不是策略一開始的獅子大開口。這樣算出來的才是真實曝險。而且剛好跟 Round 2「守門員瞎掉就主動降倉」那條對上 —— 降倉後的數字會自動傳到保全總管手上,不用另外接線。

裝修完,**保全總管這間辦公室的格局就定了**:不可拆 + 跟算量員分開 + 看打折後數字。裡面家具怎麼擺(三個動作的先後順序、上限訂幾 %)留給 V2-B 真正施工時定。

---

## R3-① Risk Engine 議題正式收官 ✓(2026-05-26)

| sub-Q | 拍板 | 一句話 |
|---|---|---|
| ①-a 存在性 | C 獨立一級元件 | 保全總管有自己的辦公室 |
| ①-bc Block 1 護欄性質 | A 寫死 + always-on | 不可拆不可關,跟斷路器同級 |
| ①-bc Block 2 站數 | B 分 2 站 | 風控 vs 算量分家,不當雜物抽屜 |
| ①-bc Block 3 gross 階段 | B post-cap | 看打折後的真實曝險 |

**新增架構元件**:`Risk Engine`(framework 級護欄,always-on)— V2 平台第三個一級元件(SymbolStrategy / PortfolioStrategy / **Risk Engine**)。

**下一子軸**:R3-② 資料流 / event bus / snapshot 組裝(議程已 frame,等使用者開議)。

---

## R3-② 資料流 / event bus / snapshot 組裝 — 待拍

**核心問題**:Round 2 #2B 拍 event-driven + LKV + 統一 event log,但**「event 從哪裡生成 / 怎麼 fan-out 給策略 / snapshot 在哪一層組裝」**沒攤。

**子題拆(2026-05-26 評估 — 精簡尺一量,塌成一刀)**:

原 frame 列 4 個子題(②-a 事件來源 / ②-b snapshot 組裝機制 / ②-c registry 格式 / ②-d event log 格式)。套精簡 litmus(「不拍 V2-B 引擎骨架會卡嗎?」)後,**3 個降級 V2-B,只剩 1 個 hard 架構題**:

| 原子題 | litmus | 去向 |
|---|---|---|
| ②-a 事件來源統一抽象 | 「具體來源(websocket/cron)」是實作;但**底層『同一套 code 跑 backtest + live』的抽象**是 hard 架構 | **升級為 R3-②(唯一 hard 題)** |
| ②-b snapshot 組裝 per-fire vs incremental | rebuild-vs-incremental 是**效能/實作**;但 **no-lookahead 契約**是 hard 架構 | no-lookahead 併入 R3-②;機制降級 V2-B |
| ②-c registry 格式(dict/YAML/DB)| 純實作選型,不影響引擎骨架 | ⛔ 降級 V2-B(Sub-Q3 早標) |
| ②-d event log 格式 | 「統一 event log 存在」Round 2 #2B 已拍;確切 schema 是實作 | ⛔ 降級 V2-B(placement 併入 R3-②)|

**塌縮後的唯一 hard 架構題 = R3-②:backtest/live parity 的資料抽象**
> 引擎透過什麼抽象拿資料,讓**同一套策略 + 引擎 code** 跑歷史回放(backtest)跟即時餵料(live)都**不用改**,且 backtest 的 snapshot 有 **point-in-time no-lookahead 保證**(時間 T 的快照只含 T 當下可得的資料,結構上不可能偷看未來)?

**為何這是 hard 而非可降級**:V2-B 是回測引擎,整個骨架圍著「資料怎麼進引擎」轉;且 backtest/live 分岔是量化頭號死法之一(M5 paper-vs-backtest 正是為抓它而設,架構該從根預防而非靠事後比對)。**litmus = 卡 → 拍。**

**明確降級 V2-B**:事件來源具體種類 / snapshot rebuild-vs-incremental 機制 / DATA_SOURCES registry 格式 / event log 確切 schema。

---

### R3-② backtest/live parity 資料抽象 — 拍板 Option A 統一 event bus + 雙 driver(2026-05-26)

**拍板:Option A — 統一 event bus + 雙 driver(backtest replay driver / live driver)**

**機制**:
```
                  ┌─ backtest driver:讀歷史,按時間順序吐 events
一個 event 介面 ──┤                                           → 引擎 + 策略(完全不知資料來源)
                  └─ live driver:接交易所 feed,即時吐 events
snapshot 由引擎從「已發生的 events + LKV(上次已知值)」point-in-time 組裝
```

**兩個結構性保證(by construction,非 by discipline)**:
1. **backtest/live parity**:backtest / live 餵同一個 event 介面 → 策略 + 引擎**同一套 code**,無從分岔
2. **no-lookahead**:引擎只處理「已發生的 event」→ **結構上不可能**碰未來資料

**為何 A(非 B/C)**:
| Option | 否決 / 拍板理由 |
|---|---|
| B 雙資料路徑 + 共同 market 介面 | 兩條 ingestion 路徑容易悄悄分岔(正是 M5 要抓的病,架構該預防非事後比對)+ no-lookahead 靠紀律維護無結構保證 |
| C pull-based 引擎主動要資料 | 跟 Round 2 #2B 拍的 event-driven(push)相左 + live「阻塞等待」是漏抽象 |
| **A**(拍) | parity + no-lookahead 皆**結構性內建非靠紀律**(同 #3C「fail-safe 丟 min 池而非事後檢查」精神)+ backtest/live 分岔是量化頭號死法值得架構層堵死 + 對齊已拍 #2B |

**前向連結(標記 R3-④,不在此拍)**:
- A 的 **live driver 天然包 V1 `exchange_api`**;**backtest driver 歷史資料跟 V1 `price_recorder`(錄價模組)同血緣** → R3-④ V1 沿用接點,先標記

**Watch(留 V2-B)**:
- event bus 具體實作(in-process queue / 第三方 lib)
- backtest driver 歷史資料來源(自錄 / 交易所 API / 第三方)
- snapshot rebuild-vs-incremental 效能選型

**拍板白話講**:

策略要先用歷史資料**考試**(回測)、過了才用真錢**上場**(實盤)。最怕兩件事:「考試一套題、上場一套題」(parity 不一致 → 回測賺翻、實盤走樣)跟「考試偷看答案」(no-lookahead → 回測假賺、上場現形)。

你選的做法是:**讓考試跟上場用同一條資料管線,而且這條管線結構上只送得出「已經發生」的資料**。

具體說:不管是回測還是實盤,資料都從**同一個「事件介面」**進來 —— 回測時有個「歷史播放器」(backtest driver)按時間順序把舊資料一筆筆吐進來,實盤時有個「即時接收器」(live driver)接交易所推送。但**策略跟引擎完全不知道、也不需要知道資料是歷史還是即時的** —— 它們看到的是同一個介面、同一套 code。

而且因為引擎**只處理「已經吐出來的事件」**,它**根本沒有管道碰到未來的資料** —— 想偷看都沒得看。

為什麼不選「兩條管線、講好要一致」(B)?因為那靠的是**人不犯錯**;你選的 A 靠的是**架構讓你想犯錯都難**。安全的東西要「結構上做對」,不要「靠自律做對」 —— 這跟 Round 2 你拍「守門員瞎了的 fail-safe 直接丟進 min 池、不靠事後檢查」是同一個品味。

---

## R3-② 資料流議題正式收官 ✓(2026-05-26)

精簡尺下塌成一刀,一刀拍完即收官:

| 題 | 拍板 |
|---|---|
| R3-② backtest/live parity 資料抽象 | A 統一 event bus + 雙 driver(parity + no-lookahead 結構性內建)|

**降級 V2-B**:事件來源具體種類 / snapshot 組裝機制 / registry 格式 / event log schema
**前向連結 R3-④**:live driver↔`exchange_api`、backtest driver↔`price_recorder`

**下一子軸**:R3-③ 執行層 over-trading 冷卻機制(議程已 frame,先評估拆法再丟第一刀)。

---

## R3-③ 執行層 over-trading 冷卻機制 — 待拍

**核心問題**:Round 1 review pass 使用者 raise 川普推文 / TACO 類噪音洗手續費 → 結論「執行層」處理(target → 實際下單轉換)。Round 1 留 Round 3 攻。

**子題拆(2026-05-26 評估 — 精簡尺一量,剩一刀但有真選擇)**:

| 原子題 | litmus | 去向 |
|---|---|---|
| ③-a dead-band 在哪一層 | **分層問題是 hard 架構**(有沒有 framework 執行政策層 + 跟策略內部節流怎麼分);threshold 值是實作 | **升級為 R3-③(唯一 hard 題)** |
| ③-b cooling period | 「執行層是否含時間節流」併入 ③-a(同一層的政策);間隔值是實作 | 併入 ③-a;值降級 V2-B |
| ③-c regime-aware 降頻 | regime detection 是 **roadmap V2-E 階段**的事,依賴它的降頻不能現在拍 | ⛔ 降級 V2-E(framework 執行層留 future hook)|
| ③-d 與 #3D「連續可衰退」關係 | 非獨立決定,是 coherence note — 策略訊號級節流跟 #3D 同家族,釐清歸屬即可 | 併入 ③-a(策略層) |

**塌縮後的唯一 hard 架構題 = R3-③:執行政策層的存在 + 分層**
> 過度交易的節流(dead-band 不動區 / cooling 冷卻)該住在哪?**純策略級**(各策略自管,如 funding 已自帶 `dead_band`)/ **純 framework 級**(統一執行政策層)/ **雙層**(策略管訊號穩定 + framework 管最終 order 紀律)?

**為何這是 hard 而非可降級**:V2-B 引擎管線**有沒有一個『執行政策層』(在最終 target → 下單之間,比對 current vs target 決定要不要動)** 直接決定骨架。**litmus = 卡 → 拍。** threshold 值 / cooling 間隔 / regime 降頻全降級。

**明確降級**:dead-band 數值 / cooling 間隔 / regime-aware 降頻(→ V2-E,依賴 regime detection)。

---

### R3-③ 執行政策層存在 + 分層 — 拍板 Option C 雙層(2026-05-26)

**拍板:Option C — 雙層節流** — 策略級管**訊號穩定**、framework 執行政策層管**最終 order 紀律**

**機制**:
```
策略層(各策略內):
  訊號級節流(funding 的 dead_band / overlay 訊號連續可衰退 #3D)
  → 策略 output target%

... PortfolioStrategy cap → Risk Engine → 算量站 → final_order_qty
                                                      ↓
                                          【framework 執行政策層】← 新增
                                            ├─ dead-band:比對 current vs final,
                                            │            差幅 < threshold → 不送單
                                            ├─ cooling period:距上次成單 < 間隔 → 不送單
                                            └─ regime-aware hook(預留,V2-E)
                                                      ↓
                                                   送 order
```

**兩種抖的雙重防線**:
| 抖的來源 | 由誰擋 | 為什麼 |
|---|---|---|
| 訊號自己抖(如 funding 小波動) | **策略級**(funding `dead_band` 等)| 策略最懂自己訊號該多鈍,是訊號語意一部分 |
| 聚合後才抖(守門員 cap 每 bar 變 + vol-targeting 隨波動變 + 多策略 capital 權重挪)| **framework 執行層** | 只有 framework 看得到最終 order;策略看不到擋不掉 |

**為何 C(非 A/B)**:
| Option | 否決 / 拍板理由 |
|---|---|
| A 純策略級 | **聚合後抖無人管**(真漏洞:守門員 cap + vol-targeting 每 bar 變,策略看不到)+ 無法做全局紀律(「每分鐘最多調一次」)+ 每策略重造輪子 |
| B 純 framework | 剝奪策略「我這訊號本來就該很鈍」的訊號語意表達(funding `dead_band` 是策略設計一部分) |
| **C**(拍) | 兩種抖**不同地方產生**要兩個地方擋 + 每層單一職責各自簡單(精簡第 ② 層 — 元件內部簡單)+ #3D 連續可衰退訊號紀律自然落策略層、對齊 |

**對 funding strategy 的影響**(具體案例 sanity check):
- funding 自帶的 `dead_band` 參數**保留**(訊號層,策略語意)
- framework 執行政策層**額外擋聚合後抖**(funding target × cap × vol-target 變動但實際差幅小 → 不送單)
- 兩層各自做,**沒有覆蓋衝突**(策略層擋的是「訊號該不該動」,framework 層擋的是「動了之後該不該下單」)

**與 Round 2 #3D「連續可衰退訊號紀律」對齊** ✓:#3D 是 overlay 訊號層紀律,屬**策略級節流家族**;R3-③ Option C 把這條紀律明確歸位到策略層,跟 framework 執行層各管各的、不重疊。

**Watch / 降級**:
- dead-band 確切數值 / cooling 間隔 — V2-B 校準
- framework 執行層是**獨立 stage** 還是**算量站/下單構造的 sub-step** — V2-B 實作(架構只需「有這個政策」)
- **regime-aware 降頻** — V2-E(依賴 regime detection),framework 執行層**預留 hook** ← 標記
- framework 執行層支援**幅度節流(dead-band)+ 時間節流(cooling)+ regime hook** 三種能力,具體啟用 / 數值 V2-B

**拍板白話講**:

過度交易其實有**兩種抖**,要在兩個地方各擋一種。

**第一種抖:訊號自己在抖**。例如 funding 數字小幅波動 → funding 策略的 target 跟著小變。這種抖**策略自己最懂該不該擋** —— 它知道「funding 抖個 0.001% 不算事」這種語意。**funding 策略本來就自帶 `dead_band` 參數**處理這個,我們不動。

**第二種抖:聚合之後才冒出來的抖**。就算每個策略訊號都很穩,**最後下單量還是會抖** —— 因為守門員每根 bar 都在重算打幾折、Risk Engine 的波動目標每 bar 都在動、多策略的資金權重也在變。**這些加總起來、那個最終下單數字**就會小幅在跳。**策略自己看不到這個**(它只管自己的 target),要 framework 在「都算完、要送單之前」攔一手 —— 比對「現在持倉」跟「想要的最終量」,差距太小就**不送單**(dead-band),或剛調過就**冷卻一下**(cooling)。

為什麼不只挑一層擋?
- **只擋策略層** = 漏掉「聚合後抖」(那是真漏洞,守門員跟波動目標每根 bar 都在動)
- **只擋 framework 層** = 把策略本來自己設定的訊號穩定度(funding 的 dead_band)抹掉,違反策略設計者的本意

剛好你 Round 2 那條「訊號要會自動降溫不能卡死」(#3D 你補的 watch)本來就是「訊號級」的紀律,**自然落在策略層**,跟這輪拍的 framework 執行層各做各的、不打架。

至於「市場特別瘋的時候要不要少調倉」(regime-aware 降頻),那個需要先有「**怎麼判斷市場特別瘋**」(regime detection,roadmap V2-E 的事),所以不在這刀拍 —— 但 framework 執行層**預留一個掛鉤的位置**,等 V2-E 真的把 regime detector 蓋出來再接上去。

---

## R3-③ 執行層 over-trading 冷卻議題正式收官 ✓(2026-05-26)

精簡尺下塌成一刀,一刀拍完即收官:

| 題 | 拍板 |
|---|---|
| R3-③ 執行政策層存在 + 分層 | C 雙層(策略訊號級 + framework 執行政策層)|

**新增架構元件**:`framework 執行政策層`(管 dead-band / cooling / regime hook),位於算量站後、送單前。

**降級 V2-B**:dead-band 數值 / cooling 間隔 / 執行層是獨立 stage 還是 sub-step
**降級 V2-E**:regime-aware 降頻(依賴 regime detection,執行層預留 hook)

**下一子軸**:R3-④ V1 模組沿用整合點(已累積 3 個前向連結:`exchange_api`、`price_recorder`、`circuit_breaker`)。Round 3 收尾在即。

---

## R3-④ V1 模組沿用整合點 — 待拍

**核心問題**:CLAUDE.md V2 邊界明列 V1 code 為技術資產(`exchange_api.py` / `trader.py` / `notifier.py` / `circuit_breaker.py` / `heartbeat.py` / `price_recorder.py` / `chaos_test.py`)。Round 2 #2D 已宣告 API error / partial fill 沿用 V1,但**整體 hook 點地圖**沒定。

**子題拆(2026-05-26 評估 — 精簡尺一量,大幅塌縮 + 關鍵發現)**:

**關鍵發現**:多數 V1 模組是**實盤/部署(V2-D)**的事,V2-B 是回測引擎、根本用不到 → 精簡 litmus(「不拍 V2-B 引擎骨架會卡嗎?」)下**大幅塌縮**。

| 原子題 / V1 模組 | V2-B 用得到? | 去向 |
|---|---|---|
| ④-a 模組對應地圖 | 部分(資料側 + 執行側介面)| 拆出唯一 hard 題(見下)|
| `exchange_api` | ✓(回測資料來源)| R3-② live driver(資料IN)+ ④-a live executor(下單OUT)— 已決 |
| `price_recorder` | ✓(回測歷史資料)| R3-② backtest 資料源 — 已決 |
| `trader` | ✓(輸出側介面定義)| ④-a live executor driver — **本輪唯一 hard 題決** |
| `notifier`(④-b)| ✗(回測無 Telegram)| 統一 alert sink 接縫(thin),channel 設計 ⛔ V2-D |
| `circuit_breaker`(④-c)| ✗(回測無實盤)| #2D 框架級 crash 處理(架構已決)+ live 實作 ⛔ V2-D |
| `heartbeat` | ✗(回測無 liveness)| 純維運監控 ⛔ V2-D |
| `chaos_test`(④-d)| ✓(M1 stress test driver)| V2-B 測試基建(note,非架構決定)|

**塌縮後的唯一 hard 架構題 = R3-④:executor / broker 抽象(輸出側 parity)**
> 訂單**執行**怎麼讓 backtest 跟 live 用同一套 code?——這是 R3-② event bus(**輸入側** parity)的**輸出側鏡像**。R3-② 讓「資料怎麼進」source-agnostic,R3-④ 讓「訂單怎麼出」destination-agnostic。V2-B 回測引擎需要一個「模擬成交器」,介面要跟 live 的 `trader.py` 一致。

**為何這是 hard 而非可降級**:V2-B 回測引擎的**輸出端**(order → 成交)非有不可,且要跟 live 同介面(否則輸出側 backtest/live 分岔,跟 R3-② 否決 B 同病)。**litmus = 卡 → 拍。**

**明確降級 V2-D(非 V2-B,實盤/部署才需要)**:notifier channel 設計 / circuit_breaker live 實作 / heartbeat 維運監控 — 全是 live 才用到、回測用不到的。

**R3-④ 實質 = 1 個 hard 決定(④-a executor 抽象)+ 一張「V1 模組落點地圖」**(多數已由前面拍板自動決定 or 降 V2-D),不是 super-題。

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
