import { getPath } from "datastar";
import { formatDuration, diffAttrValue, renderDiffText, escapeHtml, formatTime, renderDiffHtml, selectorPath, parseDatastarFetchDetail, extractDebugMeta, stripDebugKeys, injectEvent } from "./capture.js";
import { subscribeTimeline, DEBUGGER_TAG, isDebuggerMutation } from "./dom-observer.js";
import { getEntries, stripNamespace, getGroupedEntries, flattenPaths, isDebuggerSignal, valuesEqual } from "./signals.js";
const MAX_BYTES_PER_RESPONSE = 1048576;
const RAW_TEXT_MAX = 200;
const DATASTAR_EVENT_TYPES = /* @__PURE__ */ new Set([
  "datastar-patch-signals",
  "datastar-patch-elements",
  "datastar-execute-script"
]);
const VALID_SSE_FIELDS = /* @__PURE__ */ new Set(["event", "data", "id", "retry"]);
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
const CONTROL_CHAR_RE = /[\x00-\x08\x0B\x0E-\x1F\x7F]/;
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
function isDatastarHeaders(headers) {
  const h = new Headers(headers);
  return h.has("Datastar-Request") || h.get("Accept") === "text/event-stream";
}
function isDatastarSSERequest(input, init2) {
  if (init2?.headers && isDatastarHeaders(init2.headers)) return true;
  if (input instanceof Request && isDatastarHeaders(input.headers)) return true;
  return false;
}
async function interceptedFetch(input, init2) {
  if (!originalFetch) return window.fetch(input, init2);
  if (!isDatastarSSERequest(input, init2)) return originalFetch(input, init2);
  const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
  const response = await originalFetch(input, init2);
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
  validateStream(validatorCopy, url).catch(() => {
  });
  const proxied = new Response(datastarCopy, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers
  });
  for (const prop of ["url", "type", "redirected"]) {
    Object.defineProperty(proxied, prop, { value: response[prop] });
  }
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
        await reader.cancel();
        break;
      }
      const chunk = decoder.decode(value, { stream: true });
      buffer2 += chunk.replace(/\r\n?/g, "\n");
      while (true) {
        const blankIdx = buffer2.indexOf("\n\n");
        if (blankIdx === -1) break;
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
  const rawText = raw.slice(0, RAW_TEXT_MAX);
  const emit2 = (level, code, message) => emitError({ level, code, message, rawText, url, byteOffset });
  for (const line of lines) {
    if (line.startsWith(":")) continue;
    const colonIdx = line.indexOf(":");
    if (colonIdx === -1) continue;
    const field = line.slice(0, colonIdx);
    const value = line.slice(colonIdx + 1).trimStart();
    if (!VALID_SSE_FIELDS.has(field)) {
      emit2("warning", "UNKNOWN_FIELD", `Unknown SSE field: "${field}"`);
    }
    if (field === "event") {
      eventType = value;
      eventTypeCount++;
    } else if (field === "data") {
      dataLines.push(value);
      if (CONTROL_CHAR_RE.test(value)) {
        emit2("error", "BINARY_DATA", "Data line contains binary/control characters");
      }
    }
  }
  if (eventTypeCount > 1) {
    emit2(
      "error",
      "MERGED_EVENTS",
      `Found ${eventTypeCount} event: lines in one block — missing blank line separator`
    );
    return;
  }
  if (!eventType && dataLines.length > 0) {
    emit2("error", "MISSING_EVENT_TYPE", "Event has data lines but no event: type line");
    return;
  }
  if (!eventType) return;
  if (!DATASTAR_EVENT_TYPES.has(eventType)) {
    emit2("warning", "NON_DATASTAR_EVENT", `Unknown event type: "${eventType}"`);
    return;
  }
  if (eventType === "datastar-patch-signals") {
    validateSignalsData(dataLines, emit2);
  } else if (eventType === "datastar-patch-elements") {
    validateElementsData(dataLines, emit2);
  }
}
function validateSignalsData(dataLines, emit2) {
  let hasSignals = false;
  for (const line of dataLines) {
    if (line.startsWith("signals ")) {
      hasSignals = true;
      const json = line.slice("signals ".length);
      try {
        const parsed = JSON.parse(json);
        if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
          emit2("error", "INVALID_SIGNALS_JSON", "Signals data must be a JSON object");
        }
      } catch {
        emit2("error", "INVALID_SIGNALS_JSON", `Invalid JSON in signals data: ${json.slice(0, 80)}`);
      }
    }
  }
  if (!hasSignals) {
    emit2(
      "error",
      "MISSING_SIGNALS_DATA",
      "datastar-patch-signals event missing 'signals' data key"
    );
  }
}
function validateElementsData(dataLines, emit2) {
  let hasElements = false;
  let elementContent = "";
  for (const line of dataLines) {
    if (line.startsWith("elements ")) {
      hasElements = true;
      elementContent += line.slice("elements ".length);
    } else if (line.startsWith("mode ")) {
      const mode = line.slice("mode ".length).trim();
      if (!VALID_ELEMENT_MODES.has(mode)) {
        emit2(
          "error",
          "INVALID_ELEMENT_MODE",
          `Invalid mode: "${mode}". Valid: ${[...VALID_ELEMENT_MODES].join(", ")}`
        );
      }
    }
  }
  if (!hasElements) {
    emit2(
      "error",
      "MISSING_ELEMENTS_DATA",
      "datastar-patch-elements event missing 'elements' data key"
    );
  } else if (!elementContent.trim()) {
    emit2("warning", "EMPTY_FRAGMENT", "Elements event has empty fragment content");
  }
}
function emitError(error) {
  if (activeCallback) activeCallback(error);
}
const MAX_EVENTS = 5e3;
const PRESERVE_FIRST = 500;
const EVICT_BATCH = 1e3;
const STALE_TRACE_MS = 5e3;
const MAX_VALUE_SIZE = 1024;
const SSE_TERMINAL_TYPES = /* @__PURE__ */ new Set(["finished", "error", "retries-failed"]);
function isSseTerminal(sseType) {
  return SSE_TERMINAL_TYPES.has(sseType);
}
const buffer = [];
let nextEventId = 0;
let nextTraceId = 0;
let activeTraceId = null;
let activeParentId = null;
let activeDepth = 0;
let activeTraceRootType = null;
let traceCloseScheduled = false;
let traceCloseTimer = null;
let activeSseStarted = 0;
let activeSseFinished = 0;
const traceSseCounts = /* @__PURE__ */ new Map();
let sseElTraces = /* @__PURE__ */ new WeakMap();
const subscribers = /* @__PURE__ */ new Set();
let pendingNotify = false;
let initialized = false;
const traceEventCounts = /* @__PURE__ */ new Map();
let traceSummaryCache = null;
let sseListener = null;
function captureSSELifecycle() {
  sseListener = (e) => {
    const { type, el, argsRaw } = parseDatastarFetchDetail(e);
    const debugMeta = extractDebugMeta(argsRaw);
    const sseData = {
      sseType: type,
      handler: debugMeta?.handler ?? "",
      route: debugMeta?.route ?? "",
      seq: debugMeta?.seq ?? 0,
      payload: stripDebugKeys(argsRaw),
      elSelector: el ? selectorPath(el) : ""
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
      if (isSseTerminal(type)) {
        if (el) sseElTraces.delete(el);
      }
    }
  };
  document.addEventListener("datastar-fetch", sseListener);
}
const USER_ACTION_EVENTS = ["click", "input", "submit", "keydown"];
let userActionListeners = [];
function isInsideDebugger(el) {
  if (el.closest("starhtml-debugger")) return true;
  let root = el.getRootNode();
  while (root instanceof ShadowRoot) {
    if (root.host.tagName === DEBUGGER_TAG) return true;
    root = root.host.getRootNode();
  }
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
        targetSelector: selectorPath(target),
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
const MAX_PREV_VALUES = 500;
function captureSignalChanges() {
  const prevValues = /* @__PURE__ */ new Map();
  try {
    for (const [, entry] of getEntries()) {
      if (entry.status !== "removed") prevValues.set(entry.path, entry.value);
    }
  } catch {
  }
  signalPatchListener = (e) => {
    const raw = e.detail;
    if (!raw || typeof raw !== "object") return;
    let detail;
    let eventSource;
    const rawObj = raw;
    if ("signals" in rawObj && typeof rawObj.signals === "object") {
      detail = rawObj.signals;
      const src = rawObj.source;
      if (typeof src === "string") eventSource = src;
    } else {
      detail = rawObj;
    }
    const paths = flattenPaths(detail, "");
    let baseSource = activeTraceId === null ? "script" : "init";
    if (activeTraceRootType === "sse-lifecycle") baseSource = "sse";
    else if (activeTraceRootType === "user-action") baseSource = "user";
    for (const path of paths) {
      if (isDebuggerSignal(path)) continue;
      let newValue;
      try {
        newValue = getPath(path);
      } catch {
        continue;
      }
      const oldValue = prevValues.get(path);
      if (valuesEqual(oldValue, newValue)) continue;
      prevValues.delete(path);
      prevValues.set(path, newValue);
      if (prevValues.size > MAX_PREV_VALUES) {
        const first = prevValues.keys().next().value;
        if (first !== void 0) prevValues.delete(first);
      }
      let source = baseSource;
      if (eventSource === "persist") {
        source = "persist";
      } else if (baseSource !== "sse" && baseSource !== "user" && oldValue === void 0) {
        source = "init";
      }
      const data = {
        path,
        oldValue: clampValueFast(oldValue),
        newValue: clampValueFast(newValue),
        source
      };
      emit("signal-change", data);
    }
  };
  document.addEventListener("datastar-signal-patch", signalPatchListener);
}
let unsubDomObserver = null;
let elementIds = /* @__PURE__ */ new WeakMap();
let nextElementId = 0;
function getElementId(el) {
  let id = elementIds.get(el);
  if (id === void 0) {
    id = nextElementId++;
    elementIds.set(el, id);
  }
  return id;
}
function serializeNodeList(nodes) {
  const out = [];
  for (const node of nodes) {
    if (node instanceof Element) out.push(selectorPath(node));
    else if (node.nodeType === Node.TEXT_NODE)
      out.push(`"${(node.textContent ?? "").slice(0, 40)}"`);
  }
  return out;
}
function handleMutationRecords(records) {
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
        removedNodes
      });
    } else if (r.type === "attributes") {
      const oldValue = r.oldValue ?? null;
      const newValue = r.target.getAttribute(r.attributeName ?? "") ?? null;
      if (oldValue === newValue) continue;
      emit("dom-mutation", {
        mutationType: "attributes",
        targetSelector,
        attributeName: r.attributeName ?? "",
        oldValue,
        newValue,
        ...target && { elementId: getElementId(target) }
      });
    } else if (r.type === "characterData") {
      emit("dom-mutation", {
        mutationType: "characterData",
        targetSelector,
        oldValue: r.oldValue ?? null
      });
    }
  }
}
function captureDomMutations() {
  unsubDomObserver = subscribeTimeline(handleMutationRecords);
}
function captureMalformedSSE() {
  install((error) => {
    emit("sse-malformed", error);
    injectEvent({
      type: "sse-malformed",
      timestamp: Date.now(),
      el: null,
      argsRaw: { ...error }
    });
  });
}
function init() {
  if (initialized) return;
  initialized = true;
  captureSSELifecycle();
  captureUserActions();
  captureSignalChanges();
  captureDomMutations();
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
  if (unsubDomObserver) {
    unsubDomObserver();
    unsubDomObserver = null;
  }
  uninstall();
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
  sseElTraces = /* @__PURE__ */ new WeakMap();
  elementIds = /* @__PURE__ */ new WeakMap();
  nextElementId = 0;
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
  traceSummaryCache = null;
  traceEventCounts.set(event.traceId, (traceEventCounts.get(event.traceId) ?? 0) + 1);
  if (buffer.length > MAX_EVENTS) {
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
function beginTrace(rootEvent) {
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
function scheduleTraceClose() {
  if (traceCloseScheduled) return;
  traceCloseScheduled = true;
  traceCloseTimer = setTimeout(() => {
    traceCloseScheduled = false;
    traceCloseTimer = null;
    if (activeTraceId !== null && activeSseStarted <= activeSseFinished) {
      closeTrace();
    }
  }, 0);
}
function closeTrace() {
  if (activeTraceId !== null) {
    traceSseCounts.set(activeTraceId, { started: activeSseStarted, finished: activeSseFinished });
  }
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
function emit(type, data, opts) {
  const willBeginTrace = opts?.beginTrace === true;
  const isOrphan = activeTraceId === null && !willBeginTrace;
  const event = {
    id: nextEventId++,
    type,
    ts: performance.now(),
    wallTime: Date.now(),
    // beginTrace() overwrites traceId; orphans get their own; otherwise use active
    traceId: isOrphan ? nextTraceId++ : activeTraceId ?? -1,
    parentId: isOrphan ? null : activeParentId,
    depth: isOrphan ? 0 : activeDepth,
    data
  };
  if (willBeginTrace) {
    beginTrace(event);
  }
  if (type === "sse-lifecycle" && event.traceId === activeTraceId) {
    const sseType = data.sseType;
    if (sseType === "started") activeSseStarted++;
    else if (isSseTerminal(sseType)) {
      activeSseFinished++;
      if (activeSseStarted <= activeSseFinished && !traceCloseScheduled) {
        scheduleTraceClose();
      }
    }
  }
  addToBuffer(event);
  return event;
}
function getTraceEvents(traceId) {
  return buffer.filter((e) => e.traceId === traceId);
}
function getTraceCount() {
  return traceEventCounts.size;
}
function getTraces() {
  if (traceSummaryCache) return traceSummaryCache;
  const traceMap = /* @__PURE__ */ new Map();
  for (const e of buffer) {
    const arr = traceMap.get(e.traceId);
    if (arr) arr.push(e);
    else traceMap.set(e.traceId, [e]);
  }
  const now = performance.now();
  const summaries = [];
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
          const sseType = e.data.sseType;
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
      status: isStale ? "stale" : isComplete ? "complete" : "active"
    });
  }
  summaries.sort((a, b) => a.rootEvent.ts - b.rootEvent.ts);
  traceSummaryCache = summaries;
  return summaries;
}
const warningCache = /* @__PURE__ */ new Map();
function cachedDetectWarnings(traceId, events) {
  const key = `${traceId}:${events.length}`;
  let cached = warningCache.get(key);
  if (cached) return cached;
  cached = detectWarnings(events);
  warningCache.set(key, cached);
  if (warningCache.size > 1e3) {
    const first = warningCache.keys().next().value;
    if (first !== void 0) warningCache.delete(first);
  }
  return cached;
}
const PING_PONG_THRESHOLD = 3;
const MORPH_WINDOW_MS = 100;
function detectWarnings(events) {
  const warnings = [];
  detectSignalPingPong(events, warnings);
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
function detectHangingRequest(events, out) {
  const started = /* @__PURE__ */ new Map();
  const finished = /* @__PURE__ */ new Set();
  for (const e of events) {
    if (e.type !== "sse-lifecycle") continue;
    const d = e.data;
    if (d.sseType === "started") {
      started.set(d.elSelector || String(e.id), e);
    } else if (isSseTerminal(d.sseType)) {
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
        message: `${count} element events targeted "${sel}" in this trace`
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
  const attrChanges = /* @__PURE__ */ new Map();
  for (const e of events) {
    if (e.type !== "dom-mutation") continue;
    const d = e.data;
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
        message: `Attribute ${selector} changed ${count} times in this trace`
      });
    }
  }
}
function clampValueFast(value) {
  if (value === null || value === void 0) return value;
  const t = typeof value;
  if (t === "string") {
    const s = value;
    return s.length <= MAX_VALUE_SIZE ? value : `${s.slice(0, MAX_VALUE_SIZE)}...`;
  }
  if (t === "number" || t === "boolean") return value;
  if (Array.isArray(value)) {
    try {
      if (JSON.stringify(value).length <= MAX_VALUE_SIZE) return value;
    } catch {
    }
    return `[${value.length} items]`;
  }
  if (t === "object") {
    try {
      if (JSON.stringify(value).length <= MAX_VALUE_SIZE) return value;
    } catch {
    }
    return `{${Object.keys(value).length} keys}`;
  }
  return value;
}
function displaySignalPath(path) {
  try {
    let matchEntry = null;
    const seenNs = /* @__PURE__ */ new Set();
    let instanceNum = 0;
    for (const [, entry] of getEntries()) {
      if (!matchEntry && entry.path === path && entry.tagName) matchEntry = entry;
      if (matchEntry && entry.tagName === matchEntry.tagName && entry.namespace && !seenNs.has(entry.namespace)) {
        seenNs.add(entry.namespace);
        if (entry.namespace === matchEntry.namespace) instanceNum = seenNs.size;
      }
    }
    if (!matchEntry) return path;
    const bare = stripNamespace(path, matchEntry.tagName);
    const prefix = seenNs.size > 1 ? `${matchEntry.tagName}#${instanceNum}` : matchEntry.tagName;
    return `${prefix}.${bare}`;
  } catch {
  }
  return path;
}
function describeRootCause(event) {
  switch (event.type) {
    case "user-action": {
      const d = event.data;
      const label = d.targetText ? ` "${d.targetText}"` : "";
      return `${d.eventType}${label} ${d.targetSelector}`;
    }
    case "sse-lifecycle": {
      const d = event.data;
      return `SSE ${d.handler || d.route || d.sseType}`;
    }
    case "signal-change": {
      const d = event.data;
      return `signal ${displaySignalPath(d.path)}`;
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
  if (trace.signalChanges > 0)
    parts.push(`${trace.signalChanges} signal${trace.signalChanges > 1 ? "s" : ""}`);
  if (trace.domMutations > 0) parts.push(`${trace.domMutations} DOM`);
  if (trace.malformedEvents > 0) parts.push(`${trace.malformedEvents} malformed`);
  return parts.join(", ") || "no effects";
}
const ROOT_TYPE_CATEGORIES = {
  "user-action": "user",
  "sse-lifecycle": "sse",
  "signal-change": "signal",
  "sse-malformed": "warning"
};
function rootTypeCategory(event) {
  return ROOT_TYPE_CATEGORIES[event.type] ?? "other";
}
const TYPE_ICON_CLS = {
  "user-action": "tl-type-user",
  "sse-lifecycle": "tl-type-sse",
  "signal-change": "tl-type-signal",
  "sse-malformed": "tl-type-malformed"
};
function buildTraceRowHtml(trace) {
  const time = formatTime(trace.rootEvent.wallTime);
  const cause = escapeHtml(describeRootCause(trace.rootEvent));
  const summary = escapeHtml(summarizeTrace(trace));
  const dur = formatDuration(trace.totalDuration);
  const warnBadge = trace.warnings.length > 0 ? ` <span class="tl-warn-badge">⚠ ${trace.warnings.length}</span>` : "";
  const statusCls = `tl-status-${trace.status}`;
  const iconCls = TYPE_ICON_CLS[trace.rootEvent.type] ?? "tl-type-other";
  return `<div class="timeline-row ${statusCls}" data-trace-id="${trace.traceId}"><span class="tl-type-icon ${iconCls}">●</span><span class="tl-time">${time}</span><span class="tl-cause">${cause}</span><span class="tl-arrow">→</span>${warnBadge}<span class="tl-summary">${summary}</span><span class="tl-duration">${dur}</span><button class="tl-row-copy" data-copy-single="${trace.traceId}" title="Copy trace">⎘</button></div>`;
}
const PHASE_LABELS = {
  trigger: "Trigger",
  sse: "SSE",
  signal: "Signals",
  dom: "DOM",
  warning: "Warnings",
  finished: "Finished"
};
function eventPhase(e) {
  switch (e.type) {
    case "user-action":
      return "trigger";
    case "sse-lifecycle": {
      const d = e.data;
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
function formatEventLine(e, baseTs) {
  const offset = `+${Math.round(e.ts - baseTs)}ms`;
  const offsetHtml = `<span class="tl-ev-offset">${offset}</span>`;
  switch (e.type) {
    case "user-action": {
      const d = e.data;
      const textHtml = d.targetText ? ` <span class="tl-ev-text">"${escapeHtml(d.targetText)}"</span>` : "";
      return `${offsetHtml} <span class="tl-ev-type tl-type-user">${escapeHtml(d.eventType)}</span>${textHtml} <span class="tl-ev-target">${escapeHtml(d.targetSelector)}</span>${d.datastarAction ? ` <span class="tl-ev-action">${escapeHtml(d.datastarAction)}</span>` : ""}`;
    }
    case "sse-lifecycle": {
      const d = e.data;
      const label = d.sseType === "started" ? "SSE start" : d.sseType;
      return `${offsetHtml} <span class="tl-ev-type tl-type-sse">${escapeHtml(label)}</span> ${d.route ? `<span class="tl-ev-route">${escapeHtml(d.route)}</span> ` : ""}${d.handler ? `<span class="tl-ev-handler">${escapeHtml(d.handler)}</span>` : ""}`;
    }
    case "signal-change": {
      const d = e.data;
      const oldStr = d.oldValue === void 0 ? "undefined" : JSON.stringify(d.oldValue);
      const newStr = d.newValue === void 0 ? "undefined" : JSON.stringify(d.newValue);
      return `${offsetHtml} <span class="tl-ev-type tl-type-signal">${escapeHtml(displaySignalPath(d.path))}</span> <span class="tl-ev-old">${escapeHtml(oldStr)}</span> → <span class="tl-ev-new">${escapeHtml(newStr)}</span> <span class="tl-ev-source">(${escapeHtml(d.source)})</span>`;
    }
    case "dom-mutation": {
      const d = e.data;
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
        summarized: [
          `<span class="tl-ev-cycle">${escapeHtml(cycle)} … ${repeats} cycles</span>`
        ],
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
  const warnings = cachedDetectWarnings(traceId, events);
  const cycles = summarizeCycles(events);
  let html = '<div class="tl-detail">';
  if (warnings.length > 0) {
    html += '<div class="tl-phase tl-phase-warning"><div class="tl-phase-label">Warnings</div>';
    for (const w of warnings) {
      html += `<div class="tl-ev-line tl-ev-warn">⚠ <span class="tl-warn-code">${escapeHtml(w.code)}</span> ${escapeHtml(w.message)}</div>`;
    }
    html += "</div>";
  }
  let currentPhase = "";
  let shown = 0;
  const truncate = events.length > MAX_DETAIL_EVENTS && !cycles;
  const domEvents = [];
  for (let i = 0; i < events.length; i++) {
    if (truncate && shown >= MAX_DETAIL_EVENTS) break;
    const e = events[i];
    const phase = eventPhase(e);
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
      let lastSig;
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
    html += `<div class="tl-dom-toggle"><span class="tl-dom-arrow">▸</span> <span class="tl-phase-label">DOM</span> <span class="tl-dom-count">${domEvents.length} mutation${domEvents.length !== 1 ? "s" : ""}</span></div>`;
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
function buildFullTraceText(traceId) {
  const events = getTraceEvents(traceId);
  if (events.length === 0) return "No events in trace.";
  const baseTs = events[0].ts;
  const lines = [];
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
        const d = e.data;
        const text = d.targetText ? ` "${d.targetText}"` : "";
        detail = `${d.eventType}${text} ${d.targetSelector}${d.datastarAction ? ` → ${d.datastarAction}` : ""}`;
        break;
      }
      case "sse-lifecycle": {
        const d = e.data;
        detail = `SSE ${d.sseType}${d.route ? ` ${d.route}` : ""}${d.handler ? ` (${d.handler})` : ""}`;
        break;
      }
      case "signal-change": {
        const d = e.data;
        detail = `signal ${displaySignalPath(d.path)}: ${JSON.stringify(d.oldValue)} → ${JSON.stringify(d.newValue)} (${d.source})`;
        break;
      }
      case "dom-mutation": {
        const d = e.data;
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
        const d = e.data;
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
function buildCopyButtonHtml(traceId) {
  return `<div class="tl-copy-wrap"><button class="tl-copy-btn" data-copy-trace="${traceId}">Copy</button></div>`;
}
function getFilteredTraces(textFilter, chipFilter) {
  const traces = getTraces();
  const filter = textFilter.toLowerCase();
  return traces.filter((t) => {
    if (chipFilter.size > 0) {
      const cat = rootTypeCategory(t.rootEvent);
      if (!chipFilter.has(cat) && !(chipFilter.has("warning") && t.warnings.length > 0))
        return false;
    }
    if (!filter) return true;
    const cause = describeRootCause(t.rootEvent).toLowerCase();
    const summary = summarizeTrace(t).toLowerCase();
    if (cause.includes(filter) || summary.includes(filter)) return true;
    const events = getTraceEvents(t.traceId);
    for (const e of events) {
      if (e.type === "signal-change") {
        if (e.data.path.toLowerCase().includes(filter)) return true;
      } else if (e.type === "sse-lifecycle") {
        const d = e.data;
        if (d.route.toLowerCase().includes(filter) || d.handler.toLowerCase().includes(filter))
          return true;
      }
    }
    return false;
  });
}
function getTraceIdsInWindow(seconds) {
  const cutoff = Date.now() - seconds * 1e3;
  const traces = getTraces();
  const ids = [];
  for (const t of traces) {
    if (t.rootEvent.wallTime >= cutoff) ids.push(t.traceId);
  }
  return ids;
}
function getTraceIdsInRange(startId, endId) {
  const lo = Math.min(startId, endId);
  const hi = Math.max(startId, endId);
  const traces = getTraces();
  return traces.filter((t) => t.traceId >= lo && t.traceId <= hi).map((t) => t.traceId);
}
const SINGLE_TRACE_SIZE_LIMIT = 5 * 1024;
const EXPORT_SIZE_LIMIT = 20 * 1024;
const TRUNCATE_PAYLOAD = 200;
const LEGEND = "**Legend:** `[signals]` = signal patch, `[elements]` = DOM morph, `[start]`/`[done]` = SSE lifecycle,\n`[click]`/`[input]` = user action, `[malformed]` = SSE validation error";
function formatSignalSnapshot() {
  let groups;
  try {
    groups = getGroupedEntries("");
  } catch {
    return "";
  }
  if (groups.length === 0) return "";
  const lines = ["", "### Signal Snapshot", ""];
  for (const group of groups) {
    lines.push(`**${group.displayName}**`);
    for (const e of group.entries) {
      if (e.status === "removed") continue;
      const displayName = stripNamespace(e.path, e.tagName);
      const val = JSON.stringify(e.value);
      const valStr = val && val.length > TRUNCATE_PAYLOAD ? `${val.slice(0, TRUNCATE_PAYLOAD)}...` : val;
      lines.push(
        `- \`${displayName}\` = \`${valStr ?? "undefined"}\` (${e.type}${e.persistStorage ? `, persist:${e.persistStorage}` : ""})`
      );
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
      const text = d.targetText ? ` "${d.targetText}"` : "";
      return `${offset} ${indent}[${d.eventType}]${text} \`${d.targetSelector}\`${d.datastarAction ? ` → \`${d.datastarAction}\`` : ""}`;
    }
    case "sse-lifecycle": {
      const d = e.data;
      const tag = d.sseType === "started" ? "[start]" : isSseTerminal(d.sseType) ? "[done]" : `[${d.sseType}]`;
      let payload = "";
      if (d.payload && Object.keys(d.payload).length > 0) {
        const raw = JSON.stringify(d.payload);
        payload = raw.length > TRUNCATE_PAYLOAD ? ` ${raw.slice(0, TRUNCATE_PAYLOAD)}...` : ` ${raw}`;
      }
      return `${offset} ${indent}${tag} \`${d.route || d.handler || "SSE"}\`${payload}`;
    }
    case "signal-change": {
      const d = e.data;
      const oldStr = d.oldValue === void 0 ? "undefined" : JSON.stringify(d.oldValue);
      const newStr = d.newValue === void 0 ? "undefined" : JSON.stringify(d.newValue);
      return `${offset} ${indent}[signals] \`${displaySignalPath(d.path)}\`: \`${oldStr}\` → \`${newStr}\` (${d.source})`;
    }
    case "dom-mutation": {
      const d = e.data;
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
  const changeCounts = /* @__PURE__ */ new Map();
  for (const e of events) {
    if (e.type !== "signal-change") continue;
    const d = e.data;
    if (!firstSeen.has(d.path)) firstSeen.set(d.path, d.oldValue);
    lastSeen.set(d.path, d.newValue);
    changeCounts.set(d.path, (changeCounts.get(d.path) ?? 0) + 1);
  }
  if (![...changeCounts.values()].some((c) => c > 1)) return "";
  const lines = ["", "### Signal Changes (net)", ""];
  for (const [path, startVal] of firstSeen) {
    const endVal = lastSeen.get(path);
    lines.push(
      `- \`${displaySignalPath(path)}\`: \`${JSON.stringify(startVal)}\` → \`${JSON.stringify(endVal)}\``
    );
  }
  return lines.join("\n");
}
function safeSlice(text, limit) {
  const cut = text.lastIndexOf("\n", limit);
  const safe = text.slice(0, cut > 0 ? cut : limit);
  const fenceCount = (safe.match(/^```/gm) || []).length;
  const needsClose = fenceCount % 2 !== 0;
  return `${safe}${needsClose ? "\n```" : ""}

*(truncated)*`;
}
function truncateSection(text, sectionName, keepLines) {
  const start = text.indexOf(`### ${sectionName}`);
  if (start === -1) return text;
  const end = text.indexOf("\n###", start + 1);
  const before = text.slice(0, start);
  const section = text.slice(start, end === -1 ? void 0 : end);
  const after = end === -1 ? "" : text.slice(end);
  const lines = section.split("\n");
  const header = lines.slice(0, 3);
  const body = lines.slice(3, -1);
  const closing = lines.slice(-1);
  if (body.length <= keepLines * 2) return text;
  const kept = [
    ...header,
    ...body.slice(0, keepLines),
    `... (${body.length - keepLines * 2} entries omitted)`,
    ...body.slice(-keepLines),
    ...closing
  ];
  return before + kept.join("\n") + after;
}
function truncateExport(text, limit) {
  if (text.length <= limit) return text;
  let result = truncateSection(text, "DOM Mutations", 3);
  if (result.length <= limit) return result;
  result = truncateSection(result, "Event Log", 5);
  if (result.length <= limit) return result;
  return safeSlice(result, limit);
}
function formatTraceExport(traceId, opts) {
  const events = getTraceEvents(traceId);
  if (events.length === 0) return `## Trace #${traceId}

No events captured.`;
  const root = events[0];
  const baseTs = root.ts;
  const duration = events.length > 1 ? Math.round(events[events.length - 1].ts - baseTs) : 0;
  const timestamp = formatTime(root.wallTime);
  const warnings = cachedDetectWarnings(traceId, events);
  const lines = [];
  lines.push(`## Trace #${traceId}`);
  lines.push("");
  lines.push(`- **Root cause:** ${describeRootCause(root)}`);
  lines.push(`- **Time:** ${timestamp}`);
  if (duration > 0) lines.push(`- **Duration:** ${duration}ms`);
  lines.push(`- **Events:** ${events.length}`);
  lines.push("");
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
function formatAllTracesExport(traceIds) {
  const sections = [];
  let totalSize = 0;
  const header = `# Timeline Export — ${traceIds.length} trace${traceIds.length !== 1 ? "s" : ""}

Page: ${location.pathname}
Exported at ${formatTime(Date.now())}
`;
  sections.push(header);
  totalSize += header.length;
  const snapshot = formatSignalSnapshot();
  if (snapshot) {
    sections.push(snapshot);
    totalSize += snapshot.length;
  }
  sections.push(LEGEND);
  totalSize += LEGEND.length;
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
      `
---

*${omitted} older trace${omitted !== 1 ? "s" : ""} omitted (size budget exceeded)*`
    );
  }
  return sections.join("\n\n---\n\n");
}
export {
  buildCopyButtonHtml,
  buildFullTraceText,
  buildTraceDetailHtml,
  buildTraceRowHtml,
  cleanup,
  describeRootCause,
  formatAllTracesExport,
  formatTraceExport,
  getFilteredTraces,
  getTraceCount,
  getTraceIdsInRange,
  getTraceIdsInWindow,
  getTraces,
  init,
  rootTypeCategory,
  subscribe,
  summarizeTrace
};
