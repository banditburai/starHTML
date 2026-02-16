# Debugger Phase 1.5: Polish & UX Fixes

> **Epic:** `starhtml-upstream-heg`
> **Predecessor:** Phase 1 (feature/starhtml-debugger branch, commits 2721b5e..92608b9)
> **For Claude:** Use `skills/collaboration/execute-plan-with-beads` to implement.

## Prerequisite

Commit the pending style cleanup + demo fix changes before starting tasks:
```bash
git add -A && git commit -m "refactor(debugger): style cleanup + fix demo"
```

## Context

Three code review sub-agents audited the Phase 1 debugger panel. This plan addresses all findings plus user-requested features. The debugger is a single TypeScript file (`typescript/plugins/debugger.ts`) compiled to `src/starhtml/static/js/plugins/debugger.js`.

**Datastar SSE lifecycle:** `started → [signals/elements/script] → finished` (also `error`, `retrying`, `retries-failed`). These are dispatched as `datastar-fetch` CustomEvents with `detail.type` set to the lifecycle stage.

## Tasks Overview

| ID | Task | Review ID | Blocked By |
|----|------|-----------|------------|
| heg.1 | Clear button + toolbar rework | heg.10 | - |
| heg.2 | CSS polish (contrast, typography, affordances) | heg.11 | - |
| heg.3 | Architecture fixes (panelRef, define guard) | heg.12 | - |
| heg.4 | Data layer: decode JSON + serialize morphs | heg.13 | - |
| heg.5 | Event row previews | heg.14 | heg.4 |
| heg.6 | Type filter chips | heg.15 | heg.1 |
| heg.7 | Start/done request grouping + duration | heg.16 | heg.5 |
| heg.8 | Copy to clipboard + LLM export | heg.17 | heg.4 |
| heg.9 | Incremental rendering + event delegation | heg.18 | heg.1, heg.6 |

---

### Task 1: Clear button + toolbar rework

**Blocked by:** None

**Files:**
- Modify: `typescript/plugins/debugger.ts` (ensureSSEStructure, renderSSETab, PANEL_STYLES)

**What to change:**

1. Replace destructive `clearEvents()` with a **watermark pattern**:
   - Add `private visibleSinceId: number = 0` to the class
   - "Clear" button sets `visibleSinceId = events[events.length-1]?.id + 1 ?? 0` — hides old events without destroying them
   - Filter logic: `events.filter(ev => ev.id >= this.visibleSinceId && ...)`

2. Split the toolbar into clear-filter + clear-events:
   - Add an "×" button inside/after the filter input that clears filter text only (hidden when filter is empty)
   - Rename "Clear" to "Clear Events" with distinct styling (dimmer, red tint on hover)
   - Layout: `[Filter... ×] [Clear Events]  <spacer>  42 events`

3. Keep `clearEvents()` function but only call it for hard purge (e.g., Shift+Click) — or remove the function entirely and rely on ring buffer eviction.

**Verify:** Build, open panel, add events, click Clear Events → events hidden. Type filter → "×" appears → click → filter cleared, events still visible.

---

### Task 2: CSS polish (contrast, typography, affordances)

**Blocked by:** None

**Files:**
- Modify: `typescript/plugins/debugger.ts` (PANEL_STYLES only)

**What to change:**

1. **Color contrast** — Replace all `#6c7086` with `#9399b2` (Catppuccin Overlay2, 5.1:1 ratio). For lifecycle badges on `#313244` background, use `#bac2de` (Subtext1, 5.6:1).

2. **Typography** — Add `line-height: 1.5` to `:host`. Increase `.event-row` padding to `4px 8px`. Increase `.toolbar input` and `.toolbar button` padding to `4px 8px`.

3. **Badge alignment** — Add `min-width: 56px; text-align: center` to `.event-type` for column alignment across rows.

4. **Disclosure triangles** — Add `::before` pseudo-element on `.event-row` with `▸` (right triangle), rotates to `▾` when `.expanded`.

5. **Resize handle** — Add `::after` pseudo-element as a visible 36×3px grab bar centered in the handle. `#45475a` default, `#89b4fa` on hover.

6. **Focus styles** — Add `:focus-visible` outlines on `.tab-btn`, `.toolbar button`, `.toolbar input`.

7. **Scrollbar** — Add `::-webkit-scrollbar` styling for dark theme on `.tab-content` and `.event-detail`. Add Firefox `scrollbar-width: thin; scrollbar-color`.

8. **Detail panel** — Change `word-break: break-all` to `break-word`. Add `border-left: 2px solid #89b4fa` for visual connection to parent row.

9. **Placeholder contrast** — Add `.toolbar input::placeholder { color: #585b70; opacity: 1; }`

**Verify:** Build, visually inspect all states (hover, expanded, resize, filter focus, scrollbar).

---

### Task 3: Architecture fixes (panelRef, define guard)

**Blocked by:** None

**Files:**
- Modify: `typescript/plugins/debugger.ts`

**What to change:**

1. **panelRef cleanup** — In `disconnectedCallback()`, add `if (panelRef === this) panelRef = null;`

2. **Define guard** — Wrap `customElements.define` in `if (!customElements.get("starhtml-debugger"))`.

3. **Lifecycle types** — Add `"error"`, `"retrying"`, and `"retries-failed"` to `TYPE_CONFIG`:
   ```typescript
   "error": { label: "error", cls: "type-error" },
   "retrying": { label: "retry", cls: "type-lifecycle" },
   "retries-failed": { label: "failed", cls: "type-error" },
   ```

**Verify:** Build, check no console errors on double-load. Verify error/retry types have correct badges.

---

### Task 4: Data layer: decode JSON + serialize morphs

**Blocked by:** None

**Files:**
- Modify: `typescript/plugins/debugger.ts`

**What to change:**

1. **Auto-decode nested JSON** — Add `deepDecodeJsonStrings()` helper that recursively tries `JSON.parse()` on string values. Apply before `JSON.stringify` in `formatEventDetail()`. Result: `{"signals": {"count": 1}}` instead of `{"signals": "{\"count\": 1}"}`.

2. **Serialize MutationRecords at capture time** — Define a `SerializedMorph` interface:
   ```typescript
   interface SerializedMorph {
     type: "childList" | "attributes" | "characterData";
     targetSelector: string;
     attributeName?: string;
     oldValue?: string;
     newValue?: string;
     added?: string[];
     removed?: string[];
   }
   ```
   In the `setTimeout(0)` morph-window-close callback, serialize all MutationRecords into `SerializedMorph[]` and store on the event. Drop the raw MutationRecord references. This eliminates the `attrNewValues` WeakMap — capture `newValue` during serialization.

3. **Update `formatEventDetail`** to render from `SerializedMorph[]` instead of raw MutationRecords. Compute flash detection (repeated attr changes on same element) during serialization, store as a `flash: boolean` field.

4. **Update `DebugSSEEvent` interface** — Replace `morphRecords?: MutationRecord[]` with `morphs?: SerializedMorph[]`.

**Verify:** Build, click "Append Element" and "Update Attribute" in demo, expand events — decoded JSON visible, morph details still render correctly.

---

### Task 5: Event row previews

**Blocked by:** Task 4 (needs decoded JSON for signal previews)

**Files:**
- Modify: `typescript/plugins/debugger.ts` (renderSSETab, PANEL_STYLES)

**What to change:**

1. Add `eventPreview()` helper that returns a short string per event type:
   - **signals**: Parse signal keys/values, show `count: 1` (truncated to ~60 chars)
   - **elements**: Show `mode selector`, e.g., `append #dynamic-content`
   - **script**: First ~40 chars of script content
   - **lifecycle**: Empty (start/done/error are self-explanatory)

2. Add `<span class="event-preview">` to the event row HTML after the type badge.

3. Style: `color: #9399b2; overflow: hidden; text-overflow: ellipsis; min-width: 0; flex: 1;`

4. For elements events with morphs, add a compact morph badge: `+1 -0 ~1` after the preview.

**Verify:** Build, trigger increment/append/update-attr, check collapsed rows show inline previews.

---

### Task 6: Type filter chips

**Blocked by:** Task 1 (toolbar layout must be settled first)

**Files:**
- Modify: `typescript/plugins/debugger.ts` (ensureSSEStructure, renderSSETab, PANEL_STYLES)

**What to change:**

1. Add a set of clickable filter chips in the toolbar for each event type:
   ```
   [signals] [elements] [script] [lifecycle]  |  Filter: [____×]  [Clear Events]  42 events
   ```

2. Track active type filters as `private activeTypeFilters: Set<string>` (empty = show all).

3. Clicking a chip toggles that type. Visual: active chips use their type color (filled), inactive are dimmed/outline.

4. Type filtering combines with text filtering (AND logic): event must match active types AND text filter.

5. Chips show count per type: `signals (3)`.

**Verify:** Build, generate mixed events, click chips to filter, verify counts update, verify text filter still works alongside.

---

### Task 7: Start/done request grouping + duration

**Blocked by:** Task 5 (preview infrastructure)

**Files:**
- Modify: `typescript/plugins/debugger.ts`

**What to change:**

1. Track request groups: when a `started` event fires, open a group keyed by the triggering element + timestamp. When `finished` fires for the same element, close the group and compute duration.

2. Display duration on the `done` row: `done (142ms)` or `done (1.2s)`.

3. Add subtle visual grouping: a thin left-border color per request group (alternating 2-3 muted colors), so `start → signals → elements → done` events visually cluster.

4. Add the route/URL to the `start` event preview (from the element's `data-on-click` or similar attribute).

**Verify:** Build, click Increment, verify start/done show duration and events are visually grouped.

---

### Task 8: Copy to clipboard + LLM export

**Blocked by:** Task 4 (needs decoded JSON)

**Files:**
- Modify: `typescript/plugins/debugger.ts` (formatEventDetail, PANEL_STYLES)

**What to change:**

1. **Copy single event** — Add a small "Copy" button in the expanded event detail. Copies the full event detail as formatted text (JSON + morph summary) via `navigator.clipboard.writeText()`.

2. **Copy all visible events** — Add a "Copy All" button in the toolbar. Formats all currently visible (filtered) events as a structured text block suitable for LLM context:
   ```
   === StarHTML Debug Events (42 events) ===

   [20:23:34.706] start
   [20:23:34.714] signals  count: 1
     {"signals": {"count": 1}}
   [20:23:34.714] done (8ms)

   [20:23:53.554] elements  append #dynamic-content
     {"mode": "append", "selector": "#dynamic-content", ...}
     morphs: 1 added, 0 removed, 0 attributes
       + Added <div.flex.items-center> to #dynamic-content
   ...
   ```

3. Show brief "Copied!" tooltip/flash on the button after successful copy.

**Verify:** Build, generate events, click "Copy All", paste into a text editor — verify formatted output is readable and complete. Click individual "Copy" buttons — verify single-event output.

---

### Task 9: Incremental rendering + event delegation

**Blocked by:** Tasks 1, 6 (toolbar and filter settled)

**Files:**
- Modify: `typescript/plugins/debugger.ts` (renderSSETab, ensureSSEStructure)

**What to change:**

1. **Event delegation** — Replace per-row `addEventListener` in `renderSSETab()` with a single click listener on `sseEventList` using `closest(".event-row")`. Set up once in `ensureSSEStructure()`.

2. **Incremental append** — Track `lastRenderedIndex`. On new events (no filter change), only append new rows to the DOM. Set a `needsFullRender` flag when filter text changes, type filters change, expanded row changes, or events are cleared.

3. **Expand/collapse without full re-render** — When toggling a row's expanded state, only mutate that row + its detail div, not the entire list.

4. Keep the full innerHTML path as fallback for `needsFullRender` cases (filter changes, clear).

**Verify:** Build, rapidly click Increment 50+ times, verify no visible lag. Check expand/collapse still works. Check filter still works.

---

## Build & Test

After each task:
```bash
npx vite build                    # Compile TS
uv run python web/demos/30_debugger_demo.py  # Manual test on :5030
```

No Python tests needed for TypeScript-only changes (Tasks 1-9 are all in debugger.ts).
