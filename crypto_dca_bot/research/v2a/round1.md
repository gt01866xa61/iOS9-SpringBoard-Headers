# V2-A Round 1 — Strategy Interface 規範

> 2026-05-12(Asia/Taipei)— V2-A 第一輪。鎖死 Strategy interface 的 frame-level 決定(雙 interface 形狀、output 形狀、抽象層次),讓 round 2+ 進細節時不會回頭翻地基。
> 上層 frame 見 `../v2_roadmap.md` V2-A section,本檔是 round-by-round ledger。
> **狀態:三軸經 2026-05-17 白話 review pass 全數 re-validate 通過,Round 1 正式定案。**

---

## Round 1 拍板(P0)

| Axis | 拍板 | Frame implication |
|---|---|---|
| 6 Instrument 模型 | **雙 interface:`SymbolStrategy` + `PortfolioStrategy`** | per bar 執行順序鎖死:SymbolStrategy → PortfolioStrategy。SymbolStrategy 處理 per-symbol / pair 部位意圖,PortfolioStrategy 處理 portfolio-level risk overlay。 |
| 4 Output 形狀 | **SymbolStrategy = target % long-only `[0, 1]` per symbol;PortfolioStrategy = per-symbol cap multiplier `[0, 1]`** | SymbolStrategy 輸出 `{"BTC": 0.6, "ETH": 0.3}` = 該策略 allocated capital 中 BTC 60%、ETH 30%。PortfolioStrategy 輸出 `{"BTC": 1.0, "ETH": 0.3}` = ETH 上限為意圖的 30%。 |
| 1 抽象層次 | **Class + 外部可 snapshot state + 嚴格 dataclass / pydantic state schema** | params(策略邏輯參數)跟 state(run-time 變化的內部變數)分離。`get_state()` / `set_state()` 介面讓 engine 在 M3 lock 跟 walk-forward 重訓 boundary 序列化。 |

---

## Interface 骨架(預覽)

V2-A 完整 architecture 文件成品會詳寫,以下是 round 1 拍板後 derived 的形狀預覽(**非 code 提交**,具體 method signature / type 待 round 2/3 細化):

```python
from abc import ABC, abstractmethod

class SymbolStrategy(ABC):
    name: str
    state_schema: type      # 嚴格 dataclass / pydantic
    params_schema: type     # 嚴格 dataclass / pydantic

    @abstractmethod
    def initialize(self, params) -> None: ...

    @abstractmethod
    def required_data(self): ...

    @abstractmethod
    def on_bar(self, bar, market) -> dict[str, float]:
        # 回傳 {symbol: target_pct in [0, 1]}
        ...

    def get_state(self): return self.state
    def set_state(self, s): self.state = s


class PortfolioStrategy(ABC):       # 對稱形式
    name: str
    state_schema: type
    params_schema: type

    @abstractmethod
    def initialize(self, params) -> None: ...

    @abstractmethod
    def required_data(self): ...

    @abstractmethod
    def on_bar(self, bar, portfolio) -> dict[str, float]:
        # 回傳 {symbol: cap_multiplier in [0, 1]}
        ...

    def get_state(self): return self.state
    def set_state(self, s): self.state = s
```

---

## 執行管線(per bar)

```
SymbolStrategy_1..N
    ↓ each → target_i = {"BTC": 0.6, "ETH": 0.3}   (% of strategy's allocated capital)
    ↓ engine aggregate (weighted by per-strategy allocated capital from meta-layer)
combined_target = {"BTC": ..., "ETH": ...}
    ↓
PortfolioStrategy_1..M
    ↓ each → cap = {"BTC": 1.0, "ETH": 0.3}        (per-symbol multiplier)
    ↓ engine: 多個 PortfolioStrategy 怎麼疊(min / mul / sum)— round 2 拍
final_target = combined × effective_cap
    ↓ engine sizing(算 USDT / 數量 / 含 fee + slippage 預估)
orders
```

---

## V2 邊界 implication

SymbolStrategy output domain `[0, 1]`(spot-only long-only)鎖死後的後果:

- 真 short 不允許(V2 邊界鎖「不上 leverage / 衍生品」)
- **Mean-reversion 自動降級成 rebalance flavor**(ratio 偏高 → 減 BTC 配重加 ETH,而非真 long BTC short ETH 的 spread trade)
- **起步策略池 round 1 決定:Mean-reversion 換掉,候選名單 round 2 詳論**
- Trend-following:不受影響(本來就 long-only)
- Macro overlay:不受影響(它是 PortfolioStrategy cap multiplier,「VIX 高 → 減倉」在 long-only 下語意更自然)

---

## Round 1 範圍外(留 round 2 / 3)

P1 子題:

- axis 2 時間尺度 — bar-based vs event-driven(目前預設 bar-based)
- axis 3 詳細 state 管理 — engine snapshot / restore / version 演算法
- axis 5 資料宣告 — `required_data()` 具體 schema(K 線粒度、外部資料 source 形狀)
- Lifecycle methods 細節 — `initialize` / `on_session_end` / `reset` 等 contract
- Param schema 形狀 — pydantic vs frozen dataclass、validation 規範
- 多個 PortfolioStrategy 疊合演算法 — min / mul / sum
- Allocation 概念在 interface 哪一層曝露 — 等 V2-E meta-layer 設計時細

---

## Open questions(round 2 拍)

1. **策略池候選名單**:換掉 mean-reversion 後填什麼?候選包含但不限於:
   - Volatility regime / breakout(BTC vol > threshold → 退場/縮倉; vol < threshold + price > 50-day → 進場)
   - On-chain signal(Glassnode active addresses / exchange outflow / SOPR 等)
   - Calendar / seasonality(年底、減半週期、週末效應)
   - Funding rate skew(永續 funding 高 → 多頭擁擠 → 反向訊號)
   - Cross-exchange premium(Binance vs Coinbase price gap)
   - Volume / liquidity regime(高量伴隨價格 → 趨勢確認)
2. **PortfolioStrategy always-on 嗎**:macro overlay 是 risk-layer,直覺 always-on(meta-layer 不能關掉)。但 always-on 鎖會限制 V2-E meta-layer 設計空間。V2-A round 後段或 V2-E round 1 拍。
3. **多個 PortfolioStrategy 怎麼疊**:VIX overlay `{"BTC": 1.0, "ETH": 0.3}` + drawdown brake `{"BTC": 0.5, "ETH": 0.5}` → effective cap = `min(各 cap)` 還是 `prod(各 cap)`?min 比較保守、語意清晰;prod 對應「多個獨立 risk score 累積」。

---

## Round 1 review pass 衍生事項(2026-05-17)

Review pass(白話 walk-through 三軸讓使用者 re-validate)過程中浮現:

1. **Over-trading(過度交易)顧慮 → 執行層政策**:使用者 raise 川普推文 / TACO 類噪音會洗手續費。結論:雙 interface 架構不翻案,問題在「執行層」(target → 實際下單的轉換)。需加冷卻工具(dead-band 不動區 / cooling period 冷卻期 / regime-aware 降頻)。**留 round 3「資料流 / 執行管線」攻。**
2. **6 共識 gap 分析的 4 個 gap**:
   - **Gap 1(sizing 方法論)→ 已升級為 M6**(寫進 `v2_roadmap.md` Validation Standards)
   - **Gap 2(策略退役機制)→ 已升級為 M7**(寫進 `v2_roadmap.md` Validation Standards)
   - **Gap 3(最低 edge 門檻)**:M1-M7 是驗證流程標準,缺「edge 要多大才值得上線」的數字。留 V2-B 階段拍。
   - **Gap 4(回測成本模型)**:滑點 / 衝擊成本怎麼在回測模擬,roadmap 無規格。留 V2-B 階段拍。
3. **領域 landscape + 簡單派定調**:見 `v2a/domain_landscape.md`。

## 下一輪(Round 2)

重點(順序待 round 2 開頭跟使用者確認):

1. 策略池候選名單細討論 → 拍替代 mean-reversion 的 style
2. P1 子題挑 2-3 個攻(候選順序:lifecycle methods → param schema → data spec)
3. PortfolioStrategy always-on 鎖 + multiple-PortfolioStrategy 疊合演算法

Round 2 結束 review 後考慮是否進 round 3(資料流 / 多策略架構 / V1 模組沿用點)。
