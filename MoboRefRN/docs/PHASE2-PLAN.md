# MoboRef Phase 2 — 平行開發計劃（CPU + DRAM 相容性查詢）

## Context

Phase 1 已完成：MoboRef RN App 在 iPhone 上能跑、468 顆主機板 catalog、Rack 管理、雲端 boards.json 更新都通了，Mac mini 7 天續期流程驗過、repo 設成 public。

進入 **Phase 2 — 平台層擴充**，並**首次嘗試多 session 平行開發**（user 是 Max 訂閱，要實際驗證平行流程是否可行）。

選定兩條 stream：
- **Stream A — CPU 整合**：新增 CPU catalog（Brand → Gen → SKU），Motherboard 加 socket 欄位
- **Stream B — Motherboard × CPU → DRAM 最高頻率查詢**：在主機板詳細頁可選一顆 CPU，顯示該組合能跑到的 DRAM 最高頻率與限制條件（例如「14 代 K-SKU 才解鎖 DDR5-7200，非 K 只到 DDR5-6400」）

對 AGI 亞奇雷模組驗證情境的價值：B 是核心 — DRAM 模組能不能跑到標稱頻率，**取決於主機板 + CPU 組合**，不是任一單方。把這套查詢內建進 App 等於把驗證前置作業數位化。

預期成果：
1. iPhone 桌面有兩個 App 並存：`MoboRef CPU` + `MoboRef DRAM`
2. 平行開發 SOP 寫進 `CLAUDE.md`，未來 session 共用
3. 完成驗證後合併進主分支 `claude/build-iphone-app-3HKVs`

---

## 1. Roadmap 全景

```
Phase 1 ✅ COMPLETE  — 主機板 catalog + Rack 管理 + iPhone 上線
Phase 2  ← 現在     — Platform Layer：CPU 整合 + DRAM 相容性查詢
Phase 3  TBD        — DUT Layer：AGI 自家 DRAM / SSD 模組 SKU 庫
Phase 4  TBD        — Validation Matrix：平台 × DUT × 結果
Phase 5  TBD        — Reporting & Export：PDF / CSV / Dashboard
```

---

## 2. 關鍵設計決策：B 依賴 A 的資料

Feature B「Motherboard × CPU → DRAM」**邏輯上依賴 CPU 概念**。為了能平行開發，採用「**契約先行 + Stub Data 後替換**」策略：

### 2.1 契約鎖定（在分支前完成，由 Prep Session 一次落地到主分支）

在 main 分支上做**一個小型 prep commit**，先把兩個 stream 都會用到的型別骨架定義好：

- `models/CPU.ts` — 完整 interface 定義（欄位明細見 §4）
- `models/Motherboard.ts` — 加 optional 欄位 `socket?` 和 `dramCompat?`

這個 commit **只動型別 + 空檔**，不寫任何邏輯。落地之後兩個 worktree 從同一個基準分出去 → 之後 merge 不會 schema 衝突。

### 2.2 Stub Data 銜接

- Stream A 在自己分支裡實作真正的 CPU catalog + 資料
- Stream B 在自己分支裡定義「**內部 mock CPU 清單**」（10 顆代表性 CPU 寫在 fixture 檔），UI 完全跑得起來
- 兩條合進主分支後，Stream B 的 mock 換成 `useCPUs()` 真實 hook（最後一個小 PR）

這讓 B 不必等 A 完成才能開工。

### 2.3 Mock CPU 清單（**plan 內釘死，A/B 兩邊都必須涵蓋這 10 顆**）

為了 stub→real 切換 0 風險，下列 10 顆 CPU **必須**：
- 由 Stream B 的 `data/MockCPUsForDram.ts` 定義（給 B 開發期使用）
- 由 Stream A 的 `data/StaticCPUData.ts` 涵蓋（保證收尾 PR 後真實清單能命中所有 dramCompat 規則）

| id | brand | gen | socket | fullModelName | isKSku | maxOfficialDDRSpeed |
|----|-------|-----|--------|---------------|--------|---------------------|
| `intel::14gen::i9-14900k` | INTEL | 14代 | LGA1700 | Core i9-14900K | true | 5600 |
| `intel::14gen::i7-14700k` | INTEL | 14代 | LGA1700 | Core i7-14700K | true | 5600 |
| `intel::14gen::i5-14600k` | INTEL | 14代 | LGA1700 | Core i5-14600K | true | 5600 |
| `intel::14gen::i5-14400` | INTEL | 14代 | LGA1700 | Core i5-14400 | false | 4800 |
| `intel::13gen::i9-13900k` | INTEL | 13代 | LGA1700 | Core i9-13900K | true | 5600 |
| `intel::13gen::i7-13700k` | INTEL | 13代 | LGA1700 | Core i7-13700K | true | 5600 |
| `amd::ryzen9000::r9-9950x` | AMD | Ryzen 9000 | AM5 | Ryzen 9 9950X | false | 5600 |
| `amd::ryzen9000::r7-9700x` | AMD | Ryzen 9000 | AM5 | Ryzen 7 9700X | false | 5600 |
| `amd::ryzen7000::r9-7950x` | AMD | Ryzen 7000 | AM5 | Ryzen 9 7950X | false | 5200 |
| `amd::ryzen7000::r7-7800x3d` | AMD | Ryzen 7000 | AM5 | Ryzen 7 7800X3D | false | 5200 |

涵蓋情境：
- LGA1700 K-SKU（4 顆，跨 13/14 代）→ 驗 K-SKU + gen 規則
- LGA1700 non-K（1 顆）→ 驗 K vs non-K 分流
- AM5 跨代（4 顆）→ 驗 socket 過濾
- 14代 + 13代 兩代並存 → 驗 gen 條件規則

---

## 3. 平行開發基礎建設

### 3.1 Prep Session 動作（必須先做，獨立於兩條 stream）

開**第一個新 session**，cwd = `D:\Projects\iOS9-SpringBoard-Headers`（主 worktree），任務：

1. **把 plan 內容寫進 repo**（讓未來 Stream A/B session 在自己 worktree 讀得到）：
   - 建立 `MoboRefRN/docs/PHASE2-PLAN.md`，內容 = user 貼進來的整份 plan
   - 與後面的步驟一起 commit
2. **更新 `CLAUDE.md`**：把 §1 Roadmap、§3.2 平行 SOP、§8 外出測試 SOP、§9 合併策略寫進去（讓未來每個 session 自動載入這些規範）。**並在 CLAUDE.md 開頭加一行指向 `MoboRefRN/docs/PHASE2-PLAN.md`**
3. **建型別骨架**：
   - 新增 `MoboRefRN/src/models/CPU.ts`（interface 定義 + 空 export）
   - 編輯 `MoboRefRN/src/models/Motherboard.ts` 加 `socket?: string` 和 `dramCompat?: DramCompatRule[]`
   - `dramCompat` 規則型別 `DramCompatRule` 也定義在 `Motherboard.ts` 裡
4. **單一 commit & push** 到 `claude/build-iphone-app-3HKVs`（docs + CLAUDE.md + 型別骨架一起進）
5. **建立兩個 worktree**：
   ```powershell
   git worktree add ..\MoboRef-cpu  -b claude/phase2-cpu
   git worktree add ..\MoboRef-dram -b claude/phase2-dram
   cd ..\MoboRef-cpu\MoboRefRN  ; npm install
   cd ..\MoboRef-dram\MoboRefRN ; npm install
   ```
6. **驗證 CLAUDE.md 載入正確**：開一個 throwaway test session（直接在主 worktree 開新 Claude session），第一句問「你知道 Phase 2 平行 SOP 嗎？簡單講一下兩條 stream 的合併順序」。若回答正確 = CLAUDE.md 真的被讀到；錯誤 = 內容寫得不夠顯眼，重寫該段
7. **session 結束**

Prep session 不寫業務邏輯、不開兩條 stream，純 setup。

### 3.1.1 Prep 完成標記（**全部 7 項通過才算完成，任一未達成 → 重做，不得進 Stream A/B**）

```
☐ 主分支多 1 commit，內含：
    - MoboRefRN/docs/PHASE2-PLAN.md（這份 plan 完整內容）
    - MoboRefRN/src/models/CPU.ts（interface 骨架，依 §4 定義）
    - MoboRefRN/src/models/Motherboard.ts 擴充（socket?、dramCompat?、DramCompatRule 骨架）
    - CLAUDE.md 更新（§1 Roadmap、§3.2 平行 SOP、§8 tunnel SOP、§9 合併策略，開頭指向 PHASE2-PLAN.md）
☐ TypeScript 編譯通過：cd MoboRefRN && npx tsc --noEmit 無 error
☐ 兩個 worktree 資料夾存在（D:\Projects\MoboRef-cpu、D:\Projects\MoboRef-dram）
☐ 兩個 worktree 各自 npm install 完成（ls node_modules 有東西）
☐ 兩個 worktree 各自 git status 乾淨（無 untracked、無 modified）
☐ 兩個 worktree 各自 git pull 後能讀到 MoboRefRN/docs/PHASE2-PLAN.md
☐ Test session 確認 CLAUDE.md 真的被新 session 讀到
```

理由：契約先行的整個架構靠 prep 撐住。Prep 半吊子 = Stream A/B 全踩雷。

### 3.2 平行兩條 stream 的「不會炸」鐵律（要寫進 `CLAUDE.md`）

1. 一個 Phase 同時最多兩個 worktree
2. 兩條 stream 動的檔案**事前列清楚不重疊**（見 §4 §5）
3. Metro server 一個 8081、另一個 `--port 8082`
4. 合併順序固定：A 先 → B rebase 主分支 → B 合 → 最後 stub→real 一個小 PR
5. `app.json` 的 bundleId 改動不合進主分支
6. `ios/` 不進 git，Mac mini 上各 worktree 分別 prebuild

---

## 4. Stream A — CPU 整合範圍

### 動到的檔案

| 檔案 | 動作 |
|------|------|
| `MoboRefRN/src/models/CPU.ts` | **填肉** — 在 prep session 留的骨架上實作完整 interface |
| `MoboRefRN/src/data/StaticCPUData.ts` | **新增** — 內建 fallback CPU 列表（Intel 12-15 代 + AMD AM5 主流，~50 顆起手）|
| `MoboRefRN/src/services/RemoteCPUsService.ts` | **新增** — fetch `cpus.json`，仿 `RemoteBoardsService` |
| `MoboRefRN/cpus.json` | **新增** — 雲端 CPU catalog |
| `MoboRefRN/src/hooks/useCPUs.ts` | **新增** — 仿 `useCatalog.ts` |
| `MoboRefRN/src/screens/CPUScreen.tsx` | **新增** — Brand → Gen → SKU 三層 drill-down |
| `MoboRefRN/App.tsx`（或 navigator）| **擴充** — 加第三個 BottomTab |
| `MoboRefRN/app.json` | **改** — `bundleIdentifier` → `com.<user>.moboref.cpu`、`name` → `MoboRef CPU`（**不合進主分支**）|

### CPU 型別（prep session 已建好，A 只是填肉）

```ts
// models/CPU.ts
export type CPUBrand = 'INTEL' | 'AMD';

export interface CPU {
  id: string;                  // intel::14gen::i9-14900k
  brand: CPUBrand;
  gen: string;                 // "14代", "Ryzen 9000"
  socket: string;              // "LGA1700", "AM5"
  codename?: string;           // "Raptor Lake Refresh"
  fullModelName: string;       // "Core i9-14900K"
  isKSku?: boolean;            // 用於 DRAM 規則匹配
  maxOfficialDDRSpeed?: number; // 6400 (MT/s)
  channels?: number;           // 2
  officialUrl?: string;
}
```

### Reuse 既有 pattern

- `RemoteCPUsService` 抄 `MoboRefRN/src/services/RemoteBoardsService.ts`
- `useCPUs` 抄 `MoboRefRN/src/hooks/useCatalog.ts`
- `CPUScreen` 抄 `MoboRefRN/src/screens/CatalogScreen.tsx`

### 範圍刻意不做

- ❌ Motherboard ↔ CPU 相容性配對 UI（B 在做）
- ❌ DRAM 速度規則邏輯（B 在做）
- ❌ CPU 加進 Rack slot（Phase 4）

---

## 5. Stream B — Motherboard × CPU → DRAM 相容性查詢

### 5.1 資料模型（prep session 已建骨架，B 填肉）

```ts
// models/Motherboard.ts 擴充
export interface DramCompatRule {
  cpuMatch: {
    socket?: string;        // "LGA1700"
    gen?: string;           // "14代"
    isKSku?: boolean;       // 是否需要 K SKU
    minDDRSpeed?: number;   // 必須是這個或更高頻率才適用
  };
  maxDDRSpeed: number;      // 該規則下能跑的最高 DDR 頻率 (MT/s)
  modes?: ('XMP' | 'EXPO' | 'JEDEC')[];
  dimmsFilled?: 1 | 2 | 4;  // 4 DIMM 全插時規則不同
  notes?: string;           // "需 BIOS F23+"
}

export interface Motherboard {
  // ... 既有欄位
  socket?: string;
  dramCompat?: DramCompatRule[];
}
```

### 5.2 動到的檔案

| 檔案 | 動作 |
|------|------|
| `MoboRefRN/src/models/Motherboard.ts` | **填肉** — `DramCompatRule` 完整定義（prep session 已留骨架）|
| `MoboRefRN/boards.json` | **擴充** — 給 5-10 張代表性主機板加 `dramCompat` 資料 seed |
| `MoboRefRN/src/data/StaticBoardData.ts` | **同步** — 同樣幾張板補上 dramCompat（離線一致）|
| `MoboRefRN/src/services/DramCompatService.ts` | **新增** — 純函式：給 (Motherboard, CPU) → 套規則 → 回傳 `{ maxDDRSpeed, matchedRule, caveats }` |
| `MoboRefRN/src/components/DramCompatLookup.tsx` | **新增** — UI 元件：CPU dropdown + 結果卡片，嵌進主機板詳細頁 |
| `MoboRefRN/src/screens/CatalogScreen.tsx` | **小擴充** — 主機板詳細頁掛上 `<DramCompatLookup>` 元件 |
| `MoboRefRN/src/data/MockCPUsForDram.ts` | **新增（暫時）** — Stream B 開發期的 CPU 假資料（10 顆代表 SKU），合併階段最後刪除換成 `useCPUs()` |
| `MoboRefRN/app.json` | **改** — `bundleIdentifier` → `com.<user>.moboref.dram`、`name` → `MoboRef DRAM`（**不合進主分支**）|

### 5.3 DRAM 規則匹配邏輯（DramCompatService 核心）

```
給定 (motherboard, cpu)：
1. 找出 motherboard.dramCompat 中所有「cpuMatch 全部條件都符合該 cpu」的 rule
2. 從中選 maxDDRSpeed 最高的 rule
3. 回傳 { maxDDRSpeed, matchedRule, applicableCaveats }
4. 沒有任何 rule 符合 → 回傳 motherboard 的官方標示頻率作 fallback
```

UI 呈現：
- 主機板詳細頁加一張卡片「📊 DRAM 相容性查詢」
- 上半：CPU 選擇 dropdown（先按 socket 過濾 → 再列 SKU）
- 下半：選定後即時計算結果
  - 大字：`DDR5-7200` (max)
  - 小字：`需 K SKU + XMP，2 DIMM 全插`
  - caveat 區：BIOS 版本、注意事項

### 5.4 範圍刻意不做

- ❌ 反向查詢「我有這顆 CPU 想跑 DDR5-8000，哪些板可以？」（Phase 5 之 dashboard）
- ❌ 規則編輯器 UI（規則直接寫 boards.json）
- ❌ 把規則應用到 Rack slot 上自動標警（Phase 4）

---

## 6. 兩條 stream 的檔案碰撞檢查

| 檔案 | A 動 | B 動 | 衝突？ |
|------|------|------|--------|
| `models/CPU.ts` | ✅ 填肉 | – | 無 |
| `models/Motherboard.ts` | ✅ 加 `socket` | ✅ 加 `DramCompatRule` 細節 | **prep session 已先放骨架**，A/B 各自只動骨架不同段落 → 合併期最多小 conflict，不可能 schema 對立 |
| `boards.json` | – | ✅ | 無（A 不動）|
| `data/StaticBoardData.ts` | – | ✅ | 無 |
| `data/StaticCPUData.ts` | ✅ 新檔 | – | 無 |
| `data/MockCPUsForDram.ts` | – | ✅ 新檔（暫時）| 無 |
| `services/RemoteCPUsService.ts` | ✅ 新檔 | – | 無 |
| `services/DramCompatService.ts` | – | ✅ 新檔 | 無 |
| `hooks/useCPUs.ts` | ✅ 新檔 | – | 無 |
| `screens/CPUScreen.tsx` | ✅ 新檔 | – | 無 |
| `screens/CatalogScreen.tsx` | – | ✅ 小擴充（詳細頁掛元件）| 無 |
| `components/DramCompatLookup.tsx` | – | ✅ 新檔 | 無 |
| `App.tsx` | ✅ 加 tab | – | 無（B 不動）|
| `app.json` | ✅ bundleId | ✅ bundleId | 各自分支獨立，**不合進主分支** |

→ **唯一碰撞點**：`models/Motherboard.ts` 兩條都動，但 prep commit 已先放骨架，A 動的是 `socket` 欄位、B 動的是 `dramCompat` 細節（同檔案不同行段）→ 預期 git merge 自動合併成功，最壞情況是 1-2 行 conflict，30 秒可解。

---

## 7. iPhone 雙 App 並存（Xcode build 流程）

每個 stream 在 Mac mini 上：

```bash
# Stream A
cd ~/iOS9-SpringBoard-Headers
git fetch origin
git checkout claude/phase2-cpu
cd MoboRefRN
npm install
npx expo prebuild --platform ios --clean
open ios/*.xcworkspace
# Xcode → Personal Team → bundle ID com.<user>.moboref.cpu → Run
# 桌面出現「MoboRef CPU」
```

```bash
# Stream B
git checkout claude/phase2-dram
cd MoboRefRN
npm install
npx expo prebuild --platform ios --clean
open ios/*.xcworkspace
# Xcode → bundle ID com.<user>.moboref.dram → Run
# 桌面出現「MoboRef DRAM」
```

**7 天續期**：兩個 App 各 build 一次，每週插 Mac mini 約 10 分鐘。

**Apple 免費帳號 App ID**：目前用了 1 個，加這兩個 = 3 個，限額 10 個 / 7 天，遊刃有餘。

---

## 8. 外出測試（Expo Go Tunnel 流程）

User 需求：在外面 push code → tunnel → Expo Go 立刻看效果。

### 前置

- 家裡 Mac mini 或 Windows **保持開機 + 不睡眠**
- 該機器跑著對應 worktree 的 Metro tunnel server

### 流程

外面：
```powershell
git push origin claude/phase2-cpu   # 或 phase2-dram
```

家裡（事先設好）：
```powershell
# Stream A 機器
cd D:\Projects\MoboRef-cpu\MoboRefRN
git pull
npx expo start --tunnel --port 8081

# Stream B 機器（同一台都行，不同 port）
cd D:\Projects\MoboRef-dram\MoboRefRN
git pull
npx expo start --tunnel --port 8082
```

iPhone Expo Go → 掃 tunnel QR → 跑開發中版本。

⚠️ Expo Go 只跑 JS bundle，**有 native module 變更時不行**。Phase 2 兩條 stream 都是純 JS，OK。

⚠️ Expo Go 的資料 sandbox 跟 Xcode-built App **不同**，僅供功能驗證，不要當日常用。

---

## 9. 合併策略

### 9.1 順序（嚴格遵守）

1. **Prep session** 已先把 CPU.ts / Motherboard.ts 骨架 + CLAUDE.md 落到主分支
2. **Stream A 完成 + 驗證** → 合併到 `claude/build-iphone-app-3HKVs`
   - 排除 `app.json`（保留主分支的 `MoboRef` 名字與 bundleId）
   - 用：`git checkout claude/phase2-cpu -- ':!MoboRefRN/app.json'` 或 PR 內手動排除
3. **Stream B rebase** 主分支：
   ```powershell
   cd D:\Projects\MoboRef-dram
   git fetch origin
   git rebase origin/claude/build-iphone-app-3HKVs
   ```
   預期 `models/Motherboard.ts` 可能 1-2 行小 conflict，手動解：保留 A 的 `socket?` + B 的 `dramCompat?` 兩段都留下即可
4. **Stream B 合併**（同樣排除 `app.json`）
5. **Stub→Real 收尾 PR**（小，30 分鐘）：
   - 刪除 `data/MockCPUsForDram.ts`
   - `DramCompatLookup.tsx` 從讀 mock 改成 `useCPUs()`
   - 驗一次「真實 CPU dropdown 在主機板詳細頁正常顯示」
   - 合併

### 9.2 合併後清理

```powershell
cd D:\Projects\iOS9-SpringBoard-Headers
git worktree remove ..\MoboRef-cpu
git worktree remove ..\MoboRef-dram
git branch -d claude/phase2-cpu
git branch -d claude/phase2-dram
```

Mac mini 上**主分支 prebuild + Xcode build 一次** → `MoboRef`（主 App）升級到 Phase 2 完整版。

雙 App 並存只是 dev 期手段，production 回歸單一 App。

---

## 10. Session 收尾與銜接（**user 的核心問題**）

### 10.1 這個 session 結束方式

- Plan 通過後，**這個 session 的任務就結束了**
- User 不需要在這個 session 內動任何 code
- 唯一遺產：plan file 本身（`/root/.claude/plans/mac-mini-expressive-blossom.md`）→ 包含 prep session + 兩條 stream session 各自要做什麼的完整 brief

### 10.1.1 ⚠️ Plan file 跨 session 可見性問題（**必須先解決才能開 prep session**）

Plan file 路徑 `/root/.claude/plans/mac-mini-expressive-blossom.md` 是**當前這個 Claude 容器的 local 路徑**。其他 session 跑在不同容器 → 預設讀不到這個檔。

**解法（user 必須執行）：**

1. **把這個 session 的 plan 內容複製出來**（從上方對話 / 從 plan file）→ 存成 Windows 本機檔案 `D:\Projects\iOS9-SpringBoard-Headers\PHASE2-PLAN-SOURCE.md`（暫存用，不進 git）
2. **Prep session 第一個 prompt 裡，直接把整份 plan 內容貼進去**（不要叫 prep 去讀 `/root/.claude/plans/...` 那條路徑，它讀不到）
3. **Prep session 的工作項加一條**：把 plan 內容寫進 `MoboRefRN/docs/PHASE2-PLAN.md`（git tracked）並 commit
4. 之後 Stream A/B session 在各自 worktree `git pull` → 就能在本地讀 `MoboRefRN/docs/PHASE2-PLAN.md`

§3.1 prep session 步驟已加這條（見下方更新）。

### 10.2 接下來要開的 session（共 3 個，**有順序**）

#### Session 1（Prep，**必須最先**）

- **位置**：`D:\Projects\iOS9-SpringBoard-Headers`（主 worktree，分支 `claude/build-iphone-app-3HKVs`）
- **第一句話貼這段給 Claude**（**並把整份 plan 內容附在訊息後面**，因為這個 session 沒有 plan file 的 local path 存取權）：
  > 我把 Phase 2 的完整 plan 貼在訊息最下方。你的任務是執行 plan 的 §3.1 Prep Session 全部步驟（共 7 步），完成 §3.1.1 七項驗收標記。第一步就是把這份 plan 內容寫進 `MoboRefRN/docs/PHASE2-PLAN.md`。完成後告訴我 ready，列出 7 項 checkbox 對照狀態。
  > 
  > ===== PLAN START =====
  > [貼整份 plan]
  > ===== PLAN END =====
- **預估時間**：30 分鐘
- **完成標記**：主分支多了一個 commit，Windows 上多兩個資料夾 `MoboRef-cpu` 和 `MoboRef-dram`

#### Session 2（Stream A，**Prep 完才開**）

- **位置**：`D:\Projects\MoboRef-cpu`（worktree，分支 `claude/phase2-cpu`）
- **第一句話貼這段**：
  > 讀 `MoboRefRN/docs/PHASE2-PLAN.md` 的 §4 Stream A，照著做。我這個 session 只負責 CPU 整合，不要碰 Rack 或 DramCompat 相關的東西。`models/CPU.ts` 骨架 prep session 已經建好，你只要填肉。`StaticCPUData.ts` 必須涵蓋 §2.3 釘死的 10 顆 mock SKU（id 一字不差）。完成後給我驗證清單（§11.A）讓我跑一遍。
- **預估時間**：數小時，主要在 catalog 資料整理
- **時間預算**：第一次平行 + 第一次用 worktree，**預留 1.5x buffer**。超過原始預估的 1.5 倍仍未完成（例如 merge conflict 卡住、Metro port 撞、Xcode build 失敗反覆出錯）→ **觸發暫停回報**，不要硬撐，把卡點寫下來找另一 session 協助

#### Session 3（Stream B，**和 Session 2 同時開**）

- **位置**：`D:\Projects\MoboRef-dram`（worktree，分支 `claude/phase2-dram`）
- **第一句話貼這段**：
  > 讀 `MoboRefRN/docs/PHASE2-PLAN.md` 的 §5 Stream B，照著做。我這個 session 只負責 DRAM 相容性查詢，不要碰 CPU catalog 本身。CPU 資料用 `data/MockCPUsForDram.ts`，**內容必須完全使用 §2.3 釘死的 10 顆 SKU，id 一字不差，不要自己挑**。等 Stream A 合併後會做最後的 stub→real 收尾 PR。完成後給我 §11.B 驗證清單。
- **預估時間**：數小時，主要在 dramCompat 規則設計與 UI
- **時間預算**：同 Session 2，**預留 1.5x buffer**，超過 → 觸發暫停回報
- **Mock CPU 清單**：**必須**完全使用 §2.3 釘死的 10 顆 SKU（id 一字不差）。不要自己挑 SKU。否則收尾 PR 會炸

### 10.3 為什麼三個 session 互相獨立、不會踩到對方

- **Prep**：只動主分支 + 建骨架 → 完成後不再被任何人動
- **A**：worktree 物理隔離，分支隔離，動的檔案不重疊（除了 Motherboard.ts 但 prep 已劃好責任區）
- **B**：同上
- **Plan file 是 single source of truth**，三個 session 各自只讀自己需要的章節 → 不需要看其他 session 的對話歷史

### 10.4 各 session 間的「黑盒契約」

互相獨立 = 互相不知道對方在做什麼。靠 plan file 的這幾個契約點同步：

1. `CPU` interface（§4 已釘）→ A 實作、B mock 都遵守
2. `DramCompatRule` interface（§5.1 已釘）→ B 實作、A 完全不碰
3. `Motherboard` 擴充欄位（§4 §5.1）→ prep session 已合到主分支，A/B 都從這個基準分出去
4. 合併順序（§9.1）→ A 先、B rebase、最後 stub→real

---

## 11. 驗證清單

### 11.A Stream A 驗證

1. iPhone 桌面有「MoboRef CPU」icon
2. 第三個 BottomTab `CPU` 出現
3. 進 CPU tab → Brand 列表（Intel + AMD）
4. 點 Intel → Gen 列表（12-15 代）
5. 點 14 代 → SKU 列表（i9-14900K, i7-14700K …）
6. SKU 詳細頁能跳官網
7. 改 `cpus.json` push → Catalog tab 點 ↻ → 看到變更
8. Catalog tab 主機板**仍能正常運作**（無退化）

### 11.B Stream B 驗證

1. iPhone 桌面有「MoboRef DRAM」icon
2. Catalog → 點任一張有 dramCompat 資料的板（例如 ROG MAXIMUS Z790）→ 詳細頁底部出現「📊 DRAM 相容性查詢」卡片
3. CPU dropdown 列出 mock CPU（依 socket 過濾，Z790 板只列 LGA1700）
4. 選 i9-14900K → 顯示 `DDR5-7200`，caveat：「需 K SKU + XMP」
5. 選 i5-14400（非 K） → 顯示 `DDR5-6400`
6. 選一顆不相容 CPU（AM5）→ dropdown 不應出現該 CPU
7. 沒有 dramCompat 資料的板（大多數）→ 卡片顯示「資料尚未建檔」或不顯示卡片
8. Catalog / Rack 既有功能**全部不退化**

### 11.C 合併後總驗證（主分支重新 build）

1. 主 App 同時擁有 CPU tab + 主機板詳細頁的 DRAM 查詢卡片
2. DRAM 查詢的 CPU dropdown 變成「所有 socket 相符的真實 CPU」（從 useCPUs 讀，不是 mock）
3. **Socket 過濾正確性**（A↔B 真實串接驗證）：
   - **11.C.3a**：打開有 dramCompat 的 LGA1700 板（如 ROG MAXIMUS Z790）→ CPU dropdown **只列 LGA1700 CPU**，完全看不到任何 AM5 CPU（含 R9 9950X、R7 7800X3D 等）
   - **11.C.3b**：打開有 dramCompat 的 AM5 板（如 X670E-E）→ CPU dropdown **只列 AM5 CPU**，完全看不到任何 LGA1700 CPU
   - **11.C.3c**：dropdown 內的 CPU 數量 = `StaticCPUData` 中該 socket 的 CPU 數量（A 的真實資料 ≥ §2.3 mock 10 顆，整數應對得上）
4. 11.A 八項 + 11.B 八項**全部重跑一遍**確認沒互相退化（特別注意：B 的 dramCompat 結果在 mock 切 real 後數值要完全一致）
5. AsyncStorage 既有 racks_v2 / custom_boards_v1 / 等資料完整保留
6. `MoboRef CPU` 與 `MoboRef DRAM` 兩個 dev App 仍可獨立 build（雙 App 並存能力沒退化）

---

## 12. 風險清單

| 風險 | 機率 | 緩解 |
|------|------|------|
| 平行 session 互改檔案 | 低 | worktree 物理隔離 + §6 檔案責任表 |
| Metro port 衝突 | 中 | A 用 8081、B 用 8082 |
| `Motherboard.ts` 合併衝突 | 中 | prep 預留骨架 + 責任區分明，預期 30 秒可解 |
| `app.json` 合進主分支誤改名 | 中 | §9.1 合併指令明確排除 |
| Apple App ID 配額 | 極低 | 3/10 |
| 外出 tunnel 失敗 | 中 | 出門前確認家機 Metro 在跑、設定不睡眠 |
| Stub→Real 收尾忘記做 | 中 | §10.2 寫進合併 checklist，列為 Phase 2 完成的硬性條件 |
| 平行實際比序列慢 | 中 | 第一次必有學習成本，第二次起回收；不適合就退回序列 |
| B 設計的 dramCompat 規則和 A 預期的 CPU.isKSku 對不起來 | 中 | §4 CPU interface 與 §5.1 DramCompatRule 同時釘進 plan，prep session 落地骨架後就鎖契約 |

---

## 13. Critical Files Referenced

### 既有檔案（prep / A / B 不同階段會動）

- `MoboRefRN/src/models/Motherboard.ts` — prep 加骨架，A 加 socket，B 加 dramCompat 細節
- `MoboRefRN/src/models/Rack.ts` — Phase 2 不動
- `MoboRefRN/src/hooks/useCatalog.ts` — A 仿照新增 useCPUs.ts
- `MoboRefRN/src/hooks/useRacks.ts` — Phase 2 不動
- `MoboRefRN/src/services/RemoteBoardsService.ts` — A 仿照
- `MoboRefRN/src/screens/CatalogScreen.tsx` — B 在詳細頁掛 DramCompatLookup
- `MoboRefRN/src/screens/RackScreen.tsx` — Phase 2 不動
- `MoboRefRN/boards.json` — B 加 5-10 張板的 dramCompat 資料
- `MoboRefRN/src/data/StaticBoardData.ts` — B 同步 dramCompat
- `MoboRefRN/app.json` — A/B 各自改 bundleId（不合主分支）
- `CLAUDE.md` — prep session 更新（§10.2 Session 1）

### 新增檔案

- `MoboRefRN/src/models/CPU.ts`（prep 骨架，A 填肉）
- `MoboRefRN/src/data/StaticCPUData.ts`（A）
- `MoboRefRN/src/services/RemoteCPUsService.ts`（A）
- `MoboRefRN/cpus.json`（A）
- `MoboRefRN/src/hooks/useCPUs.ts`（A）
- `MoboRefRN/src/screens/CPUScreen.tsx`（A）
- `MoboRefRN/src/services/DramCompatService.ts`（B）
- `MoboRefRN/src/components/DramCompatLookup.tsx`（B）
- `MoboRefRN/src/data/MockCPUsForDram.ts`（B 暫時，最後 PR 刪除）

---

## 14. 不在這次範圍內

- DRAM 反向查詢 dashboard（Phase 5）
- DRAM / SSD 模組 SKU 庫（Phase 3）
- Validation Matrix 三維資料（Phase 4）
- PDF / CSV 報表匯出（Phase 5）
- Swift 重寫
- TestFlight / App Store 上架
