# Debugger Timeline Tab — Implementation Plan

> **Epic:** `starhtml-upstream-b4o`
> **Design:** `docs/designs/2026-02-17-debugger-timeline-tab.md`
> **For Claude:** Use `skills/collaboration/execute-plan-with-beads` to implement.

## Tasks Overview

| ID | Task | Review | Blocked By |
|----|------|--------|------------|
| b4o.1 | Server-side debug context | b4o.14 | - |
| b4o.2 | Timeline event schema + ring buffer | b4o.15 | - |
| b4o.3 | Malformed SSE validator | b4o.16 | - |
| b4o.4 | Causal linking + trace assembly | b4o.17 | b4o.2 |
| b4o.5 | User action + signal change capture | b4o.18 | b4o.2 |
| b4o.6 | Wire malformed SSE into capture | b4o.19 | b4o.2, b4o.3 |
| b4o.7 | Warning detection + anomaly patterns | b4o.20 | b4o.4 |
| b4o.8 | Timeline UI: tab scaffolding + CSS | b4o.21 | b4o.2 |
| b4o.9 | Timeline UI: trace row rendering | b4o.22 | b4o.4, b4o.8 |
| b4o.10 | Timeline UI: expanded cascade + full trace | b4o.23 | b4o.9 |
| b4o.11 | Export: Markdown trace formatter | b4o.24 | b4o.4, b4o.7 |
| b4o.12 | Export: selection modes + copy UI | b4o.25 | b4o.10, b4o.11 |
| b4o.13 | End-to-end verification + polish | b4o.26 | b4o.1, b4o.6, b4o.12 |

---

### Task 1: Server-side debug context

**Blocked by:** None (independent Python work)

**Files:**
- Modify: `src/starhtml/realtime.py` — add `contextvars` request context, auto-populate `debug_ctx`
- Modify: `src/starhtml/server.py` — populate context in `_endp()` handler wrapper
- Verify: `web/demos/30_debugger_demo.py` — confirm x-debug-* headers appear in SSE events

**Steps:**

1. Add `contextvars.ContextVar('starhtml_debug')` and a sequence counter to `realtime.py`
2. In `server.py`'s `_endp()` (or equivalent handler wrapper), create debug context dict with `seq`, `handler` (function name), `route` (path), `start_time` and set it on the context var. Wrap handler call in try/finally to reset.
3. In `format_sse_event()`, `format_signal_event()`, `format_element_event()`: if `debug_ctx` param is None, auto-read from context var. Only when `debug=True` on the app.
4. Run demo, open debugger, verify SSE Events tab shows handler names and routes in event rows (the UI already renders `debugMeta` fields — they were just always empty).

**Acceptance:** SSE events in the debugger show handler name and route without any developer code changes.

---

### Task 2: Timeline event schema + ring buffer

**Blocked by:** None (foundational TS module)

**Files:**
- Create: `typescript/plugins/debugger-timeline.ts` — event types, buffer, emit, subscribe
- Modify: `vite.config.ts` — add `debugger-timeline` entry point

**Steps:**

1. Define `TimelineEvent`, `TimelineEventType`, and per-type data interfaces (`UserActionData`, `SseEventData`, `SignalChangeData`, `EffectEvalData`, `DomMutationData`, `MalformedSseData`).
2. Implement ring buffer: `TIMELINE_MAX_EVENTS = 5000`, `TIMELINE_PRESERVE_FIRST = 500`. FIFO eviction. Array-based.
3. Implement `emit(event)` that assigns monotonic `id`, stores `performance.now()` and `Date.now()`, appends to buffer.
4. Implement `subscribe(fn)` / `unsubscribe(fn)` for render notifications (same pattern as `debugger-capture.ts`).
5. Implement `getTraces(): TraceSummary[]` that groups events by `traceId` and computes aggregate stats (counts per type, total duration, root event description).
6. Implement `getTraceEvents(traceId): TimelineEvent[]`.
7. Export `init()` and `cleanup()`.
8. Add entry to `vite.config.ts`, verify `npx vite build` succeeds.

**Acceptance:** Module compiles, exports are importable, ring buffer stores and evicts correctly.

---

### Task 3: Malformed SSE validator

**Blocked by:** None (independent TS module)

**Files:**
- Create: `typescript/plugins/debugger-sse-validator.ts` — fetch monkey-patch, stream tee, validation rules

**Steps:**

1. Implement `install(callback)` that monkey-patches `window.fetch`.
2. Detection: intercept requests with `Datastar-Request` header or `Accept: text/event-stream`.
3. For matching requests, `response.body.tee()` — one copy to Datastar, one to validator.
4. Return new `Response` with the Datastar copy.
5. `validateStream()`: async function that reads the validator copy, accumulates lines, validates on blank-line boundaries.
6. Implement `validateRawEvent()` with rules: `MERGED_EVENTS` (two `event:` lines), `MISSING_EVENT_TYPE`, `UNKNOWN_FIELD`, `BINARY_DATA`, `MISSING_TRAILING_BLANK_LINE`.
7. Implement per-type validators: `validateSignalsData` (JSON parse, required `signals` key), `validateElementsData` (required `elements` key, valid modes), `validateScriptData`.
8. Implement `WRONG_CONTENT_TYPE` check on response headers.
9. Implement `STREAM_ERROR` catch for reader failures.
10. Safety valve: stop validating after 1MB per response.

**Acceptance:** Validator catches all 10 defined error types. Callback fires with structured `SSEValidationError` objects.

---

### Task 4: Causal linking + trace assembly

**Blocked by:** Task 2

**Files:**
- Modify: `typescript/plugins/debugger-timeline.ts` — add traceId/parentId assignment, microtask detection

**Steps:**

1. Add trace state: `activeTraceId`, `activeParentId`, `activeDepth`, `nextTraceId`.
2. Implement `beginTrace(rootEvent)` — opens a new trace, sets root event as parent.
3. Implement `emitChild(event)` — assigns current traceId/parentId/depth.
4. Implement `pushParent(event)` / `popParent()` for nesting.
5. Implement microtask boundary detection: after opening a trace, schedule `Promise.resolve().then()` to close it. This naturally captures synchronous cascades.
6. For async SSE responses: correlate by matching `sse-lifecycle:started` element reference to subsequent SSE events (reuse `openGroups` pattern from debugger-capture.ts via the groupId).
7. Wire into existing `datastar-fetch` event listener: SSE lifecycle events create/extend traces.
8. Test with demo: verify a click → SSE → signal → DOM chain produces a single trace with correct parent/child relationships.

**Acceptance:** Events within a synchronous cascade share a traceId. Parent-child relationships are correct. Async SSE responses are linked to their originating trace.

---

### Task 5: User action + signal change capture

**Blocked by:** Task 2

**Files:**
- Modify: `typescript/plugins/debugger-timeline.ts` — add user action listeners and signal-patch integration

**Steps:**

1. Add delegated `document.addEventListener` (capture phase) for `click`, `input`, `submit`, `keydown`.
2. Filter: ignore events targeting `starhtml-debugger` (the debugger itself). For non-click events, only capture if the target has a `data-on-*` attribute.
3. Extract `datastarAction` from the target's relevant `data-on-{eventType}` attribute.
4. Build `targetSelector` (id-based if available, otherwise tag.class).
5. Emit `user-action` event and call `beginTrace()`.
6. Wire `datastar-signal-patch` listener: for each changed signal path, emit `signal-change` event with old/new values and source inference ("sse" if inside an active SSE trace, "user" if inside a user-action trace, "init" otherwise).
7. Signal change values capped at 1KB serialized (reuse truncation pattern from debugger-signals.ts).

**Acceptance:** User clicks appear as trace roots. Signal changes are emitted with correct source tags and old/new values.

---

### Task 6: Wire malformed SSE into capture

**Blocked by:** Tasks 2, 3

**Files:**
- Modify: `typescript/plugins/debugger-timeline.ts` — import validator, emit malformed events
- Modify: `typescript/plugins/debugger-capture.ts` — add `sse-malformed` type to TYPE_CONFIG and chip categories

**Steps:**

1. In `debugger-timeline.ts` `init()`, call `installSSEValidator(callback)`.
2. Callback emits `sse-malformed` timeline events with `MalformedSseData`.
3. Also inject synthetic `DebugSSEEvent` into the capture store (so malformed events appear in the SSE Events tab too).
4. In `debugger-capture.ts`: add `"sse-malformed"` to `TYPE_CONFIG` with error styling. Add to lifecycle chip category.
5. In `debugger.py`: add CSS for malformed event rows (`.type-malformed` with red badge, matching existing error styling).
6. Test: create a demo route that sends intentionally malformed SSE (missing event line, bad JSON, missing blank line). Verify errors appear in both SSE Events tab and Timeline.

**Acceptance:** Malformed SSE events are visible in both tabs. SSE Events tab shows them with error badges. Timeline shows them as trace events with warning/error level.

---

### Task 7: Warning detection + anomaly patterns

**Blocked by:** Task 4

**Files:**
- Modify: `typescript/plugins/debugger-timeline.ts` — add `detectWarnings()` and pattern matchers

**Steps:**

1. Implement `detectWarnings(events: TimelineEvent[]): Warning[]` that runs pattern matchers on a trace's events.
2. Implement matchers:
   - `detectSignalPingPong`: same signal changed 3+ times in one trace
   - `detectExcessiveEffects`: >15 effect-eval events per trace
   - `detectHangingRequest`: sse-lifecycle:started with no finished after 5s
   - `detectSelectorRace`: two elements events targeting same selector
   - `detectNoMorphs`: elements event that produced zero DOM mutations (correlate with MutationObserver window)
   - `detectAttributeFlash`: same attribute changed 2+ times in morph window
3. Store warnings on `TraceSummary`.
4. Mark hanging traces as "stale" after 5s timeout (check in render cycle).

**Acceptance:** Pathological patterns are detected and surfaced as warnings on TraceSummary objects. Stale traces are marked.

---

### Task 8: Timeline UI: tab scaffolding + CSS

**Blocked by:** Task 2

**Files:**
- Modify: `src/starhtml/debugger.py` — replace Timeline placeholder with real tab content, toolbar, container, CSS, setup script

**Steps:**

1. Replace the "Coming in Phase 3" placeholder with actual Timeline tab content structure:
   - Toolbar: filter input, event count, "Copy Trace" button, "Last Ns" dropdown
   - Container: `data_ref="timeline_list"` div for trace rows
2. Add CSS for timeline-specific elements: `.timeline-row`, `.tl-time`, `.tl-cause`, `.tl-summary`, `.tl-duration`, `.tl-warn-badge`, `.timeline-warn`, `.timeline-stale`.
3. Follow existing tab patterns: use same toolbar height, font sizes, chip styles as SSE Events tab.
4. Add setup script section that imports `debugger-timeline.js`, calls `init()`, subscribes to updates, and schedules renders via `requestAnimationFrame`.
5. Wire active tab switching: only render timeline when tab is active (performance, same pattern as other tabs).
6. Add event count to tab button: `Timeline (N)`.

**Acceptance:** Timeline tab is visible, has correct layout, setup script initializes the module. Tab shows event count.

---

### Task 9: Timeline UI: trace row rendering

**Blocked by:** Tasks 4, 8

**Files:**
- Modify: `typescript/plugins/debugger-timeline.ts` — add `buildTraceRowHtml()` render helper
- Modify: `src/starhtml/debugger.py` — wire render into setup script

**Steps:**

1. Implement `buildTraceRowHtml(trace: TraceSummary): string` that renders a collapsed trace row:
   - Time (HH:MM:SS.mmm)
   - Root cause icon + description (click target, SSE route, timer, etc.)
   - Arrow → summary counts (N signals, N effects, N DOM)
   - Duration badge
   - Warning badge(s) if any
2. Implement `scheduleTimelineRender()` in the setup script. Pattern: incremental append for new traces, full re-render on filter change.
3. Add click delegation on `timeline_list` container for expand/collapse.
4. Implement filter: text search across trace root cause, signal paths, routes.
5. Add type-based chip filters (user actions, SSE, signals, warnings).
6. Auto-scroll to bottom with "Jump to latest" button if user has scrolled up (reuse SSE tab pattern).

**Acceptance:** Traces appear as scannable rows. Clicking expands/collapses. Filter and chips work. Auto-scroll works.

---

### Task 10: Timeline UI: expanded cascade + full trace

**Blocked by:** Task 9

**Files:**
- Modify: `typescript/plugins/debugger-timeline.ts` — add `buildTraceDetailHtml()` and `buildFullTraceHtml()`
- Modify: `src/starhtml/debugger.py` — CSS for nested tree, full trace `<pre>` block

**Steps:**

1. Implement `buildTraceDetailHtml(traceId): string` — expanded cascade tree:
   - Group events by phase: TRIGGER, SSE, SIGNAL (with nested effects/DOM), FINISHED
   - Tree-line characters (┣, ┃, ┗, └) via CSS borders, not actual characters
   - Signal changes show old → new with type coloring
   - DOM mutations show selector + change summary
   - Warnings inline with ⚠ badges
2. For pathological cascades: summarize repeated patterns ("x→y→x→y... 12 cycles") instead of showing all events. "Show all N events" link at bottom.
3. Implement `buildFullTraceHtml(traceId): string` — flat timestamped event dump in `<pre>` block with copy button.
4. Add CSS for cascade tree: indentation levels, phase labels with type colors, tree lines.
5. Copy button on full trace: copies plain text to clipboard.

**Acceptance:** Expanded view shows nested cascade tree. Pathological cascades are summarized. Full trace view shows all events. Copy works.

---

### Task 11: Export: Markdown trace formatter

**Blocked by:** Tasks 4, 7

**Files:**
- Modify: `typescript/plugins/debugger-timeline.ts` — add `formatTraceExport()` and `formatAllTracesExport()`

**Steps:**

1. Implement `formatTraceExport(traceId): string` that produces Markdown:
   - Header: trace ID, event count, duration, root cause, timestamp
   - Format legend section explaining `[signals]`, `[elements]`, `[start]`/`[done]`
   - Page context: framework version, active components (from signal namespaces), signal snapshot
   - Chronological event log with relative timestamps (`[+Nms]`)
   - Signal changes section (start → end diff)
   - Diagnostic notes section from warning detection patterns
2. Implement `formatAllTracesExport(traceIds): string` for multi-trace export.
3. Implement progressive truncation: collapse repeated patterns → truncate HTML payloads to 200 chars → keep first/last N events. Hard cap at 20KB.
4. Size-aware: if single trace >5KB, apply truncation. If multi-trace >50KB, omit older traces with note.
5. Signal snapshot integration: read current entries from `debugger-signals.ts` exports.

**Acceptance:** Export produces well-formatted Markdown. Size stays within budget. Diagnostic notes are generated from warning patterns.

---

### Task 12: Export: selection modes + copy UI

**Blocked by:** Tasks 10, 11

**Files:**
- Modify: `typescript/plugins/debugger-timeline.ts` — selection state, copy handlers
- Modify: `src/starhtml/debugger.py` — toolbar buttons, dropdown, shift-click handling

**Steps:**

1. **Copy Interaction Group**: clicking a trace's copy icon exports that single trace via `formatTraceExport()`.
2. **Copy Last N Seconds**: toolbar dropdown (5s / 15s / 30s / 60s). Filters traces by `wallTime` within window, exports via `formatAllTracesExport()`.
3. **Copy Time Range**: shift-click two trace rows to mark start/end. Highlight selected range. Export button exports the selection.
4. All copy actions: write to clipboard via `navigator.clipboard.writeText()`, show brief "Copied!" confirmation flash.
5. Add copy icon to trace rows (small clipboard icon, appears on hover).
6. Add "Export" dropdown button to toolbar with the three modes.

**Acceptance:** All three selection modes work. Clipboard contains well-formatted Markdown. Confirmation flash shows on copy.

---

### Task 13: End-to-end verification + polish

**Blocked by:** Tasks 1, 6, 12

**Files:**
- Modify: `web/demos/30_debugger_demo.py` — add timeline test scenarios
- Modify: various — bug fixes and polish

**Steps:**

1. Add demo scenarios that exercise the Timeline:
   - Simple click → SSE → signal → DOM chain
   - Concurrent SSE requests (two buttons clicked rapidly)
   - Timer-based signal changes (existing ticker)
   - Persist restore on page reload
   - Malformed SSE endpoint (intentionally broken for testing)
2. Verify server debug context: handler names and routes appear in timeline events.
3. Verify malformed SSE: broken endpoint shows errors in both SSE Events and Timeline tabs.
4. Verify warning detection: create a signal ping-pong scenario, verify warning badge appears.
5. Verify export: copy a trace, paste into a text editor, confirm it's readable and includes diagnostic notes.
6. Verify progressive disclosure: collapsed → expanded → full trace all work correctly.
7. Performance check: generate 1000+ events rapidly, verify UI stays responsive (incremental render, RAF batching).
8. Fix any edge cases found during testing.
9. Build: `npx vite build` succeeds, demo works end-to-end.

**Acceptance:** Demo exercises all Timeline features. No console errors. Export is LLM-readable. Performance is acceptable at 1000+ events.
