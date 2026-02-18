// debugger-timeline.ts — Causality-chain timeline for the StarHTML debugger.
// Captures user actions, SSE events, signal changes, and DOM mutations as
// a ring buffer of TimelineEvents grouped into causal traces.

import { getPath } from "datastar";
import { install as installSSEValidator, uninstall as uninstallSSEValidator, type SSEValidationError } from "./debugger-sse-validator";
import { injectEvent as injectCaptureEvent } from "./debugger-capture";

// ─── Event Types ──────────────────────────────────────────────────

export type TimelineEventType =
  | "user-action"
  | "sse-lifecycle"
  | "signal-change"
  | "effect-eval"
  | "dom-mutation"
  | "sse-malformed";

export interface UserActionData {
  eventType: string;
  targetSelector: string;
  targetText: string;
  datastarAction: string | null;
}

export interface SseEventData {
  sseType: string;
  handler: string;
  route: string;
  seq: number;
  payload: Record<string, unknown>;
  elSelector: string;
  groupId?: number;
}

export interface SignalChangeData {
  path: string;
  oldValue: unknown;
  newValue: unknown;
  source: "sse" | "effect" | "user" | "init" | "persist";
}

export interface EffectEvalData {
  effectId: number;
  label: string;
  signalsRead: string[];
  duration: number;
  triggeredBy: string | null;
}

export interface DomMutationData {
  mutationType: "childList" | "attributes" | "characterData";
  targetSelector: string;
  attributeName: string | null;
  oldValue: string | null;
  newValue: string | null;
  addedNodes: string[];
  removedNodes: string[];
}

export interface MalformedSseData {
  level: "warning" | "error";
  code: string;
  message: string;
  rawText: string;
  url: string;
  byteOffset: number;
}

export type TimelineEventData =
  | UserActionData
  | SseEventData
  | SignalChangeData
  | EffectEvalData
  | DomMutationData
  | MalformedSseData;

export interface TimelineEvent {
  id: number;
  type: TimelineEventType;
  ts: number;        // performance.now()
  wallTime: number;  // Date.now()
  traceId: number;
  parentId: number | null;
  depth: number;
  data: TimelineEventData;
}

// ─── Trace Summary ────────────────────────────────────────────────

export interface Warning {
  code: string;
  message: string;
}

export interface TraceSummary {
  traceId: number;
  rootEvent: TimelineEvent;
  lastEventTs: number;
  totalDuration: number;
  eventCount: number;
  signalChanges: number;
  effectEvals: number;
  domMutations: number;
  sseEvents: number;
  malformedEvents: number;
  warnings: Warning[];
  status: "active" | "complete" | "stale";
}

// ─── Constants ────────────────────────────────────────────────────

const MAX_EVENTS = 5000;
const PRESERVE_FIRST = 500;
const STALE_TRACE_MS = 5000;
const MAX_VALUE_SIZE = 1024;

// ─── State ────────────────────────────────────────────────────────

const buffer: TimelineEvent[] = [];
let nextEventId = 0;
let nextTraceId = 0;

// Active trace state
let activeTraceId: number | null = null;
let activeParentId: number | null = null;
let activeDepth = 0;
let activeTraceRootType: TimelineEventType | null = null;
let traceCloseScheduled = false;

// Async SSE correlation: element → { traceId, startedEventId }
// When an SSE request starts during a trace, we save the mapping. When async
// SSE responses arrive later, we resume the original trace.
let sseElTraces = new WeakMap<HTMLElement, { traceId: number; startedEventId: number }>();

// Subscriber notifications
const subscribers = new Set<() => void>();
let pendingNotify = false;
let initialized = false;

// ─── SSE Lifecycle Capture ────────────────────────────────────────

let sseListener: ((e: Event) => void) | null = null;

function captureSSELifecycle(): void {
  sseListener = (e: Event) => {
    const { type, el, argsRaw } = (e as CustomEvent).detail;

    const debugMeta = argsRaw?.["x-debug-seq"] != null ? {
      seq: Number(argsRaw["x-debug-seq"]),
      handler: String(argsRaw["x-debug-handler"] ?? ""),
      route: String(argsRaw["x-debug-route"] ?? ""),
    } : undefined;

    // Build payload without x-debug- keys
    const payload: Record<string, unknown> = {};
    if (argsRaw) {
      for (const [k, v] of Object.entries(argsRaw)) {
        if (!k.startsWith("x-debug-")) payload[k] = v;
      }
    }

    const sseData: SseEventData = {
      sseType: type,
      handler: debugMeta?.handler ?? "",
      route: debugMeta?.route ?? "",
      seq: debugMeta?.seq ?? 0,
      payload,
      elSelector: el ? selectorFor(el) : "",
    };

    if (type === "started") {
      // SSE request started — extend current trace or start new one
      const isNewTrace = activeTraceId === null;
      const event = emit("sse-lifecycle", sseData, { beginTrace: isNewTrace });

      // Save element → trace mapping for async SSE correlation
      if (el) {
        sseElTraces.set(el, { traceId: event.traceId, startedEventId: event.id });
      }
    } else {
      // Async SSE event — look up trace from element
      if (el && activeTraceId === null) {
        const saved = sseElTraces.get(el);
        if (saved) {
          resumeTrace(saved.traceId, saved.startedEventId, "sse-lifecycle");
        }
      }

      emit("sse-lifecycle", sseData);

      // Clean up on terminal events
      if (type === "finished" || type === "error" || type === "retries-failed") {
        if (el) sseElTraces.delete(el);
      }
    }
  };
  document.addEventListener("datastar-fetch", sseListener);
}

// ─── User Action Capture ─────────────────────────────────────────

const DEBUGGER_TAG = "STARHTML-DEBUGGER";
const USER_ACTION_EVENTS = ["click", "input", "submit", "keydown"] as const;
let userActionListeners: Array<{ type: string; fn: (e: Event) => void }> = [];

function isInsideDebugger(el: Element): boolean {
  let node: Element | null = el;
  while (node) {
    if (node.tagName === DEBUGGER_TAG) return true;
    node = node.parentElement;
  }
  // Also check shadow DOM host
  const root = el.getRootNode();
  if (root instanceof ShadowRoot && root.host?.tagName === DEBUGGER_TAG) return true;
  return false;
}

function captureUserActions(): void {
  for (const eventType of USER_ACTION_EVENTS) {
    const fn = (e: Event) => {
      const target = e.target;
      if (!(target instanceof Element)) return;
      if (isInsideDebugger(target)) return;

      // For non-click events, only capture if target has a data-on-* attribute
      if (eventType !== "click") {
        const attrName = `data-on-${eventType}`;
        if (!target.hasAttribute(attrName) && !target.closest(`[${attrName}]`)) return;
      }

      // Extract datastar action from data-on-{eventType} attribute
      let datastarAction: string | null = null;
      const actionEl = target.closest(`[data-on-${eventType}]`) ?? target;
      const actionAttr = actionEl.getAttribute(`data-on-${eventType}`);
      if (actionAttr) datastarAction = actionAttr.slice(0, 100);

      const data: UserActionData = {
        eventType,
        targetSelector: selectorFor(target),
        targetText: (target.textContent ?? "").trim().slice(0, 40),
        datastarAction,
      };

      emit("user-action", data, { beginTrace: true });
    };
    document.addEventListener(eventType, fn, true); // capture phase
    userActionListeners.push({ type: eventType, fn });
  }
}

// ─── Signal Change Capture ───────────────────────────────────────

let signalPatchListener: ((e: Event) => void) | null = null;

/** Flatten nested object into dot-separated paths. */
function flattenPaths(obj: unknown, prefix: string, out: string[]): void {
  if (obj && typeof obj === "object" && !Array.isArray(obj)) {
    for (const [k, v] of Object.entries(obj as Record<string, unknown>)) {
      const path = prefix ? `${prefix}.${k}` : k;
      if (v && typeof v === "object" && !Array.isArray(v)) {
        flattenPaths(v, path, out);
      } else {
        out.push(path);
      }
    }
  }
}

function captureSignalChanges(): void {
  // Cache previous signal values for old→new diff
  const prevValues = new Map<string, unknown>();

  signalPatchListener = (e: Event) => {
    const detail = (e as CustomEvent).detail;
    if (!detail || typeof detail !== "object") return;

    const paths: string[] = [];
    flattenPaths(detail, "", paths);

    // Infer source from cached root type (O(1) instead of buffer scan)
    let source: SignalChangeData["source"] = "init";
    if (activeTraceRootType === "sse-lifecycle") source = "sse";
    else if (activeTraceRootType === "user-action") source = "user";

    for (const path of paths) {
      // Skip debugger's own signals
      if (path.startsWith("starhtml_debugger")) continue;

      let newValue: unknown;
      try {
        newValue = getPath(path);
      } catch { continue; }

      const oldValue = prevValues.get(path);
      // Deep equality: reference check for primitives, JSON for objects/arrays
      if (oldValue === newValue) continue;
      if (typeof oldValue === "object" && typeof newValue === "object") {
        try {
          if (JSON.stringify(oldValue) === JSON.stringify(newValue)) continue;
        } catch { /* incomparable — treat as changed */ }
      }

      prevValues.set(path, newValue);

      const data: SignalChangeData = {
        path,
        oldValue: clampValue(oldValue),
        newValue: clampValue(newValue),
        source,
      };
      emit("signal-change", data);
    }
  };
  document.addEventListener("datastar-signal-patch", signalPatchListener);
}

// ─── Malformed SSE Capture ───────────────────────────────────────

function captureMalformedSSE(): void {
  installSSEValidator((error: SSEValidationError) => {
    // Emit into timeline ring buffer
    const data: MalformedSseData = {
      level: error.level,
      code: error.code,
      message: error.message,
      rawText: error.rawText,
      url: error.url,
      byteOffset: error.byteOffset,
    };
    emit("sse-malformed", data);

    // Also inject into capture store so it shows in SSE Events tab
    injectCaptureEvent({
      type: "sse-malformed",
      timestamp: Date.now(),
      el: null,
      argsRaw: {
        level: error.level,
        code: error.code,
        message: error.message,
        rawText: error.rawText,
        url: error.url,
        byteOffset: error.byteOffset,
      },
    });
  });
}

// ─── Init / Cleanup ──────────────────────────────────────────────

export function init(): void {
  if (initialized) return;
  initialized = true;
  captureSSELifecycle();
  captureUserActions();
  captureSignalChanges();
  captureMalformedSSE();
}

export function cleanup(): void {
  if (sseListener) {
    document.removeEventListener("datastar-fetch", sseListener);
    sseListener = null;
  }
  for (const { type, fn } of userActionListeners) {
    document.removeEventListener(type, fn, true);
  }
  userActionListeners = [];
  if (signalPatchListener) {
    document.removeEventListener("datastar-signal-patch", signalPatchListener);
    signalPatchListener = null;
  }
  uninstallSSEValidator();
  initialized = false;
  buffer.length = 0;
  nextEventId = 0;
  nextTraceId = 0;
  activeTraceId = null;
  activeParentId = null;
  activeDepth = 0;
  activeTraceRootType = null;
  sseElTraces = new WeakMap();
  subscribers.clear();
}

// ─── Subscribe ────────────────────────────────────────────────────

export function subscribe(fn: () => void): () => void {
  subscribers.add(fn);
  return () => subscribers.delete(fn);
}

function notifySubscribers(): void {
  if (pendingNotify) return;
  pendingNotify = true;
  queueMicrotask(() => {
    pendingNotify = false;
    for (const fn of subscribers) fn();
  });
}

// ─── Ring Buffer ──────────────────────────────────────────────────

function addToBuffer(event: TimelineEvent): void {
  buffer.push(event);
  if (buffer.length > MAX_EVENTS) {
    // Evict from middle (after preserved first N)
    const excess = buffer.length - MAX_EVENTS;
    buffer.splice(PRESERVE_FIRST, excess);
  }
  notifySubscribers();
}

// ─── Trace Management ─────────────────────────────────────────────

/** Open a new causal trace rooted at this event. */
export function beginTrace(rootEvent: TimelineEvent): void {
  const tid = nextTraceId++;
  rootEvent.traceId = tid;
  rootEvent.parentId = null;
  rootEvent.depth = 0;
  activeTraceId = tid;
  activeParentId = rootEvent.id;
  activeDepth = 1;
  activeTraceRootType = rootEvent.type;
  scheduleTraceClose();
}

/** Schedule trace close at end of microtask queue. */
function scheduleTraceClose(): void {
  if (traceCloseScheduled) return;
  traceCloseScheduled = true;
  Promise.resolve().then(() => {
    traceCloseScheduled = false;
    // Don't close if an SSE request is still open — count starts vs finishes
    // to handle concurrent SSE requests within the same trace
    if (activeTraceId !== null) {
      let startedCount = 0;
      let finishedCount = 0;
      for (const e of buffer) {
        if (e.traceId === activeTraceId && e.type === "sse-lifecycle") {
          const sseType = (e.data as SseEventData).sseType;
          if (sseType === "started") startedCount++;
          else if (sseType === "finished" || sseType === "error" || sseType === "retries-failed") finishedCount++;
        }
      }
      if (startedCount <= finishedCount) {
        closeTrace();
      }
    }
  });
}

function closeTrace(): void {
  activeTraceId = null;
  activeParentId = null;
  activeDepth = 0;
  activeTraceRootType = null;
}

/** Resume an existing trace for async SSE correlation.
 *  When an SSE response arrives asynchronously, we reactivate the trace so
 *  downstream signal changes and DOM mutations are grouped correctly. The
 *  trace closes again when the microtask queue drains. */
function resumeTrace(traceId: number, parentId: number, rootType?: TimelineEventType): void {
  if (activeTraceId !== null && activeTraceId !== traceId) {
    closeTrace();
  }
  activeTraceId = traceId;
  activeParentId = parentId;
  activeDepth = 1;
  if (rootType) activeTraceRootType = rootType;
  traceCloseScheduled = false; // allow re-scheduling
  scheduleTraceClose();
}

// ─── Emit Events ──────────────────────────────────────────────────

/** Emit a timeline event. Assigns trace/parent IDs if a trace is active.
 *  If beginTrace is set, starts a new causal trace rooted at this event.
 *  If no trace is active and beginTrace is not set, the event gets an
 *  isolated traceId (no activeTraceId is set, so subsequent events won't
 *  be grouped with it unless they also specify beginTrace). */
export function emit(
  type: TimelineEventType,
  data: TimelineEventData,
  opts?: { beginTrace?: boolean; parentOverride?: number | null },
): TimelineEvent {
  const isOrphan = activeTraceId === null && !opts?.beginTrace;
  const orphanTraceId = isOrphan ? nextTraceId++ : undefined;

  const event: TimelineEvent = {
    id: nextEventId++,
    type,
    ts: performance.now(),
    wallTime: Date.now(),
    traceId: orphanTraceId ?? activeTraceId ?? nextTraceId,
    parentId: isOrphan ? null : activeParentId,
    depth: isOrphan ? 0 : activeDepth,
    data,
  };

  if (opts?.beginTrace) {
    beginTrace(event);
  }

  if (opts?.parentOverride !== undefined) {
    event.parentId = opts.parentOverride;
  }

  addToBuffer(event);
  return event;
}

/** Push a new parent context (for nesting). Returns restore function. */
export function pushParent(event: TimelineEvent): () => void {
  const prevParentId = activeParentId;
  const prevDepth = activeDepth;
  activeParentId = event.id;
  activeDepth++;
  return () => {
    activeParentId = prevParentId;
    activeDepth = prevDepth;
  };
}

// ─── Query ────────────────────────────────────────────────────────

/** Get all events in the buffer. */
export function getEvents(): readonly TimelineEvent[] {
  return buffer;
}

/** Get events for a specific trace. */
export function getTraceEvents(traceId: number): TimelineEvent[] {
  return buffer.filter(e => e.traceId === traceId);
}

/** Get the current trace count. */
export function getTraceCount(): number {
  const ids = new Set<number>();
  for (const e of buffer) ids.add(e.traceId);
  return ids.size;
}

/** Get trace summaries, most recent first. */
export function getTraces(): TraceSummary[] {
  const traceMap = new Map<number, TimelineEvent[]>();
  for (const e of buffer) {
    let arr = traceMap.get(e.traceId);
    if (!arr) {
      arr = [];
      traceMap.set(e.traceId, arr);
    }
    arr.push(e);
  }

  const now = performance.now();
  const summaries: TraceSummary[] = [];

  for (const [traceId, events] of traceMap) {
    const root = events.find(e => e.parentId === null) ?? events[0];
    const lastTs = events[events.length - 1].ts;

    let signalChanges = 0;
    let effectEvals = 0;
    let domMutations = 0;
    let sseEvents = 0;
    let malformedEvents = 0;
    let sseStarted = 0;
    let sseFinished = 0;

    for (const e of events) {
      switch (e.type) {
        case "signal-change": signalChanges++; break;
        case "effect-eval": effectEvals++; break;
        case "dom-mutation": domMutations++; break;
        case "sse-lifecycle": {
          sseEvents++;
          const sseType = (e.data as SseEventData).sseType;
          if (sseType === "started") sseStarted++;
          else if (sseType === "finished" || sseType === "error" || sseType === "retries-failed") sseFinished++;
          break;
        }
        case "sse-malformed": malformedEvents++; break;
      }
    }

    const isComplete = sseStarted === 0 || sseStarted <= sseFinished;
    const isStale = !isComplete && (now - lastTs > STALE_TRACE_MS);

    summaries.push({
      traceId,
      rootEvent: root,
      lastEventTs: lastTs,
      totalDuration: lastTs - root.ts,
      eventCount: events.length,
      signalChanges,
      effectEvals,
      domMutations,
      sseEvents,
      malformedEvents,
      warnings: detectWarnings(events),
      status: isStale ? "stale" : isComplete ? "complete" : "active",
    });
  }

  // Most recent first
  summaries.sort((a, b) => b.rootEvent.ts - a.rootEvent.ts);
  return summaries;
}

// ─── Warning Detection ────────────────────────────────────────────

const EXCESSIVE_EFFECTS_THRESHOLD = 15;
const PING_PONG_THRESHOLD = 3;
const MORPH_WINDOW_MS = 100;

/** Detect anomaly patterns in a trace's events. */
export function detectWarnings(events: TimelineEvent[]): Warning[] {
  const warnings: Warning[] = [];

  detectSignalPingPong(events, warnings);
  detectExcessiveEffects(events, warnings);
  detectHangingRequest(events, warnings);
  detectSelectorRace(events, warnings);
  detectNoMorphs(events, warnings);
  detectAttributeFlash(events, warnings);

  return warnings;
}

/** Same signal changed 3+ times in one trace. */
function detectSignalPingPong(events: TimelineEvent[], out: Warning[]): void {
  const counts = new Map<string, number>();
  for (const e of events) {
    if (e.type === "signal-change") {
      const path = (e.data as SignalChangeData).path;
      counts.set(path, (counts.get(path) ?? 0) + 1);
    }
  }
  for (const [path, count] of counts) {
    if (count >= PING_PONG_THRESHOLD) {
      out.push({
        code: "SIGNAL_PING_PONG",
        message: `Signal "${path}" changed ${count} times in this trace`,
      });
    }
  }
}

/** More than 15 effect evaluations per trace. */
function detectExcessiveEffects(events: TimelineEvent[], out: Warning[]): void {
  let count = 0;
  for (const e of events) {
    if (e.type === "effect-eval") count++;
  }
  if (count > EXCESSIVE_EFFECTS_THRESHOLD) {
    out.push({
      code: "EXCESSIVE_EFFECTS",
      message: `${count} effect evaluations in this trace (threshold: ${EXCESSIVE_EFFECTS_THRESHOLD})`,
    });
  }
}

/** SSE started with no finished after 5s. */
function detectHangingRequest(events: TimelineEvent[], out: Warning[]): void {
  const started = new Map<string, TimelineEvent>(); // elSelector → started event
  const finished = new Set<string>();

  for (const e of events) {
    if (e.type !== "sse-lifecycle") continue;
    const d = e.data as SseEventData;
    if (d.sseType === "started") {
      started.set(d.elSelector || String(e.id), e);
    } else if (d.sseType === "finished" || d.sseType === "error" || d.sseType === "retries-failed") {
      finished.add(d.elSelector || String(e.id));
    }
  }

  const now = performance.now();
  for (const [key, startEvent] of started) {
    if (!finished.has(key) && (now - startEvent.ts > STALE_TRACE_MS)) {
      const d = startEvent.data as SseEventData;
      out.push({
        code: "HANGING_REQUEST",
        message: `SSE request to ${d.route || d.handler || "unknown"} started ${Math.round((now - startEvent.ts) / 1000)}s ago with no response`,
      });
    }
  }
}

/** Two elements events targeting same selector in one trace. */
function detectSelectorRace(events: TimelineEvent[], out: Warning[]): void {
  const selectorCounts = new Map<string, number>();
  for (const e of events) {
    if (e.type !== "sse-lifecycle") continue;
    const d = e.data as SseEventData;
    if (d.payload?.selector) {
      const sel = String(d.payload.selector);
      selectorCounts.set(sel, (selectorCounts.get(sel) ?? 0) + 1);
    }
  }

  for (const [sel, count] of selectorCounts) {
    if (count >= 2) {
      out.push({
        code: "SELECTOR_RACE",
        message: `${count} elements events targeted "${sel}" in this trace`,
      });
    }
  }
}

/** Elements event that produced zero DOM mutations (within morph window). */
function detectNoMorphs(events: TimelineEvent[], out: Warning[]): void {
  const now = performance.now();
  for (let i = 0; i < events.length; i++) {
    const e = events[i];
    if (e.type !== "sse-lifecycle") continue;
    const d = e.data as SseEventData;
    if (d.sseType !== "datastar-patch-elements") continue;
    // Skip events whose morph window hasn't elapsed yet (avoids false-positives on active traces)
    if (now - e.ts < MORPH_WINDOW_MS) continue;

    // Look for DOM mutations within morph window after this event
    let hasMorph = false;
    for (let j = i + 1; j < events.length; j++) {
      if (events[j].ts - e.ts > MORPH_WINDOW_MS) break;
      if (events[j].type === "dom-mutation") {
        hasMorph = true;
        break;
      }
    }

    if (!hasMorph) {
      const sel = d.payload?.selector ? String(d.payload.selector) : "unknown";
      out.push({
        code: "NO_MORPHS",
        message: `Elements event targeting "${sel}" produced zero DOM mutations`,
      });
    }
  }
}

/** Same attribute changed 2+ times in a single trace (potential visual flash). */
function detectAttributeFlash(events: TimelineEvent[], out: Warning[]): void {
  const domEvents = events.filter(e => e.type === "dom-mutation");
  if (domEvents.length < 2) return;

  const attrChanges = new Map<string, number>(); // "selector[attr]" → count

  for (let i = 0; i < domEvents.length; i++) {
    const d = domEvents[i].data as DomMutationData;
    if (d.mutationType !== "attributes" || !d.attributeName) continue;

    const key = `${d.targetSelector}[${d.attributeName}]`;
    attrChanges.set(key, (attrChanges.get(key) ?? 0) + 1);
  }

  for (const [key, count] of attrChanges) {
    if (count >= 2) {
      out.push({
        code: "ATTRIBUTE_FLASH",
        message: `Attribute ${key} changed ${count} times in this trace`,
      });
    }
  }
}

// ─── Helpers ──────────────────────────────────────────────────────

/** Build a CSS selector string for an element (best-effort). */
export function selectorFor(el: Element): string {
  if (el.id) return `#${el.id}`;
  const tag = el.tagName.toLowerCase();
  const cls = el.className && typeof el.className === "string"
    ? "." + el.className.trim().split(/\s+/).slice(0, 2).join(".")
    : "";
  return tag + cls;
}

/** Truncate a value for storage (cap serialized size). */
export function clampValue(value: unknown): unknown {
  if (value === null || value === undefined) return value;
  try {
    const s = JSON.stringify(value);
    if (s.length <= MAX_VALUE_SIZE) return value;
    if (typeof value === "string") return value.slice(0, MAX_VALUE_SIZE) + "...";
    if (Array.isArray(value)) return `[${value.length} items]`;
    if (typeof value === "object") return `{${Object.keys(value as object).length} keys}`;
    return value;
  } catch {
    return String(value).slice(0, MAX_VALUE_SIZE);
  }
}

/** Format a wall-clock timestamp as HH:MM:SS.mmm */
export function formatTime(wallTime: number): string {
  const d = new Date(wallTime);
  const h = String(d.getHours()).padStart(2, "0");
  const m = String(d.getMinutes()).padStart(2, "0");
  const s = String(d.getSeconds()).padStart(2, "0");
  const ms = String(d.getMilliseconds()).padStart(3, "0");
  return `${h}:${m}:${s}.${ms}`;
}

/** Describe the root cause of a trace in a short string. */
export function describeRootCause(event: TimelineEvent): string {
  switch (event.type) {
    case "user-action": {
      const d = event.data as UserActionData;
      return `${d.eventType} ${d.targetSelector}`;
    }
    case "sse-lifecycle": {
      const d = event.data as SseEventData;
      return `SSE ${d.handler || d.route || d.sseType}`;
    }
    case "signal-change": {
      const d = event.data as SignalChangeData;
      return `signal ${d.path}`;
    }
    case "sse-malformed": {
      const d = event.data as MalformedSseData;
      return `malformed SSE: ${d.code}`;
    }
    default:
      return event.type;
  }
}

/** Summarize a trace's effects as a compact string. */
export function summarizeTrace(trace: TraceSummary): string {
  const parts: string[] = [];
  if (trace.sseEvents > 0) parts.push(`${trace.sseEvents} SSE`);
  if (trace.signalChanges > 0) parts.push(`${trace.signalChanges} signal${trace.signalChanges > 1 ? "s" : ""}`);
  if (trace.effectEvals > 0) parts.push(`${trace.effectEvals} effect${trace.effectEvals > 1 ? "s" : ""}`);
  if (trace.domMutations > 0) parts.push(`${trace.domMutations} DOM`);
  if (trace.malformedEvents > 0) parts.push(`${trace.malformedEvents} malformed`);
  return parts.join(", ") || "no effects";
}

/** Check if the active trace is for an SSE group. */
export function getActiveTraceId(): number | null {
  return activeTraceId;
}

/** Get the current event count. */
export function getEventCount(): number {
  return buffer.length;
}

// ─── Rendering Helpers ────────────────────────────────────────────

const ESCAPE_MAP: Record<string, string> = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

export function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, c => ESCAPE_MAP[c]);
}

/** Get the root type category for chip filtering. */
export function rootTypeCategory(event: TimelineEvent): string {
  switch (event.type) {
    case "user-action": return "user";
    case "sse-lifecycle": return "sse";
    case "signal-change": return "signal";
    case "sse-malformed": return "warning";
    default: return "other";
  }
}

/** Classify a trace for chip filtering based on root event + warnings.
 *  When no chips are active (empty set), all traces pass — "no filter = show all". */
export function traceMatchesChips(trace: TraceSummary, activeChips: Set<string>): boolean {
  if (activeChips.size === 0) return true; // no filter = show all
  const cat = rootTypeCategory(trace.rootEvent);
  if (activeChips.has(cat)) return true;
  if (activeChips.has("warning") && trace.warnings.length > 0) return true;
  return false;
}

/** Build a collapsed trace row HTML string. */
export function buildTraceRowHtml(trace: TraceSummary): string {
  const time = formatTime(trace.rootEvent.wallTime);
  const cause = escapeHtml(describeRootCause(trace.rootEvent));
  const summary = escapeHtml(summarizeTrace(trace));
  const dur = trace.totalDuration >= 1000
    ? (trace.totalDuration / 1000).toFixed(1) + "s"
    : Math.round(trace.totalDuration) + "ms";
  const warnBadge = trace.warnings.length > 0
    ? ` <span class="tl-warn-badge">\u26A0 ${trace.warnings.length}</span>`
    : "";
  const statusCls = "tl-status-" + trace.status;

  const iconCls = {
    "user-action": "tl-type-user",
    "sse-lifecycle": "tl-type-sse",
    "signal-change": "tl-type-signal",
    "sse-malformed": "tl-type-malformed",
  }[trace.rootEvent.type] ?? "tl-type-other";

  return `<div class="timeline-row ${statusCls}" data-trace-id="${trace.traceId}">`
    + `<span class="tl-type-icon ${iconCls}">\u25CF</span>`
    + `<span class="tl-time">${time}</span>`
    + `<span class="tl-cause">${cause}</span>`
    + `<span class="tl-arrow">\u2192</span>`
    + `<span class="tl-summary">${summary}</span>`
    + `<span class="tl-duration">${dur}</span>`
    + warnBadge
    + `</div>`;
}

// ─── Expanded Detail Rendering ────────────────────────────────────

/** Phase labels for grouping trace events. */
const PHASE_LABELS: Record<string, string> = {
  trigger: "Trigger",
  sse: "SSE",
  signal: "Signals",
  dom: "DOM",
  warning: "Warnings",
  finished: "Finished",
  other: "Other",
};

/** Classify an event into a display phase. */
function eventPhase(e: TimelineEvent): string {
  switch (e.type) {
    case "user-action": return "trigger";
    case "sse-lifecycle": {
      const d = e.data as SseEventData;
      return (d.sseType === "finished" || d.sseType === "error" || d.sseType === "retries-failed")
        ? "finished" : "sse";
    }
    case "signal-change": return "signal";
    case "effect-eval": return "signal";
    case "dom-mutation": return "dom";
    case "sse-malformed": return "warning";
    default: return "other";
  }
}

/** Format a single event as an HTML line for the cascade tree. */
function formatEventLine(e: TimelineEvent, baseTs: number): string {
  const offset = `+${Math.round(e.ts - baseTs)}ms`;
  const offsetHtml = `<span class="tl-ev-offset">${offset}</span>`;

  switch (e.type) {
    case "user-action": {
      const d = e.data as UserActionData;
      return `${offsetHtml} <span class="tl-ev-type tl-type-user">${escapeHtml(d.eventType)}</span> `
        + `<span class="tl-ev-target">${escapeHtml(d.targetSelector)}</span>`
        + (d.datastarAction ? ` <span class="tl-ev-action">${escapeHtml(d.datastarAction)}</span>` : "");
    }
    case "sse-lifecycle": {
      const d = e.data as SseEventData;
      const label = d.sseType === "started" ? "SSE start" : d.sseType;
      return `${offsetHtml} <span class="tl-ev-type tl-type-sse">${escapeHtml(label)}</span> `
        + (d.route ? `<span class="tl-ev-route">${escapeHtml(d.route)}</span> ` : "")
        + (d.handler ? `<span class="tl-ev-handler">${escapeHtml(d.handler)}</span>` : "");
    }
    case "signal-change": {
      const d = e.data as SignalChangeData;
      const oldStr = JSON.stringify(d.oldValue) ?? "undefined";
      const newStr = JSON.stringify(d.newValue) ?? "undefined";
      return `${offsetHtml} <span class="tl-ev-type tl-type-signal">${escapeHtml(d.path)}</span> `
        + `<span class="tl-ev-old">${escapeHtml(oldStr)}</span>`
        + ` \u2192 `
        + `<span class="tl-ev-new">${escapeHtml(newStr)}</span>`
        + ` <span class="tl-ev-source">(${escapeHtml(d.source)})</span>`;
    }
    case "effect-eval": {
      const d = e.data as EffectEvalData;
      return `${offsetHtml} <span class="tl-ev-type tl-type-signal">effect</span> `
        + `<span class="tl-ev-label">${escapeHtml(d.label || `#${d.effectId}`)}</span> `
        + `<span class="tl-ev-dur">${d.duration.toFixed(1)}ms</span>`;
    }
    case "dom-mutation": {
      const d = e.data as DomMutationData;
      let detail = escapeHtml(d.targetSelector);
      if (d.mutationType === "attributes" && d.attributeName) {
        detail += ` [${escapeHtml(d.attributeName)}]`;
        if (d.oldValue != null || d.newValue != null) {
          detail += ` ${escapeHtml(d.oldValue ?? "")} \u2192 ${escapeHtml(d.newValue ?? "")}`;
        }
      } else if (d.mutationType === "childList") {
        if (d.addedNodes.length) detail += ` +${d.addedNodes.length}`;
        if (d.removedNodes.length) detail += ` -${d.removedNodes.length}`;
      }
      return `${offsetHtml} <span class="tl-ev-type tl-type-dom">${escapeHtml(d.mutationType)}</span> ${detail}`;
    }
    case "sse-malformed": {
      const d = e.data as MalformedSseData;
      return `${offsetHtml} <span class="tl-ev-type tl-type-malformed">${escapeHtml(d.code)}</span> `
        + `<span class="tl-ev-msg">${escapeHtml(d.message)}</span>`;
    }
    default:
      return `${offsetHtml} <span class="tl-ev-type">${e.type}</span>`;
  }
}

/** Detect repeated signal ping-pong patterns and summarize them.
 *  Heuristic: seeds pattern from first N signal events. Cycles that
 *  don't start at index 0 (e.g., preceded by an init signal) are missed.
 *  Effect-eval events interleaved with cycles are collapsed in the summary. */
function summarizeCycles(events: TimelineEvent[]): { summarized: string[]; truncated: number } | null {
  if (events.length < 8) return null;

  // Look for signal ping-pong: same signal changing back and forth
  const signalEvents = events.filter(e => e.type === "signal-change");
  if (signalEvents.length < 6) return null;

  // Check for repeated path sequence
  const paths = signalEvents.map(e => (e.data as SignalChangeData).path);
  // Find repeating pattern of length 2-3
  for (const patLen of [2, 3]) {
    if (paths.length < patLen * 3) continue;
    const pattern = paths.slice(0, patLen);
    let repeats = 0;
    for (let i = 0; i + patLen <= paths.length; i += patLen) {
      const chunk = paths.slice(i, i + patLen);
      if (chunk.every((p, j) => p === pattern[j])) repeats++;
      else break;
    }
    if (repeats >= 3) {
      const cycle = pattern.join(" \u2192 ");
      return {
        summarized: [`<span class="tl-ev-cycle">${escapeHtml(cycle)} \u2026 ${repeats} cycles</span>`],
        truncated: signalEvents.length - 2, // show first + last
      };
    }
  }
  return null;
}

const MAX_DETAIL_EVENTS = 100;

/** Build expanded cascade tree HTML for a trace. */
export function buildTraceDetailHtml(traceId: number): string {
  const events = getTraceEvents(traceId);
  if (events.length === 0) return '<div class="tl-detail-empty">No events</div>';

  const baseTs = events[0].ts;

  // Check for pathological cycles
  const cycles = summarizeCycles(events);

  let html = '<div class="tl-detail">';

  // Group by phase
  let currentPhase = "";
  let shown = 0;
  const truncate = events.length > MAX_DETAIL_EVENTS && !cycles;

  for (let i = 0; i < events.length; i++) {
    if (truncate && shown >= MAX_DETAIL_EVENTS) break;

    const e = events[i];
    const phase = eventPhase(e);

    if (phase !== currentPhase) {
      if (currentPhase) html += '</div>'; // close previous phase
      currentPhase = phase;
      const label = PHASE_LABELS[phase] ?? phase;
      const phaseCls = `tl-phase-${phase}`;
      html += `<div class="tl-phase ${phaseCls}"><div class="tl-phase-label">${label}</div>`;
    }

    // For cycles, inject summary after trigger phase
    if (cycles && phase === "signal" && shown === 0) {
      for (const line of cycles.summarized) {
        html += `<div class="tl-ev-line tl-ev-indent">${line}</div>`;
      }
      // Show first and last signal events only
      html += `<div class="tl-ev-line tl-ev-indent">${formatEventLine(events.find(ev => ev.type === "signal-change")!, baseTs)}</div>`;
      const lastSig = [...events].reverse().find(ev => ev.type === "signal-change");
      if (lastSig && lastSig !== events.find(ev => ev.type === "signal-change")) {
        html += `<div class="tl-ev-line tl-ev-indent">${formatEventLine(lastSig, baseTs)}</div>`;
      }
      // Skip remaining signal events
      while (i + 1 < events.length && eventPhase(events[i + 1]) === "signal") i++;
      shown += 2;
      continue;
    }

    const indent = e.depth > 0 ? ' tl-ev-indent' : '';
    html += `<div class="tl-ev-line${indent}">${formatEventLine(e, baseTs)}</div>`;
    shown++;
  }

  if (currentPhase) html += '</div>'; // close last phase

  // Truncation notice
  if (truncate) {
    html += `<div class="tl-truncated">Showing ${MAX_DETAIL_EVENTS} of ${events.length} events</div>`;
  }

  // Warnings section
  const trace = getTraces().find(t => t.traceId === traceId);
  if (trace && trace.warnings.length > 0) {
    html += '<div class="tl-phase tl-phase-warning"><div class="tl-phase-label">Warnings</div>';
    for (const w of trace.warnings) {
      html += `<div class="tl-ev-line tl-ev-warn">\u26A0 <span class="tl-warn-code">${escapeHtml(w.code)}</span> ${escapeHtml(w.message)}</div>`;
    }
    html += '</div>';
  }

  html += '</div>';
  return html;
}

/** Build flat timestamped event dump as copyable text. */
export function buildFullTraceText(traceId: number): string {
  const events = getTraceEvents(traceId);
  if (events.length === 0) return "No events in trace.";

  const baseTs = events[0].ts;
  const lines: string[] = [];

  lines.push(`Trace #${traceId} — ${events.length} events`);
  lines.push(`Root: ${describeRootCause(events[0])}`);
  lines.push(`Duration: ${events.length > 1 ? Math.round(events[events.length - 1].ts - baseTs) : 0}ms`);
  lines.push("");

  for (const e of events) {
    const offset = `[+${Math.round(e.ts - baseTs)}ms]`;
    const indent = "  ".repeat(e.depth);
    let detail = "";

    switch (e.type) {
      case "user-action": {
        const d = e.data as UserActionData;
        detail = `${d.eventType} ${d.targetSelector}${d.datastarAction ? ` → ${d.datastarAction}` : ""}`;
        break;
      }
      case "sse-lifecycle": {
        const d = e.data as SseEventData;
        detail = `SSE ${d.sseType}${d.route ? ` ${d.route}` : ""}${d.handler ? ` (${d.handler})` : ""}`;
        break;
      }
      case "signal-change": {
        const d = e.data as SignalChangeData;
        detail = `signal ${d.path}: ${JSON.stringify(d.oldValue)} → ${JSON.stringify(d.newValue)} (${d.source})`;
        break;
      }
      case "effect-eval": {
        const d = e.data as EffectEvalData;
        detail = `effect ${d.label || `#${d.effectId}`} ${d.duration.toFixed(1)}ms`;
        break;
      }
      case "dom-mutation": {
        const d = e.data as DomMutationData;
        detail = `DOM ${d.mutationType} ${d.targetSelector}`;
        if (d.attributeName) detail += ` [${d.attributeName}]`;
        break;
      }
      case "sse-malformed": {
        const d = e.data as MalformedSseData;
        detail = `malformed ${d.code}: ${d.message}`;
        break;
      }
      default:
        detail = e.type;
    }

    lines.push(`${offset} ${indent}${detail}`);
  }

  // Warnings
  const trace = getTraces().find(t => t.traceId === traceId);
  if (trace && trace.warnings.length > 0) {
    lines.push("");
    lines.push("Warnings:");
    for (const w of trace.warnings) {
      lines.push(`  ⚠ ${w.code}: ${w.message}`);
    }
  }

  return lines.join("\n");
}

/** Build HTML for the full trace pre-block with copy button. */
export function buildFullTraceHtml(traceId: number): string {
  const text = buildFullTraceText(traceId);
  return `<div class="tl-full-trace">`
    + `<button class="tl-copy-btn" data-copy-trace="${traceId}">Copy</button>`
    + `<pre class="tl-full-pre">${escapeHtml(text)}</pre>`
    + `</div>`;
}

/** Filter and sort traces for display (oldest first). */
export function getFilteredTraces(
  textFilter: string,
  chipFilter: Set<string>,
): TraceSummary[] {
  const traces = getTraces();
  traces.reverse(); // oldest first

  const filter = textFilter.toLowerCase();
  return traces.filter(t => {
    if (!traceMatchesChips(t, chipFilter)) return false;
    if (!filter) return true;
    const cause = describeRootCause(t.rootEvent).toLowerCase();
    const summary = summarizeTrace(t).toLowerCase();
    // Also search signal paths within the trace
    const events = getTraceEvents(t.traceId);
    for (const e of events) {
      if (e.type === "signal-change") {
        if ((e.data as SignalChangeData).path.toLowerCase().includes(filter)) return true;
      }
      if (e.type === "sse-lifecycle") {
        const d = e.data as SseEventData;
        if (d.route.toLowerCase().includes(filter)) return true;
        if (d.handler.toLowerCase().includes(filter)) return true;
      }
    }
    return cause.includes(filter) || summary.includes(filter);
  });
}
