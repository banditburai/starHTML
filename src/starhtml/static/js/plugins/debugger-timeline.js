import { getPath } from "datastar";
import { injectEvent } from "./debugger-capture.js";
import { getEntries } from "./debugger-signals.js";
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
      warnings: detectWarnings(events),
      status: isStale ? "stale" : isComplete ? "complete" : "active"
    });
  }
  summaries.sort((a, b) => b.rootEvent.ts - a.rootEvent.ts);
  return summaries;
}
const EXCESSIVE_EFFECTS_THRESHOLD = 15;
const PING_PONG_THRESHOLD = 3;
const MORPH_WINDOW_MS = 100;
function detectWarnings(events) {
  const warnings = [];
  detectSignalPingPong(events, warnings);
  detectExcessiveEffects(events, warnings);
  detectHangingRequest(events, warnings);
  detectSelectorRace(events, warnings);
  detectNoMorphs(events, warnings);
  detectAttributeFlash(events, warnings);
  return warnings;
}
function detectSignalPingPong(events, out) {
  const counts = /* @__PURE__ */ new Map();
  for (const e of events) {
    if (e.type === "signal-change") {
      const path = e.data.path;
      counts.set(path, (counts.get(path) ?? 0) + 1);
    }
  }
  for (const [path, count] of counts) {
    if (count >= PING_PONG_THRESHOLD) {
      out.push({
        code: "SIGNAL_PING_PONG",
        message: `Signal "${path}" changed ${count} times in this trace`
      });
    }
  }
}
function detectExcessiveEffects(events, out) {
  let count = 0;
  for (const e of events) {
    if (e.type === "effect-eval") count++;
  }
  if (count > EXCESSIVE_EFFECTS_THRESHOLD) {
    out.push({
      code: "EXCESSIVE_EFFECTS",
      message: `${count} effect evaluations in this trace (threshold: ${EXCESSIVE_EFFECTS_THRESHOLD})`
    });
  }
}
function detectHangingRequest(events, out) {
  const started = /* @__PURE__ */ new Map();
  const finished = /* @__PURE__ */ new Set();
  for (const e of events) {
    if (e.type !== "sse-lifecycle") continue;
    const d = e.data;
    if (d.sseType === "started") {
      started.set(d.elSelector || String(e.id), e);
    } else if (d.sseType === "finished" || d.sseType === "error" || d.sseType === "retries-failed") {
      finished.add(d.elSelector || String(e.id));
    }
  }
  const now = performance.now();
  for (const [key, startEvent] of started) {
    if (!finished.has(key) && now - startEvent.ts > STALE_TRACE_MS) {
      const d = startEvent.data;
      out.push({
        code: "HANGING_REQUEST",
        message: `SSE request to ${d.route || d.handler || "unknown"} started ${Math.round((now - startEvent.ts) / 1e3)}s ago with no response`
      });
    }
  }
}
function detectSelectorRace(events, out) {
  const selectorCounts = /* @__PURE__ */ new Map();
  for (const e of events) {
    if (e.type !== "sse-lifecycle") continue;
    const d = e.data;
    if (d.payload?.selector) {
      const sel = String(d.payload.selector);
      selectorCounts.set(sel, (selectorCounts.get(sel) ?? 0) + 1);
    }
  }
  for (const [sel, count] of selectorCounts) {
    if (count >= 2) {
      out.push({
        code: "SELECTOR_RACE",
        message: `${count} elements events targeted "${sel}" in this trace`
      });
    }
  }
}
function detectNoMorphs(events, out) {
  const now = performance.now();
  for (let i = 0; i < events.length; i++) {
    const e = events[i];
    if (e.type !== "sse-lifecycle") continue;
    const d = e.data;
    if (d.sseType !== "datastar-patch-elements") continue;
    if (now - e.ts < MORPH_WINDOW_MS) continue;
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
        message: `Elements event targeting "${sel}" produced zero DOM mutations`
      });
    }
  }
}
function detectAttributeFlash(events, out) {
  const domEvents = events.filter((e) => e.type === "dom-mutation");
  if (domEvents.length < 2) return;
  const attrChanges = /* @__PURE__ */ new Map();
  for (let i = 0; i < domEvents.length; i++) {
    const d = domEvents[i].data;
    if (d.mutationType !== "attributes" || !d.attributeName) continue;
    const key = `${d.targetSelector}[${d.attributeName}]`;
    attrChanges.set(key, (attrChanges.get(key) ?? 0) + 1);
  }
  for (const [key, count] of attrChanges) {
    if (count >= 2) {
      out.push({
        code: "ATTRIBUTE_FLASH",
        message: `Attribute ${key} changed ${count} times in this trace`
      });
    }
  }
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
const ESCAPE_MAP = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ESCAPE_MAP[c]);
}
function rootTypeCategory(event) {
  switch (event.type) {
    case "user-action":
      return "user";
    case "sse-lifecycle":
      return "sse";
    case "signal-change":
      return "signal";
    case "sse-malformed":
      return "warning";
    default:
      return "other";
  }
}
function traceMatchesChips(trace, activeChips) {
  if (activeChips.size === 0) return true;
  const cat = rootTypeCategory(trace.rootEvent);
  if (activeChips.has(cat)) return true;
  if (activeChips.has("warning") && trace.warnings.length > 0) return true;
  return false;
}
function buildTraceRowHtml(trace) {
  const time = formatTime(trace.rootEvent.wallTime);
  const cause = escapeHtml(describeRootCause(trace.rootEvent));
  const summary = escapeHtml(summarizeTrace(trace));
  const dur = trace.totalDuration >= 1e3 ? (trace.totalDuration / 1e3).toFixed(1) + "s" : Math.round(trace.totalDuration) + "ms";
  const warnBadge = trace.warnings.length > 0 ? ` <span class="tl-warn-badge">⚠ ${trace.warnings.length}</span>` : "";
  const statusCls = "tl-status-" + trace.status;
  const iconCls = {
    "user-action": "tl-type-user",
    "sse-lifecycle": "tl-type-sse",
    "signal-change": "tl-type-signal",
    "sse-malformed": "tl-type-malformed"
  }[trace.rootEvent.type] ?? "tl-type-other";
  return `<div class="timeline-row ${statusCls}" data-trace-id="${trace.traceId}"><span class="tl-type-icon ${iconCls}">●</span><span class="tl-time">${time}</span><span class="tl-cause">${cause}</span><span class="tl-arrow">→</span><span class="tl-summary">${summary}</span><span class="tl-duration">${dur}</span>` + warnBadge + `</div>`;
}
const PHASE_LABELS = {
  trigger: "Trigger",
  sse: "SSE",
  signal: "Signals",
  dom: "DOM",
  warning: "Warnings",
  finished: "Finished",
  other: "Other"
};
function eventPhase(e) {
  switch (e.type) {
    case "user-action":
      return "trigger";
    case "sse-lifecycle": {
      const d = e.data;
      return d.sseType === "finished" || d.sseType === "error" || d.sseType === "retries-failed" ? "finished" : "sse";
    }
    case "signal-change":
      return "signal";
    case "effect-eval":
      return "signal";
    case "dom-mutation":
      return "dom";
    case "sse-malformed":
      return "warning";
    default:
      return "other";
  }
}
function formatEventLine(e, baseTs) {
  const offset = `+${Math.round(e.ts - baseTs)}ms`;
  const offsetHtml = `<span class="tl-ev-offset">${offset}</span>`;
  switch (e.type) {
    case "user-action": {
      const d = e.data;
      return `${offsetHtml} <span class="tl-ev-type tl-type-user">${escapeHtml(d.eventType)}</span> <span class="tl-ev-target">${escapeHtml(d.targetSelector)}</span>` + (d.datastarAction ? ` <span class="tl-ev-action">${escapeHtml(d.datastarAction)}</span>` : "");
    }
    case "sse-lifecycle": {
      const d = e.data;
      const label = d.sseType === "started" ? "SSE start" : d.sseType;
      return `${offsetHtml} <span class="tl-ev-type tl-type-sse">${escapeHtml(label)}</span> ` + (d.route ? `<span class="tl-ev-route">${escapeHtml(d.route)}</span> ` : "") + (d.handler ? `<span class="tl-ev-handler">${escapeHtml(d.handler)}</span>` : "");
    }
    case "signal-change": {
      const d = e.data;
      const oldStr = JSON.stringify(d.oldValue) ?? "undefined";
      const newStr = JSON.stringify(d.newValue) ?? "undefined";
      return `${offsetHtml} <span class="tl-ev-type tl-type-signal">${escapeHtml(d.path)}</span> <span class="tl-ev-old">${escapeHtml(oldStr)}</span> → <span class="tl-ev-new">${escapeHtml(newStr)}</span> <span class="tl-ev-source">(${escapeHtml(d.source)})</span>`;
    }
    case "effect-eval": {
      const d = e.data;
      return `${offsetHtml} <span class="tl-ev-type tl-type-signal">effect</span> <span class="tl-ev-label">${escapeHtml(d.label || `#${d.effectId}`)}</span> <span class="tl-ev-dur">${d.duration.toFixed(1)}ms</span>`;
    }
    case "dom-mutation": {
      const d = e.data;
      let detail = escapeHtml(d.targetSelector);
      if (d.mutationType === "attributes" && d.attributeName) {
        detail += ` [${escapeHtml(d.attributeName)}]`;
        if (d.oldValue != null || d.newValue != null) {
          detail += ` ${escapeHtml(d.oldValue ?? "")} → ${escapeHtml(d.newValue ?? "")}`;
        }
      } else if (d.mutationType === "childList") {
        if (d.addedNodes.length) detail += ` +${d.addedNodes.length}`;
        if (d.removedNodes.length) detail += ` -${d.removedNodes.length}`;
      }
      return `${offsetHtml} <span class="tl-ev-type tl-type-dom">${escapeHtml(d.mutationType)}</span> ${detail}`;
    }
    case "sse-malformed": {
      const d = e.data;
      return `${offsetHtml} <span class="tl-ev-type tl-type-malformed">${escapeHtml(d.code)}</span> <span class="tl-ev-msg">${escapeHtml(d.message)}</span>`;
    }
    default:
      return `${offsetHtml} <span class="tl-ev-type">${e.type}</span>`;
  }
}
function summarizeCycles(events) {
  if (events.length < 8) return null;
  const signalEvents = events.filter((e) => e.type === "signal-change");
  if (signalEvents.length < 6) return null;
  const paths = signalEvents.map((e) => e.data.path);
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
      const cycle = pattern.join(" → ");
      return {
        summarized: [`<span class="tl-ev-cycle">${escapeHtml(cycle)} … ${repeats} cycles</span>`],
        truncated: signalEvents.length - 2
        // show first + last
      };
    }
  }
  return null;
}
const MAX_DETAIL_EVENTS = 100;
function buildTraceDetailHtml(traceId) {
  const events = getTraceEvents(traceId);
  if (events.length === 0) return '<div class="tl-detail-empty">No events</div>';
  const baseTs = events[0].ts;
  const cycles = summarizeCycles(events);
  let html = '<div class="tl-detail">';
  let currentPhase = "";
  let shown = 0;
  const truncate = events.length > MAX_DETAIL_EVENTS && !cycles;
  for (let i = 0; i < events.length; i++) {
    if (truncate && shown >= MAX_DETAIL_EVENTS) break;
    const e = events[i];
    const phase = eventPhase(e);
    if (phase !== currentPhase) {
      if (currentPhase) html += "</div>";
      currentPhase = phase;
      const label = PHASE_LABELS[phase] ?? phase;
      const phaseCls = `tl-phase-${phase}`;
      html += `<div class="tl-phase ${phaseCls}"><div class="tl-phase-label">${label}</div>`;
    }
    if (cycles && phase === "signal" && shown === 0) {
      for (const line of cycles.summarized) {
        html += `<div class="tl-ev-line tl-ev-indent">${line}</div>`;
      }
      html += `<div class="tl-ev-line tl-ev-indent">${formatEventLine(events.find((ev) => ev.type === "signal-change"), baseTs)}</div>`;
      const lastSig = [...events].reverse().find((ev) => ev.type === "signal-change");
      if (lastSig && lastSig !== events.find((ev) => ev.type === "signal-change")) {
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
  if (truncate) {
    html += `<div class="tl-truncated">Showing ${MAX_DETAIL_EVENTS} of ${events.length} events</div>`;
  }
  const trace = getTraces().find((t) => t.traceId === traceId);
  if (trace && trace.warnings.length > 0) {
    html += '<div class="tl-phase tl-phase-warning"><div class="tl-phase-label">Warnings</div>';
    for (const w of trace.warnings) {
      html += `<div class="tl-ev-line tl-ev-warn">⚠ <span class="tl-warn-code">${escapeHtml(w.code)}</span> ${escapeHtml(w.message)}</div>`;
    }
    html += "</div>";
  }
  html += "</div>";
  return html;
}
function buildFullTraceText(traceId) {
  const events = getTraceEvents(traceId);
  if (events.length === 0) return "No events in trace.";
  const baseTs = events[0].ts;
  const lines = [];
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
        const d = e.data;
        detail = `${d.eventType} ${d.targetSelector}${d.datastarAction ? ` → ${d.datastarAction}` : ""}`;
        break;
      }
      case "sse-lifecycle": {
        const d = e.data;
        detail = `SSE ${d.sseType}${d.route ? ` ${d.route}` : ""}${d.handler ? ` (${d.handler})` : ""}`;
        break;
      }
      case "signal-change": {
        const d = e.data;
        detail = `signal ${d.path}: ${JSON.stringify(d.oldValue)} → ${JSON.stringify(d.newValue)} (${d.source})`;
        break;
      }
      case "effect-eval": {
        const d = e.data;
        detail = `effect ${d.label || `#${d.effectId}`} ${d.duration.toFixed(1)}ms`;
        break;
      }
      case "dom-mutation": {
        const d = e.data;
        detail = `DOM ${d.mutationType} ${d.targetSelector}`;
        if (d.attributeName) detail += ` [${d.attributeName}]`;
        break;
      }
      case "sse-malformed": {
        const d = e.data;
        detail = `malformed ${d.code}: ${d.message}`;
        break;
      }
      default:
        detail = e.type;
    }
    lines.push(`${offset} ${indent}${detail}`);
  }
  const trace = getTraces().find((t) => t.traceId === traceId);
  if (trace && trace.warnings.length > 0) {
    lines.push("");
    lines.push("Warnings:");
    for (const w of trace.warnings) {
      lines.push(`  ⚠ ${w.code}: ${w.message}`);
    }
  }
  return lines.join("\n");
}
function buildFullTraceHtml(traceId) {
  const text = buildFullTraceText(traceId);
  return `<div class="tl-full-trace"><button class="tl-copy-btn" data-copy-trace="${traceId}">Copy</button><pre class="tl-full-pre">${escapeHtml(text)}</pre></div>`;
}
function getFilteredTraces(textFilter, chipFilter) {
  const traces = getTraces();
  traces.reverse();
  const filter = textFilter.toLowerCase();
  return traces.filter((t) => {
    if (!traceMatchesChips(t, chipFilter)) return false;
    if (!filter) return true;
    const cause = describeRootCause(t.rootEvent).toLowerCase();
    const summary = summarizeTrace(t).toLowerCase();
    const events = getTraceEvents(t.traceId);
    for (const e of events) {
      if (e.type === "signal-change") {
        if (e.data.path.toLowerCase().includes(filter)) return true;
      }
      if (e.type === "sse-lifecycle") {
        const d = e.data;
        if (d.route.toLowerCase().includes(filter)) return true;
        if (d.handler.toLowerCase().includes(filter)) return true;
      }
    }
    return cause.includes(filter) || summary.includes(filter);
  });
}
const SINGLE_TRACE_SIZE_LIMIT = 5 * 1024;
const MULTI_TRACE_SIZE_LIMIT = 20 * 1024;
const EXPORT_HARD_CAP = 20 * 1024;
const TRUNCATE_PAYLOAD = 200;
function formatLegend() {
  return [
    "**Legend:** `[signals]` = signal patch, `[elements]` = DOM morph, `[start]`/`[done]` = SSE lifecycle,",
    "`[click]`/`[input]` = user action, `[effect]` = reactive effect, `[malformed]` = SSE validation error"
  ].join("\n");
}
function formatSignalSnapshot() {
  let entries;
  try {
    entries = new Map(getEntries());
  } catch {
    return "";
  }
  if (entries.size === 0) return "";
  const lines = ["", "### Signal Snapshot", ""];
  const namespaces = /* @__PURE__ */ new Map();
  for (const entry of entries.values()) {
    if (entry.status === "removed") continue;
    const ns = entry.namespace || "(global)";
    let arr = namespaces.get(ns);
    if (!arr) {
      arr = [];
      namespaces.set(ns, arr);
    }
    arr.push(entry);
  }
  for (const [ns, nsEntries] of namespaces) {
    lines.push(`**${ns}**`);
    for (const e of nsEntries) {
      const val = JSON.stringify(e.value);
      const valStr = val && val.length > TRUNCATE_PAYLOAD ? val.slice(0, TRUNCATE_PAYLOAD) + "..." : val;
      lines.push(`- \`${e.path}\` = \`${valStr ?? "undefined"}\` (${e.type}${e.persistStorage ? `, persist:${e.persistStorage}` : ""})`);
    }
    lines.push("");
  }
  return lines.join("\n");
}
function formatEventExport(e, baseTs) {
  const offset = `[+${Math.round(e.ts - baseTs)}ms]`;
  const indent = "  ".repeat(e.depth);
  switch (e.type) {
    case "user-action": {
      const d = e.data;
      return `${offset} ${indent}[${d.eventType}] \`${d.targetSelector}\`${d.datastarAction ? ` → \`${d.datastarAction}\`` : ""}`;
    }
    case "sse-lifecycle": {
      const d = e.data;
      const tag = d.sseType === "started" ? "[start]" : d.sseType === "finished" || d.sseType === "error" || d.sseType === "retries-failed" ? "[done]" : `[${d.sseType}]`;
      let payload = "";
      if (d.payload && Object.keys(d.payload).length > 0) {
        const raw = JSON.stringify(d.payload);
        payload = raw.length > TRUNCATE_PAYLOAD ? ` ${raw.slice(0, TRUNCATE_PAYLOAD)}...` : ` ${raw}`;
      }
      return `${offset} ${indent}${tag} \`${d.route || d.handler || "SSE"}\`${payload}`;
    }
    case "signal-change": {
      const d = e.data;
      const oldStr = JSON.stringify(d.oldValue) ?? "undefined";
      const newStr = JSON.stringify(d.newValue) ?? "undefined";
      return `${offset} ${indent}[signals] \`${d.path}\`: \`${oldStr}\` → \`${newStr}\` (${d.source})`;
    }
    case "effect-eval": {
      const d = e.data;
      return `${offset} ${indent}[effect] ${d.label || `#${d.effectId}`} (${d.duration.toFixed(1)}ms)`;
    }
    case "dom-mutation": {
      const d = e.data;
      let detail = `\`${d.targetSelector}\``;
      if (d.mutationType === "attributes" && d.attributeName) {
        detail += ` [${d.attributeName}]`;
      } else if (d.mutationType === "childList") {
        if (d.addedNodes.length) detail += ` +${d.addedNodes.length}`;
        if (d.removedNodes.length) detail += ` -${d.removedNodes.length}`;
      }
      return `${offset} ${indent}[elements] ${d.mutationType} ${detail}`;
    }
    case "sse-malformed": {
      const d = e.data;
      return `${offset} ${indent}[malformed] ${d.code}: ${d.message}`;
    }
    default:
      return `${offset} ${indent}[${e.type}]`;
  }
}
function formatSignalDiff(events) {
  const firstSeen = /* @__PURE__ */ new Map();
  const lastSeen = /* @__PURE__ */ new Map();
  for (const e of events) {
    if (e.type !== "signal-change") continue;
    const d = e.data;
    if (!firstSeen.has(d.path)) firstSeen.set(d.path, d.oldValue);
    lastSeen.set(d.path, d.newValue);
  }
  if (firstSeen.size === 0) return "";
  const lines = ["", "### Signal Changes", ""];
  for (const [path, startVal] of firstSeen) {
    const endVal = lastSeen.get(path);
    lines.push(`- \`${path}\`: \`${JSON.stringify(startVal)}\` → \`${JSON.stringify(endVal)}\``);
  }
  return lines.join("\n");
}
function formatDiagnosticNotes(warnings) {
  if (warnings.length === 0) return "";
  const lines = ["", "### Diagnostic Notes", ""];
  for (const w of warnings) {
    lines.push(`- **${w.code}**: ${w.message}`);
  }
  return lines.join("\n");
}
function safeSlice(text, limit) {
  const cut = text.lastIndexOf("\n", limit);
  const safe = text.slice(0, cut > 0 ? cut : limit);
  const fenceCount = (safe.match(/^```/gm) || []).length;
  const needsClose = fenceCount % 2 !== 0;
  return safe + (needsClose ? "\n```" : "") + "\n\n*(truncated)*";
}
function truncateExport(text, limit) {
  if (text.length <= limit) return text;
  const logStart = text.indexOf("### Event Log");
  const logEnd = text.indexOf("\n###", logStart + 1);
  if (logStart === -1) return safeSlice(text, limit);
  const before = text.slice(0, logStart);
  const logSection = text.slice(logStart, logEnd === -1 ? void 0 : logEnd);
  const after = logEnd === -1 ? "" : text.slice(logEnd);
  const logLines = logSection.split("\n");
  const headerLines = logLines.slice(0, 3);
  const eventLines = logLines.slice(3, -1);
  const closingLines = logLines.slice(-1);
  if (eventLines.length <= 10) return safeSlice(text, limit);
  const kept = [
    ...headerLines,
    ...eventLines.slice(0, 5),
    `... (${eventLines.length - 10} events omitted)`,
    ...eventLines.slice(-5),
    ...closingLines
  ];
  const truncated = before + kept.join("\n") + after;
  if (truncated.length <= limit) return truncated;
  return safeSlice(truncated, limit);
}
function formatTraceExport(traceId) {
  const events = getTraceEvents(traceId);
  if (events.length === 0) return `## Trace #${traceId}

No events captured.`;
  const trace = getTraces().find((t) => t.traceId === traceId);
  const root = events[0];
  const baseTs = root.ts;
  const duration = events.length > 1 ? Math.round(events[events.length - 1].ts - baseTs) : 0;
  const timestamp = formatTime(root.wallTime);
  const lines = [];
  lines.push(`## Trace #${traceId}`);
  lines.push("");
  lines.push(`- **Root cause:** ${describeRootCause(root)}`);
  lines.push(`- **Time:** ${timestamp}`);
  lines.push(`- **Duration:** ${duration}ms`);
  lines.push(`- **Events:** ${events.length}`);
  if (trace) {
    lines.push(`- **Summary:** ${summarizeTrace(trace)}`);
    if (trace.status !== "complete") lines.push(`- **Status:** ${trace.status}`);
  }
  lines.push("");
  lines.push(formatLegend());
  lines.push("");
  lines.push("### Event Log");
  lines.push("");
  lines.push("```");
  for (const e of events) {
    lines.push(formatEventExport(e, baseTs));
  }
  lines.push("```");
  const diff = formatSignalDiff(events);
  if (diff) lines.push(diff);
  if (trace) {
    const notes = formatDiagnosticNotes(trace.warnings);
    if (notes) lines.push(notes);
  }
  let result = lines.join("\n");
  if (result.length > SINGLE_TRACE_SIZE_LIMIT) {
    result = truncateExport(result, SINGLE_TRACE_SIZE_LIMIT);
  }
  return result;
}
function formatAllTracesExport(traceIds) {
  const sections = [];
  let totalSize = 0;
  const header = `# Timeline Export — ${traceIds.length} trace${traceIds.length !== 1 ? "s" : ""}

Exported at ${formatTime(Date.now())}
`;
  sections.push(header);
  totalSize += header.length;
  const snapshot = formatSignalSnapshot();
  if (snapshot) {
    sections.push(snapshot);
    totalSize += snapshot.length;
  }
  let omitted = 0;
  for (let i = 0; i < traceIds.length; i++) {
    const section = formatTraceExport(traceIds[i]);
    if (totalSize + section.length > MULTI_TRACE_SIZE_LIMIT && sections.length > 2) {
      omitted = traceIds.length - i;
      break;
    }
    sections.push(section);
    totalSize += section.length;
  }
  if (omitted > 0) {
    sections.push(`
---

*${omitted} older trace${omitted !== 1 ? "s" : ""} omitted (size budget exceeded)*`);
  }
  let result = sections.join("\n\n---\n\n");
  if (result.length > EXPORT_HARD_CAP) {
    result = safeSlice(result, EXPORT_HARD_CAP);
  }
  return result;
}
export {
  beginTrace,
  buildFullTraceHtml,
  buildFullTraceText,
  buildTraceDetailHtml,
  buildTraceRowHtml,
  clampValue,
  cleanup,
  describeRootCause,
  detectWarnings,
  emit,
  escapeHtml,
  formatAllTracesExport,
  formatTime,
  formatTraceExport,
  getActiveTraceId,
  getEventCount,
  getEvents,
  getFilteredTraces,
  getTraceCount,
  getTraceEvents,
  getTraces,
  init,
  pushParent,
  rootTypeCategory,
  selectorFor,
  subscribe,
  summarizeTrace,
  traceMatchesChips
};
