// timeline.ts — Causality-chain timeline for the StarHTML debugger.
// Captures user actions, SSE events, signal changes, and DOM mutations as
// a ring buffer of TimelineEvents grouped into causal traces.

import { getPath } from "datastar";
import {
  diffAttrValue,
  escapeHtml,
  extractDebugMeta,
  formatDuration,
  formatTime,
  injectEvent as injectCaptureEvent,
  parseDatastarFetchDetail,
  renderDiffHtml,
  renderDiffText,
  selectorPath,
  stripDebugKeys,
} from "./capture";
import { DEBUGGER_TAG, isDebuggerMutation, subscribeTimeline } from "./dom-observer";
import {
  type SignalEntry,
  flattenPaths,
  getEntries as getSignalEntries,
  getGroupedEntries as getSignalGroups,
  isDebuggerSignal,
  stripNamespace,
  valuesEqual,
} from "./signals";
import {
  type SSEValidationError,
  install as installSSEValidator,
  uninstall as uninstallSSEValidator,
} from "./sse-validator";

// ─── Event Types ──────────────────────────────────────────────────

export type TimelineEventType =
  | "user-action"
  | "sse-lifecycle"
  | "signal-change"
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
}

export interface SignalChangeData {
  path: string;
  oldValue: unknown;
  newValue: unknown;
  source: "sse" | "user" | "init" | "script" | "persist";
}

export interface DomMutationData {
  mutationType: "childList" | "attributes" | "characterData";
  targetSelector: string;
  attributeName?: string | null;
  oldValue?: string | null;
  newValue?: string | null;
  addedNodes?: string[];
  removedNodes?: string[];
  /** Disambiguates elements that share a selector path in warning detection. */
  elementId?: number;
}

export type MalformedSseData = SSEValidationError;

export type TimelineEventData =
  | UserActionData
  | SseEventData
  | SignalChangeData
  | DomMutationData
  | MalformedSseData;

export interface TimelineEvent {
  id: number;
  type: TimelineEventType;
  ts: number; // performance.now()
  wallTime: number; // Date.now()
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
  domMutations: number;
  sseEvents: number;
  malformedEvents: number;
  warnings: Warning[];
  status: "active" | "complete" | "stale";
}

// ─── Constants ────────────────────────────────────────────────────

const MAX_EVENTS = 5000;
const PRESERVE_FIRST = 500;
const EVICT_BATCH = 1000;
const STALE_TRACE_MS = 5000;
const MAX_VALUE_SIZE = 1024;
const SSE_TERMINAL_TYPES = new Set(["finished", "error", "retries-failed"]);

function isSseTerminal(sseType: string): boolean {
  return SSE_TERMINAL_TYPES.has(sseType);
}

// ─── State ────────────────────────────────────────────────────────

const buffer: TimelineEvent[] = [];
let nextEventId = 0;
let nextTraceId = 0;

let activeTraceId: number | null = null;
let activeParentId: number | null = null;
let activeDepth = 0;
let activeTraceRootType: TimelineEventType | null = null;
let traceCloseScheduled = false;
let traceCloseTimer: ReturnType<typeof setTimeout> | null = null;
let activeSseStarted = 0;
let activeSseFinished = 0;

const traceSseCounts = new Map<number, { started: number; finished: number }>();

// Async SSE correlation: element → { traceId, startedEventId }
// When an SSE request starts during a trace, we save the mapping. When async
// SSE responses arrive later, we resume the original trace.
let sseElTraces = new WeakMap<HTMLElement, { traceId: number; startedEventId: number }>();

const subscribers = new Set<() => void>();
let pendingNotify = false;
let initialized = false;

// Avoids O(N) buffer scan in getTraceCount()
const traceEventCounts = new Map<number, number>();

let traceSummaryCache: TraceSummary[] | null = null;

// ─── SSE Lifecycle Capture ────────────────────────────────────────

let sseListener: ((e: Event) => void) | null = null;

function captureSSELifecycle(): void {
  sseListener = (e: Event) => {
    const { type, el, argsRaw } = parseDatastarFetchDetail(e);
    const debugMeta = extractDebugMeta(argsRaw);

    const sseData: SseEventData = {
      sseType: type,
      handler: debugMeta?.handler ?? "",
      route: debugMeta?.route ?? "",
      seq: debugMeta?.seq ?? 0,
      payload: stripDebugKeys(argsRaw),
      elSelector: el ? selectorPath(el) : "",
    };

    if (type === "started") {
      const isNewTrace = activeTraceId === null;
      const event = emit("sse-lifecycle", sseData, { beginTrace: isNewTrace });

      // Save element → trace mapping for async SSE correlation
      if (el) {
        sseElTraces.set(el, { traceId: event.traceId, startedEventId: event.id });
      }
    } else {
      if (el && activeTraceId === null) {
        const saved = sseElTraces.get(el);
        if (saved) {
          resumeTrace(saved.traceId, saved.startedEventId, "sse-lifecycle");
        }
      }

      emit("sse-lifecycle", sseData);

      if (isSseTerminal(type)) {
        if (el) sseElTraces.delete(el);
      }
    }
  };
  document.addEventListener("datastar-fetch", sseListener);
}

// ─── User Action Capture ─────────────────────────────────────────

const USER_ACTION_EVENTS = ["click", "input", "submit", "keydown"] as const;
let userActionListeners: Array<{ type: string; fn: (e: Event) => void }> = [];

function isInsideDebugger(el: Element): boolean {
  if (el.closest("starhtml-debugger")) return true;
  // Walk up shadow roots in case of nested shadow DOM inside the debugger
  let root = el.getRootNode();
  while (root instanceof ShadowRoot) {
    if (root.host.tagName === DEBUGGER_TAG) return true;
    root = root.host.getRootNode();
  }
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

      let datastarAction: string | null = null;
      const actionEl = target.closest(`[data-on-${eventType}]`) ?? target;
      const actionAttr = actionEl.getAttribute(`data-on-${eventType}`);
      if (actionAttr) datastarAction = actionAttr.slice(0, 100);

      const data: UserActionData = {
        eventType,
        targetSelector: selectorPath(target),
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

const MAX_PREV_VALUES = 500;

function captureSignalChanges(): void {
  const prevValues = new Map<string, unknown>();

  // Pre-populate with current signal values so the first change shows
  // the actual old value instead of undefined
  try {
    for (const [, entry] of getSignalEntries()) {
      if (entry.status !== "removed") prevValues.set(entry.path, entry.value);
    }
  } catch {
    /* signals may not be ready yet */
  }

  signalPatchListener = (e: Event) => {
    const raw = (e as CustomEvent).detail;
    if (!raw || typeof raw !== "object") return;

    // Patched Datastar sends {signals, source} when source is tagged;
    // unpatched sends the signal object directly (backward-compatible).
    let detail: Record<string, unknown>;
    let eventSource: string | undefined;
    const rawObj = raw as Record<string, unknown>;
    if ("signals" in rawObj && typeof rawObj.signals === "object") {
      detail = rawObj.signals as Record<string, unknown>;
      const src = rawObj.source;
      if (typeof src === "string") eventSource = src;
    } else {
      detail = rawObj;
    }

    const paths = flattenPaths(detail, "");

    let baseSource: SignalChangeData["source"] = activeTraceId === null ? "script" : "init";
    if (activeTraceRootType === "sse-lifecycle") baseSource = "sse";
    else if (activeTraceRootType === "user-action") baseSource = "user";

    for (const path of paths) {
      if (isDebuggerSignal(path)) continue;

      let newValue: unknown;
      try {
        newValue = getPath(path);
      } catch {
        continue;
      }

      const oldValue = prevValues.get(path);
      if (valuesEqual(oldValue, newValue)) continue;

      // LRU: delete + re-insert so frequently-changed signals stay at the end
      prevValues.delete(path);
      prevValues.set(path, newValue);
      if (prevValues.size > MAX_PREV_VALUES) {
        const first = prevValues.keys().next().value;
        if (first !== undefined) prevValues.delete(first);
      }

      // Definitive source from the patched event; fall back to trace heuristic
      let source: SignalChangeData["source"] = baseSource;
      if (eventSource === "persist") {
        source = "persist";
      } else if (baseSource !== "sse" && baseSource !== "user" && oldValue === undefined) {
        source = "init";
      }
      const data: SignalChangeData = {
        path,
        oldValue: clampValueFast(oldValue),
        newValue: clampValueFast(newValue),
        source,
      };
      emit("signal-change", data);
    }
  };
  document.addEventListener("datastar-signal-patch", signalPatchListener);
}

// ─── DOM Mutation Capture (via shared debugger-dom-observer) ──────

let unsubDomObserver: (() => void) | null = null;

let elementIds = new WeakMap<Element, number>();
let nextElementId = 0;

function getElementId(el: Element): number {
  let id = elementIds.get(el);
  if (id === undefined) {
    id = nextElementId++;
    elementIds.set(el, id);
  }
  return id;
}

function serializeNodeList(nodes: NodeList): string[] {
  const out: string[] = [];
  for (const node of nodes) {
    if (node instanceof Element) out.push(selectorPath(node));
    else if (node.nodeType === Node.TEXT_NODE)
      out.push(`"${(node.textContent ?? "").slice(0, 40)}"`);
  }
  return out;
}

function handleMutationRecords(records: MutationRecord[]): void {
  // Only emit when a trace is active — orphan mutations are noise
  if (activeTraceId === null) return;

  for (const r of records) {
    if (isDebuggerMutation(r)) continue;

    const target = r.target instanceof Element ? r.target : r.target.parentElement;
    const targetSelector = target ? selectorPath(target) : "#text";

    if (r.type === "childList") {
      const addedNodes = serializeNodeList(r.addedNodes);
      const removedNodes = serializeNodeList(r.removedNodes);
      if (addedNodes.length === 0 && removedNodes.length === 0) continue;

      emit("dom-mutation", {
        mutationType: "childList",
        targetSelector,
        addedNodes,
        removedNodes,
      });
    } else if (r.type === "attributes") {
      const oldValue = r.oldValue ?? null;
      const newValue = (r.target as Element).getAttribute(r.attributeName ?? "") ?? null;
      // setAttribute fires MutationObserver even when the value is unchanged
      if (oldValue === newValue) continue;
      emit("dom-mutation", {
        mutationType: "attributes",
        targetSelector,
        attributeName: r.attributeName ?? "",
        oldValue,
        newValue,
        ...(target && { elementId: getElementId(target) }),
      });
    } else if (r.type === "characterData") {
      emit("dom-mutation", {
        mutationType: "characterData",
        targetSelector,
        oldValue: r.oldValue ?? null,
      });
    }
  }
}

function captureDomMutations(): void {
  unsubDomObserver = subscribeTimeline(handleMutationRecords);
}

// ─── Malformed SSE Capture ───────────────────────────────────────

function captureMalformedSSE(): void {
  installSSEValidator((error: SSEValidationError) => {
    emit("sse-malformed", error);
    injectCaptureEvent({
      type: "sse-malformed",
      timestamp: Date.now(),
      el: null,
      argsRaw: { ...error },
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
  captureDomMutations();
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
  if (unsubDomObserver) {
    unsubDomObserver();
    unsubDomObserver = null;
  }
  uninstallSSEValidator();
  if (traceCloseTimer !== null) {
    clearTimeout(traceCloseTimer);
    traceCloseTimer = null;
  }
  traceCloseScheduled = false;
  initialized = false;
  buffer.length = 0;
  nextEventId = 0;
  nextTraceId = 0;
  activeTraceId = null;
  activeParentId = null;
  activeDepth = 0;
  activeTraceRootType = null;
  activeSseStarted = 0;
  activeSseFinished = 0;
  traceSseCounts.clear();
  traceEventCounts.clear();
  traceSummaryCache = null;
  warningCache.clear();
  sseElTraces = new WeakMap();
  elementIds = new WeakMap();
  nextElementId = 0;
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
  traceSummaryCache = null;
  traceEventCounts.set(event.traceId, (traceEventCounts.get(event.traceId) ?? 0) + 1);

  if (buffer.length > MAX_EVENTS) {
    // Evict at trace boundaries to avoid splitting traces
    let evictStart = PRESERVE_FIRST;
    const startTraceId = buffer[evictStart]?.traceId;
    while (evictStart < buffer.length && buffer[evictStart].traceId === startTraceId) {
      evictStart++;
    }
    if (evictStart >= PRESERVE_FIRST + EVICT_BATCH) evictStart = PRESERVE_FIRST;
    let evictEnd = Math.min(evictStart + EVICT_BATCH, buffer.length - 1);
    const endTraceId = buffer[evictEnd]?.traceId;
    while (evictEnd < buffer.length - 1 && buffer[evictEnd + 1].traceId === endTraceId) {
      evictEnd++;
    }
    for (let i = evictStart; i <= evictEnd; i++) {
      const tid = buffer[i].traceId;
      const remaining = (traceEventCounts.get(tid) ?? 1) - 1;
      if (remaining <= 0) {
        traceEventCounts.delete(tid);
        traceSseCounts.delete(tid);
      } else {
        traceEventCounts.set(tid, remaining);
      }
    }
    buffer.splice(evictStart, evictEnd - evictStart + 1);
  }
  notifySubscribers();
}

// ─── Trace Management ─────────────────────────────────────────────

function beginTrace(rootEvent: TimelineEvent): void {
  // Close any active trace before starting a new one (e.g. rapid clicks)
  if (activeTraceId !== null) {
    if (traceCloseTimer !== null) {
      clearTimeout(traceCloseTimer);
      traceCloseTimer = null;
    }
    traceCloseScheduled = false;
    closeTrace();
  }
  const tid = nextTraceId++;
  rootEvent.traceId = tid;
  rootEvent.parentId = null;
  rootEvent.depth = 0;
  activeTraceId = tid;
  activeParentId = rootEvent.id;
  activeDepth = 1;
  activeTraceRootType = rootEvent.type;
  activeSseStarted = 0;
  activeSseFinished = 0;
  scheduleTraceClose();
}

function scheduleTraceClose(): void {
  if (traceCloseScheduled) return;
  traceCloseScheduled = true;
  // Use macrotask (setTimeout) instead of microtask so the trace stays open
  // through the full event propagation cycle — our capture-phase listener
  // fires before Datastar's bubble-phase handler which dispatches
  // datastar-signal-patch synchronously within its endBatch() call.
  traceCloseTimer = setTimeout(() => {
    traceCloseScheduled = false;
    traceCloseTimer = null;
    // Don't close if an SSE request is still open (concurrent SSE in same trace)
    if (activeTraceId !== null && activeSseStarted <= activeSseFinished) {
      closeTrace();
    }
  }, 0);
}

function closeTrace(): void {
  if (activeTraceId !== null) {
    traceSseCounts.set(activeTraceId, { started: activeSseStarted, finished: activeSseFinished });
  }
  activeTraceId = null;
  activeParentId = null;
  activeDepth = 0;
  activeTraceRootType = null;
}

/** Resume an existing trace for async SSE correlation.
 *  When an SSE response arrives asynchronously, we reactivate the trace so
 *  downstream signal changes and DOM mutations are grouped correctly. */
function resumeTrace(traceId: number, parentId: number, rootType?: TimelineEventType): void {
  if (activeTraceId !== null && activeTraceId !== traceId) {
    closeTrace();
  }
  activeTraceId = traceId;
  activeParentId = parentId;
  activeDepth = 1;
  if (rootType) activeTraceRootType = rootType;
  const saved = traceSseCounts.get(traceId);
  if (saved) {
    activeSseStarted = saved.started;
    activeSseFinished = saved.finished;
  }
  if (traceCloseTimer !== null) {
    clearTimeout(traceCloseTimer);
    traceCloseTimer = null;
  }
  traceCloseScheduled = false;
  scheduleTraceClose();
}

// ─── Emit Events ──────────────────────────────────────────────────

/** Emit a timeline event. Assigns trace/parent IDs if a trace is active.
 *  If beginTrace is set, starts a new causal trace rooted at this event.
 *  If no trace is active and beginTrace is not set, the event gets an
 *  isolated traceId (no activeTraceId is set, so subsequent events won't
 *  be grouped with it unless they also specify beginTrace). */
function emit(
  type: TimelineEventType,
  data: TimelineEventData,
  opts?: { beginTrace?: boolean }
): TimelineEvent {
  const willBeginTrace = opts?.beginTrace === true;
  const isOrphan = activeTraceId === null && !willBeginTrace;

  const event: TimelineEvent = {
    id: nextEventId++,
    type,
    ts: performance.now(),
    wallTime: Date.now(),
    // beginTrace() overwrites traceId; orphans get their own; otherwise use active
    traceId: isOrphan ? nextTraceId++ : (activeTraceId ?? -1),
    parentId: isOrphan ? null : activeParentId,
    depth: isOrphan ? 0 : activeDepth,
    data,
  };

  if (willBeginTrace) {
    beginTrace(event);
  }

  // Track SSE lifecycle counters for active trace (avoids O(n) scan in scheduleTraceClose)
  if (type === "sse-lifecycle" && event.traceId === activeTraceId) {
    const sseType = (data as SseEventData).sseType;
    if (sseType === "started") activeSseStarted++;
    else if (isSseTerminal(sseType)) {
      activeSseFinished++;
      // All SSE requests done — re-schedule close (the earlier timer may have
      // already fired and skipped close because SSE was still open)
      if (activeSseStarted <= activeSseFinished && !traceCloseScheduled) {
        scheduleTraceClose();
      }
    }
  }

  addToBuffer(event);
  return event;
}

// ─── Query ────────────────────────────────────────────────────────

function getTraceEvents(traceId: number): TimelineEvent[] {
  return buffer.filter((e) => e.traceId === traceId);
}

export function getTraceCount(): number {
  return traceEventCounts.size;
}

export function getTraces(): TraceSummary[] {
  if (traceSummaryCache) return traceSummaryCache;

  const traceMap = new Map<number, TimelineEvent[]>();
  for (const e of buffer) {
    const arr = traceMap.get(e.traceId);
    if (arr) arr.push(e);
    else traceMap.set(e.traceId, [e]);
  }

  const now = performance.now();
  const summaries: TraceSummary[] = [];

  for (const [traceId, events] of traceMap) {
    const root = events.find((e) => e.parentId === null) ?? events[0];
    const lastTs = events[events.length - 1].ts;

    let signalChanges = 0;
    let domMutations = 0;
    let sseEvents = 0;
    let malformedEvents = 0;
    let sseStarted = 0;
    let sseFinished = 0;

    for (const e of events) {
      switch (e.type) {
        case "signal-change":
          signalChanges++;
          break;
        case "dom-mutation":
          domMutations++;
          break;
        case "sse-lifecycle": {
          sseEvents++;
          const sseType = (e.data as SseEventData).sseType;
          if (sseType === "started") sseStarted++;
          else if (isSseTerminal(sseType)) sseFinished++;
          break;
        }
        case "sse-malformed":
          malformedEvents++;
          break;
      }
    }

    const isComplete = sseStarted <= sseFinished;
    const isStale = !isComplete && now - lastTs > STALE_TRACE_MS;

    summaries.push({
      traceId,
      rootEvent: root,
      lastEventTs: lastTs,
      totalDuration: lastTs - root.ts,
      eventCount: events.length,
      signalChanges,
      domMutations,
      sseEvents,
      malformedEvents,
      warnings: cachedDetectWarnings(traceId, events),
      status: isStale ? "stale" : isComplete ? "complete" : "active",
    });
  }

  summaries.sort((a, b) => a.rootEvent.ts - b.rootEvent.ts);
  traceSummaryCache = summaries;
  return summaries;
}

// ─── Warning Detection ────────────────────────────────────────────

const warningCache = new Map<string, Warning[]>();

function cachedDetectWarnings(traceId: number, events: TimelineEvent[]): Warning[] {
  const key = `${traceId}:${events.length}`;
  let cached = warningCache.get(key);
  if (cached) return cached;
  cached = detectWarnings(events);
  warningCache.set(key, cached);
  // Cap cache size to prevent unbounded growth
  if (warningCache.size > 1000) {
    const first = warningCache.keys().next().value;
    if (first !== undefined) warningCache.delete(first);
  }
  return cached;
}

const PING_PONG_THRESHOLD = 3;
const MORPH_WINDOW_MS = 100;

function detectWarnings(events: TimelineEvent[]): Warning[] {
  const warnings: Warning[] = [];

  detectSignalPingPong(events, warnings);
  detectHangingRequest(events, warnings);
  detectSelectorRace(events, warnings);
  detectNoMorphs(events, warnings);
  detectAttributeFlash(events, warnings);

  return warnings;
}

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

function detectHangingRequest(events: TimelineEvent[], out: Warning[]): void {
  const started = new Map<string, TimelineEvent>(); // elSelector → started event
  const finished = new Set<string>();

  for (const e of events) {
    if (e.type !== "sse-lifecycle") continue;
    const d = e.data as SseEventData;
    if (d.sseType === "started") {
      started.set(d.elSelector || String(e.id), e);
    } else if (isSseTerminal(d.sseType)) {
      finished.add(d.elSelector || String(e.id));
    }
  }

  const now = performance.now();
  for (const [key, startEvent] of started) {
    if (!finished.has(key) && now - startEvent.ts > STALE_TRACE_MS) {
      const d = startEvent.data as SseEventData;
      out.push({
        code: "HANGING_REQUEST",
        message: `SSE request to ${d.route || d.handler || "unknown"} started ${Math.round((now - startEvent.ts) / 1000)}s ago with no response`,
      });
    }
  }
}

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
        message: `${count} element events targeted "${sel}" in this trace`,
      });
    }
  }
}

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

function detectAttributeFlash(events: TimelineEvent[], out: Warning[]): void {
  // Two different elements can share the same selectorPath, so prefer
  // elementId when available to avoid false-positive flash warnings.
  const attrChanges = new Map<string, { count: number; selector: string }>();

  for (const e of events) {
    if (e.type !== "dom-mutation") continue;
    const d = e.data as DomMutationData;
    if (d.mutationType !== "attributes" || !d.attributeName) continue;

    const identity = d.elementId != null ? `#eid${d.elementId}` : d.targetSelector;
    const key = `${identity}[${d.attributeName}]`;
    const existing = attrChanges.get(key);
    if (existing) {
      existing.count++;
    } else {
      attrChanges.set(key, { count: 1, selector: `${d.targetSelector}[${d.attributeName}]` });
    }
  }

  for (const [, { count, selector }] of attrChanges) {
    if (count >= 2) {
      out.push({
        code: "ATTRIBUTE_FLASH",
        message: `Attribute ${selector} changed ${count} times in this trace`,
      });
    }
  }
}

// ─── Helpers ──────────────────────────────────────────────────────

/** Clamp large values to MAX_VALUE_SIZE, avoiding JSON.stringify for primitives. */
function clampValueFast(value: unknown): unknown {
  if (value === null || value === undefined) return value;
  const t = typeof value;
  if (t === "string") {
    const s = value as string;
    return s.length <= MAX_VALUE_SIZE ? value : `${s.slice(0, MAX_VALUE_SIZE)}...`;
  }
  if (t === "number" || t === "boolean") return value;
  if (Array.isArray(value)) {
    try {
      if (JSON.stringify(value).length <= MAX_VALUE_SIZE) return value;
    } catch {}
    return `[${value.length} items]`;
  }
  if (t === "object") {
    try {
      if (JSON.stringify(value).length <= MAX_VALUE_SIZE) return value;
    } catch {}
    return `{${Object.keys(value as object).length} keys}`;
  }
  return value;
}

/** Look up human-readable name for a signal path.
 *  Component signals: "_star_demo_counter_id1_count" → "demo-counter#1.count"
 *  Global signals: "count" → "count" (unchanged) */
function displaySignalPath(path: string): string {
  try {
    let matchEntry: SignalEntry | null = null;
    const seenNs = new Set<string>();
    let instanceNum = 0;
    for (const [, entry] of getSignalEntries()) {
      if (!matchEntry && entry.path === path && entry.tagName) matchEntry = entry;
      if (
        matchEntry &&
        entry.tagName === matchEntry.tagName &&
        entry.namespace &&
        !seenNs.has(entry.namespace)
      ) {
        seenNs.add(entry.namespace);
        if (entry.namespace === matchEntry.namespace) instanceNum = seenNs.size;
      }
    }
    if (!matchEntry) return path;
    const bare = stripNamespace(path, matchEntry.tagName);
    const prefix = seenNs.size > 1 ? `${matchEntry.tagName}#${instanceNum}` : matchEntry.tagName;
    return `${prefix}.${bare}`;
  } catch {}
  return path;
}

export function describeRootCause(event: TimelineEvent): string {
  switch (event.type) {
    case "user-action": {
      const d = event.data as UserActionData;
      const label = d.targetText ? ` "${d.targetText}"` : "";
      return `${d.eventType}${label} ${d.targetSelector}`;
    }
    case "sse-lifecycle": {
      const d = event.data as SseEventData;
      return `SSE ${d.handler || d.route || d.sseType}`;
    }
    case "signal-change": {
      const d = event.data as SignalChangeData;
      return `signal ${displaySignalPath(d.path)}`;
    }
    case "sse-malformed": {
      const d = event.data as MalformedSseData;
      return `malformed SSE: ${d.code}`;
    }
    default:
      return event.type;
  }
}

export function summarizeTrace(trace: TraceSummary): string {
  const parts: string[] = [];
  if (trace.sseEvents > 0) parts.push(`${trace.sseEvents} SSE`);
  if (trace.signalChanges > 0)
    parts.push(`${trace.signalChanges} signal${trace.signalChanges > 1 ? "s" : ""}`);
  if (trace.domMutations > 0) parts.push(`${trace.domMutations} DOM`);
  if (trace.malformedEvents > 0) parts.push(`${trace.malformedEvents} malformed`);
  return parts.join(", ") || "no effects";
}

// ─── Rendering Helpers ────────────────────────────────────────────

const ROOT_TYPE_CATEGORIES: Record<string, string> = {
  "user-action": "user",
  "sse-lifecycle": "sse",
  "signal-change": "signal",
  "sse-malformed": "warning",
};

export function rootTypeCategory(event: TimelineEvent): string {
  return ROOT_TYPE_CATEGORIES[event.type] ?? "other";
}

const TYPE_ICON_CLS: Record<string, string> = {
  "user-action": "tl-type-user",
  "sse-lifecycle": "tl-type-sse",
  "signal-change": "tl-type-signal",
  "sse-malformed": "tl-type-malformed",
};

export function buildTraceRowHtml(trace: TraceSummary): string {
  const time = formatTime(trace.rootEvent.wallTime);
  const cause = escapeHtml(describeRootCause(trace.rootEvent));
  const summary = escapeHtml(summarizeTrace(trace));
  const dur = formatDuration(trace.totalDuration);
  const warnBadge =
    trace.warnings.length > 0
      ? ` <span class="tl-warn-badge">\u26A0 ${trace.warnings.length}</span>`
      : "";
  const statusCls = `tl-status-${trace.status}`;
  const iconCls = TYPE_ICON_CLS[trace.rootEvent.type] ?? "tl-type-other";

  return `<div class="timeline-row ${statusCls}" data-trace-id="${trace.traceId}"><span class="tl-type-icon ${iconCls}">\u25CF</span><span class="tl-time">${time}</span><span class="tl-cause">${cause}</span><span class="tl-arrow">\u2192</span>${warnBadge}<span class="tl-summary">${summary}</span><span class="tl-duration">${dur}</span><button class="tl-row-copy" data-copy-single="${trace.traceId}" title="Copy trace">\u2398</button></div>`;
}

// ─── Expanded Detail Rendering ────────────────────────────────────

const PHASE_LABELS: Record<string, string> = {
  trigger: "Trigger",
  sse: "SSE",
  signal: "Signals",
  dom: "DOM",
  warning: "Warnings",
  finished: "Finished",
};

function eventPhase(e: TimelineEvent): string {
  switch (e.type) {
    case "user-action":
      return "trigger";
    case "sse-lifecycle": {
      const d = e.data as SseEventData;
      return isSseTerminal(d.sseType) ? "finished" : "sse";
    }
    case "signal-change":
      return "signal";
    case "dom-mutation":
      return "dom";
    case "sse-malformed":
      return "warning";
    default:
      return "other";
  }
}

function formatEventLine(e: TimelineEvent, baseTs: number): string {
  const offset = `+${Math.round(e.ts - baseTs)}ms`;
  const offsetHtml = `<span class="tl-ev-offset">${offset}</span>`;

  switch (e.type) {
    case "user-action": {
      const d = e.data as UserActionData;
      const textHtml = d.targetText
        ? ` <span class="tl-ev-text">"${escapeHtml(d.targetText)}"</span>`
        : "";
      return `${offsetHtml} <span class="tl-ev-type tl-type-user">${escapeHtml(d.eventType)}</span>${textHtml} <span class="tl-ev-target">${escapeHtml(d.targetSelector)}</span>${d.datastarAction ? ` <span class="tl-ev-action">${escapeHtml(d.datastarAction)}</span>` : ""}`;
    }
    case "sse-lifecycle": {
      const d = e.data as SseEventData;
      const label = d.sseType === "started" ? "SSE start" : d.sseType;
      return `${offsetHtml} <span class="tl-ev-type tl-type-sse">${escapeHtml(label)}</span> ${d.route ? `<span class="tl-ev-route">${escapeHtml(d.route)}</span> ` : ""}${d.handler ? `<span class="tl-ev-handler">${escapeHtml(d.handler)}</span>` : ""}`;
    }
    case "signal-change": {
      const d = e.data as SignalChangeData;
      const oldStr = d.oldValue === undefined ? "undefined" : JSON.stringify(d.oldValue);
      const newStr = d.newValue === undefined ? "undefined" : JSON.stringify(d.newValue);
      return `${offsetHtml} <span class="tl-ev-type tl-type-signal">${escapeHtml(displaySignalPath(d.path))}</span> <span class="tl-ev-old">${escapeHtml(oldStr)}</span> \u2192 <span class="tl-ev-new">${escapeHtml(newStr)}</span> <span class="tl-ev-source">(${escapeHtml(d.source)})</span>`;
    }
    case "dom-mutation": {
      const d = e.data as DomMutationData;
      let detail = `<span class="tl-ev-target">${escapeHtml(d.targetSelector)}</span>`;
      if (d.mutationType === "attributes" && d.attributeName) {
        detail += ` <span class="tl-ev-attr">[${escapeHtml(d.attributeName)}]</span>`;
        if (d.oldValue != null || d.newValue != null) {
          const diff = diffAttrValue(d.attributeName, d.oldValue ?? "", d.newValue ?? "");
          detail += ` ${renderDiffHtml(diff)}`;
        }
      } else if (d.mutationType === "childList") {
        if (d.addedNodes?.length)
          detail += ` <span class="tl-ev-new">+${d.addedNodes.length}</span>`;
        if (d.removedNodes?.length)
          detail += ` <span class="tl-ev-old">-${d.removedNodes.length}</span>`;
      }
      return `${offsetHtml} <span class="tl-ev-type tl-type-dom">${escapeHtml(d.mutationType)}</span> ${detail}`;
    }
    case "sse-malformed": {
      const d = e.data as MalformedSseData;
      return `${offsetHtml} <span class="tl-ev-type tl-type-malformed">${escapeHtml(d.code)}</span> <span class="tl-ev-msg">${escapeHtml(d.message)}</span>`;
    }
    default:
      return `${offsetHtml} <span class="tl-ev-type">${e.type}</span>`;
  }
}

/** Detect repeated signal ping-pong patterns and summarize them.
 *  Heuristic: seeds pattern from first N signal events. Cycles that
 *  don't start at index 0 (e.g., preceded by an init signal) are missed. */
function summarizeCycles(
  events: TimelineEvent[]
): { summarized: string[]; truncated: number } | null {
  if (events.length < 8) return null;

  const signalEvents = events.filter((e) => e.type === "signal-change");
  if (signalEvents.length < 6) return null;

  const paths = signalEvents.map((e) => (e.data as SignalChangeData).path);
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
        summarized: [
          `<span class="tl-ev-cycle">${escapeHtml(cycle)} \u2026 ${repeats} cycles</span>`,
        ],
        truncated: signalEvents.length - 2, // show first + last
      };
    }
  }
  return null;
}

const MAX_DETAIL_EVENTS = 100;

export function buildTraceDetailHtml(traceId: number): string {
  const events = getTraceEvents(traceId);
  if (events.length === 0) return '<div class="tl-detail-empty">No events</div>';

  const baseTs = events[0].ts;
  const warnings = cachedDetectWarnings(traceId, events);
  const cycles = summarizeCycles(events);

  let html = '<div class="tl-detail">';

  if (warnings.length > 0) {
    html += '<div class="tl-phase tl-phase-warning"><div class="tl-phase-label">Warnings</div>';
    for (const w of warnings) {
      html += `<div class="tl-ev-line tl-ev-warn">\u26A0 <span class="tl-warn-code">${escapeHtml(w.code)}</span> ${escapeHtml(w.message)}</div>`;
    }
    html += "</div>";
  }

  let currentPhase = "";
  let shown = 0;
  const truncate = events.length > MAX_DETAIL_EVENTS && !cycles;
  const domEvents: TimelineEvent[] = [];

  for (let i = 0; i < events.length; i++) {
    if (truncate && shown >= MAX_DETAIL_EVENTS) break;

    const e = events[i];
    const phase = eventPhase(e);

    // Already surfaced in Warnings section above
    if (phase === "warning") continue;

    if (phase === "dom") {
      domEvents.push(e);
      continue;
    }

    if (phase !== currentPhase) {
      if (currentPhase) html += "</div>";
      currentPhase = phase;
      const label = PHASE_LABELS[phase] ?? phase;
      html += `<div class="tl-phase tl-phase-${phase}"><div class="tl-phase-label">${label}</div>`;
    }

    if (cycles && phase === "signal" && shown === 0) {
      for (const line of cycles.summarized) {
        html += `<div class="tl-ev-line tl-ev-indent">${line}</div>`;
      }
      const firstSig = events.find((ev) => ev.type === "signal-change");
      if (!firstSig) continue;
      html += `<div class="tl-ev-line tl-ev-indent">${formatEventLine(firstSig, baseTs)}</div>`;
      let lastSig: TimelineEvent | undefined;
      for (let j = events.length - 1; j >= 0; j--) {
        if (events[j].type === "signal-change") {
          lastSig = events[j];
          break;
        }
      }
      if (lastSig && lastSig !== firstSig) {
        html += `<div class="tl-ev-line tl-ev-indent">${formatEventLine(lastSig, baseTs)}</div>`;
      }
      while (i + 1 < events.length && eventPhase(events[i + 1]) === "signal") i++;
      shown += 2;
      continue;
    }

    const indent = e.depth > 0 ? " tl-ev-indent" : "";
    html += `<div class="tl-ev-line${indent}">${formatEventLine(e, baseTs)}</div>`;
    shown++;
  }

  if (currentPhase) html += "</div>";

  if (domEvents.length > 0) {
    html += '<div class="tl-phase tl-phase-dom">';
    html += `<div class="tl-dom-toggle"><span class="tl-dom-arrow">\u25B8</span> <span class="tl-phase-label">DOM</span> <span class="tl-dom-count">${domEvents.length} mutation${domEvents.length !== 1 ? "s" : ""}</span></div>`;
    html += '<div class="tl-dom-body" style="display:none">';
    for (const e of domEvents) {
      const indent = e.depth > 0 ? " tl-ev-indent" : "";
      html += `<div class="tl-ev-line${indent}">${formatEventLine(e, baseTs)}</div>`;
    }
    html += "</div></div>";
  }

  if (truncate) {
    html += `<div class="tl-truncated">Showing ${MAX_DETAIL_EVENTS} of ${events.length} events</div>`;
  }

  html += "</div>";
  return html;
}

export function buildFullTraceText(traceId: number): string {
  const events = getTraceEvents(traceId);
  if (events.length === 0) return "No events in trace.";

  const baseTs = events[0].ts;
  const lines: string[] = [];

  lines.push(`Trace #${traceId} — ${events.length} events`);
  lines.push(`Root: ${describeRootCause(events[0])}`);
  lines.push(
    `Duration: ${formatDuration(events.length > 1 ? events[events.length - 1].ts - baseTs : 0)}`
  );
  lines.push("");

  for (const e of events) {
    const offset = `[+${Math.round(e.ts - baseTs)}ms]`;
    const indent = "  ".repeat(e.depth);
    let detail = "";

    switch (e.type) {
      case "user-action": {
        const d = e.data as UserActionData;
        const text = d.targetText ? ` "${d.targetText}"` : "";
        detail = `${d.eventType}${text} ${d.targetSelector}${d.datastarAction ? ` → ${d.datastarAction}` : ""}`;
        break;
      }
      case "sse-lifecycle": {
        const d = e.data as SseEventData;
        detail = `SSE ${d.sseType}${d.route ? ` ${d.route}` : ""}${d.handler ? ` (${d.handler})` : ""}`;
        break;
      }
      case "signal-change": {
        const d = e.data as SignalChangeData;
        detail = `signal ${displaySignalPath(d.path)}: ${JSON.stringify(d.oldValue)} → ${JSON.stringify(d.newValue)} (${d.source})`;
        break;
      }
      case "dom-mutation": {
        const d = e.data as DomMutationData;
        detail = `DOM ${d.mutationType} ${d.targetSelector}`;
        if (d.mutationType === "attributes" && d.attributeName) {
          detail += ` [${d.attributeName}]`;
          if (d.oldValue != null || d.newValue != null) {
            const diff = diffAttrValue(d.attributeName, d.oldValue ?? "", d.newValue ?? "");
            const text = renderDiffText(diff);
            if (text) detail += ` ${text}`;
          }
        } else if (d.mutationType === "childList") {
          if (d.addedNodes?.length) detail += ` +${d.addedNodes.length}`;
          if (d.removedNodes?.length) detail += ` -${d.removedNodes.length}`;
        }
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

  const warnings = cachedDetectWarnings(traceId, events);
  if (warnings.length > 0) {
    lines.push("");
    lines.push("Warnings:");
    for (const w of warnings) {
      lines.push(`  ⚠ ${w.code}: ${w.message}`);
    }
  }

  return lines.join("\n");
}

export function buildCopyButtonHtml(traceId: number): string {
  return `<div class="tl-copy-wrap"><button class="tl-copy-btn" data-copy-trace="${traceId}">Copy</button></div>`;
}

export function getFilteredTraces(textFilter: string, chipFilter: Set<string>): TraceSummary[] {
  const traces = getTraces();

  const filter = textFilter.toLowerCase();
  return traces.filter((t) => {
    if (chipFilter.size > 0) {
      const cat = rootTypeCategory(t.rootEvent);
      if (!chipFilter.has(cat) && !(chipFilter.has("warning") && t.warnings.length > 0))
        return false;
    }
    if (!filter) return true;
    // Check summary fields first (O(1)) before scanning events
    const cause = describeRootCause(t.rootEvent).toLowerCase();
    const summary = summarizeTrace(t).toLowerCase();
    if (cause.includes(filter) || summary.includes(filter)) return true;
    const events = getTraceEvents(t.traceId);
    for (const e of events) {
      if (e.type === "signal-change") {
        if ((e.data as SignalChangeData).path.toLowerCase().includes(filter)) return true;
      } else if (e.type === "sse-lifecycle") {
        const d = e.data as SseEventData;
        if (d.route.toLowerCase().includes(filter) || d.handler.toLowerCase().includes(filter))
          return true;
      }
    }
    return false;
  });
}

/** Get trace IDs within the last N seconds (by wall time).
 *  Returns ALL traces in the window, ignoring text/chip filters.
 *  This is intentional: time-based export captures full context. */
export function getTraceIdsInWindow(seconds: number): number[] {
  const cutoff = Date.now() - seconds * 1000;
  const traces = getTraces();
  const ids: number[] = [];
  for (const t of traces) {
    if (t.rootEvent.wallTime >= cutoff) ids.push(t.traceId);
  }
  return ids;
}

/** Get trace IDs in a range (inclusive, by traceId). */
export function getTraceIdsInRange(startId: number, endId: number): number[] {
  const lo = Math.min(startId, endId);
  const hi = Math.max(startId, endId);
  const traces = getTraces();
  return traces.filter((t) => t.traceId >= lo && t.traceId <= hi).map((t) => t.traceId);
}

// ─── Markdown Export ──────────────────────────────────────────────

const SINGLE_TRACE_SIZE_LIMIT = 5 * 1024;
const EXPORT_SIZE_LIMIT = 20 * 1024;
const TRUNCATE_PAYLOAD = 200;

const LEGEND =
  "**Legend:** `[signals]` = signal patch, `[elements]` = DOM morph, `[start]`/`[done]` = SSE lifecycle,\n" +
  "`[click]`/`[input]` = user action, `[malformed]` = SSE validation error";

function formatSignalSnapshot(): string {
  let groups: ReturnType<typeof getSignalGroups>;
  try {
    groups = getSignalGroups("");
  } catch {
    return "";
  }
  if (groups.length === 0) return "";

  const lines: string[] = ["", "### Signal Snapshot", ""];
  for (const group of groups) {
    lines.push(`**${group.displayName}**`);
    for (const e of group.entries) {
      if (e.status === "removed") continue;
      const displayName = stripNamespace(e.path, e.tagName);
      const val = JSON.stringify(e.value);
      const valStr =
        val && val.length > TRUNCATE_PAYLOAD ? `${val.slice(0, TRUNCATE_PAYLOAD)}...` : val;
      lines.push(
        `- \`${displayName}\` = \`${valStr ?? "undefined"}\` (${e.type}${e.persistStorage ? `, persist:${e.persistStorage}` : ""})`
      );
    }
    lines.push("");
  }
  return lines.join("\n");
}

function formatEventExport(e: TimelineEvent, baseTs: number): string {
  const offset = `[+${Math.round(e.ts - baseTs)}ms]`;
  const indent = "  ".repeat(e.depth);

  switch (e.type) {
    case "user-action": {
      const d = e.data as UserActionData;
      const text = d.targetText ? ` "${d.targetText}"` : "";
      return `${offset} ${indent}[${d.eventType}]${text} \`${d.targetSelector}\`${d.datastarAction ? ` → \`${d.datastarAction}\`` : ""}`;
    }
    case "sse-lifecycle": {
      const d = e.data as SseEventData;
      const tag =
        d.sseType === "started"
          ? "[start]"
          : isSseTerminal(d.sseType)
            ? "[done]"
            : `[${d.sseType}]`;
      let payload = "";
      if (d.payload && Object.keys(d.payload).length > 0) {
        const raw = JSON.stringify(d.payload);
        payload =
          raw.length > TRUNCATE_PAYLOAD ? ` ${raw.slice(0, TRUNCATE_PAYLOAD)}...` : ` ${raw}`;
      }
      return `${offset} ${indent}${tag} \`${d.route || d.handler || "SSE"}\`${payload}`;
    }
    case "signal-change": {
      const d = e.data as SignalChangeData;
      const oldStr = d.oldValue === undefined ? "undefined" : JSON.stringify(d.oldValue);
      const newStr = d.newValue === undefined ? "undefined" : JSON.stringify(d.newValue);
      return `${offset} ${indent}[signals] \`${displaySignalPath(d.path)}\`: \`${oldStr}\` → \`${newStr}\` (${d.source})`;
    }
    case "dom-mutation": {
      const d = e.data as DomMutationData;
      let detail = `\`${d.targetSelector}\``;
      if (d.mutationType === "attributes" && d.attributeName) {
        detail += ` [${d.attributeName}]`;
        if (d.oldValue != null || d.newValue != null) {
          const diff = diffAttrValue(d.attributeName, d.oldValue ?? "", d.newValue ?? "");
          const text = renderDiffText(diff);
          if (text) detail += ` ${text}`;
        }
      } else if (d.mutationType === "childList") {
        if (d.addedNodes?.length) detail += ` +${d.addedNodes.length}`;
        if (d.removedNodes?.length) detail += ` -${d.removedNodes.length}`;
      }
      return `${offset} ${indent}[elements] ${d.mutationType} ${detail}`;
    }
    case "sse-malformed": {
      const d = e.data as MalformedSseData;
      return `${offset} ${indent}[malformed] ${d.code}: ${d.message}`;
    }
    default:
      return `${offset} ${indent}[${e.type}]`;
  }
}

function formatSignalDiff(events: TimelineEvent[]): string {
  const firstSeen = new Map<string, unknown>();
  const lastSeen = new Map<string, unknown>();
  const changeCounts = new Map<string, number>();

  for (const e of events) {
    if (e.type !== "signal-change") continue;
    const d = e.data as SignalChangeData;
    if (!firstSeen.has(d.path)) firstSeen.set(d.path, d.oldValue);
    lastSeen.set(d.path, d.newValue);
    changeCounts.set(d.path, (changeCounts.get(d.path) ?? 0) + 1);
  }

  // Only show the summary when it adds info (at least one signal changed > 1 time)
  if (![...changeCounts.values()].some((c) => c > 1)) return "";

  const lines: string[] = ["", "### Signal Changes (net)", ""];
  for (const [path, startVal] of firstSeen) {
    const endVal = lastSeen.get(path);
    lines.push(
      `- \`${displaySignalPath(path)}\`: \`${JSON.stringify(startVal)}\` → \`${JSON.stringify(endVal)}\``
    );
  }
  return lines.join("\n");
}

function safeSlice(text: string, limit: number): string {
  const cut = text.lastIndexOf("\n", limit);
  const safe = text.slice(0, cut > 0 ? cut : limit);
  // Check if we're inside an unclosed fenced code block
  const fenceCount = (safe.match(/^```/gm) || []).length;
  const needsClose = fenceCount % 2 !== 0;
  return `${safe}${needsClose ? "\n```" : ""}\n\n*(truncated)*`;
}

/** Truncate a fenced code block section by name, keeping first/last N lines. */
function truncateSection(text: string, sectionName: string, keepLines: number): string {
  const start = text.indexOf(`### ${sectionName}`);
  if (start === -1) return text;
  const end = text.indexOf("\n###", start + 1);

  const before = text.slice(0, start);
  const section = text.slice(start, end === -1 ? undefined : end);
  const after = end === -1 ? "" : text.slice(end);

  const lines = section.split("\n");
  const header = lines.slice(0, 3); // "### Name", "", "```"
  const body = lines.slice(3, -1);
  const closing = lines.slice(-1); // "```"

  if (body.length <= keepLines * 2) return text;

  const kept = [
    ...header,
    ...body.slice(0, keepLines),
    `... (${body.length - keepLines * 2} entries omitted)`,
    ...body.slice(-keepLines),
    ...closing,
  ];
  return before + kept.join("\n") + after;
}

function truncateExport(text: string, limit: number): string {
  if (text.length <= limit) return text;

  // Lower-priority sections truncated first
  let result = truncateSection(text, "DOM Mutations", 3);
  if (result.length <= limit) return result;

  result = truncateSection(result, "Event Log", 5);
  if (result.length <= limit) return result;

  return safeSlice(result, limit);
}

export function formatTraceExport(traceId: number, opts?: { includeLegend?: boolean }): string {
  const events = getTraceEvents(traceId);
  if (events.length === 0) return `## Trace #${traceId}\n\nNo events captured.`;

  const root = events[0];
  const baseTs = root.ts;
  const duration = events.length > 1 ? Math.round(events[events.length - 1].ts - baseTs) : 0;
  const timestamp = formatTime(root.wallTime);
  const warnings = cachedDetectWarnings(traceId, events);

  const lines: string[] = [];

  lines.push(`## Trace #${traceId}`);
  lines.push("");
  lines.push(`- **Root cause:** ${describeRootCause(root)}`);
  lines.push(`- **Time:** ${timestamp}`);
  if (duration > 0) lines.push(`- **Duration:** ${duration}ms`);
  lines.push(`- **Events:** ${events.length}`);
  lines.push("");

  // Legend — only in standalone single-trace copies
  if (opts?.includeLegend !== false) {
    lines.push(LEGEND);
    lines.push("");
  }

  if (warnings.length > 0) {
    lines.push("", "### Diagnostic Notes", "");
    for (const w of warnings) {
      lines.push(`- **${w.code}**: ${w.message}`);
    }
    lines.push("");
  }

  const primaryEvents = events.filter((e) => e.type !== "dom-mutation");
  const domEvents = events.filter((e) => e.type === "dom-mutation");

  lines.push("### Event Log");
  lines.push("");
  lines.push("```");
  for (const e of primaryEvents) {
    lines.push(formatEventExport(e, baseTs));
  }
  lines.push("```");

  const diff = formatSignalDiff(events);
  if (diff) lines.push(diff);

  // Separated so DOM mutations don't eat truncation budget
  if (domEvents.length > 0) {
    lines.push("");
    lines.push("### DOM Mutations");
    lines.push("");
    lines.push("```");
    for (const e of domEvents) {
      lines.push(formatEventExport(e, baseTs));
    }
    lines.push("```");
  }

  let result = lines.join("\n");

  if (result.length > SINGLE_TRACE_SIZE_LIMIT) {
    result = truncateExport(result, SINGLE_TRACE_SIZE_LIMIT);
  }

  return result;
}

export function formatAllTracesExport(traceIds: number[]): string {
  const sections: string[] = [];
  let totalSize = 0;

  const header =
    `# Timeline Export — ${traceIds.length} trace${traceIds.length !== 1 ? "s" : ""}\n\n` +
    `Page: ${location.pathname}\n` +
    `Exported at ${formatTime(Date.now())}\n`;
  sections.push(header);
  totalSize += header.length;

  const snapshot = formatSignalSnapshot();
  if (snapshot) {
    sections.push(snapshot);
    totalSize += snapshot.length;
  }

  sections.push(LEGEND);
  totalSize += LEGEND.length;

  // Newest first — older traces get omitted if over budget
  let omitted = 0;
  for (let i = 0; i < traceIds.length; i++) {
    const section = formatTraceExport(traceIds[i], { includeLegend: false });

    if (totalSize + section.length > EXPORT_SIZE_LIMIT && sections.length > 2) {
      omitted = traceIds.length - i;
      break;
    }

    sections.push(section);
    totalSize += section.length;
  }

  if (omitted > 0) {
    sections.push(
      `\n---\n\n*${omitted} older trace${omitted !== 1 ? "s" : ""} omitted (size budget exceeded)*`
    );
  }

  return sections.join("\n\n---\n\n");
}
