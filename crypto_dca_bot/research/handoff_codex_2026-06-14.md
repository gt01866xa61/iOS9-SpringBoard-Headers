# Codex 交接文件(2026-06-14,自 Claude Code session)

> **這份文件是什麼**:V2 專案從 Claude Code 遷移到 Codex 的完整交接。目標:
> Codex(或任何接手的 CLI/人)讀完這份 + 四必讀檔,能**無縫接手**,不漏任何
> 對話中才存在的脈絡。
>
> **接手第一步(照順序)**:
> 1. clone repo、checkout `claude/v2-trading-platform-continue-8nYhQ`
> 2. `cd crypto_dca_bot && pip install pytest pydantic`(容器基底沒有)
> 3. `python3 -m pytest v2/tests/ -q` → 預期 **255 passed 零 skip**(交接時已驗)
> 4. 讀根目錄 `CLAUDE.md`(工作流鐵律 + 溝通規則,**全部照樣執行**)
> 5. 讀 `research/CLAUDE.md` → `research/v2_roadmap.md` → `research/decisions.md`
>    → `research/v2t_prereqs.md` → 本檔
> 6. 跑三支工具對數字:`python3 -m v2.tools.real_demo` /
>    `v2.tools.walk_forward_demo` / `v2.tools.regime_diagnostic`
>    (數字應與本檔 §4 完全一致 — 全 pipeline 是 deterministic 的)

---

## 1. 一句話現況

**V2-T 進行到 T2 完成。三個策略全部沒過 M2 walk-forward 閘(WFE < 50%),
regime 診斷證實三個都是趨勢型(策略池 DNA 單一)。專案暫停在「等使用者
(Jeff)拍上層方向」— 見 §5 開放問題。T3-T9 未動工(使用者明令暫停)。**

---

## 2. Repo / Branch / 環境

### Repo 借殼(⚠️ 不知道會踩雷)
- repo 名叫 `iOS9-SpringBoard-Headers`(gt01866xa61/iOS9-SpringBoard-Headers),
  根目錄 `System/` 與 `usr/` 是 iOS dyld cache dump,**與 bot 完全無關,不要動**。
- 所有 bot code 在 `crypto_dca_bot/` 底下。V1 code 在該目錄第一層(結案保留,
  不運行);V2 在 `crypto_dca_bot/v2/`。

### Branch 紀律(使用者明令)
- **固定在 `claude/v2-trading-platform-continue-8nYhQ` 工作。不開新 branch,
  除非先問過使用者。**(2026-06-13 使用者訓令:進度散在多條 branch 難追)
- `claude/wonderful-fermat-qe9dp8` 是歷史殘留指標(內容已全數 ff-merge 進
  continue-8nYhQ),**不要用**。
- 交接時 HEAD:見 git log 最新(本檔 commit 即交接點)。工作樹乾淨、全數已 push。

### 容器環境現實
- Python 3.11;`pytest`/`pydantic` 每次新容器要 `pip install`(見 `v2/requirements.txt`)。
- **交易所 API 全被 egress proxy 擋(403)**。真資料工作流(已固化,未來更新照走):
  使用者本機 Windows + ccxt(V1 那套)抓 → `to_csv()` → 上傳容器 →
  `v2/data/fixtures/import_binance_uploads.py` 轉檔覆蓋 fixtures → tests 自動啟用。
- 測試跑法:`cd crypto_dca_bot && python3 -m pytest v2/tests/ -q`。
- 工具跑法(都要在 `crypto_dca_bot/` 底下):`python3 -m v2.tools.<name>`。

### Fixtures 覆蓋範圍(交接時實測)
| 檔 | 範圍 | 備註 |
|---|---|---|
| `btc_usd_1d.csv` / `eth_usd_1d.csv` | 2019-01-01 → 2026-06-13(2721 天真 OHLCV)| Binance 正典 |
| `btc_funding_8h.csv` | 2019-09-10 → 2026-06-13(7405 筆)| Binance USDT-M 永續 |
| `eth_funding_8h.csv` | 2019-11-27 → 2026-06-13(7171 筆)| 同上 |
| `vix_daily.csv` | 2019-01-02 → **2024-12-31**(1529 交易日)| ⚠️ 見 §9 caveat #1 |

---

## 3. 完整敘事時間軸(從頭到交接點)

1. **V1(Phase 4 DCA bot)2026-05-08 結案**,停止運行。code 保留當技術資產。
2. **V2 builder pivot(2026-05-09)**:六階段 A/B/S/T/E/D。
3. **V2-A 架構(完成)**:單一 source of truth = `research/v2a/architecture.md`。
   核心拍板:雙 interface(SymbolStrategy 出 target% / PortfolioStrategy 出 cap)、
   #3D min 合併取最狠、#3C fallback 進 min 池、Risk Engine framework 一級護欄、
   執行政策層(dead-band/cooling)、event bus + 雙 driver(I/O parity by
   construction)、缺席統一模型、crash counter。詳見 glossary + round1-3。
4. **V2-B 回測引擎(完成)**:六層 pipeline,fingerprint determinism(M3 基礎)。
5. **V2-S 策略池 3 個 codify(完成)**:S1 Donchian(20/10)、S2 FundingSkew
   (lookback 21)、S3 MacroOverlay(VIX>30 → cap 0.5)。
6. **V2-T 前置 1(2026-06-13 ✅)**:Binance 正典真資料接入,close-only 數字作廢。
7. **V2-T 前置 2(2026-06-13 結案)**:
   - 真資料診斷推翻原拍板假設:11206/958/968 rejections 的 dominant 成因是
     **cross-symbol 搶現金**(event-driven 單幣 fire × gross 只看本 fire),
     不是 within-fire 排序。sell-before-buy 在此架構是 no-op(0 個 fire 同時
     有買賣單)。
   - **第 1 件做成「組合視角 sizing」**(`held_elsewhere_pct` 進 Risk Engine
     gross)→ 三場 rejections **全部誠實歸零**(非裁切作弊;S1 交易零變動、
     S2/S3 最高曝險反降 100%→97%)。
   - 第 2、3 件(sell-before-buy / partial fill)**延後 V2-E**。
   - P&L 跳動成因已寫死在 decisions.md(免得誤判 bug)。
8. **T1 績效指標層(2026-06-13 ✅)**:`v2/analysis/metrics.py`。
9. **T2 walk-forward(2026-06-14 ✅)**:`v2/analysis/walk_forward.py`。
   低頻策略 feasibility 修正(見 §7):pooled WFE(主)+ 70/30 split(對照)。
   **結果:三策略全 FAIL M2,兩法一致**(見 §4)。
10. **regime 診斷(2026-06-14 ✅,工具已固化)**:`v2/tools/regime_diagnostic.py`。
    結論:**三策略全趨勢型、高度相關 = 策略池 DNA 單一**。「看天吃飯,不是壞掉」
    — 上升趨勢 OOS 有真 edge,盤整/下跌一起垮;in-sample 好看是因為 2020-21
    史詩牛市。**使用者拍板:每個新策略都要過 regime 診斷這關。**
11. **策略池互補諮詢(2026-06-14,純諮詢無 code)**:long-only spot 下非趨勢
    可選型:①均值回歸(接刀風險)②再平衡/波動收割(最乾淨互補,吃多資產擴張
    紅利)③估值慢回歸(MVRV 等)④現貨原生 carry(質押,太小隻是配角)。
12. **軍師端新方向(使用者帶入,2026-06-14)**:個人玩家純機械挖 alpha = 死路。
    收斂兩條:**路一**=自動化 Jeff 已驗證的手動策略(稍後做);**路二**=收
    風險溢酬(funding rate 溢酬)。
13. **路二解剖(2026-06-14,純分析)— 結論 B:結構性關閉**(見 §5-A,數字 §4-E)。
    ⚠️ 此結論**只存在於對話+本檔+decisions.md**,沒有對應的 committed 分析工具
    (重現腳本在 §10)。

---

## 4. 關鍵數字總表(全部真資料實測,deterministic 可重現)

### A. 前置 2 baseline → 修正後(`v2.tools.real_demo`)
| 場景 | rejections 前→後 | fills 前→後 | equity 前→後 | 最高曝險 前→後 |
|---|---|---|---|---|
| S1 Donchian | 958 → **0** | 111 → 111 | $137,324 → $137,324(不變)| 97.3% → 97.3% |
| S2 FundingSkew | 11206 → **0** | 379 → 396 | $48,672 → $59,693 | 100% → 97.1% |
| S3 +MacroOverlay | 968 → **0** | 177 → 187 | $197,854 → $225,679 | 100% → 97.3% |

⚠️ 歷史插曲:曾有 demo 顯示 bug 把 S2 印成 $3,041(只印了 cash;field 名當
price key 導致未平倉部位估 0)。已修(commit `2ce1f4c`)。**decisions log 的
$48k baseline 一直是對的。** 若在舊訊息看到 $103/$3,041,是那個 bug。

### B. T1 in-sample 指標(2720 天,前置 2 修正後;⚠️ in-sample 單跑,僅參考)
| | CAGR | Sharpe | Sortino | maxDD | Calmar |
|---|---|---|---|---|---|
| S1 | 42.1% | 0.98 | 1.52 | 50.7% | 0.83 |
| S2 | 27.1% | 0.72 | 1.06 | 73.5% | 0.37 |
| S3 | 51.9% | 1.13 | 1.75 | 46.2% | 1.12 |

### C. T2 walk-forward OOS(IS=30mo/OOS=3mo/step=3mo → 19 窗;M2 閘 WFE>50%)
| | pooled WFE(主)| split WFE(70/30 對照)| 兩法 | M2 |
|---|---|---|---|---|
| S1 | 20.6%(OOS Sh 0.216 / mean IS 1.051)| −37.5%(OOS −0.545 / IS 1.455)| 一致 | **FAIL** |
| S2 | 39.1%(0.376 / 0.961)| 4.2%(0.041 / 0.966)| 一致 | **FAIL** |
| S3 | 28.8%(0.330 / 1.145)| −24.7%(−0.386 / 1.562)| 一致 | **FAIL** |

split 切點 2024-03-19(S2:2024-04-26)。總 OOS 交易:S1 74 / S2 148 / S3 110。
per-window 中位交易只有 1~5 筆 → **per-window WFE 不可用**(見 §7)。

### D. regime 分桶(`v2.tools.regime_diagnostic`;OOS 19 窗,BTC net ±15% 分類)
| regime | 窗數 | S1 平均/勝率 | S2 | S3 | 市場 ER |
|---|---|---|---|---|---|
| 上升趨勢 | 6 | +19.9% / 83% | **+44.1% / 100%** | +22.6% / 100% | 0.22 |
| 盤整 | 10 | −3.8% / 30% | −2.3% / 40% | −3.4% / 30% | 0.06 |
| 下跌趨勢 | 3 | −16.9% / 0% | **−38.1% / 0%(接刀)** | −16.6% / 0% | 0.23 |

年度行情佐證:2020 BTC +302%/ETH +463%、2021 ETH +404%(= in-sample 史詩牛市);
2025 −7%/−12%、2026 至 6 月 −28%/−44%。
B&H 50/50 對照(OOS 2024-03→2026-06):報酬 −21.7%、Sharpe 0.06
(策略 OOS Sharpe −0.55 → 該段整體難做 + 策略還輸躺平 = whipsaw 稅)。

### E. 路二 funding 溢酬解剖(未固化成工具,重現腳本 §10)
- funding 統計:BTC 平均 0.0108%/8h(**年化 +11.8%**)、ETH 0.0130%(**+14.2%**);
  funding 為負的時間只占 15%/14%。
- 純 basis carry(現貨多+永續空,理想無成本)逐年:**每年都正**
  (BTC:2020 +17.2%、2021 +30.6%、2022 +4.2%、2023 +7.9%、2024 +12.0%、
  2025 +5.1%;ETH 2021 高達 +37.5%)。全期 BTC +121.9%/ETH +153.4%,
  理想化 **Sharpe 10.6 / maxDD 1.5%**。
- **FundingSkew 實際收到的 funding = $0**(結構事實:現貨持有者不參與永續
  多空互付)。它 100% P&L = 價格 beta,funding 只是進出場計時器 → 這就是
  regime 實測它是趨勢型的根因。

---

## 5. ★ 等 Jeff 拍板的開放問題(交接時的停點,最重要一節)

### A. 路二(收 funding 風險溢酬)= 結論 B,結構性關閉 — 待 Jeff 正式拍
分析結論(2026-06-14,已交付 Jeff、Jeff 未回覆):
- **long-only spot 收不到 funding 溢酬**:收 funding 要當永續空方(85% 時間
  funding 為正,收錢的是空方),long-only 禁做空 → 無法對沖價格隔離 carry →
  精修做法救不了(不是 A「做法太粗」,是 B「結構死路」)。
- **basis trade 悖論(要給 Jeff 權衡的)**:能收 carry 的「現貨多+永續空」是
  delta-neutral,理想 maxDD 1.5% — **比 Jeff 現在的 long-only 方向性賭注
  (maxDD 50-73%)風險低得多**。「不碰衍生品」這條為降風險設的邊界,反而擋掉
  風險最低的機會。代價:保證金/強平管理、兩腿手續費+基差風險、對手方風險
  (FTX 殷鑑)、牽動 M8 資安。真實淨 carry 估 ~8-12%/年。
- **決策點:維持 strict long-only spot(路二死)vs 放寬允許 delta-neutral
  basis trade(路二活)**。這是風險偏好拍板,不是技術題。

### B. 策略池方向(regime 診斷後的岔路)
三選一(或組合),Jeff 說要想清楚「更上層的問題」再定:
1. 接受趨勢策略天性(賭未來還有大牛市,忍受盤整期難看);
2. 加互補策略(首選=再平衡/波動收割,次選=均值回歸;皆須過 regime 診斷關);
3. 路一:自動化 Jeff 已驗證的手動策略(軍師端說稍後做)。

### C. 明確的「不要做」清單(使用者訓令,違反 = 白做)
- **不准 p-hacking**:不准掃參數找「能過 M2 的組合」(risk #3,每試一次汙染
  OOS 可信度)。regime 診斷輪已明令「純診斷、不調參」。
- **不准作弊式 rejections 歸零**:每個 reject 路徑要對得上「Binance 同情境
  會怎樣」。
- **T3-T9 暫停**:使用者明令先不做,等上層方向拍板。

---

## 6. 工作流鐵律 + 溝通規則(→ 根目錄 `CLAUDE.md`,全文照守)

摘要(細節以 CLAUDE.md 為準):
- 每個邏輯單元立刻 commit+push,不累積;每個功能/docs commit 後在根目錄
  `PROGRESS.md` 表頂插一行(格式:日期 | hash 前 7 碼 | 描述;PROGRESS 維護類
  meta-commit 不自記)。
- session 開頭:`git status` + `git log --oneline -10` 對齊 → 讀四必讀 →
  掃 `research/v2a/glossary.md`。session 結束前確認全 push。
- 遇 API 400 / context error / 異常**立刻停手回報**,不硬跑。
- **使用者非 quant 背景**:新術語第一次出現用白話+比喻解釋;拍板必附「白話
  walk-through」段;一輪一 axis 不轟炸;新術語追加進 glossary;不假設 quant
  基礎、寧可重複。
- **溝通 sense**(2026-05-04 訓令):使用者 bracket 掉的範圍不要偷渡回答案;
  timing-critical 前置單獨 surface;不用罐頭 hedge;partner 等級的 sense。

---

## 7. 技術慣例與陷阱(code-level,接手改 code 前必讀)

1. **metrics 的 std 用 population(ddof=0)** — 刻意選擇,文件化在
   `metrics.py` docstring。別「修正」成 sample std,測試會炸且是故意的。
2. **年化用 365**(crypto 24/7,`PERIODS_PER_YEAR_DAILY=365`),不是 252。
3. **時間區間一律半開 `[start, end)`**(slice_series / closes_in_range /
   `_curve_sharpe`)。
4. **degenerate 約定**:報酬 <2 筆 → 指標回 0;std=0 且 mean≠0 → ±inf(零波動
   正報酬 = 數學誠實);無下行 → Sortino +inf。
5. **equity_curve 是 observability,不進 fingerprint**(M3 determinism 不受影響)。
6. **暖機通則**:`min_history=0` + 策略內部自管 buffer(rolling 通道類策略
   必須這樣,否則 framework buffer gate 會擋掉累積用的 bar)。
7. **walk-forward**:每窗 fresh 策略實例(固定 params 下等價 `reset()`,更不易錯);
   OOS 段時間連續不重疊(pooled 拼報酬的前提,有 test 釘住);**per-window
   Sharpe 只當診斷**(低頻策略每窗 <30 筆交易,單窗數字是噪音)。
8. **regime 分類必須用策略無關度量**(BTC net ±15% + Kaufman ER),不能用策略
   自己的 P&L 定義 regime(循環論證)。
9. **組合視角 sizing 的語意**:`held_elsewhere_pct` = 本 fire 沒在管的 symbol
   已持曝險;gross 看整桌;本 fire 只配剩餘額度;別處持倉不在此回觸發賣出
   (各自 fire 時自我 rebalance)。這**不是**「餘額不足裁切」。
10. **funding 是永續多空互付的現金流,現貨持有者收到 $0** — 任何「用 funding
    當訊號的 spot 策略」都是在賭價格,不是收溢酬。別再混淆(路二解剖核心)。
11. dispatch:SymbolStrategy 事件驅動訂閱(一次 fire 一個幣);PortfolioStrategy
    是 decision-time overlay(每 fire 都評估)。**「同 fire 多幣協同」目前不存在**,
    這是 sell-before-buy 延後 V2-E 的原因。
12. Backtest 的 `price_map` 預設是 `*_kline_1h`;所有日線場景要顯式傳
    `{"BTC": "BTC_kline_1d", "ETH": "ETH_kline_1d"}`。

---

## 8. 檔案地圖

```
CLAUDE.md                       ← 全局工作流+溝通鐵律(先讀)
PROGRESS.md                     ← commit ledger(倒序)
crypto_dca_bot/
  README.md                     ← V1 歷史(結案)
  exchange_api.py trader.py ... ← V1 資產(V2-D 沿用,現不運行)
  research/
    CLAUDE.md                   ← V2 研究脈絡 + 進度指針
    v2_roadmap.md               ← 六階段 roadmap + M1-M8 validation 標準
    decisions.md                ← 決策 ledger(倒序,最新=本次交接條目)
    v2t_prereqs.md              ← V2-T 進度表 + T1-T9 frame + 4 真風險
    handoff_codex_2026-06-14.md ← 本檔
    v2a/architecture.md         ← ★ 架構單一 source of truth
    v2a/glossary.md             ← 白話詞彙表(對使用者溝通的基線)
    v2a/round1-3.md, m8_security.md, role_codex.md, role_gemini.md
  v2/
    interfaces/  data/  engine/  execution/  observability/  strategies/
    analysis/    ← T1 metrics.py / T2 walk_forward.py / regime.py
    tools/       ← real_demo.py / walk_forward_demo.py / regime_diagnostic.py
    tests/       ← 255 tests(交接時全綠)
    data/fixtures/ ← 真資料 CSV(§2 表)+ import_binance_uploads.py
```

---

## 9. 已知 caveats(誠實清單,接手別被騙)

1. **VIX fixture 只到 2024-12-31**,klines 到 2026-06。→ S3 的 MacroOverlay 在
   2025-2026 整段對 VIX 是**永久 stale** → framework 跳過 overlay → #3C
   fallback_cap=0.5 進 min 池 → **S3 的 2025+ 行為 = 恆定半倉,不是 VIX 訊號**。
   S3 的 $225,679 與 2025-26 OOS 視窗較抗跌,部分是這個 data artifact。
   要真測 overlay 必須先補 VIX 2025-2026 資料(來源:datahub.io CBOE,
   非 ccxt;見 `fixtures/README`)。
2. **所有回測無滑點外的市場衝擊**、fee=0.1% taker + 固定 bps slippage
   (`v2/execution/cost.py`)。M5 paper-vs-backtest 才會校準真實成本。
3. **T2 的「訓練」= 暖機+跑 IS**(params 固定,無最佳化)。WFE 測的是跨時間
   穩定性;等未來有參數最佳化時,walk-forward 要升級成「IS 內 optimize」語意。
4. **單一歷史實現**:19 個 OOS 窗全來自同一條 BTC/ETH 歷史;WFE 是合理閘,
   不是統計鐵證(risk #3/#4 永遠在)。
5. 理想 basis carry(Sharpe 10.6/maxDD 1.5%)是**無成本完美對沖上限**,
   真實要扣兩腿費用/基差/對手方風險,估年化剩 ~8-12%。
6. 容器會被回收:**任何沒 push 的東西 = 丟失**。本 session 就發生過一次
   (靠 origin 完整恢復)。commit 節奏鐵律的另一個理由。

---

## 10. 路二分析重現腳本(未 commit 成工具,inline 保存)

```python
# cd crypto_dca_bot && python3 <this>
from pathlib import Path
from statistics import mean
from v2.data import CsvFundingLoader
from v2.analysis import sharpe, max_drawdown, equity_returns, daily_equity
FIX = Path("v2/data/fixtures")
for name in ("btc", "eth"):
    f = CsvFundingLoader(FIX / f"{name}_funding_8h.csv", "F").fetch()
    rates = [r for _, r in f]
    print(name.upper(), "mean/8h=%.4f%%" % (mean(rates)*100),
          "年化=%.1f%%" % (mean(rates)*3*365*100),
          "負占比=%.0f%%" % (sum(1 for r in rates if r < 0)/len(rates)*100))
    by_year = {}
    for ts, r in f: by_year.setdefault(ts.year, []).append(r)
    for y in sorted(by_year): print(f"  {y}: carry {sum(by_year[y])*100:+.1f}%")
    eq, curve = 1.0, []
    for ts, r in f: eq *= (1 + r); curve.append((ts, eq))
    d = daily_equity(curve)
    print(f"  全期 {(curve[-1][1]-1)*100:+.1f}%  Sharpe {sharpe(equity_returns(d)):.2f}"
          f"  maxDD {max_drawdown(d)*100:.1f}%")
```

---

## 11. 本次 Claude Code session 的 commit 時間軸(2026-06-13~14)

| hash | 內容 |
|---|---|
| `f165645` | 前置 2 baseline:三策略真資料 demo runner |
| `22c8301` | 前置 2 第 1 件:組合視角 sizing(rejections 全歸零)+ 6 tests |
| `2ce1f4c` | real_demo equity 顯示 bug 修正($3,041 事件)|
| `f0baf98` | 前置 2 結案 docs(P&L 跳動成因寫死 / 2-②③ 延後 V2-E)|
| `1b47df5` | T1 績效指標層 + equity_curve + 28 tests |
| `45651be` | T2 walk-forward(pooled + split 雙法)+ 13 tests |
| `1eb8418` | regime 診斷工具 + 12 tests |
| (本檔 commit) | 交接文件 + decisions/進度表更新 |

(每個功能 commit 後都有對應 `docs: backfill ...` PROGRESS 條目,略。)
