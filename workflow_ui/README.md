# 工作流 / workflow_ui

極簡風工作管理介面。所有工作放在一處，下拉選單會記住你新增過的選項。

## 本地開發

```bash
npm install
npm run dev      # 開 http://localhost:5173
npm run build    # type-check + 產出 dist/
```

## 資料

所有資料只存在瀏覽器 `localStorage`，key = `workflow_ui:v1`。
之後 Phase 6 會加 JSON 匯出/匯入做備份。

## Phase 進度

- [x] Phase 0 — Vite + React + TS + Tailwind v4 scaffold + 資料 schema + localStorage hook
- [x] Phase 1 — 新增/編輯/刪除 task，動態下拉（首次新增即記憶）
- [ ] Phase 2 — Kanban 看板 + 拖曳改 status
- [ ] Phase 3 — 列表視圖 + 搜尋 + 篩選
- [ ] Phase 4 — Dashboard 視覺化 (即將到期 / 各組織工作量)
- [ ] Phase 5 — 匯入舊筆記
- [ ] Phase 6 — 匯出 JSON 備份 + 暗色模式 toggle

## 結構

```
src/
  types/Task.ts        資料型別
  lib/seed.ts          初始下拉選項 + 顏色對照
  hooks/useStore.ts    state + localStorage + CRUD
  components/
    ComboInput.tsx     下拉 + 自由輸入 (datalist)
    TagsInput.tsx      多標籤輸入 (Enter 加入)
    TaskFormModal.tsx  新增/編輯表單
    TaskCard.tsx       單筆工作卡片
    TaskList.tsx       工作列表 grid
  App.tsx              shell
```
