# Debugger Timeline Tab Design

**Created:** 2026-02-17
**Status:** Approved
**Predecessor:** Phase 3 (Signals Tab, completed)

## Problem Statement

The StarHTML debugger has SSE Events (chronological event list) and Signals (reactive state snapshot) tabs, but neither answers: **"What caused what, and when?"** Debugging timing issues, race conditions, malformed SSE, and unexpected cascades requires mentally correlating across multiple tools (browser console, Network tab, SSE tab, Signals tab) with no shared timeline or causality linking.

## Solution Overview

A Timeline tab that presents **causality-chain groups** — each user action or SSE response traced through its downstream signal changes, effect evaluations, and DOM mutations as a nested tree. Three-tier data architecture: full-fidelity ring buffer capture, progressive-disclosure UI, and LLM-friendly Markdown export with automatic diagnostics.

## Architecture

### Core Model: Causality Trees (not SSE-centric)

Every chain starts with a **root trigger** — any of:

| Trigger | Example |
|---------|---------|
| User interaction | `data-on-click`, `data-on-input` |
| SSE response arriving | `datastar-patch-signals`, `datastar-patch-elements` |
| Page load / scan | `data-init`, Datastar's initial `nn()` scan |
| Timer/interval | `setInterval` callback modifying signals |
| Component lifecycle | `connectedCallback`, `disconnectedCallback` |
| Persist restore | Plugin reading from localStorage on init |
| Arbitrary JS | `datastar-execute-script`, inline scripts |

Effects cascade into: signal mutations, reactive binding evaluations, DOM mutations, new SSE requests, persist writes, script execution.

### TimelineEvent Schema

```typescript
interface TimelineEvent {
  id: number;                    // monotonic, never reused
  type: TimelineEventType;       // discriminated union tag
  ts: number;                    // performance.now() — sub-ms, monotonic
  wallTime: number;              // Date.now() — for display
  traceId: number;               // groups causally-related events
  parentId: number | null;       // direct cause (null = root)
  depth: number;                 // nesting level (0 = root)
  data: UserActionData | SseEventData | SignalChangeData
      | EffectEvalData | DomMutationData | MalformedSseData;
}

type TimelineEventType =
  | "user-action"       // click, input, submit, keydown
  | "sse-lifecycle"     // started, finished, error, retrying
  | "signal-change"     // signal value changed
  | "effect-eval"       // Datastar effect() callback invoked
  | "dom-mutation"      // MutationObserver record
  | "sse-malformed"     // raw SSE validation failure
  ;
```

Per-type data payloads:

```typescript
interface UserActionData {
  eventType: string;             // "click", "input", etc.
  targetSelector: string;        // "#increment-btn"
  targetText: string;            // first 40 chars of textContent
  datastarAction: string | null; // parsed from data-on-click
}

interface SseEventData {
  sseType: string;               // "started" | "finished" | event type
  handler: string;               // from x-debug-handler
  route: string;                 // from x-debug-route
  seq: number;                   // server sequence number
  payload: Record<string, unknown>;
  elSelector: string;
}

interface SignalChangeData {
  path: string;
  oldValue: unknown;             // capped at 1KB serialized
  newValue: unknown;
  source: "sse" | "effect" | "user" | "init" | "persist";
}

interface EffectEvalData {
  effectId: number;
  label: string;                 // e.g. "text-binding"
  signalsRead: string[];
  duration: number;              // performance.now() delta
  triggeredBy: string | null;    // signal path
}

interface DomMutationData {
  mutationType: "childList" | "attributes" | "characterData";
  targetSelector: string;
  attributeName: string | null;
  oldValue: string | null;
  newValue: string | null;
  addedNodes: string[];
  removedNodes: string[];
}

interface MalformedSseData {
  level: "warning" | "error";
  code: string;                  // e.g. "MERGED_EVENTS"
  message: string;
  rawText: string;               // truncated to 200 chars
  url: string;
  byteOffset: number;
}
```

### Causal Linking: traceId + parentId

Each cascade starts with one root cause. A `traceId` groups everything caused by it. A `parentId` links each event to its direct cause.

```
traceId=7:
  [user-action]  click #increment-btn          parentId=null  depth=0
    [sse-lifecycle]  started /increment         parentId=0     depth=1
    [signal-change]  count: 3 → 4              parentId=0     depth=1
      [effect-eval]  effect#0 (text) 0.1ms     parentId=2     depth=2
        [dom-mutation]  #counter text "3"→"4"   parentId=3     depth=3
    [sse-lifecycle]  finished (45ms)            parentId=0     depth=1
```

Trace opened on user-action or sse-lifecycle:started. Closed when microtask queue drains (detected via `Promise.resolve().then()`). Async SSE responses correlated via element reference from `openGroups` WeakMap.

### Ring Buffer

```
TIMELINE_MAX_EVENTS = 5000      // ~2MB at ~400 bytes/event
TIMELINE_PRESERVE_FIRST = 500   // keep session-start context
```

FIFO eviction preserving first 500 events. Both `performance.now()` (duration math) and `Date.now()` (display) stored per event.

## Data Flow

### Three Tiers

**Tier 1 — Capture (ring buffer).** Full-fidelity event stream. Sources:
- `datastar-fetch` custom events (existing, from debugger-capture.ts)
- `datastar-signal-patch` custom events (existing, from debugger-signals.ts)
- `MutationObserver` on document.body (existing)
- Delegated DOM event listeners for user actions (new)
- Malformed SSE validator via fetch monkey-patch (new)
- Effect evaluation via Datastar dev-only patch (phase 2)

**Tier 2 — UI (progressive disclosure).** Three levels:
- **Collapsed row**: `14:32:07  click #increment-btn → 1 signal, 3 effects, 2 DOM (45ms)`
- **Expanded tree**: Nested trigger → SSE → signals → effects → DOM
- **Full trace**: Every event with timestamps, via "Show all events" link

**Tier 3 — Export (LLM-friendly Markdown).** Structured text with preamble (app context), chronological event log, signal diff, and auto-generated diagnostic notes. Selection modes: copy interaction group (primary), copy last N seconds, copy time range.

### Warning Detection (automatic)

| Pattern | Detection |
|---------|-----------|
| Signal ping-pong | Same signal changed 3+ times in one trace |
| Excessive effects | >15 effect evaluations per trace |
| Hanging request | SSE started with no finished after 5s |
| Race condition | Two elements events to same selector in one trace |
| No morphs | Elements event produced zero DOM mutations |
| Attribute flash | Same attribute changed 2+ times in morph window |
| Malformed SSE | Validation errors from fetch interceptor |

Warnings show as colored badges on trace rows. Not shown individually in the list unless expanded.

## Malformed SSE Detection

### Approach: Monkey-patch `fetch()` + `ReadableStream.tee()`

Intercept Datastar SSE requests, tee the response stream. One copy goes to Datastar normally, the other runs through validation. Zero Datastar patches needed, async/non-blocking, debug-only.

Detection targets SSE requests via `Datastar-Request` header or `Accept: text/event-stream`.

### Validation Rules

| # | Mistake | Code | Level |
|---|---------|------|-------|
| 1 | Missing blank line between events | `MERGED_EVENTS` | error |
| 2 | Missing `event:` line | `MISSING_EVENT_TYPE` | error |
| 3 | Invalid signals JSON | `INVALID_SIGNALS_JSON` | error |
| 4 | Empty fragment content | `EMPTY_FRAGMENT` | warning |
| 5 | Binary/control chars in data | `BINARY_DATA` | error |
| 6 | Wrong Content-Type header | `WRONG_CONTENT_TYPE` | error |
| 7 | Missing required data keys | `MISSING_SIGNALS_DATA` / `MISSING_ELEMENTS_DATA` | error |
| 8 | Stream error (Python exception) | `STREAM_ERROR` | error |
| 9 | Missing trailing blank line | `MISSING_TRAILING_BLANK_LINE` | warning |
| 10 | Non-datastar event type | `NON_DATASTAR_EVENT` | warning |

Per-event-type validation: signals events must have valid JSON in `signals` key, elements events must have `elements` key with content, known merge modes validated.

### Module: `debugger-sse-validator.ts`

~250 lines. Exports `install(callback)`. Feeds errors into capture store as synthetic `sse-malformed` events. Bundled into `debugger-capture.js` (not a separate entry point). Safety valve: stops validating after 1MB per response.

## Server-Side Debug Context

### Current State: Plumbing exists but isn't wired

`realtime.py` has `debug_ctx` parameter on `format_sse_event()`, `format_signal_event()`, `format_element_event()`. Appends `x-debug-seq`, `x-debug-ts`, `x-debug-handler`, `x-debug-route`. Client capture code already reads these. **But `debug_ctx` is never populated.**

### Fix: ~20 lines via `contextvars`

```python
_request_ctx = contextvars.ContextVar('starhtml_debug')

# In _endp() handler wrapper:
ctx = {'seq': next_seq(), 'handler': f.__name__, 'route': path}
token = _request_ctx.set(ctx)
try:
    resp = await handler(req)
finally:
    _request_ctx.reset(token)

# SSE format functions auto-read:
if debug_ctx is None:
    debug_ctx = _request_ctx.get(None)
```

Every SSE event then carries handler name, route, sequence number, and server timestamp. No developer action required — automatic when `debug=True`.

## Datastar Reactivity Instrumentation (Phase 2)

### What Datastar Already Tracks

Datastar uses a bidirectional reactive graph internally:
- Each signal has a `subs_` linked list of subscriber effects
- Each effect has a `deps_` linked list of signal dependencies
- `propagate()` walks the graph on signal change, `notify()`/`flush()` executes effects
- Batching via `beginBatch`/`endBatch` defers execution

### Dev-Only Vendor Patch (deferred)

A ~30-line patch to expose effect evaluation events:

```js
__debugNotify(signalPath, subscriberCount, effectIds)
```

This enables the full chain: signal changed → N effects queued → each effect mutated specific DOM. **Not required for v1** — the Timeline works without it using temporal correlation (signal change at t=100, DOM mutation at t=101 on element with `data-text="$count"` → inferred link). The data schema reserves `effect-eval` type for when the patch lands.

## Export Format

### Structure: Markdown with Diagnostic Notes

```markdown
## StarHTML Debug Trace

Captured: 2026-02-17 14:23:07 - 14:23:08 (1.5s)
Framework: StarHTML + Datastar (SSE reactivity)

### Page Context
Components: <status-panel>, <nav-bar>
Signals at start: status="unsaved", form.dirty=true

### Events
14:23:07.412  [start]   save_form    POST /api/save
14:23:07.823  [elements] poll_status  morph #status-panel (+0 -0 ~2)
14:23:07.891  [signals]  save_form    {"status":"saved"}
14:23:07.893  [elements] save_form    morph #status-panel (+0 -0 ~2)

### Signal Changes
  status: "unsaved" → "saved" (via save_form)

### Diagnostic Notes
- RACE: Two SSE responses targeted #status-panel within 70ms
- FLASH: #status-panel class changed twice in 70ms
```

### Selection Modes

1. **Copy Interaction Group** (primary) — click group stripe → "Export Trace"
2. **Copy Last N Seconds** — toolbar dropdown (5s / 15s / 30s / 60s)
3. **Copy Time Range** — shift-click two events

### Size Budget

| Scenario | Size |
|----------|------|
| Single trace (simple) | ~0.5 KB |
| Single trace (pathological) | ~4 KB |
| Copy last 15s (typical) | ~8-15 KB |
| Hard cap | 20 KB (progressive truncation) |

Truncation: collapse repeated patterns → truncate HTML payloads → keep first/last N events.

## Module Architecture

```
debugger-timeline.ts    → new module: ring buffer, trace assembly, export
debugger-sse-validator.ts → new module: malformed SSE detection
debugger-capture.ts     → modified: wire validator, tag events with traceId
debugger-signals.ts     → read-only: signal snapshots for export context
debugger.py             → modified: Timeline tab UI, toolbar, setup script
realtime.py             → modified: wire debug_ctx via contextvars
server.py               → modified: populate debug_ctx in _endp()
```

All TypeScript compiled by Vite to `src/starhtml/static/js/plugins/`.

## Key Decisions

1. **Causality chains over SSE groups** — triggers can be clicks, timers, persist, not just SSE
2. **Vertical linked stream over waterfall lanes** — constrained panel space, consistent with existing tabs, 3x less code
3. **Dev-only instrumentation** — all capture overhead is debug-mode only, zero production cost
4. **Malformed SSE via fetch tee** — no Datastar patches, catches all 10 common mistakes
5. **Markdown export** — LLM-friendly AND human-readable, renders in GitHub issues
6. **Effect tracking deferred** — v1 works via temporal correlation, vendor patch adds precision later

## Open Questions

- Should the trace export include a "paste this into Claude for diagnosis" prompt template?
- Should malformed SSE warnings appear in the Timeline tab, SSE Events tab, or both?
- Exact heuristics for "stale trace" timeout (5s proposed, may need tuning)

## Next Steps

→ Create implementation plan with write-plan-with-beads
