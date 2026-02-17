import { getPath } from "datastar";
import { injectEvent } from "./debugger-capture.js";
const MAX_BYTES_PER_RESPONSE = 1048576;
const RAW_TEXT_MAX = 200;
const DATASTAR_EVENT_TYPES = /* @__PURE__ */ new Set([
  "datastar-patch-signals",
  "datastar-patch-elements",
  "datastar-execute-script"
]);
const VALID_SSE_FIELDS = /* @__PURE__ */ new Set([
  "event",
  "data",
  "id",
  "retry"
]);
const VALID_ELEMENT_MODES = /* @__PURE__ */ new Set([
  "outer",
  "inner",
  "replace",
  "prepend",
  "append",
  "before",
  "after",
  "remove"
]);
let originalFetch = null;
let activeCallback = null;
const encoder = new TextEncoder();
function install(callback) {
  if (originalFetch) return;
  activeCallback = callback;
  originalFetch = window.fetch;
  window.fetch = interceptedFetch;
}
function uninstall() {
  if (originalFetch) {
    window.fetch = originalFetch;
    originalFetch = null;
  }
  activeCallback = null;
}
function checkHeadersInit(headers) {
  if (headers instanceof Headers) {
    if (headers.has("Datastar-Request")) return true;
    if (headers.get("Accept") === "text/event-stream") return true;
  } else if (Array.isArray(headers)) {
    for (const [k, v] of headers) {
      if (k === "Datastar-Request") return true;
      if (k === "Accept" && v === "text/event-stream") return true;
    }
  } else {
    if ("Datastar-Request" in headers) return true;
    if (headers["Accept"] === "text/event-stream") return true;
  }
  return false;
}
function isDatastarSSERequest(input, init2) {
  if (init2?.headers && checkHeadersInit(init2.headers)) return true;
  if (input instanceof Request) {
    if (input.headers.has("Datastar-Request")) return true;
    if (input.headers.get("Accept") === "text/event-stream") return true;
  }
  return false;
}
function getRequestUrl(input) {
  if (typeof input === "string") return input;
  if (input instanceof URL) return input.href;
  return input.url;
}
async function interceptedFetch(input, init2) {
  if (!isDatastarSSERequest(input, init2) || !originalFetch) {
    return originalFetch(input, init2);
  }
  const url = getRequestUrl(input);
  let response;
  try {
    response = await originalFetch(input, init2);
  } catch (err) {
    throw err;
  }
  const ct = response.headers.get("Content-Type") ?? "";
  if (!ct.includes("text/event-stream")) {
    emitError({
      level: "error",
      code: "WRONG_CONTENT_TYPE",
      message: `Expected text/event-stream, got: ${ct}`,
      rawText: "",
      url,
      byteOffset: 0
    });
  }
  if (!response.body) return response;
  const [datastarCopy, validatorCopy] = response.body.tee();
  validateStream(validatorCopy, url);
  const proxied = new Response(datastarCopy, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers
  });
  Object.defineProperty(proxied, "url", { value: response.url });
  Object.defineProperty(proxied, "type", { value: response.type });
  Object.defineProperty(proxied, "redirected", { value: response.redirected });
  return proxied;
}
async function validateStream(stream, url) {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer2 = "";
  let totalBytes = 0;
  let byteOffset = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      totalBytes += value.byteLength;
      if (totalBytes > MAX_BYTES_PER_RESPONSE) {
        reader.cancel();
        break;
      }
      buffer2 += decoder.decode(value, { stream: true });
      let blankIdx;
      while ((blankIdx = buffer2.indexOf("\n\n")) !== -1) {
        const rawEvent = buffer2.slice(0, blankIdx);
        buffer2 = buffer2.slice(blankIdx + 2);
        if (rawEvent.trim()) {
          validateRawEvent(rawEvent, url, byteOffset);
        }
        byteOffset += encoder.encode(rawEvent).byteLength + 2;
      }
    }
    const remaining = buffer2.trim();
    if (remaining) {
      if (remaining.includes("event:") || remaining.includes("data:")) {
        emitError({
          level: "warning",
          code: "MISSING_TRAILING_BLANK_LINE",
          message: "Stream ended without trailing blank line after last event",
          rawText: remaining.slice(0, RAW_TEXT_MAX),
          url,
          byteOffset
        });
        validateRawEvent(remaining, url, byteOffset);
      }
    }
  } catch (err) {
    emitError({
      level: "error",
      code: "STREAM_ERROR",
      message: `Stream read failed: ${err instanceof Error ? err.message : String(err)}`,
      rawText: "",
      url,
      byteOffset
    });
  } finally {
    try {
      reader.releaseLock();
    } catch {
    }
  }
}
function validateRawEvent(raw, url, byteOffset) {
  const lines = raw.split("\n");
  let eventType = null;
  let eventTypeCount = 0;
  const dataLines = [];
  const truncated = raw.slice(0, RAW_TEXT_MAX);
  for (const line of lines) {
    if (line.startsWith(":")) continue;
    const colonIdx = line.indexOf(":");
    if (colonIdx === -1) continue;
    const field = line.slice(0, colonIdx);
    const value = line.slice(colonIdx + 1).trimStart();
    if (!VALID_SSE_FIELDS.has(field)) {
      emitError({
        level: "warning",
        code: "UNKNOWN_FIELD",
        message: `Unknown SSE field: "${field}"`,
        rawText: truncated,
        url,
        byteOffset
      });
    }
    if (field === "event") {
      eventType = value;
      eventTypeCount++;
    } else if (field === "data") {
      dataLines.push(value);
      if (/[\x00-\x08\x0B\x0E-\x1F\x7F]/.test(value)) {
        emitError({
          level: "error",
          code: "BINARY_DATA",
          message: "Data line contains binary/control characters",
          rawText: truncated,
          url,
          byteOffset
        });
      }
    }
  }
  if (eventTypeCount > 1) {
    emitError({
      level: "error",
      code: "MERGED_EVENTS",
      message: `Found ${eventTypeCount} event: lines in one block — missing blank line separator`,
      rawText: truncated,
      url,
      byteOffset
    });
    return;
  }
  if (!eventType && dataLines.length > 0) {
    emitError({
      level: "error",
      code: "MISSING_EVENT_TYPE",
      message: "Event has data lines but no event: type line",
      rawText: truncated,
      url,
      byteOffset
    });
    return;
  }
  if (!eventType) return;
  if (!DATASTAR_EVENT_TYPES.has(eventType)) {
    emitError({
      level: "warning",
      code: "NON_DATASTAR_EVENT",
      message: `Unknown event type: "${eventType}"`,
      rawText: truncated,
      url,
      byteOffset
    });
    return;
  }
  if (eventType === "datastar-patch-signals") {
    validateSignalsData(dataLines, truncated, url, byteOffset);
  } else if (eventType === "datastar-patch-elements") {
    validateElementsData(dataLines, truncated, url, byteOffset);
  }
}
function validateSignalsData(dataLines, rawText, url, byteOffset) {
  let hasSignals = false;
  for (const line of dataLines) {
    if (line.startsWith("signals ")) {
      hasSignals = true;
      const json = line.slice("signals ".length);
      try {
        const parsed = JSON.parse(json);
        if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
          emitError({
            level: "error",
            code: "INVALID_SIGNALS_JSON",
            message: "Signals data must be a JSON object",
            rawText,
            url,
            byteOffset
          });
        }
      } catch {
        emitError({
          level: "error",
          code: "INVALID_SIGNALS_JSON",
          message: `Invalid JSON in signals data: ${json.slice(0, 80)}`,
          rawText,
          url,
          byteOffset
        });
      }
    }
  }
  if (!hasSignals) {
    emitError({
      level: "error",
      code: "MISSING_SIGNALS_DATA",
      message: "datastar-patch-signals event missing 'signals' data key",
      rawText,
      url,
      byteOffset
    });
  }
}
function validateElementsData(dataLines, rawText, url, byteOffset) {
  let hasElements = false;
  let elementContent = "";
  for (const line of dataLines) {
    if (line.startsWith("elements ")) {
      hasElements = true;
      elementContent += line.slice("elements ".length);
    } else if (line.startsWith("mode ")) {
      const mode = line.slice("mode ".length).trim();
      if (!VALID_ELEMENT_MODES.has(mode)) {
        emitError({
          level: "error",
          code: "INVALID_ELEMENT_MODE",
          message: `Invalid mode: "${mode}". Valid: ${[...VALID_ELEMENT_MODES].join(", ")}`,
          rawText,
          url,
          byteOffset
        });
      }
    }
  }
  if (!hasElements) {
    emitError({
      level: "error",
      code: "MISSING_ELEMENTS_DATA",
      message: "datastar-patch-elements event missing 'elements' data key",
      rawText,
      url,
      byteOffset
    });
  } else if (!elementContent.trim()) {
    emitError({
      level: "warning",
      code: "EMPTY_FRAGMENT",
      message: "Elements event has empty fragment content",
      rawText,
      url,
      byteOffset
    });
  }
}
function emitError(error) {
  if (activeCallback) activeCallback(error);
}
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
let activeTraceRootType = null;
let traceCloseScheduled = false;
let sseElTraces = /* @__PURE__ */ new WeakMap();
const subscribers = /* @__PURE__ */ new Set();
let pendingNotify = false;
let initialized = false;
let sseListener = null;
function captureSSELifecycle() {
  sseListener = (e) => {
    const { type, el, argsRaw } = e.detail;
    const debugMeta = argsRaw?.["x-debug-seq"] != null ? {
      seq: Number(argsRaw["x-debug-seq"]),
      handler: String(argsRaw["x-debug-handler"] ?? ""),
      route: String(argsRaw["x-debug-route"] ?? "")
    } : void 0;
    const payload = {};
    if (argsRaw) {
      for (const [k, v] of Object.entries(argsRaw)) {
        if (!k.startsWith("x-debug-")) payload[k] = v;
      }
    }
    const sseData = {
      sseType: type,
      handler: debugMeta?.handler ?? "",
      route: debugMeta?.route ?? "",
      seq: debugMeta?.seq ?? 0,
      payload,
      elSelector: el ? selectorFor(el) : ""
    };
    if (type === "started") {
      const isNewTrace = activeTraceId === null;
      const event = emit("sse-lifecycle", sseData, { beginTrace: isNewTrace });
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
      if (type === "finished" || type === "error" || type === "retries-failed") {
        if (el) sseElTraces.delete(el);
      }
    }
  };
  document.addEventListener("datastar-fetch", sseListener);
}
const DEBUGGER_TAG = "STARHTML-DEBUGGER";
const USER_ACTION_EVENTS = ["click", "input", "submit", "keydown"];
let userActionListeners = [];
function isInsideDebugger(el) {
  let node = el;
  while (node) {
    if (node.tagName === DEBUGGER_TAG) return true;
    node = node.parentElement;
  }
  const root = el.getRootNode();
  if (root instanceof ShadowRoot && root.host?.tagName === DEBUGGER_TAG) return true;
  return false;
}
function captureUserActions() {
  for (const eventType of USER_ACTION_EVENTS) {
    const fn = (e) => {
      const target = e.target;
      if (!(target instanceof Element)) return;
      if (isInsideDebugger(target)) return;
      if (eventType !== "click") {
        const attrName = `data-on-${eventType}`;
        if (!target.hasAttribute(attrName) && !target.closest(`[${attrName}]`)) return;
      }
      let datastarAction = null;
      const actionEl = target.closest(`[data-on-${eventType}]`) ?? target;
      const actionAttr = actionEl.getAttribute(`data-on-${eventType}`);
      if (actionAttr) datastarAction = actionAttr.slice(0, 100);
      const data = {
        eventType,
        targetSelector: selectorFor(target),
        targetText: (target.textContent ?? "").trim().slice(0, 40),
        datastarAction
      };
      emit("user-action", data, { beginTrace: true });
    };
    document.addEventListener(eventType, fn, true);
    userActionListeners.push({ type: eventType, fn });
  }
}
let signalPatchListener = null;
function flattenPaths(obj, prefix, out) {
  if (obj && typeof obj === "object" && !Array.isArray(obj)) {
    for (const [k, v] of Object.entries(obj)) {
      const path = prefix ? `${prefix}.${k}` : k;
      if (v && typeof v === "object" && !Array.isArray(v)) {
        flattenPaths(v, path, out);
      } else {
        out.push(path);
      }
    }
  }
}
function captureSignalChanges() {
  const prevValues = /* @__PURE__ */ new Map();
  signalPatchListener = (e) => {
    const detail = e.detail;
    if (!detail || typeof detail !== "object") return;
    const paths = [];
    flattenPaths(detail, "", paths);
    let source = "init";
    if (activeTraceRootType === "sse-lifecycle") source = "sse";
    else if (activeTraceRootType === "user-action") source = "user";
    for (const path of paths) {
      if (path.startsWith("starhtml_debugger")) continue;
      let newValue;
      try {
        newValue = getPath(path);
      } catch {
        continue;
      }
      const oldValue = prevValues.get(path);
      if (oldValue === newValue) continue;
      if (typeof oldValue === "object" && typeof newValue === "object") {
        try {
          if (JSON.stringify(oldValue) === JSON.stringify(newValue)) continue;
        } catch {
        }
      }
      prevValues.set(path, newValue);
      const data = {
        path,
        oldValue: clampValue(oldValue),
        newValue: clampValue(newValue),
        source
      };
      emit("signal-change", data);
    }
  };
  document.addEventListener("datastar-signal-patch", signalPatchListener);
}
function captureMalformedSSE() {
  install((error) => {
    const data = {
      level: error.level,
      code: error.code,
      message: error.message,
      rawText: error.rawText,
      url: error.url,
      byteOffset: error.byteOffset
    };
    emit("sse-malformed", data);
    injectEvent({
      type: "sse-malformed",
      timestamp: Date.now(),
      el: null,
      argsRaw: {
        level: error.level,
        code: error.code,
        message: error.message,
        rawText: error.rawText,
        url: error.url,
        byteOffset: error.byteOffset
      }
    });
  });
}
function init() {
  if (initialized) return;
  initialized = true;
  captureSSELifecycle();
  captureUserActions();
  captureSignalChanges();
  captureMalformedSSE();
}
function cleanup() {
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
  uninstall();
  initialized = false;
  buffer.length = 0;
  nextEventId = 0;
  nextTraceId = 0;
  activeTraceId = null;
  activeParentId = null;
  activeDepth = 0;
  activeTraceRootType = null;
  sseElTraces = /* @__PURE__ */ new WeakMap();
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
  activeTraceRootType = rootEvent.type;
  scheduleTraceClose();
}
function scheduleTraceClose() {
  if (traceCloseScheduled) return;
  traceCloseScheduled = true;
  Promise.resolve().then(() => {
    traceCloseScheduled = false;
    if (activeTraceId !== null) {
      let startedCount = 0;
      let finishedCount = 0;
      for (const e of buffer) {
        if (e.traceId === activeTraceId && e.type === "sse-lifecycle") {
          const sseType = e.data.sseType;
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
function closeTrace() {
  activeTraceId = null;
  activeParentId = null;
  activeDepth = 0;
  activeTraceRootType = null;
}
function resumeTrace(traceId, parentId, rootType) {
  if (activeTraceId !== null && activeTraceId !== traceId) {
    closeTrace();
  }
  activeTraceId = traceId;
  activeParentId = parentId;
  activeDepth = 1;
  activeTraceRootType = rootType;
  traceCloseScheduled = false;
  scheduleTraceClose();
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
    let sseStarted = 0;
    let sseFinished = 0;
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
          if (sseType === "started") sseStarted++;
          else if (sseType === "finished" || sseType === "error" || sseType === "retries-failed") sseFinished++;
          break;
        }
        case "sse-malformed":
          malformedEvents++;
          break;
      }
    }
    const isComplete = sseStarted === 0 || sseStarted <= sseFinished;
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
