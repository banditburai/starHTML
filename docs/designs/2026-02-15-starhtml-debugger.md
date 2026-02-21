# StarHTML Debugger Design

**Created:** 2026-02-15
**Status:** Approved

## Problem Statement

Debugging StarHTML apps currently requires opening browser DevTools, parsing raw SSE event streams manually, hunting through DOM attributes for signal values, and using the Banshee Chrome extension for console log capture. When issues like flash/flicker occur during DOM morphing (e.g., in StarMo notebooks), there's no way to trace the causal chain: which SSE event triggered which morph, which morph caused which DOM mutations, and where the visual glitch originated.

Existing tools (Datastar Pro Inspector, HTMX debugger, browser DevTools) don't provide morph-aware debugging -- correlating SSE events with their resulting DOM mutations.

## Solution Overview

A built-in debug panel activated by `debug=True` on `serve()`, implemented as a StarElement web component (Shadow DOM, bottom drawer). Three tabs focused on StarHTML-specific debugging needs, with server-side SSE enrichment for full-stack observability. The key differentiator is morph-aware debugging that correlates SSE events with their resulting DOM mutations.

## Architecture

### Activation

When `debug=True` is passed to `serve()`:

1. **Debug StarElement auto-registered** -- equivalent to `app.register(StarHTMLDebugger)`, injecting template, CSS, and JS into every page
2. **`<starhtml-debugger>` element appended to `<body>`** -- bottom drawer panel with Shadow DOM for style isolation
3. **SSE events enriched** with debug metadata (sequence number, timestamp, handler name, route)
4. **`data-ignore` attribute** on the debugger host element to prevent morph removal

When `debug=False` (default): nothing registered, nothing injected, zero overhead.

### Production Safeguards

- Startup warning to stderr: `WARNING: StarHTML debug mode is ON. Do not use in production.`
- Visual indicator on the debug panel (bright border or "DEBUG MODE" label)
- `STARHTML_DEBUG` env var override to force debug off regardless of code
- Debug JS bundle is separate from main StarHTML runtime -- never loaded in production

### Client-Side Instrumentation

**SSE Event Capture:** Uses Datastar's `datastar-fetch` CustomEvent (dispatched on `document` for every SSE event). No EventSource wrapping or fetch monkey-patching needed. Server-side debug metadata (x-debug-seq, x-debug-ts, x-debug-handler, x-debug-route) is included as extra SSE data lines and surfaces automatically in `argsRaw`.

**Signal Tracking:** Uses Datastar's exported `effect()` + `filtered()` API for reactive signal state tracking. Uses `datastar-signal-patch` CustomEvent for change diffs. No polling.

**Morph Correlation:** MutationObserver on `document.body`. When a `datastar-patch-elements` event arrives via `datastar-fetch`, a morph window opens. MutationObserver records are grouped to that SSE event using microtask boundary (`queueMicrotask`), since Datastar's morph (Idiomorph) is synchronous. Deterministic correlation, not time-based heuristics.

**Flash Detection:** Heuristic watching for rapid attribute toggles (visibility, opacity, display, class) on the same element within ~100ms. Flags these in the morph log with warning indicators.

### Server-Side Instrumentation

When `debug=True`, SSE response helpers add metadata as extra data lines:

```
event: datastar-patch-signals
data: signals {"count":5}
data: x-debug-seq 42
data: x-debug-ts 1708012800000
data: x-debug-handler update_cell
data: x-debug-route /sse/notebook
```

Datastar parses unknown keys into `argsRaw` but ignores them in destructuring. Safe and forward-compatible.

## Data Flow

```
Python Server (debug=True)
  │
  ├─ SSE event + debug metadata ──► datastar-fetch CustomEvent
  │                                    ├─► SSE Events tab
  │                                    └─► Morph correlation (marks morph window)
  │
  ├─ HTML page + <starhtml-debugger> ──► Browser renders panel
  │
  └─ Debug JS bundle ────────────────► Debugger runtime loads

Browser (client-side hooks)
  │
  ├─ MutationObserver on body ────► Morph Log (grouped by SSE event)
  │                                 └─► Flash detection (heuristic flags)
  │
  ├─ effect() + filtered() ──────► Signals tab (live values, change highlights)
  │   datastar-signal-patch        └─► Persisted signals sub-view
  │
  └─ All converge in ────────────► Timeline / "What Just Happened?" view
```

## Panel UI

### Bottom Drawer

- Collapsed: small tab at bottom (~30px) with "StarHTML Debug" label, badge for new events
- Expanded: ~35% viewport height, resizable via drag handle
- Keyboard shortcut to toggle (configurable, default TBD -- avoiding Cmd+Shift+D Safari conflict)
- Panel state (open/closed, active tab, height) persisted in sessionStorage
- Shadow DOM for complete style isolation from the app

### Three Tabs

#### Tab 1: SSE Events + Morph Correlation

The primary debugging view. Shows every SSE event in real-time with:

- Parsed structure: event type, data payload, server-provided metadata (handler, route, sequence, timestamp)
- Color-coded by event type (merge-signals, patch-elements, execute-script, etc.)
- Filterable by type, searchable by content
- Auto-scroll when at bottom, freeze when scrolled up, "Jump to latest" button
- **Expandable morph detail**: for `datastar-patch-elements` events, inline display of resulting DOM mutations (elements added/removed, attributes changed, before/after values)
- **Flash indicators**: warning badges on events whose morph caused rapid attribute toggles

#### Tab 2: Signals

- Live view of all Datastar signal values via `effect()` + `filtered()`
- JSON tree or flat table view, togglable
- Search/filter by signal name
- Change highlighting (brief yellow flash on mutation, throttled for frequently-updating signals)
- Grouped by namespace (StarElement component signals vs page-level)
- **Persisted signals sub-view**: toggle to show localStorage/sessionStorage values matching Datastar persist patterns, with clear actions

#### Tab 3: Timeline / "What Just Happened?"

- Unified chronological view: SSE events + signal changes + DOM mutations on one timeline
- "Flight recorder" mode: keyboard shortcut captures the last N seconds as a snapshot
- Cross-links to other tabs for drill-down (click an SSE event to see it in Tab 1, click a signal change to see it in Tab 2)
- The tab for diagnosing flashes: hit the shortcut after seeing a flash, get the complete causal chain

### Performance & Memory

- MutationObserver only active when panel is open; disconnected when collapsed
- In-memory ring buffer with two-tier strategy: first 200 entries preserved (page load context), rest ring-buffered
- Default cap: 2000-5000 entries per tab
- Lazy evaluation: store summaries, compute full display only when user expands an entry
- Virtual scrolling for log tabs
- Morph log filters: ignore mutations within debugger host, default to SSE-correlated mutations only

## Key Decisions

1. **Embedded panel over browser extension**: Zero-friction `debug=True` activation, full access to page JS context, no cross-browser maintenance burden
2. **Shadow DOM for the panel**: Style isolation from the app, prevents Datastar from processing debugger's data-* attributes
3. **Server-instrumented (Approach B)**: Full-stack observability -- knowing which Python handler sent which event is critical for tracing issues
4. **Three focused tabs over five generic ones**: Morph tracking is the differentiator; Console tab cut (DevTools still available); Persisted Signals folded into Signals tab
5. **Built as a StarElement**: Uses the @element() decorator pattern from StarElements, consistent with the ecosystem
6. **Datastar public API for signals**: `effect()`, `filtered()`, `datastar-signal-patch` -- no polling, no internals hacking
7. **`datastar-fetch` CustomEvent for SSE capture**: No fetch wrapping or EventSource patching needed

## Open Questions

- Exact keyboard shortcut for panel toggle (need to avoid browser conflicts)
- Keyboard shortcut for "flight recorder" capture
- Whether to support an export/share feature for SSE event logs (JSON export)
- Whether the debug panel needs `data-ignore` or `data-ignore-morph` attribute naming (verify against current Datastar)
- Timeline tab visualization approach (horizontal timeline vs vertical log)
- Whether to add element-to-event reverse lookup (right-click element to trace which SSE event last modified it)

## Next Steps

### Phase 1: Foundation + SSE Events with Morph Tracking
- `debug=True` flag on `serve()`, auto-injection
- StarElement with Shadow DOM, bottom drawer UI
- SSE event capture via `datastar-fetch` + server-side metadata enrichment
- MutationObserver morph correlation via microtask boundary
- Validate on StarMo's flash problem

### Phase 2: Signals Tab
- Signal state via `effect()` + `filtered()`
- Change history via `datastar-signal-patch`
- Persisted signals as sub-view

### Phase 3: Timeline + Flash Detection
- Unified timeline correlating SSE events, signal changes, and DOM mutations
- Flash detection heuristics layered on Phase 1 morph tracking
- "What just happened?" flight recorder

### Phase 4: Evaluate based on real usage before adding more
