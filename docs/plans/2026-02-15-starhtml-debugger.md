# StarHTML Debugger - Phase 1 Implementation Plan

> **Epic:** `starhtml-upstream-b0x`
> **Design:** `docs/designs/2026-02-15-starhtml-debugger.md`
> **For Claude:** Use `skills/collaboration/execute-plan-with-beads` to implement.

**Goal:** Build Phase 1 of the StarHTML debugger: `debug=True` flag, server-side SSE enrichment, and a bottom-drawer debug panel with SSE Events + Morph Correlation tab.

**Architecture:** Python-side `debug=True` flag on `serve()` auto-injects a debugger web component (Shadow DOM bottom drawer). Server enriches SSE events with debug metadata. Client-side TypeScript runtime listens to `datastar-fetch` CustomEvents and a MutationObserver to correlate SSE events with DOM mutations.

**Tech Stack:** Python (StarHTML server/realtime modules), TypeScript (Vite-compiled plugin), Shadow DOM web component, Datastar CustomEvent API

**Key files:**
- `src/starhtml/server.py` - `serve()` function (line 172)
- `src/starhtml/core.py` - `StarHTML` class, `register()`, header injection
- `src/starhtml/realtime.py` - SSE formatters (`format_sse_event` line 204, `format_signal_event` line 243, `format_element_event` line 259, `process_sse_item` line 357)
- `src/starhtml/starapp.py` - `def_hdrs()` (line 122), `star_app()` factory
- `typescript/plugins/` - Existing plugin TS sources
- `vite.config.ts` - Build entry points (line 22)
- `src/starhtml/static/js/plugins/` - Compiled plugin output

**Datastar interception points:**
- `datastar-fetch` CustomEvent on `document`: `{type, el, argsRaw}` — fires for every SSE event type including `datastar-patch-signals`, `datastar-patch-elements`, `datastar-execute-script`, plus lifecycle events (`started`, `finished`, `error`)
- `datastar-signal-patch` CustomEvent on `document`: flat dotted-key object of changed signals
- `data-ignore` attribute prevents Datastar from processing element and descendants

---

## Tasks Overview

| ID | Task | Review ID | Blocked By |
|----|------|-----------|------------|
| b0x.1 | debug flag infrastructure | 67r | - |
| b0x.2 | SSE debug metadata enrichment | 7j0 | b0x.1 |
| b0x.3 | Debugger TS entry + build config | xl2 | - |
| b0x.4 | Bottom drawer panel shell | xba | b0x.3 |
| b0x.5 | SSE event capture + ring buffer | 7gd | b0x.3 |
| b0x.6 | SSE Events tab rendering | 9qw | b0x.4, b0x.5 |
| b0x.7 | MutationObserver + morph correlation | lgp | b0x.5 |
| b0x.8 | Morph detail display in SSE tab | z24 | b0x.6, b0x.7 |
| b0x.9 | Python auto-injection when debug=True | o8n | b0x.1, b0x.4 |
| b0x.10 | Demo page + end-to-end verification | 63d | b0x.2, b0x.8, b0x.9 |

---

### Task 1: debug flag infrastructure

**Blocked by:** None

**Files:**
- Modify: `src/starhtml/server.py:172-203` (serve function)
- Modify: `src/starhtml/core.py` (StarHTML class)
- Test: `tests/unit/test_debug_flag.py`

**Step 1: Write failing test**

```python
# tests/unit/test_debug_flag.py
import os
from unittest.mock import patch
from starhtml.core import StarHTML

class TestDebugFlag:
    def test_debug_default_false(self):
        app = StarHTML()
        assert app.debug is False

    def test_debug_explicit_true(self):
        app = StarHTML(debug=True)
        assert app.debug is True

    def test_debug_env_override_off(self):
        """STARHTML_DEBUG=0 forces debug off even if code says True."""
        with patch.dict(os.environ, {"STARHTML_DEBUG": "0"}):
            app = StarHTML(debug=True)
            assert app.debug is False

    def test_debug_env_override_on(self):
        """STARHTML_DEBUG=1 forces debug on."""
        with patch.dict(os.environ, {"STARHTML_DEBUG": "1"}):
            app = StarHTML(debug=False)
            assert app.debug is True
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_debug_flag.py -v`
Expected: FAIL — `StarHTML.__init__` doesn't accept `debug` param

**Step 3: Implement**

In `src/starhtml/core.py`, add `debug` parameter to `StarHTML.__init__()`:

```python
import os, sys

# In __init__, add debug param and resolve with env var
self.debug = debug
env_debug = os.environ.get("STARHTML_DEBUG")
if env_debug is not None:
    self.debug = env_debug in ("1", "true", "yes")

if self.debug:
    print("WARNING: StarHTML debug mode is ON. Do not use in production.", file=sys.stderr)
```

In `src/starhtml/server.py`, pass `debug` through `serve()`:

```python
def serve(
    appname=None, app="app", host="0.0.0.0", port=None,
    reload=True, reload_includes=None, reload_excludes=None,
    debug=False,  # NEW
):
```

Note: `serve()` uses `uvicorn.run()` with a string reference (`f"{appname}:{app}"`), so the debug flag needs to be set on the app object before `serve()` is called, or `serve()` needs to modify the app. Check how the app is accessed — `serve()` introspects the calling frame to find the app variable. The simplest approach: add `debug` to `StarHTML.__init__()` and document `star_app(debug=True)`.

Also update `star_app()` in `src/starhtml/starapp.py` to pass through `debug`:

```python
def star_app(debug=False, ...):
    ...
    app = StarHTML(..., debug=debug)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_debug_flag.py -v`

**Step 5: Commit**

```bash
git add src/starhtml/core.py src/starhtml/server.py src/starhtml/starapp.py tests/unit/test_debug_flag.py
git commit -m "feat(debugger): add debug flag to StarHTML with env var override"
```

---

### Task 2: SSE debug metadata enrichment

**Blocked by:** Task 1

**Files:**
- Modify: `src/starhtml/realtime.py:204-226` (format_sse_event), `:243-256` (format_signal_event), `:259-299` (format_element_event), `:321-344` (execute_script), `:357-391` (process_sse_item)
- Test: `tests/unit/test_debug_sse_metadata.py`

**Step 1: Write failing test**

```python
# tests/unit/test_debug_sse_metadata.py
import re
from starhtml.realtime import format_signal_event, format_element_event

class TestSSEDebugMetadata:
    def test_signal_event_no_debug(self):
        """Without debug context, no x-debug lines."""
        event = format_signal_event({"count": 5})
        assert "x-debug" not in event

    def test_signal_event_with_debug(self):
        """With debug context, x-debug lines are appended."""
        debug_ctx = {"handler": "update_count", "route": "/sse/counter", "seq": 1}
        event = format_signal_event({"count": 5}, debug_ctx=debug_ctx)
        assert "data: x-debug-seq 1" in event
        assert "data: x-debug-handler update_count" in event
        assert "data: x-debug-route /sse/counter" in event
        assert re.search(r"data: x-debug-ts \d+", event)

    def test_element_event_with_debug(self):
        debug_ctx = {"handler": "render_cell", "route": "/sse/notebook", "seq": 2}
        event = format_element_event("<div>hello</div>", debug_ctx=debug_ctx)
        assert "data: x-debug-seq 2" in event
        assert "data: x-debug-handler render_cell" in event
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_debug_sse_metadata.py -v`
Expected: FAIL — `format_signal_event` doesn't accept `debug_ctx`

**Step 3: Implement**

Add `debug_ctx` parameter to `format_sse_event()` (the core formatter all others use):

```python
import time

def format_sse_event(event_type, data_lines, event_id=None, retry=RETRY_DURATION, debug_ctx=None):
    lines = [f"event: {event_type}\n"]
    if event_id: lines.append(f"id: {event_id}\n")
    if retry: lines.append(f"retry: {retry}\n")
    for dl in data_lines:
        lines.append(f"data: {dl}\n")
    if debug_ctx:
        lines.append(f"data: x-debug-seq {debug_ctx['seq']}\n")
        lines.append(f"data: x-debug-ts {int(time.time() * 1000)}\n")
        lines.append(f"data: x-debug-handler {debug_ctx['handler']}\n")
        lines.append(f"data: x-debug-route {debug_ctx['route']}\n")
    lines.append("\n")
    return "".join(lines)
```

Thread `debug_ctx` through `format_signal_event()`, `format_element_event()`, and `execute_script()` to their calls to `format_sse_event()`.

In `process_sse_item()` and `stream_sse_items()`, accept and forward debug context. The debug context should be constructed from the request's route handler info when `app.debug` is True.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_debug_sse_metadata.py -v`

**Step 5: Commit**

```bash
git add src/starhtml/realtime.py tests/unit/test_debug_sse_metadata.py
git commit -m "feat(debugger): add debug metadata to SSE events"
```

---

### Task 3: Debugger TS entry + build config

**Blocked by:** None

**Files:**
- Create: `typescript/plugins/debugger.ts`
- Modify: `vite.config.ts:22-40` (add entry)
- Test: build succeeds with `npx vite build`

**Step 1: Create minimal TS entry**

```typescript
// typescript/plugins/debugger.ts

/**
 * StarHTML Debugger - Phase 1
 * Captures SSE events, signal patches, and DOM mutations.
 * Renders a bottom-drawer debug panel in Shadow DOM.
 */

// Types
interface DebugSSEEvent {
  type: string;
  timestamp: number;
  el: HTMLElement | null;
  argsRaw: Record<string, unknown>;
  debugMeta?: {
    seq: number;
    ts: number;
    handler: string;
    route: string;
  };
  morphRecords?: MutationRecord[];
}

// Ring buffer for events
const MAX_EVENTS = 3000;
const PRESERVE_INITIAL = 200;
let events: DebugSSEEvent[] = [];

export function getEvents(): readonly DebugSSEEvent[] {
  return events;
}

export function clearEvents(): void {
  events = [];
}

// Will be populated in subsequent tasks
export function init(): void {
  console.log("[starhtml-debugger] initialized");
}
```

**Step 2: Add to vite.config.ts**

In the `entry` object (around line 22), add:

```typescript
'debugger': './typescript/plugins/debugger.ts',
```

**Step 3: Build and verify**

Run: `npx vite build`
Expected: `src/starhtml/static/js/plugins/debugger.js` is created

**Step 4: Commit**

```bash
git add typescript/plugins/debugger.ts vite.config.ts src/starhtml/static/js/plugins/debugger.js
git commit -m "feat(debugger): add debugger TS entry point and build config"
```

---

### Task 4: Bottom drawer panel shell (Shadow DOM)

**Blocked by:** Task 3

**Files:**
- Modify: `typescript/plugins/debugger.ts`

**Step 1: Implement the custom element**

```typescript
// Add to debugger.ts

const PANEL_STYLES = `
  :host {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 99999;
    font-family: ui-monospace, 'SF Mono', Monaco, 'Cascadia Mono', monospace;
    font-size: 12px;
  }
  .debugger-tab {
    position: absolute;
    bottom: 0;
    right: 20px;
    background: #1e1e2e;
    color: #cdd6f4;
    padding: 4px 16px;
    border-radius: 6px 6px 0 0;
    cursor: pointer;
    font-size: 11px;
    user-select: none;
    border: 1px solid #45475a;
    border-bottom: none;
  }
  .debugger-tab .badge {
    background: #f38ba8;
    color: #1e1e2e;
    border-radius: 8px;
    padding: 0 5px;
    margin-left: 6px;
    font-size: 10px;
  }
  .debugger-panel {
    background: #1e1e2e;
    color: #cdd6f4;
    border-top: 2px solid #89b4fa;
    display: none;
    flex-direction: column;
    overflow: hidden;
  }
  .debugger-panel.open {
    display: flex;
  }
  .resize-handle {
    height: 4px;
    cursor: ns-resize;
    background: transparent;
  }
  .resize-handle:hover { background: #89b4fa33; }
  .tab-bar {
    display: flex;
    gap: 0;
    border-bottom: 1px solid #45475a;
    padding: 0 8px;
  }
  .tab-btn {
    padding: 6px 16px;
    background: none;
    border: none;
    color: #6c7086;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    font-family: inherit;
    font-size: 11px;
  }
  .tab-btn.active {
    color: #89b4fa;
    border-bottom-color: #89b4fa;
  }
  .tab-btn:hover { color: #cdd6f4; }
  .tab-content {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
  }
  .toolbar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 8px;
    border-bottom: 1px solid #313244;
  }
  .toolbar input {
    background: #313244;
    border: 1px solid #45475a;
    color: #cdd6f4;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: inherit;
    font-size: 11px;
  }
  .toolbar button {
    background: #313244;
    border: 1px solid #45475a;
    color: #cdd6f4;
    padding: 2px 8px;
    border-radius: 4px;
    cursor: pointer;
    font-family: inherit;
    font-size: 11px;
  }
  .toolbar button:hover { background: #45475a; }
`;

class StarHTMLDebugger extends HTMLElement {
  private shadow: ShadowRoot;
  private panel: HTMLDivElement;
  private tab: HTMLDivElement;
  private isOpen: boolean;
  private panelHeight: number;
  private activeTab: string;
  private badge: HTMLSpanElement;
  private unseenCount: number = 0;

  constructor() {
    super();
    this.shadow = this.attachShadow({ mode: "open" });

    // Restore state from sessionStorage
    this.isOpen = sessionStorage.getItem("starhtml-debug-open") === "true";
    this.panelHeight = parseInt(sessionStorage.getItem("starhtml-debug-height") || "300");
    this.activeTab = sessionStorage.getItem("starhtml-debug-tab") || "sse";

    this.render();
  }

  private render(): void {
    this.shadow.innerHTML = `
      <style>${PANEL_STYLES}</style>
      <div class="debugger-tab">
        StarHTML Debug<span class="badge" style="display:none"></span>
      </div>
      <div class="debugger-panel" style="height:${this.panelHeight}px">
        <div class="resize-handle"></div>
        <div class="tab-bar">
          <button class="tab-btn ${this.activeTab === "sse" ? "active" : ""}" data-tab="sse">SSE Events</button>
          <button class="tab-btn ${this.activeTab === "signals" ? "active" : ""}" data-tab="signals">Signals</button>
          <button class="tab-btn ${this.activeTab === "timeline" ? "active" : ""}" data-tab="timeline">Timeline</button>
        </div>
        <div class="tab-content" id="tab-content">
          <!-- Tab content rendered here -->
        </div>
      </div>
    `;

    this.panel = this.shadow.querySelector(".debugger-panel")!;
    this.tab = this.shadow.querySelector(".debugger-tab")!;
    this.badge = this.shadow.querySelector(".badge")!;

    if (this.isOpen) this.panel.classList.add("open");

    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    // Toggle panel
    this.tab.addEventListener("click", () => this.toggle());

    // Tab switching
    this.shadow.querySelector(".tab-bar")!.addEventListener("click", (e) => {
      const btn = (e.target as HTMLElement).closest(".tab-btn") as HTMLElement;
      if (!btn) return;
      this.switchTab(btn.dataset.tab!);
    });

    // Resize handle
    const handle = this.shadow.querySelector(".resize-handle")!;
    let startY = 0, startH = 0;
    handle.addEventListener("mousedown", (e: Event) => {
      const me = e as MouseEvent;
      startY = me.clientY;
      startH = this.panelHeight;
      const onMove = (e: MouseEvent) => {
        this.panelHeight = Math.max(150, Math.min(window.innerHeight * 0.8, startH - (e.clientY - startY)));
        this.panel.style.height = `${this.panelHeight}px`;
      };
      const onUp = () => {
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
        sessionStorage.setItem("starhtml-debug-height", String(this.panelHeight));
      };
      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    });

    // Keyboard shortcut: Ctrl/Cmd + Shift + .
    document.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === ".") {
        e.preventDefault();
        this.toggle();
      }
    });
  }

  private toggle(): void {
    this.isOpen = !this.isOpen;
    this.panel.classList.toggle("open", this.isOpen);
    sessionStorage.setItem("starhtml-debug-open", String(this.isOpen));
    if (this.isOpen) {
      this.unseenCount = 0;
      this.badge.style.display = "none";
    }
  }

  private switchTab(tabId: string): void {
    this.activeTab = tabId;
    sessionStorage.setItem("starhtml-debug-tab", tabId);
    for (const btn of this.shadow.querySelectorAll(".tab-btn")) {
      btn.classList.toggle("active", (btn as HTMLElement).dataset.tab === tabId);
    }
    // Re-render tab content (implemented in Task 6)
  }

  // Called by event capture (Task 5) when new events arrive
  public notifyNewEvent(): void {
    if (!this.isOpen) {
      this.unseenCount++;
      this.badge.textContent = String(this.unseenCount);
      this.badge.style.display = "";
    }
  }
}

customElements.define("starhtml-debugger", StarHTMLDebugger);
```

**Step 2: Build and verify**

Run: `npx vite build`
Open a test HTML page with `<starhtml-debugger></starhtml-debugger>` to visually verify the drawer.

**Step 3: Commit**

```bash
git add typescript/plugins/debugger.ts src/starhtml/static/js/plugins/debugger.js
git commit -m "feat(debugger): bottom drawer panel with Shadow DOM, tabs, resize, keyboard shortcut"
```

---

### Task 5: SSE event capture + ring buffer

**Blocked by:** Task 3

**Files:**
- Modify: `typescript/plugins/debugger.ts`

**Step 1: Implement event capture**

```typescript
// Add to debugger.ts — event capture module

let morphWindow: { sseEvent: DebugSSEEvent; records: MutationRecord[] } | null = null;

function captureSSEEvents(): void {
  document.addEventListener("datastar-fetch", (e: Event) => {
    const detail = (e as CustomEvent).detail;
    const { type, el, argsRaw } = detail;

    // Extract debug metadata from argsRaw if present
    const debugMeta = argsRaw?.["x-debug-seq"] != null ? {
      seq: Number(argsRaw["x-debug-seq"]),
      ts: Number(argsRaw["x-debug-ts"]),
      handler: String(argsRaw["x-debug-handler"] ?? ""),
      route: String(argsRaw["x-debug-route"] ?? ""),
    } : undefined;

    const event: DebugSSEEvent = {
      type,
      timestamp: Date.now(),
      el,
      argsRaw: { ...argsRaw },
      debugMeta,
    };

    addEvent(event);

    // If this is a patch-elements event, open a morph window
    if (type === "datastar-patch-elements") {
      morphWindow = { sseEvent: event, records: [] };
      // Close the morph window on next microtask (morph is synchronous)
      queueMicrotask(() => {
        if (morphWindow) {
          event.morphRecords = morphWindow.records;
          morphWindow = null;
        }
      });
    }
  });
}

function addEvent(event: DebugSSEEvent): void {
  events.push(event);
  // Two-tier eviction: preserve first PRESERVE_INITIAL, ring-buffer the rest
  if (events.length > MAX_EVENTS) {
    const preserved = events.slice(0, PRESERVE_INITIAL);
    const recent = events.slice(-(MAX_EVENTS - PRESERVE_INITIAL));
    events = [...preserved, ...recent];
  }
  // Notify the panel component
  const panel = document.querySelector("starhtml-debugger") as StarHTMLDebugger | null;
  panel?.notifyNewEvent();
}

// Update init() to start capture
export function init(): void {
  captureSSEEvents();
}
```

**Step 2: Build and verify**

Run: `npx vite build`
Test: Load a StarHTML page with debug on, check browser console for `[starhtml-debugger] initialized`

**Step 3: Commit**

```bash
git add typescript/plugins/debugger.ts src/starhtml/static/js/plugins/debugger.js
git commit -m "feat(debugger): SSE event capture via datastar-fetch with ring buffer"
```

---

### Task 6: SSE Events tab rendering

**Blocked by:** Task 4, Task 5

**Files:**
- Modify: `typescript/plugins/debugger.ts`

**Step 1: Implement tab rendering**

Add methods to `StarHTMLDebugger` class for rendering the SSE event list:

- Color map: `datastar-patch-signals` → blue, `datastar-patch-elements` → green, `datastar-execute-script` → purple, `started`/`finished` → gray, `error` → red
- Each row shows: timestamp, type badge, handler name (from debug metadata), expandable payload
- Filter input in toolbar: filters by type or content
- Auto-scroll: track whether user is at bottom, only auto-scroll if so
- "Jump to latest" button appears when scrolled up
- "Clear" button to reset events
- Use `requestAnimationFrame` to batch UI updates (don't re-render on every event)

Key rendering method:
```typescript
private renderSSETab(): void {
  const content = this.shadow.getElementById("tab-content")!;
  // Render toolbar: filter input, clear button, event count
  // Render event list: virtual scroll or simple list with max visible
  // Each event row: click to expand payload
}
```

**Step 2: Build and manually test**

Run: `npx vite build`
Test: Open a StarHTML demo with debug, trigger SSE events, verify they appear in the panel.

**Step 3: Commit**

```bash
git add typescript/plugins/debugger.ts src/starhtml/static/js/plugins/debugger.js
git commit -m "feat(debugger): SSE Events tab with filtering, color coding, auto-scroll"
```

---

### Task 7: MutationObserver + morph correlation

**Blocked by:** Task 5

**Files:**
- Modify: `typescript/plugins/debugger.ts`

**Step 1: Implement MutationObserver**

```typescript
let observer: MutationObserver | null = null;
const debuggerTag = "starhtml-debugger";

function startObserving(): void {
  if (observer) return;
  observer = new MutationObserver((records) => {
    // Filter out mutations within the debugger itself
    const filtered = records.filter(r => {
      let node = r.target as HTMLElement;
      while (node) {
        if (node.tagName?.toLowerCase() === debuggerTag) return false;
        node = node.parentElement as HTMLElement;
      }
      return true;
    });

    // If morph window is open, collect records
    if (morphWindow && filtered.length > 0) {
      morphWindow.records.push(...filtered);
    }
  });

  observer.observe(document.body, {
    childList: true,
    attributes: true,
    attributeOldValue: true,
    subtree: true,
  });
}

function stopObserving(): void {
  observer?.disconnect();
  observer = null;
}
```

Wire `startObserving()` / `stopObserving()` to panel open/close state. When the panel is collapsed, disconnect the observer to avoid overhead.

**Step 2: Build and verify**

Run: `npx vite build`
Test: Open panel, trigger an SSE fragment merge, verify `morphRecords` array is populated on the event.

**Step 3: Commit**

```bash
git add typescript/plugins/debugger.ts src/starhtml/static/js/plugins/debugger.js
git commit -m "feat(debugger): MutationObserver with morph correlation via microtask boundary"
```

---

### Task 8: Morph detail display in SSE tab

**Blocked by:** Task 6, Task 7

**Files:**
- Modify: `typescript/plugins/debugger.ts`

**Step 1: Implement morph detail rendering**

When a `datastar-patch-elements` event row is expanded, show:

- Count summary: "3 added, 1 removed, 2 attributes changed"
- Expandable list of individual mutations:
  - `childList`: "Added `<div class='output'>` to `div#cell-3`" / "Removed `<span>` from `div#cell-3`"
  - `attributes`: "Changed `class` on `div.cell` from `'cell loading'` to `'cell ready'`" (using `attributeOldValue`)
- Flash detection: if the same element had the same attribute changed multiple times in the mutation batch, flag with a warning icon

For element display, generate a short CSS-like selector path:
```typescript
function selectorPath(el: Element): string {
  if (el.id) return `#${el.id}`;
  let path = el.tagName.toLowerCase();
  if (el.className && typeof el.className === "string") {
    path += "." + el.className.trim().split(/\s+/).slice(0, 2).join(".");
  }
  return path;
}
```

**Step 2: Build and manually test**

Run: `npx vite build`
Test: Trigger an SSE fragment merge, expand the event row, verify morph details display.

**Step 3: Commit**

```bash
git add typescript/plugins/debugger.ts src/starhtml/static/js/plugins/debugger.js
git commit -m "feat(debugger): morph detail display with mutation summary and flash detection"
```

---

### Task 9: Python auto-injection when debug=True

**Blocked by:** Task 1, Task 4

**Files:**
- Create: `src/starhtml/debugger.py`
- Modify: `src/starhtml/core.py` (auto-register when debug=True)
- Test: `tests/unit/test_debug_injection.py`

**Step 1: Write failing test**

```python
# tests/unit/test_debug_injection.py
from starhtml.core import StarHTML

class TestDebugInjection:
    def test_debug_injects_script(self):
        """When debug=True, the debugger script is in headers."""
        app = StarHTML(debug=True)
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert "debugger.js" in hdrs_html

    def test_no_debug_no_script(self):
        """When debug=False, no debugger script."""
        app = StarHTML(debug=False)
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert "debugger.js" not in hdrs_html
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_debug_injection.py -v`

**Step 3: Implement**

Create `src/starhtml/debugger.py`:

```python
"""StarHTML Debugger - auto-injected when debug=True."""

from pathlib import Path
from fastcore.xml import Script, NotStr

DEBUGGER_JS_PATH = Path(__file__).parent / "static" / "js" / "plugins" / "debugger.js"

def debugger_hdrs():
    """Return headers that inject the debugger panel."""
    return (
        Script(src="/static/js/plugins/debugger.js", type="module"),
    )

def debugger_ftrs():
    """Return footer elements: the debugger component + init script."""
    return (
        NotStr('<starhtml-debugger data-ignore></starhtml-debugger>'),
    )
```

In `src/starhtml/core.py`, in `StarHTML.__init__()`, after setting `self.debug`:

```python
if self.debug:
    from .debugger import debugger_hdrs, debugger_ftrs
    self.hdrs = (*self.hdrs, *debugger_hdrs())
    self.ftrs = (*self.ftrs, *debugger_ftrs())
```

Also serve the debugger JS file — add a route for `/static/js/plugins/debugger.js` similar to how `datastar.js` is served, or rely on the existing static file serving if it covers that path.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_debug_injection.py -v`

**Step 5: Commit**

```bash
git add src/starhtml/debugger.py src/starhtml/core.py tests/unit/test_debug_injection.py
git commit -m "feat(debugger): auto-inject debug panel when debug=True"
```

---

### Task 10: Demo page + end-to-end verification

**Blocked by:** Task 2, Task 8, Task 9

**Files:**
- Create: `web/demos/30_debugger_demo.py`

**Step 1: Create demo**

```python
"""StarHTML Debugger Demo - demonstrates the debug panel."""
from starhtml.starapp import star_app
from starhtml.datastar import *

app, rt = star_app(debug=True)

count = Signal("count", 0)

@rt("/")
def home():
    return Div(
        H1("Debugger Demo"),
        P("Open the debug panel with Ctrl/Cmd+Shift+. or click the tab at the bottom."),
        Div(
            Button("Increment", data_on_click=sse("/increment")),
            Button("Add Element", data_on_click=sse("/add-element")),
            Span(data_text=count, id="counter"),
        ),
        Div(id="dynamic-content"),
    )

@rt("/increment")
async def increment(request):
    from starhtml.realtime import sse, signals
    @sse(request)
    async def stream():
        yield signals(count=count + 1)
    return stream

@rt("/add-element")
async def add_element(request):
    from starhtml.realtime import sse, elements
    @sse(request)
    async def stream():
        yield elements(
            P("New paragraph added!", cls="text-green-500"),
            selector="#dynamic-content",
            mode="append",
        )
    return stream

from starhtml.server import serve
serve(port=5030)
```

**Step 2: Run and manually test**

Run: `python web/demos/30_debugger_demo.py`

Verify:
- [ ] Debug panel tab visible at bottom of page
- [ ] Ctrl/Cmd+Shift+. toggles panel
- [ ] Panel is resizable
- [ ] Panel state persists across page reload
- [ ] SSE Events tab shows events when buttons clicked
- [ ] Events are color-coded by type
- [ ] Server debug metadata (handler, route, seq) appears in events
- [ ] Expanding a patch-elements event shows morph details
- [ ] Filter input works
- [ ] Clear button works
- [ ] Badge shows unseen count when panel is collapsed

**Step 3: Commit**

```bash
git add web/demos/30_debugger_demo.py
git commit -m "feat(debugger): add demo page for debugger testing"
```
