# V2 Decisions Log(決策日誌)

> 重要決策記錄,每個決定一段:日期 + 決定 + 理由。
> 這是 V2 旅程的 ledger(分類帳)— 寫下來才不會忘記當時為什麼這樣決定。
> **新的放最上面**(倒序)。

---

## 2026-06-14 — T1+T2 完成、三策略全 FAIL M2、regime 診斷、路二=B(待拍)、交接 Codex

**完整脈絡見 `handoff_codex_2026-06-14.md`(本日交接文件,數字總表在該檔 §4)。**

### T1 績效指標層 ✅(commit `1b47df5`)
`v2/analysis/metrics.py`:Sharpe/Sortino/maxDD/CAGR/Calmar/滾動 Sharpe。
純 stdlib、可釘死;std 用 population(ddof=0,刻意)、年化 365(crypto 24/7)。
Backtest 加 mark-to-market `equity_curve`(不進 fingerprint)。

### T2 walk-forward ✅(commit `45651be`)— ★ 三策略全 FAIL M2
低頻 feasibility 修正:三策略 30/3 每窗僅 2~5 筆交易 → per-window WFE = 噪音。
拍板(使用者):**pooled OOS WFE(主)+ 70/30 single-split(對照),兩法一致
才信**。真資料結果(19 窗,M2 閘 WFE>50%):
- S1 Donchian:pooled **20.6%** / split **−37.5%** → FAIL
- S2 FundingSkew:**39.1%** / **4.2%** → FAIL
- S3 +MacroOverlay:**28.8%** / **−24.7%** → FAIL
三者 in-sample Sharpe 0.96~1.56 → OOS 崩(0.04~−0.55),兩法結論一致(可信)。
**健康訊號非 bug**(risk #4「數字一路縮」);M2 閘做了它該做的事。

### regime 診斷 ✅(commit `1eb8418`,工具固化:`v2.tools.regime_diagnostic`)
「2024-2026 為什麼垮」答案:**看天吃飯,不是壞掉**。OOS 19 窗按 BTC net ±15%
分桶:上升趨勢 6 窗三策略全賺(S1 +19.9%/S2 +44.1%/S3 +22.6%,勝率 83-100%)
= edge 真實;盤整 10 窗全垮(−2~−4%);下跌 3 窗全挨打(S2 −38% 接刀)。
in-sample 2020-21 = 史詩牛市(ETH +463%/+404%)→ in-sample 好看 = 天時。
OOS B&H 對照 Sharpe 0.06(策略 −0.55)→ 該段整體難做 + 策略還輸躺平(whipsaw 稅)。
**→ 三策略全趨勢型、高度相關 = 策略池 DNA 單一(違反「兩兩相關 ≤0.5」設計目標)。
使用者拍板:每個新策略都要過 regime 診斷這關。**

### 路二(收 funding 風險溢酬)解剖 — 結論 B:結構性關閉(**分析結論,待 Jeff 拍板**)
軍師端新 frame:路一=自動化 Jeff 已驗證手動策略(稍後);路二=收風險溢酬(本輪驗)。
解剖 FundingSkew:**現貨持有者收到的 funding = $0**(funding 是永續多空互付),
它 100% P&L = 價格 beta,funding 只是進出場計時器 → regime 實測趨勢型的根因。
溢酬本身很肥:BTC 年化 +11.8%/ETH +14.2%,負 funding 只占 15%;純 basis carry
(現貨多+永續空)逐年**每年皆正**,理想化 Sharpe 10.6/maxDD 1.5%。
但收它**必須做空永續腿** → long-only spot 邊界下無法對沖 → **不是做法問題(A),
是結構死路(B)**。**basis trade 悖論**:delta-neutral carry 的風險(maxDD 1.5%)
遠低於現行方向性賭注(maxDD 50-73%)—「不碰衍生品」的邊界反而擋掉風險最低的
機會。**決策點(等 Jeff):維持 strict long-only(路二死)vs 放寬允許
delta-neutral basis trade(路二活)。** 代價:保證金/強平、兩腿成本、對手方
風險(FTX 殷鑑)、M8 資安擴面;真實淨 carry 估 ~8-12%/年。

### 交接
本日專案自 Claude Code 遷移至 Codex。交接文件 `handoff_codex_2026-06-14.md`
(環境/敘事/數字/開放問題/慣例陷阱/caveats 全收錄)。**T3-T9 暫停,停點=
等 Jeff 拍上層方向(路二邊界 + 策略池 DNA)。** 交接時 255 tests 全綠零 skip。

---

## 2026-06-13 — V2-T 前置 2 第 1 件:組合視角 sizing(rejections 11206→0)+ P&L 跳動成因

**背景**:前置 2 動工前用真資料重跑(`v2/tools/real_demo.py`)確認 baseline:
S1 Donchian 958 rejections / S2 FundingSkew 11206 / S3 +MacroOverlay 968,
三場 rejections **全為 `insufficient_cash`**。

**真資料診斷揪出 dominant 成因**(原以為是 within-fire 多單排序問題,**錯**):
引擎 event-driven 一次只 fire 一個幣(BTC kline 只叫醒 BTC 策略),Risk Engine
的 gross sub-stage **只看「本 fire 的 symbol」**、用總 equity 當基數無視別處
已押的錢 → 單一幣被推到 gross_limit,加上別處持倉後總曝險破表 → 產生**結構上
買不起的單** → executor `insufficient_cash`。實測:每筆 reject 的 need/have =
**15~31×**,**0 筆**是「加倉差一點」的小單,**0 個 fire** 同時有買單和賣單。

→ **重要 frame 修正**:拍板的三件裡,**(2) sell-before-buy 在這事件驅動架構
下打不到這些 rejections**(需要「同 fire 又買又賣」,實測一次都沒發生);
**(1) delta-aware 字面(target−current)跟現有 `execution_policy.delta_q` 數值
相同**,也無效。真正治本的是讓 sizing **看整桌**。

**拍板(使用者選):第 1 件做成「組合視角 sizing」**(portfolio-aware gross):
`apply_risk_engine` 加 `held_elsewhere_pct`(本 fire 沒在管的 symbol 已持有的
曝險),gross 改看「整桌 = 本 fire vol-targeting 後 + 別處已持有」。總曝險上限
是對**整個帳戶**不是對單一幣;本 fire 的 symbol 只配剩餘額度,別處持倉各自
fire 時才自我 rebalance。`gross_limit=0.95` 留 5% buffer → 買單結構上恆可成交
(friction 0.15% << 5%)→ `insufficient_cash` **誠實歸零**。

**鐵則對齊**:這**不是**「餘額不足就裁切到能買的量」(那是作弊);是**從源頭
只配給剩餘額度** — 真人不會對只剩 5% 現金的帳戶丟 95% 市價單。每個 reject
路徑對得上 Binance:市價單 notional > 餘額 = 整單拒,我們改成根本不產生那張單。

**真資料結果(BTC+ETH,default exec policy)**:

| 場景 | rejections | fills | **最高曝險** | equity 前→後 |
|---|---|---|---|---|
| S1 Donchian | 958 → **0** | 111 → 111 | 97.3% → 97.3% | $137,324 → $137,324 |
| S2 FundingSkew | 11206 → **0** | 379 → 396 | **100.0% → 97.1%** | $48,672 → **$59,693** |
| S3 +MacroOverlay | 968 → **0** | 177 → 187 | **100.0% → 97.3%** | $197,854 → **$225,679** |

**★ P&L 跳動成因(寫死,免得日後看到數字變動以為 bug)**:S2/S3 equity 上升
**不是引擎變寬鬆讓它多賺**,是**髒交易清掉後的誠實數字**。三條鐵證:
1. **S1 一個字都沒變**(equity / fills / 曝險全等)→ 純清帳,958 張注定被拒的
   單擋在源頭,零真實交易被動。
2. **S2/S3 最高曝險「下降」**(100% → 97%)→ 引擎變**更緊**。以前 cross-
   contention 讓某幣把帳戶吃到 100% 滿、另一個被拒;現在整桌封頂。最高曝險
   降了、獲利卻升 → 多賺的不可能來自「押更多」。
3. **手續費還變高**(S2 $1,448→$1,645)→ 也不是「少交易省成本」。
   → 唯一解釋:以前把錢在錯時點亂搬(集中單幣的混亂進出)磨掉價值;現在預算
   在 BTC/ETH 連貫分配、對的時機進出 → 同曝險上限內賺更多。

**ETH 不是被作弊式餓死**:per-symbol S1 BTC 68 / ETH 43 fills、S2 BTC 236 /
ETH 160 — 兩幣都會出場(Donchian 跌破 / funding 飆高)讓出預算 → 自然輪替。
「同時各 47.5% 公平分」是 V2-E meta-layer 的事(glossary 已定 meta-layer 管
資金分配),非 V2-T。

**第 2、3 件(sell-before-buy / partial fill)延後到 V2-E**:這事件驅動架構
一次只 fire 一個幣,fire 內永遠不會同時有買賣單,sell-before-buy 無用武之地;
等 V2-E 多幣協同 rebalance 時(一個 fire 內同時調多個幣)才有意義。記進
`v2t_prereqs.md` backlog。

**附帶修正**:`real_demo.py` equity 顯示曾有 bug(用 field 名當 price key →
未平倉部位估 0、只印現金),導致 S2 第 1 件後一度顯示 $3,041(其實只是現金,
全額 $59,693)。已修(commit 2ce1f4c)。decisions log 的「$48k」一直正確。

**202 tests 全綠**(196 + 6 新:整桌 gross / 滿池歸零 / 漂移 clamp 不放寬 /
向後相容 / 比例分 / 單 symbol fire 尊重別處持倉且送出單買得起)。

---

## 2026-06-13 — V2-T 真資料接入(前置 1 解,正典 Binance OHLCV + funding)

使用者本機 Windows + ccxt(V1 那套)抓 Binance 正典資料、上傳容器:
- BTCUSDT_1d.csv / ETHUSDT_1d.csv:2019-01-01 ~ 2026-06-13(2721 天)真 OHLCV
- BTCUSDT_funding.csv(7405 筆,2019-09 起)/ ETHUSDT_funding.csv(7171 筆,
  2019-11 起):Binance USDT-M 永續 8h funding

`v2/data/fixtures/import_binance_uploads.py` 純轉檔(ms ts → ISO date,
`fundingRate` → `funding_rate`)後覆蓋 fixtures。檔頭 + fixtures/README
標清楚 source / 工作流 / close-only 退役。

**close-only sanity 退役**(V2-S 期數字作廢):同參數 Donchian(entry=20/exit=10
BTC+ETH,$10k 起,2019-2024 範圍)
- close-only(CoinMetrics PriceUSD,Donchian-on-CLOSE):$171k
- 真 OHLCV(Binance,真 high/low):$137k(差 $34k,close-only 通道窄、訊號偏多)

正典版實跑(V2-T 開工現況,2019-01-01 ~ 2026-06-13):
- S1 Donchian:111 fills(53/58)/ 958 rejections / $137k
- S2 Funding skew:379 fills / **11206 rejections** / $48k
  — funding 每 8h tick,下單頻率高,752 → 11206 rejections,**引擎精修
    急迫性大幅提高**
- S1 + S3 MacroOverlay(VIX):177 fills / 968 rejections / $197k
  — risk-off 反而保住長期淨值(但 V2-T walk-forward 才能驗是否 fit 週期)

**V2-S2 真資料 sanity 自動啟用**(`requires_funding_fixture` 偵測新 fixture):
196 tests 全綠(原 195 + 1 skipped → 196,零 skip)。

V2-S 既有 tests 對「2192 天 close-only」的硬編斷言改成 `>= 2192` + 真 OHLC
sanity(`high >= close >= low` / 日內波動 > 0)。

**V2-T 開工前置 1 完成**;前置 2(752 → 11206 rejections 引擎精修)接著做。
詳見 `research/v2t_prereqs.md`。

---

## 2026-06-13 — V2-S 收官 + V2-T 開工前置 backlog(session 結束)

**V2-S 起步策略池 3 個全 codify 完成**(S1 Donchian / S2 Funding skew /
S3 Macro overlay,195 tests + 1 skip)。V2-S officially own 完(review pass
13 checkpoint 全綠)。

**session 收尾**:V2-T 卡在**真資料硬前置**(使用者本機 ccxt 抓 Binance
正典 OHLCV + funding,容器擋交易所不能硬連)。下個 session 開 V2-T。

**V2-T 開工前置記成 `v2t_prereqs.md`(下個 session 開頭必讀)**:
- **前置 1（硬 blocker）**:正典真資料接入 — V2-S 用 sanity 級(BTC/ETH
  close-only / funding 合成 / DXY 無),V2-T 要正典級(Binance OHLCV +
  funding history）。使用者本機跑 CcxtLoader / CcxtFundingLoader → to_csv →
  帶回容器 commit fixtures。**Donchian close-only vs 真 high/low 訊號會不同
  → 正典進來後 V2-S 回測數字作廢、重跑。**
- **前置 2（使用者 V2-S1 拍板留 V2-T）**:752 rejections 引擎精修 —
  multi-symbol near-fully-invested 時 sizing-to-absolute-target × executor
  reject-whole 互動。選項:sell-before-buy ordering / partial fill /
  delta-aware sizing。不依賴真資料,可先做。
- **V2-T 本體**:M2 walk-forward(IS 30mo/OOS 3mo/WFE>50%）/ M1 真資料壓測 /
  M4 paper trading（要 LiveDriver 輸入側,V2-B 只做 backtest driver）/ M5-M7。
  還要蓋「績效指標計算層」(Sharpe/maxDD/WFE) + walk-forward 多窗 runner
  (B7 Backtest 是單次跑)。

**未動的真相**(誠實記錄):V2-S 的回測損益數字($171k Donchian / $167k +
overlay）是 **close-only sanity 級**,**非正典**,正典資料進來後重跑才算數。

---

## 2026-06-13 — V2-S3 Macro overlay(第一個真守門員)+ VIX 真資料

**V2-S3 策略**:MacroOverlay(PortfolioStrategy,起步策略池 #3,DXY/VIX 上升
減倉)。設計:多 indicator 門檻 overlay,每 indicator=(field, risk_off_above,
cap),某 symbol 的 cap = 所有觸發 indicator 的 cap **取 min**(內部沿用 #3D
最狠者勝)。無 state,讀當前 snapshot level(Bar 取 close / float)。stale →
framework 跳過 overlay → #3C fallback(缺席統一模型,overlay 自己不處理)。

**真資料 = VIX-primary**:`datasets/finance-vix`(datahub.io core,CBOE 官方,
**真 OHLC** 非 close-only)2019-2024 1529 交易日。2020-03-16 VIX close 82.69
(COVID 真實峰值,sanity 對得上)。
**DXY 缺口**:FRED/CBOE/stooq/yahoo 全 403,datahub 無 dollar-index →
無 reputable 公開源。**處置同 funding**:DXY 留 optional 第二 indicator hook,
本機抓 dxy_daily commit 後加進 indicators 即生效。

**整合驗證(使用者點名)**:cap 真的套到 S1/S2 下單上 —
`test_overlay_cap_flows_to_donchian_orders` / `..._to_funding_skew_orders`:
同進場下,VIX risk-off(45)的最終部位 < calm(18)× 0.7,證明 cap 流到下單。
真資料 demo(2×Donchian BTC+ETH + MacroOverlay,2019-2024):overlay 438 次
risk-off(VIX>30 的 COVID/2022),淨值 $167k vs 無 overlay $171k —— 風控在
恐慌期收斂曝險,符合預期。

LKV 驗證:VIX 週末不開盤(1-2 天 stale)< registry 3d 容忍 → overlay 仍用
last known(Friday VIX);斷流 > 3d → framework 跳過 → fallback。真實世界
multi-timeframe staleness 設計被真資料驗證。

15 tests(params validation / overlay 邏輯 / 多 indicator min / Bar+float
level / cap 套到 S1+S2 下單 / stale 跳過 fallback / LKV 週末容忍 / 真 VIX
COVID spike + 真資料 sanity)。

**V2-S 起步策略池 3 個全 codify 完成**(S1 Donchian / S2 Funding skew /
S3 Macro overlay)。M1-M7 正式驗證 = V2-T。

---

## 2026-06-13 — V2-S2 Funding skew codify + 真資料 fixture 缺口處置

**V2-S2 策略**:Round 2 #1 規格(2026-05-21 拍,5 params 簡單派)直翻 code。
每 8h funding event → 過去 `lookback_periods=21` 個 8h funding 滾動平均 →
`raw ≤ low_threshold(0.005%/8h)` 滿倉 / `raw ≥ high_threshold(0.03%/8h)` 出場 /
中間 linear interp;`dead_band(0.002% 訊號變動)` = R3-③ 策略訊號級節流,
跟 framework 執行政策層雙層分工。**thesis 不交易永續、只把 funding 當 spot 訊號**
(V2 邊界 long-only spot 對齊)。22 tests 含 dead_band 抑制 + 累積觸發 + linear
interp 邊界 + per-symbol 獨立 + state 序列化 + 合成 backtest 進出場 + M3 determinism。

**Loader 雙軌擴**(對稱 BTC OHLCV):新增 `CcxtFundingLoader` /
`CsvFundingLoader`(配 `to_csv` 對應格式 + 行對行 roundtrip 測試)。
DataLoader Protocol 通用化(value 異質:Bar / float / ...)。

**真資料 fixture 缺口**:系統性探勘 GitHub 5+ 候選 + Kaggle/HuggingFace
egress 全 403 → **無可達 reputable 公開 funding rate dataset**
(haozhu18 發 Kaggle 容器擋、leepacific 只有兩行 README、其他 0-7 ★ code-only 或
PostgreSQL pipeline)。**處置照使用者 (a) 拍板**:
1. 容器內 sanity = 合成 funding 序列(`testing/scenarios.make_funding_series`),
   驗策略邏輯。
2. 正典路徑 = 使用者本機 Windows + ccxt 跑 `CcxtFundingLoader` →
   `to_csv()` → 帶回容器 commit 進 `v2/data/fixtures/` → `CsvFundingLoader` 讀。
3. `test_funding_skew_real_data_sanity` 的 `requires_funding_fixture` 自動偵測
   (同 BTC `requires_fixtures` 機制),fixture 缺則 skip、commit 即啟用。

`v2/data/fixtures/README.md` 加 funding 章節(缺口紀錄 + 正典路徑 + 範例 code)。

---

## 2026-06-13 — V2-S 開工:Donchian 策略 + 真資料雙軌 loader 拍板

### V2-S1 策略:Donchian breakout(海龜經典)

使用者拍規格:日線 / 進場突破過去 20 日高 / 出場跌破過去 10 日低 / long-only /
BTC+ETH / 2 params(entry=20, exit=10,簡單派)/ 停損 = 跌破 exit 通道內建
(海龜 ATR 停損列為之後可選)。codify 完成 12 tests 合成驗證。

**rolling-window 暖機通則釘清**:rolling 通道要逐 bar 累積歷史,但 framework
buffer-based is_ready gate(#2C1)會擋掉「還沒 ready」的 bar → 策略反拿不到
累積所需 bar。解法 = `min_history=0`(每 bar 都 call)+ 策略內部自管暖機
(buffer 未滿回 flat)。在 default+override 框架內,不動 framework。is_ready
buffer-gate 留給「指標=當前 snapshot 純函式」那類策略。

**澄清**:V2-A roadmap 寫「trend-following 對應使用者既有合約 setup」,實查 V1
是純 DCA bot、無 trend code → trend 策略從零 codify(Donchian),非沿用 V1。

### 真資料接入:CsvLoader + CcxtLoader 雙軌(Option A)

**網路現實**:容器 egress proxy 擋所有交易所 / 資料 API(Binance/Coinbase/
Kraken/CryptoCompare/Yahoo/CoinGecko 全 403),只 github + pypi 可達。→
「ccxt 容器內直接抓」不可行。

**拍板 A**:雙軌 loader(同介面、可換 driver,跟引擎 I/O parity 同哲學):
- `CsvLoader`:讀 committed CSV fixture → 容器能跑(sanity / 回測 / CI)
- `CcxtLoader`:從 Binance 抓 → **使用者本機 env**(Windows + ccxt,V1 那套)
  跑、`to_csv()` 存檔帶回容器餵。**不在容器硬連交易所。**

**sanity fixture**:CoinMetrics community `PriceUSD`(reputable),BTC/ETH
2019-2024(2192 天,含 M1 五段崩盤)。**close-only**(無 OHLC high/low)→
Donchian 退化成 Donchian-on-CLOSE,**僅 sanity 用,正典 = Binance via ccxt
(V2-T)**。檔頭 + fixtures/README.md 標清楚。

**真資料 sanity 結果**(Donchian 20/10,BTC+ETH,$10k 起,2019-2024):
跑通 4384 fires、131 fills(63 買/68 賣)、最終 flat、確定性 fingerprint、
長期 long-only 趨勢捕捉淨值成長。**finding**:752 rejections(near-fully-
invested 時 sizing-to-target × executor reject-whole 互動)— V2-B 簡化的
已知後果,partial-fill / sell-before-buy / delta-aware sizing 留 V2-T 精修。

格式 CSV(日線小、git-diff 友善)/ 存 `v2/data/fixtures/`(committed);
intraday(之後大)→ gitignore。

---

## 2026-05-26 — V2-B 回測引擎全段完成(B1-B7,144 tests 全綠)

V2 從「畫設計圖」(V2-A)跨進「寫 code」(V2-B)。架構文件 `architecture.md`
翻譯成可跑的多策略回測引擎,7 個 milestone:

- **B1 interface 層**(19 tests):策略 base class + 8 lifecycle method +
  NoOp + pydantic schema + framework-default 偵測
- **B2 資料層**(17):DATA_SOURCES registry(Python dict)+ event bus +
  backtest replay driver + LKV/snapshot(per-fire 重建,no-lookahead by
  construction)
- **B3 dispatch core**(21):缺席統一模型(stale/crash/not_ready/disabled)+
  counter + #3A 鎖 + 湧現停機
- **B4 風控管線**(29):Symbol 加總 + #3D min 合併 + #3C fallback 丟 min 池 +
  Risk Engine 三 sub-stage + 算量站 + 執行政策層雙層節流
- **B5 executor**(17):sim 成交器 + Gap 4 成本模型(slippage 5bps / fee
  0.1% default,Protocol hook)+ R3-④ 輸出側 parity
- **B6 observability**(30):結構化 EventLog + query + M3 fingerprint(可重現
  鎖檔)+ alert channel 分流(回測 Noop / 實盤 Telegram stub)
- **B7 整合驗收**(11):end-to-end Backtest runner + dummy 策略 + M1 五段
  崩盤 stale-aware 合成壓測

**開發節奏**:Claude 寫 + 使用者驗收 milestone;碰 §8 要拍的決定停下來
options(registry 格式 / snapshot 組裝 / Gap 4 成本模型 / 壓測合成 vs 真資料
皆使用者拍)。每 milestone 白話 walk-through + commit/push。

**架構承諾變成可執行測試(test 釘死的性質)**:
- no-lookahead by construction(replay 邊吐邊組 snapshot,所有值 ts ≤ now)
- #3C fallback 丟 min 池非二次施加(明眼守門員緊 cap 不被瞎子兜底放寬)
- min 池單調性(加 voter/fallback 只更保守不放寬)
- M3 fingerprint determinism(同回測同 hash、改參數不同 hash)
- I/O 兩側 parity(event bus 輸入 + executor 輸出,同介面雙 driver)
- 湧現停機(最後守門員 crash 停用 → #3A 鎖 → halt)

**B7 整合抓到一個真 bug + 釘死語意**:PortfolioStrategy 不是 event-driven
訂閱觸發,而是 **decision-time overlay,每次 fire 都評估**(否則守門員只在
自己資料 tick cap、kline tick 上的下單決策沒守門員)。已寫進 architecture.md
§3.4 Dispatch 語意澄清段。

**全部數字是 placeholder**(staleness / alert_n / fallback_cap / gross_limit /
dead-band / cooling / slippage / fee),V2-S 用真資料 + V2-B 後期校準。
**真策略 codify、真歷史資料、真數值校準 = V2-S 起的事。**

下一步:V2-B review pass(可選)→ 進 V2-S(第一個真策略 trend-following
codify + 真資料接入 + walk-forward)。

---

## 2026-05-26 — V2-A 收斂總圖落地(architecture.md)+ 資安尾巴結案

### V2-A 平台架構總圖收斂

V2-A 三輪(Round 1 interface / Round 2 contract / Round 3 平台底盤)拍板收斂成 `v2a/architecture.md`(356 行 self-contained single source of truth),9 sections 含每節白話 summary + 每拍板帶「是什麼+為什麼+ref」。**V2-B 開工讀這份就夠**,不必爬三個 round 檔。`research/CLAUDE.md` reference 清單置頂 architecture.md 為 ★。

V2-A 階段(畫設計圖、不寫 code)三輪畫圖**正式收官**。下一步進 V2-B(寫第一行回測引擎 code)。

### 資安尾巴結案(M8 audit 處置)

針對 2026-06-06 backlog #8 M8 audit 的「處置建議」:
- ✅ **V1 Telegram bot 已 revoke**(整隻刪了,`@BotFather /deletebot` 完成)
- 🟰 **V1 Binance key 不需要 revoke** — owner 事實覆蓋 audit 假設:**V1 只跑模擬、從沒真錢交易、從未開過會 leak 的 trading key**。audit 段「若 Phase 2 真開過實 key」前提不成立 → 無 revoke 對象。

**結論**:M8 audit 殘留處置全部結案。下次需要 Binance key = V2-D step 4 tiny live 真錢上場前,屆時依 `v2a/m8_security.md` § 2 規格生成(read-only / trading 分離 + 禁提現 + IP whitelist + 90 天 rotate)。

`v2a/m8_security.md` § 1 處置結果段 + § 6 殘留處置 checklist 已更新狀態。

---

## 2026-05-26 — V2-A Round 3 全段收官:平台底盤定形(Risk Engine + I/O parity + 雙層節流)

V2-A Round 3 四議程 / 6 sub-Q 拍板完成,V2 平台從 Round 2 的「Strategy interface 完整契約」推上**整棟樓的公共系統**:組合級風控、資料流、執行紀律、V1 整合接點全定。完整 ledger 見 `v2a/round3.md` 末段「Round 3 全段收官」。

**拍板總清單(6 條)**:
- R3-① Risk Engine 模組邊界(吸收 backlog #4):
  - ①-a C 獨立成一級元件層(保全總管有自己的辦公室)
  - ①-bc:Block 1 = A 寫死護欄 + always-on(類比 V1 circuit_breaker) / Block 2 = B 分 2 站(Risk Engine 風控 vs 算量站技術轉換) / Block 3 = B post-cap(看守門員打折後算 gross)
- R3-② 資料流 = A 統一 event bus + 雙 driver(parity + no-lookahead by construction)
- R3-③ 執行層 = C 雙層節流(策略訊號級 + framework 執行政策層,分擋訊號自抖 vs 聚合後抖)
- R3-④ executor 抽象 = A 對稱 R3-②(輸出側 parity by construction)+ V1 落點表確認

**Round 3 浮現的 4 條新設計哲學(沿用 Round 2 6 條共 10 條)**:
7. 精簡尺反覆作用 — litmus「不拍 V2-B 引擎骨架會卡嗎」,4 議題 3 個塌成一刀
8. I/O 兩側對稱 parity — R3-② 輸入 + R3-④ 輸出 by construction,M5 paper-vs-backtest 從根堵死
9. framework 級護欄 vs 策略級風控分層 — 區分「業務語意」(留使用者)vs「安全機制存在性」(framework 寫死),解 framework 不假設業務的表面衝突
10. 雙層職責對抗雜物抽屜 — 寧多開盒子不變萬能間(R3-① Risk Engine vs 算量站、R3-③ 訊號層 vs 執行層)

**V2-A 平台完整元件清單(Round 1-3 累積)**:
- 策略層:`SymbolStrategy`(Round 1)+ `PortfolioStrategy`(可換 NoOp,Round 1+Round 2 #3A)
- Framework 一級護欄(non-bypass):`Risk Engine`(R3-①)+ `framework 執行政策層`(R3-③)
- Framework 管線基建:算量站 / event bus + 雙 driver(R3-②)/ executor + 雙 driver(R3-④)/ 統一 event log + alert sink / DATA_SOURCES registry
- Framework 政策:always-on 鎖(#3A)+ 策略缺席統一模型(#2C2 + #2D)+ crash counter 永久停用(#2D)

**Round 3 review pass 補釘**:#3C × #3D fail-safe 值丟進 min 池(非二次施加)— 保住單調性,Round 3 才完整適用

**Carry over**:
- V2-B 必驗清單:模擬成交器演算法 / 滑點+手續費模型(Round 1 Gap 4 同源)/ Risk Engine 3 sub-stage 順序 / snapshot rebuild vs incremental / dead-band+cooling 數值校準 / N 值校準 / counter 鋸齒評估 / whipsaw 量化 / trend×funding correlation / M1 stale-aware 受測
- V2-D 順延(實盤才需):notifier channel 分流 / circuit_breaker 實盤層整合 / heartbeat liveness 監控
- V2-E 順延(依賴 regime detection):regime-aware 降頻(執行政策層已預留 hook)
- V2-S 各策略 codify 紀律:overlay 訊號連續可衰退禁 binary latch

V2-A 階段(畫設計圖、不寫 code)三輪拍板全部完成。下一步建議:Round 3 全段 review pass → V2-A 收斂出總圖(平台架構文件,V2-B 開工依據)→ 進 V2-B(寫第一行 code)。Glossary 累積 Round 3 期間新增 11 條(以「故事/比喻」風格,使用者非 quant 背景可快速 reference)。

---

## 2026-06-06 — Backlog #8 資安規格(M8)落地 + git 歷史洩漏稽核

獨立工作項(跟 V2-A Round 3 主線架構無關),處理平台資安。**注意:此條為維運安全,非架構討論。**

### 1. git 歷史洩漏稽核(急事先查)

起因:V1 時代有 Telegram bot token,記憶中 commit `fcb6976` 做過 redact。查 repo 是否 public + 歷史是否殘留真金鑰。

**稽核結論:**
- **Repo 是 public**(`gt01866xa61/iOS9-SpringBoard-Headers`,`private:false`)。
- **git 全歷史(50 commit / 所有 ref / 所有 blob)無真金鑰殘留** — 只找到 chaos test 故意的假值(`0000000000:ChAoS_invalid_token_for_testing_xxxxx`、`bad_key_xxxxxxxx`)。
- **從未 commit 過真 `.env`**(任何路徑);code 全 `os.environ` 讀、無寫死;`.gitignore` 正確擋 `.env`。
- **`fcb6976` 不在本 repo 歷史**(rev-parse 找不到)→ 那段「redact」歷史若存在則在別處,本 repo 看不到。
- **處置**:不緊急(本 repo 沒在漏);但已退役 V1 Telegram token 查不到去向 + V1 已死(revoke 零成本)→ **建議直接 revoke**(`@BotFather /deletebot`)+ 刪 V1 Binance key(若開過實 key)。關鍵觀念:**改檔案式 redact 不會把 secret 移出 git 歷史**,只要曾 push public 就視同外洩。

### 2. M8 資安規格(照業界標準)

新增 `v2a/m8_security.md`(完整規格 + 驗收 checklist),`v2_roadmap.md` Validation Standards 由 M1–M7 擴成 **M1–M8** 並補 M8 stub + 連結。**分類**:M1–M7 = 策略上線閘門(市場風險);M8 = 系統運行閘門(維運風險)。前者防少賺,後者防歸零,真錢上線前皆硬閘門。

四大面向定案:
- **API key**:trading key 禁提現 + 綁 IP whitelist / read-only 與 trading 分離 / 實盤與測試 key 分離 / 90 天 rotate / 永不寫死(`.env` + `.gitignore`,沿用 V1)
- **帳戶**:交易所 / email / GitHub / VPS 全開 2FA / 第二道用硬體金鑰 / passkey(禁 SMS OTP 防 SIM swap)/ password manager 每站獨立密碼 / email 為命門用最強 2FA
- **Host(VPS)**:對外只開 SSH(只認金鑰、禁密碼)/ UFW / log 不露完整 secret(沿用並擴大 V1 `[REDACTED]`)/ production 不跑 notebook / 非 root 跑 bot / fail2ban + unattended-upgrades
- **Repo**:設 private(現況 public,bot code 建議搬獨立 private repo)/ detect-secrets pre-commit hook / git 全歷史掃過(本次已做)/ GitHub secret scanning + push protection

Glossary 追加「## 5. 資安 / 維運」16 條白話詞條(operational risk / 2FA / TOTP / 硬體金鑰-passkey / SIM swap / IP whitelist / key rotate / 提現權限 / read-only vs trading key / testnet vs mainnet / UFW / SSH 金鑰登入 / redact / pre-commit hook / detect-secrets / push protection)。門檻數字(rotate 週期等)為初版,V2-D 上線前校準。

---

## 2026-05-26 — V2-A Round 2 全段收官:Strategy interface + PortfolioStrategy 完整契約鎖死

Round 2 全 13 個議程 / 子題拍板完成,Strategy interface 從骨架(Round 1)推進到**完整 framework 契約**。完整 ledger 見 `v2a/round2.md` 末段「Round 2 全段收官」總覽表。

**拍板總清單(13 條,本檔只列骨幹)**:
- #1 起步策略池 #2 → Funding rate skew(2026-05-21,已 prepend)
- #2A Lifecycle 4 必要 + 1 可選 / #2B Event-driven + LKV + 統一 event log / #2C1 暖機 is_ready buffer-based + 防呆 / #2C2-A Framework 偵測 stale 跳過策略無感 / #2C2-B Sub-Q1 on_stale 可選 hook / Sub-Q2 per-field counter + V1 notifier alert / Sub-Q3 max_staleness/N 寫 framework registry default + 策略可 override + per-strategy 判定 / #2D 錯誤路徑 = 復用「策略缺席」+ crash counter + #3A 湧現停機 / #3A always-on 鎖 + NoOpPortfolioStrategy 明確 register / #3B Dispatch 順序 Symbol → Portfolio → 相乘 / #3D 多 PortfolioStrategy min 取最狠 / #3C cross-strategy stale override fail-safe 丟進 min 池(非二次施加)

**Round 2 浮現的 6 條設計哲學(沿用至 Round 3)**:
1. Framework 不假設業務語意 — 否決所有「替使用者預設業務」option
2. Default + override 老路 — framework 給合理 default,策略可特化
3. Counter + 門檻 pattern — 連續 N 次累積觸發升級,框架統一 primitive,#2C1 / Sub-Q2 / #2D 共用
4. 單調往最保守倒 — fail-safe 只能往緊永不放寬(#3D min / #3C 丟 min 池而非二次施加)
5. 強迫表態 > 默默裸奔(#3A NoOp 明確 register / #2C1 ack 防呆)
6. 湧現 > 顯式條文(#2D crash + #3A 鎖 → 自動停機;比寫死規矩穩)

**Round 2 review pass 撞點處理**:
- #3C × #3D 合併位置(fail-safe 值丟進 min 池 vs 二次施加)→ 拍丟 min 池,保住單調性、保住明眼守門員警報、實作零新層
- silent divergence(風控失能其他策略繼續滿倉)→ 整套 #3 + #2C2 落地完成

**Round 3 議程(carry over)**:
- R3-① Risk Engine 模組邊界(吸收 backlog #4 + portfolio-gross 約束 + M6 sizing 落地)
- R3-② 資料流 / event bus / snapshot 組裝(Round 1 + Round 2 #2B 留)
- R3-③ 執行層 over-trading 冷卻機制(Round 1 review pass 留)
- R3-④ V1 模組沿用整合點(#2D 開頭,完整定 hook)

**V2-B 必驗清單(實測題)**:N 值校準 / counter 鋸齒評估 / whipsaw 量化 / trend × funding correlation / M1 stale-aware 受測

**V2-S 各策略 codify 紀律**:overlay 訊號連續可衰退禁 binary latch(使用者補)

Round 2 完整 ledger 見 `v2a/round2.md`,Round 3 議程 frame 見 `v2a/round3.md`。新增專有名詞已追加 `v2a/glossary.md`(共 Round 2 期間新增 20+ 條,以「故事 / 比喻」風格寫,使用者非 quant 背景可快速 reference)。

---

## 2026-05-21 — V2-A Round 2 (Part 1):策略池 #2 拍 Funding rate skew

Round 2 第一題(策略池 #2 替代 mean-reversion)拍板。

**選 D:Funding rate skew(永續資金費率偏度)** 為起步策略池 #2。
**C(BTC halving cycle / calendar)退為 PortfolioStrategy 子訊號候選**,V2-E ensemble 階段再評估。

**拍板理由 — 驗證流程可通,不是賺率高:**
- D vs C 6 維對照(訊號 / 參數 / 資料 / M1-M7 / 失效 / correlation 推導,見 `v2a/round2.md`)
- C 結構性問題:高品質 BTC/ETH 資料只覆蓋 2 次 halving(2020-05 / 2024-04),N=2 違反 M2 walk-forward + M4 paper 60 日 + M5 paper-vs-backtest 的「足夠樣本」前提 — 不是調參能解決
- D 資料 Binance Futures `/fapi/v1/fundingRate` 2019-09 起,M1 五段崩盤全覆蓋,M1-M7 結構性可驗

**核心設計**:funding 持續高(永續多頭擁擠) → 縮 spot 多單;funding 持續低/負 → 滿倉。5 個 params(`lookback_periods` / `low_threshold` / `high_threshold` / `dead_band` / `symbol_list`),邏輯一句話。**不交易永續、只把 funding 當訊號**,符合 V2 邊界(只玩 spot)。

**對 trend correlation 預估**:**-0.1 ~ +0.2**(邏輯反向 — trend 賺動能持續、D 在動能過熱時減倉)。**Caveat**:邏輯推導非實測,若 EMA crossover lag 跟 funding 升溫時間軸接近,實測可能 0.3+。**M1 五段崩盤是 reality check 關鍵**,V2-B 跑出結果再校準。

**起步策略池(round 2 後狀態):**

| # | Style | 角色 |
|---|---|---|
| 1 | Trend-following | SymbolStrategy |
| 2 | **Funding rate skew** | SymbolStrategy |
| 3 | Macro overlay | PortfolioStrategy |

Round 2 完整 ledger 見 `v2a/round2.md`。下一題:P1 細節(lifecycle methods / param schema / data spec)。

---

## 2026-05-17 — V2-A Round 1 review pass:Validation Standards 擴 M6/M7 + 簡單派定調

Round 1 review pass(用白話 walk-through 三軸讓使用者 re-validate)過程中浮現的結構性決策:

**Validation Standards 從 M1-M5 擴成 M1-M7**(寫進 `v2_roadmap.md`):
- **M6:Position sizing 必須 risk-based** — 對應核心共識「風險管理 > 預測」。部位大小不得用固定比例,預設 volatility targeting;V2-B/T 階段須證明 risk-based 版 max drawdown 優於 naive 版。
- **M7:策略退役機制** — 對應核心共識「edge 會衰退」。M1-M6 是上線前關卡,M7 是上線後持續監控:滾動 Sharpe 連續 2 窗低於 backtest 50%、或 live 回撤超 backtest 1.5 倍 → 退役。
- 來源:對照量化交易 6 條核心共識做 gap 分析,Gap 1(sizing)/ Gap 2(退役)被判定跟 M1-M5 同級重要,升級進 roadmap。M6/M7 門檻數字為初版,V2-D 前校準。

**簡單 vs 複雜爭議定調:簡單派**(使用者委託 Claude 專業判斷):
- V2 實際策略數目標 anchor 在 **3 個**,roadmap 的「3-7」中 7 當理論上限不當目標
- 「簡單」不只指策略數量,每個策略內部也要簡單:參數理想 < 5 個、邏輯一句話講得清
- 理由:複雜派玩法需規模才成立(文藝復興等級資源),個人玩家頭號死因是複雜度爆炸而非分散不足

**Round 1 三軸正式定案:** 雙 interface / output 形狀 / class+snapshot+strict schema 三軸經白話 review pass(用買菜阿姨聽得懂的話逐軸 walk-through、使用者 re-validate)全數通過,Round 1 結束,進 Round 2。

完整領域脈絡(6 共識 + 3 爭議 + 雙方論據)見 `v2a/domain_landscape.md`。Round 1 衍生事項(over-trading 執行層政策、Gap 3/4)見 `v2a/round1.md`。

---

## 2026-05-12 — V2-A Round 1(Strategy Interface 規範)

V2-A 第一輪鎖死 Strategy interface frame-level 三件事:

- **Axis 6 Instrument 模型**:雙 interface — `SymbolStrategy`(per-symbol / pair 部位意圖)+ `PortfolioStrategy`(portfolio-level risk overlay)。Per bar 執行順序鎖死 SymbolStrategy → PortfolioStrategy。
- **Axis 4 Output 形狀**:SymbolStrategy = target % long-only `[0, 1]` per symbol(% of strategy's allocated capital);PortfolioStrategy = per-symbol cap multiplier `[0, 1]`。
- **Axis 1 抽象層次**:Class + 外部可 snapshot state + 嚴格 dataclass / pydantic state schema。params(策略邏輯參數)跟 state(run-time 內部變數)分離。

V2 邊界 implication:SymbolStrategy output domain `[0, 1]` spot-only long-only 鎖死 → **Mean-reversion(BTC/ETH ratio)自動降級成 rebalance flavor**(ratio 偏高 → 減 BTC 配重加 ETH,非真 spread trade)。Round 1 拍板**起步策略池中 Mean-reversion 換掉**,候選名單 round 2 詳論(volatility regime / on-chain / calendar / funding skew / cross-exchange premium 等)。Trend-following 跟 Macro overlay 不受影響。

Round 1 完整 ledger 見 `v2a/round1.md`(P0 拍板 + interface 骨架預覽 + 執行管線 + 範圍外 P1 子題 + open questions)。

下一輪 V2-A Round 2 重點:策略池候選 finalize、P1 子題(lifecycle methods / param schema / data spec)、PortfolioStrategy always-on 鎖 + 疊合演算法。

---

## 2026-05-09 — V2 Builder Pivot(框架重寫)

V1 結案後使用者揭露真實意圖:**不是 problem-solver 模式**(沒明確痛點),而是 **builder 模式**(想創造大型量化平台)。原本的 V2-Q/R/D(問題驅動)框架不適用,**整套重寫成 V2-A/B/S/T/E/D**(蓋房子模式)。

關鍵決定:

- **V1 停止運行**,不當儲蓄機(使用者已有手動長期部位,V1 重疊無意義)
- V1 code 保留當技術資產,V2 沿用 `exchange_api.py` / `trader.py` / `notifier.py` / `circuit_breaker.py` / `heartbeat.py` / `price_recorder.py` / `chaos_test.py`
- V1 **不會被 wrap 成 V2 策略模組**(原 plan 該段刪除)
- V2 框架:V2-A(架構)→ V2-B(回測引擎)→ V2-S1..N(策略 codify)→ V2-T1..N(策略驗證)→ V2-E(集成)→ V2-D(部署)
- 起步策略池:trend-following + mean-reversion + macro overlay(3 個業界 style,V2-A 可調)
- Validation Standards 寫死 M1-M5:
  - M1:V2-B 內建 5 段歷史崩盤 stress-test(COVID 2020-03 / China crackdown 2021-05 / LUNA 2022-05 / FTX 2022-11 / 日圓 carry unwind 2024-08-05)
  - M2:walk-forward 規格 — IS 30 個月 / OOS 3 個月 / retrain 每 3 個月 / WFE > 50% / OOS 每視窗 ≥ 30 trades
  - M3:backtest 結果 lock — 自動 timestamp + commit hash,策略邏輯改 = 新編號(避免 retrofit)
  - M4:paper trading 最少 60 個交易日(不是自然日)
  - M5:paper vs backtest 並排 — Sharpe 差 ≤ 30%、Fill rate 差 ≤ 10%,超過 = reject
- 預算策略:simulation-first 5-step cascade(backtest → walk-forward → paper → tiny live 50-100 USDT → scale up)
- 第一階段嚴格鎖 BTC/ETH,Gold / Oil / NDX 是後續

V2-Q 框架已過時:`v2_questions.md` 已 archive 到 `archive/`。完整 builder roadmap 見 `v2_roadmap.md`。

下一步:V2-A 架構設計(我跟使用者來回討論平台骨架,**不寫 code**,產出架構文件)。

---

## 2026-05-08 — V1 結案,V2-Q 啟動

V1 Stage 4 trial 全綠(3 trades + 5 次跨日 reset 驗證 + failures 0/5)。
Phase 4 status → Validated(commit `346108e`)。
進入 V2-Q 階段(用戶思考三題,Claude + Codex + Gemini 平行協助)。

決定:
- 不充值,V1 不重寫
- V2 邊界保持(無 leverage / 衍生品)
- 用 multi-CLI 工作流(Claude / Codex / Gemini),角色分工見各 role_*.md

下一個 milestone:V2-D(48h 後評估三策略 go/no-go)
