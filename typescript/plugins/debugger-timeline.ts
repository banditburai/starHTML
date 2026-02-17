// debugger-timeline.ts — Causality-chain timeline for the StarHTML debugger.
// Captures user actions, SSE events, signal changes, and DOM mutations as
// a ring buffer of TimelineEvents grouped into causal traces.

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
let traceCloseScheduled = false;

// Subscriber notifications
const subscribers = new Set<() => void>();
let pendingNotify = false;
let initialized = false;

// ─── Init / Cleanup ──────────────────────────────────────────────

export function init(): void {
  if (initialized) return;
  initialized = true;
}

export function cleanup(): void {
  initialized = false;
  buffer.length = 0;
  nextEventId = 0;
  nextTraceId = 0;
  activeTraceId = null;
  activeParentId = null;
  activeDepth = 0;
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
  scheduleTraceClose();
}

/** Schedule trace close at end of microtask queue. */
function scheduleTraceClose(): void {
  if (traceCloseScheduled) return;
  traceCloseScheduled = true;
  Promise.resolve().then(() => {
    traceCloseScheduled = false;
    // Don't close if an SSE request is still open — it will close on 'finished'
    if (activeTraceId !== null) {
      const hasOpenSse = buffer.some(
        e => e.traceId === activeTraceId &&
             e.type === "sse-lifecycle" &&
             (e.data as SseEventData).sseType === "started"
      ) && !buffer.some(
        e => e.traceId === activeTraceId &&
             e.type === "sse-lifecycle" &&
             ((e.data as SseEventData).sseType === "finished" ||
              (e.data as SseEventData).sseType === "error" ||
              (e.data as SseEventData).sseType === "retries-failed")
      );
      if (!hasOpenSse) {
        closeTrace();
      }
    }
  });
}

function closeTrace(): void {
  activeTraceId = null;
  activeParentId = null;
  activeDepth = 0;
}

// ─── Emit Events ──────────────────────────────────────────────────

/** Emit a timeline event. Assigns trace/parent IDs if a trace is active. */
export function emit(
  type: TimelineEventType,
  data: TimelineEventData,
  opts?: { beginTrace?: boolean; parentOverride?: number | null },
): TimelineEvent {
  const event: TimelineEvent = {
    id: nextEventId++,
    type,
    ts: performance.now(),
    wallTime: Date.now(),
    traceId: activeTraceId ?? nextTraceId,
    parentId: activeParentId,
    depth: activeDepth,
    data,
  };

  if (opts?.beginTrace) {
    beginTrace(event);
  } else if (activeTraceId === null) {
    // No active trace — start a new one implicitly
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
    let hasOpenSse = false;
    let hasClosedSse = false;

    for (const e of events) {
      switch (e.type) {
        case "signal-change": signalChanges++; break;
        case "effect-eval": effectEvals++; break;
        case "dom-mutation": domMutations++; break;
        case "sse-lifecycle": {
          sseEvents++;
          const sseType = (e.data as SseEventData).sseType;
          if (sseType === "started") hasOpenSse = true;
          if (sseType === "finished" || sseType === "error" || sseType === "retries-failed") {
            hasClosedSse = true;
          }
          break;
        }
        case "sse-malformed": malformedEvents++; break;
      }
    }

    const isComplete = !hasOpenSse || hasClosedSse;
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
      warnings: [], // Populated by detectWarnings() in task 7
      status: isStale ? "stale" : isComplete ? "complete" : "active",
    });
  }

  // Most recent first
  summaries.sort((a, b) => b.rootEvent.ts - a.rootEvent.ts);
  return summaries;
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
