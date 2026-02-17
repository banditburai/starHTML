const MAX_EVENTS = 5e3;
const PRESERVE_FIRST = 500;
const STALE_TRACE_MS = 5e3;
const MAX_VALUE_SIZE = 1024;
const buffer = [];
let nextEventId = 0;
let nextTraceId = 0;
let activeTraceId = null;
let activeParentId = null;
let activeDepth = 0;
let traceCloseScheduled = false;
const subscribers = /* @__PURE__ */ new Set();
let pendingNotify = false;
let initialized = false;
function init() {
  if (initialized) return;
  initialized = true;
}
function cleanup() {
  initialized = false;
  buffer.length = 0;
  nextEventId = 0;
  nextTraceId = 0;
  activeTraceId = null;
  activeParentId = null;
  activeDepth = 0;
  subscribers.clear();
}
function subscribe(fn) {
  subscribers.add(fn);
  return () => subscribers.delete(fn);
}
function notifySubscribers() {
  if (pendingNotify) return;
  pendingNotify = true;
  queueMicrotask(() => {
    pendingNotify = false;
    for (const fn of subscribers) fn();
  });
}
function addToBuffer(event) {
  buffer.push(event);
  if (buffer.length > MAX_EVENTS) {
    const excess = buffer.length - MAX_EVENTS;
    buffer.splice(PRESERVE_FIRST, excess);
  }
  notifySubscribers();
}
function beginTrace(rootEvent) {
  const tid = nextTraceId++;
  rootEvent.traceId = tid;
  rootEvent.parentId = null;
  rootEvent.depth = 0;
  activeTraceId = tid;
  activeParentId = rootEvent.id;
  activeDepth = 1;
  scheduleTraceClose();
}
function scheduleTraceClose() {
  if (traceCloseScheduled) return;
  traceCloseScheduled = true;
  Promise.resolve().then(() => {
    traceCloseScheduled = false;
    if (activeTraceId !== null) {
      const hasOpenSse = buffer.some(
        (e) => e.traceId === activeTraceId && e.type === "sse-lifecycle" && e.data.sseType === "started"
      ) && !buffer.some(
        (e) => e.traceId === activeTraceId && e.type === "sse-lifecycle" && (e.data.sseType === "finished" || e.data.sseType === "error" || e.data.sseType === "retries-failed")
      );
      if (!hasOpenSse) {
        closeTrace();
      }
    }
  });
}
function closeTrace() {
  activeTraceId = null;
  activeParentId = null;
  activeDepth = 0;
}
function emit(type, data, opts) {
  const isOrphan = activeTraceId === null && !opts?.beginTrace;
  const orphanTraceId = isOrphan ? nextTraceId++ : void 0;
  const event = {
    id: nextEventId++,
    type,
    ts: performance.now(),
    wallTime: Date.now(),
    traceId: orphanTraceId ?? activeTraceId ?? nextTraceId,
    parentId: isOrphan ? null : activeParentId,
    depth: isOrphan ? 0 : activeDepth,
    data
  };
  if (opts?.beginTrace) {
    beginTrace(event);
  }
  if (opts?.parentOverride !== void 0) {
    event.parentId = opts.parentOverride;
  }
  addToBuffer(event);
  return event;
}
function pushParent(event) {
  const prevParentId = activeParentId;
  const prevDepth = activeDepth;
  activeParentId = event.id;
  activeDepth++;
  return () => {
    activeParentId = prevParentId;
    activeDepth = prevDepth;
  };
}
function getEvents() {
  return buffer;
}
function getTraceEvents(traceId) {
  return buffer.filter((e) => e.traceId === traceId);
}
function getTraceCount() {
  const ids = /* @__PURE__ */ new Set();
  for (const e of buffer) ids.add(e.traceId);
  return ids.size;
}
function getTraces() {
  const traceMap = /* @__PURE__ */ new Map();
  for (const e of buffer) {
    let arr = traceMap.get(e.traceId);
    if (!arr) {
      arr = [];
      traceMap.set(e.traceId, arr);
    }
    arr.push(e);
  }
  const now = performance.now();
  const summaries = [];
  for (const [traceId, events] of traceMap) {
    const root = events.find((e) => e.parentId === null) ?? events[0];
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
        case "signal-change":
          signalChanges++;
          break;
        case "effect-eval":
          effectEvals++;
          break;
        case "dom-mutation":
          domMutations++;
          break;
        case "sse-lifecycle": {
          sseEvents++;
          const sseType = e.data.sseType;
          if (sseType === "started") hasOpenSse = true;
          if (sseType === "finished" || sseType === "error" || sseType === "retries-failed") {
            hasClosedSse = true;
          }
          break;
        }
        case "sse-malformed":
          malformedEvents++;
          break;
      }
    }
    const isComplete = !hasOpenSse || hasClosedSse;
    const isStale = !isComplete && now - lastTs > STALE_TRACE_MS;
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
      warnings: [],
      // Populated by detectWarnings() in task 7
      status: isStale ? "stale" : isComplete ? "complete" : "active"
    });
  }
  summaries.sort((a, b) => b.rootEvent.ts - a.rootEvent.ts);
  return summaries;
}
function selectorFor(el) {
  if (el.id) return `#${el.id}`;
  const tag = el.tagName.toLowerCase();
  const cls = el.className && typeof el.className === "string" ? "." + el.className.trim().split(/\s+/).slice(0, 2).join(".") : "";
  return tag + cls;
}
function clampValue(value) {
  if (value === null || value === void 0) return value;
  try {
    const s = JSON.stringify(value);
    if (s.length <= MAX_VALUE_SIZE) return value;
    if (typeof value === "string") return value.slice(0, MAX_VALUE_SIZE) + "...";
    if (Array.isArray(value)) return `[${value.length} items]`;
    if (typeof value === "object") return `{${Object.keys(value).length} keys}`;
    return value;
  } catch {
    return String(value).slice(0, MAX_VALUE_SIZE);
  }
}
function formatTime(wallTime) {
  const d = new Date(wallTime);
  const h = String(d.getHours()).padStart(2, "0");
  const m = String(d.getMinutes()).padStart(2, "0");
  const s = String(d.getSeconds()).padStart(2, "0");
  const ms = String(d.getMilliseconds()).padStart(3, "0");
  return `${h}:${m}:${s}.${ms}`;
}
function describeRootCause(event) {
  switch (event.type) {
    case "user-action": {
      const d = event.data;
      return `${d.eventType} ${d.targetSelector}`;
    }
    case "sse-lifecycle": {
      const d = event.data;
      return `SSE ${d.handler || d.route || d.sseType}`;
    }
    case "signal-change": {
      const d = event.data;
      return `signal ${d.path}`;
    }
    case "sse-malformed": {
      const d = event.data;
      return `malformed SSE: ${d.code}`;
    }
    default:
      return event.type;
  }
}
function summarizeTrace(trace) {
  const parts = [];
  if (trace.sseEvents > 0) parts.push(`${trace.sseEvents} SSE`);
  if (trace.signalChanges > 0) parts.push(`${trace.signalChanges} signal${trace.signalChanges > 1 ? "s" : ""}`);
  if (trace.effectEvals > 0) parts.push(`${trace.effectEvals} effect${trace.effectEvals > 1 ? "s" : ""}`);
  if (trace.domMutations > 0) parts.push(`${trace.domMutations} DOM`);
  if (trace.malformedEvents > 0) parts.push(`${trace.malformedEvents} malformed`);
  return parts.join(", ") || "no effects";
}
function getActiveTraceId() {
  return activeTraceId;
}
function getEventCount() {
  return buffer.length;
}
export {
  beginTrace,
  clampValue,
  cleanup,
  describeRootCause,
  emit,
  formatTime,
  getActiveTraceId,
  getEventCount,
  getEvents,
  getTraceCount,
  getTraceEvents,
  getTraces,
  init,
  pushParent,
  selectorFor,
  subscribe,
  summarizeTrace
};
