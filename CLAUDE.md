# MoboRef — Claude Onboarding

Active project: a React Native / Expo iOS app for managing motherboard
catalogs and physical "racks" of test boards. Don't touch the legacy
`SpringBoard.framework/` headers — those are unrelated archive material.

## Project paths

- **App root**: `MoboRefRN/`
- **Dev branch**: `claude/build-iphone-app-3HKVs` (commit + push every change here)
- **User dev environment**: Windows + PowerShell, repo cloned at `D:\Projects\iOS9-SpringBoard-Headers`
- **Test target**: iPhone 17 Pro via Expo Go on the same Wi-Fi
- **No Mac**: builds are via EAS cloud later, not local Xcode

## Architecture

Two tabs (BottomTab navigator):

- **CatalogScreen** — Brand → Chipset → model list. Tap → open spec page in
  in-app browser. Custom user-added boards mixed in.
- **RackScreen** — 3-column grid of "racks". Three independent layers per cell:
  1. **Space** — absolute grid coordinate, never changes (1..N)
  2. **Slot**  — whether the framework exists at that space (deletable, sparse)
  3. **Board** — motherboard info inside the slot (clearable)

### Rack edit-mode UX (iPhone home-screen analogue)

- 🔴 RED `×` on filled slot → clear board, slot stays as drop target
- ⚫ GRAY `×` on empty slot → delete slot framework, later slots shift forward
- `+` on empty space → restore a slot at that exact space
- Long-press slot → drag mode
- Drag onto **empty space** → only the dragged slot moves (others unchanged)
- Drag onto **occupied space** → iPhone-style splice-insert across the
  sorted list of existing slots
- `−` next to row → remove the entire row (3 spaces)
- `+ Add Row` → 3 new spaces + 3 new empty slot frameworks

## Critical files

| File | Role |
|------|------|
| `MoboRefRN/src/models/Motherboard.ts` | Board type (id, brand, chipset, model, isCustom) |
| `MoboRefRN/src/models/Rack.ts` | `Rack { totalSpaces, slots[] }`, `RackSlot { id, space, motherboard? }` |
| `MoboRefRN/src/data/StaticBoardData.ts` | Bundled fallback catalog (~308 boards) |
| `MoboRefRN/boards.json` | Remote catalog source on GitHub raw |
| `MoboRefRN/src/services/RemoteBoardsService.ts` | Fetches `boards.json`, 24hr cache |
| `MoboRefRN/src/services/URLResolverService.ts` | Builds brand-specific spec URLs (no Google for major boards) |
| `MoboRefRN/src/hooks/useCatalog.ts` | Catalog state + `openOfficialPage` |
| `MoboRefRN/src/hooks/useRacks.ts` | Rack CRUD; v1 → v2 migration on load |
| `MoboRefRN/src/hooks/useCustomBoards.ts` | User-added boards (AsyncStorage) |
| `MoboRefRN/src/hooks/useSavedUrls.ts` | Confirmed spec URLs per board id |
| `MoboRefRN/src/hooks/useVisitedBoards.ts` | Per-board confirmed/wrong status |
| `MoboRefRN/src/screens/RackScreen.tsx` | Rack grid + drag + edit mode (~1100 lines) |
| `MoboRefRN/src/screens/CatalogScreen.tsx` | Brand/chipset filters + flat list |

## Storage keys (AsyncStorage)

- `racks_v2` — current rack data (space-based, sparse-allowed)
- `racks_v1` — legacy (auto-migrated to v2 on first load)
- `custom_boards_v1` — user-added boards
- `saved_urls_v1` — confirmed spec page URLs per board id
- `visited_boards_v1` — confirmed/wrong status per board id
- Cache for `boards.json` is handled inside `RemoteBoardsService`

## Common pitfalls (already fixed, don't reintroduce)

1. **Two iOS Modals at once** → SFSafariViewController (`expo-web-browser`
   PAGE_SHEET) refuses to present while another Modal is on screen.
   `LoadingOverlay` is a Modal — never wrap `openBrowserAsync` in it.
   For InfoCard → browser handoff use `Modal onDismiss` (fires AFTER the
   slide-out animation) before opening the browser.
2. **Concurrent `openBrowserAsync`** also hangs. Guard with `isBrowserOpenRef`.
3. **PanResponder + long-press** must live on an ANCESTOR `View` of the slots
   so it can capture touches mid-press (use `onMoveShouldSetPanResponderCapture`).
4. **`measureInWindow` returns window coords** — drag overlay sits inside the
   container, so subtract the container origin from all `dragPos` calcs.
5. **Position vs space**: `slot.space` is the absolute grid coordinate.
   `slots` is sorted by space but may be SPARSE (gaps allowed). Don't assume
   `slot.space === arrayIndex`.
6. **`moveSlot(rackId, fromId, toSpace)`** handles BOTH cases (empty target =
   direct relocate; occupied = iPhone splice-insert). Don't call it with a
   slot id — it expects a space coordinate.

## Dev loop (Windows / PowerShell)

```powershell
# Pull latest
cd D:\Projects\iOS9-SpringBoard-Headers
git pull origin claude/build-iphone-app-3HKVs

# Start Expo (clear Metro cache when code changes don't take effect)
cd MoboRefRN
npx expo start -c
```

If the iPhone shows stale code: shake device → Reload, or press `r` in the
Expo terminal. If a "Stopped server" line appears in Expo logs, the server
needs `npx expo start -c` again.

## Updating the remote board catalog

Edit `MoboRefRN/boards.json` directly OR run the helper:

```powershell
node scripts/update-boards.js     # crawls 4 brands for new models
git add MoboRefRN/boards.json
git commit -m "db: add N new boards YYYY-MM-DD"
git push origin claude/build-iphone-app-3HKVs
```

App users press the `↻` button (Catalog tab header) to fetch the new file.

## Test plan after any rack/grid change

1. New rack → 9 spaces, all with empty slot frameworks
2. Edit mode → red `×` on filled slots, gray `×` on empty slots
3. Gray `×` on slot 5 → slots 6–9 shift forward, space 9 becomes empty (`+`)
4. Tap `+` on empty space → slot reappears at that space
5. Long-press slot → drag mode → drop on empty space → only that slot moves
6. Drag onto an occupied space → intermediate slots shift (iPhone insert)
7. Reload App → state persists exactly (verify AsyncStorage round-trip)

## Style rules

- TypeScript everywhere; avoid `any`
- Prefer `useMemo` for derived `slots` to keep `slotsRef.current` consistent
- Comments only when WHY is non-obvious (modal stacking, ref forwarding,
  TDZ, etc.) — never describe WHAT the code does
- Don't add error handling for impossible cases; trust framework guarantees
- Match existing iOS UI conventions (system blue `#007AFF`, red `#FF3B30`,
  rounded corners, sheet-style modals)

## Out of scope

- Native iOS / Swift implementation (deferred until Mac mini arrives)
- Android (Expo will work, but the user only targets iPhone)
- Anything in `SpringBoard.framework/` — those are unrelated header files
