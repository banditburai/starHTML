import { mergePatch, getPath, filtered } from "datastar";
import { escapeHtml } from "./capture.js";
const POLL_INTERVAL_MS = 2e3;
const CHANGE_FLASH_MS = 2e3;
const REMOVED_CLEANUP_MS = 6e3;
const REMOVED_DISPLAY_MS = 4e3;
const MAX_DISPLAY_STRING = 40;
const entries = /* @__PURE__ */ new Map();
let debuggerPrefix = "";
let excludeRe;
let debuggerSignalNames = /* @__PURE__ */ new Set();
let pollInterval = null;
const subscribers = /* @__PURE__ */ new Set();
let pendingNotify = false;
let initialized = false;
let isVisible = null;
function init(excludePrefix, excludeNames, visibilityFn) {
  if (initialized) return;
  initialized = true;
  debuggerPrefix = excludePrefix;
  excludeRe = excludePrefix ? new RegExp(`^${escapeRegex(excludePrefix)}`) : void 0;
  debuggerSignalNames = new Set(excludeNames ?? []);
  if (visibilityFn) isVisible = visibilityFn;
  document.addEventListener("datastar-signal-patch", onSignalPatch);
  structuralPoll();
  pollInterval = setInterval(structuralPoll, POLL_INTERVAL_MS);
}
function cleanup() {
  document.removeEventListener("datastar-signal-patch", onSignalPatch);
  if (pollInterval !== null) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
  entries.clear();
  subscribers.clear();
  debuggerPrefix = "";
  excludeRe = void 0;
  debuggerSignalNames = /* @__PURE__ */ new Set();
  pendingNotify = false;
  isVisible = null;
  initialized = false;
}
function subscribe(fn) {
  subscribers.add(fn);
  return () => {
    subscribers.delete(fn);
  };
}
function getEntries() {
  return entries;
}
function getSignalCount() {
  let count = 0;
  for (const entry of entries.values()) {
    if (entry.status !== "removed") count++;
  }
  return count;
}
function clearPersistedData() {
  const persistedPaths = /* @__PURE__ */ new Set();
  for (const [path, entry] of entries) {
    if (entry.persistStorage) persistedPaths.add(path);
  }
  for (const storage of [localStorage, sessionStorage]) {
    const keysToRemove = [];
    try {
      for (let i = 0; i < storage.length; i++) {
        const key = storage.key(i);
        if (key?.startsWith("starhtml-persist")) keysToRemove.push(key);
      }
      for (const k of keysToRemove) storage.removeItem(k);
    } catch {
    }
  }
  window.__starhtml_pc = void 0;
  if (persistedPaths.size > 0) {
    const defaults = {};
    const prefix = "data-signals:";
    for (const el of document.querySelectorAll("*")) {
      for (const attr of el.attributes) {
        if (!attr.name.startsWith(prefix)) continue;
        const name = attr.name.slice(prefix.length).split("__")[0];
        if (!persistedPaths.has(name)) continue;
        try {
          defaults[name] = JSON.parse(attr.value);
        } catch {
          defaults[name] = attr.value;
        }
      }
    }
    if (Object.keys(defaults).length > 0) mergePatch(defaults);
  }
  notifySubscribers();
}
function isDebuggerSignal(path) {
  return !!debuggerPrefix && path.startsWith(debuggerPrefix) || debuggerSignalNames.has(path);
}
function onSignalPatch(e) {
  const detail = e.detail;
  if (!detail || typeof detail !== "object") return;
  const paths = flattenPaths(detail, "");
  let changed = false;
  for (const path of paths) {
    if (isDebuggerSignal(path)) continue;
    try {
      const value = getPath(path);
      if (updateOrCreateEntry(path, value)) changed = true;
    } catch {
    }
  }
  if (changed) scheduleNotify();
}
function structuralPoll() {
  if (isVisible && !isVisible()) return;
  let result;
  try {
    result = filtered(excludeRe ? { exclude: excludeRe } : void 0);
  } catch {
    return;
  }
  const allSignals = flattenToEntries(result, "");
  const seenPaths = /* @__PURE__ */ new Set();
  for (const [path, value] of allSignals) {
    if (isDebuggerSignal(path)) continue;
    seenPaths.add(path);
    const entry = entries.get(path);
    if (!entry) {
      updateOrCreateEntry(path, value);
    } else {
      if (!valuesEqual(entry.value, value)) {
        updateExistingEntry(entry, value);
      }
      if (entry.status === "stale") entry.status = "live";
    }
  }
  for (const [path, entry] of entries) {
    if (!seenPaths.has(path)) {
      if (entry.status === "live") entry.status = "stale";
      else if (entry.status === "stale") entry.status = "removed";
    }
    if (entry.status === "removed" && Date.now() - entry.lastChanged > REMOVED_CLEANUP_MS) {
      entries.delete(path);
    }
  }
  detectNamespaces();
  detectPersistence();
  notifySubscribers();
}
function updateOrCreateEntry(path, value) {
  const existing = entries.get(path);
  if (existing) {
    if (valuesEqual(existing.value, value)) return false;
    updateExistingEntry(existing, value);
    return true;
  }
  entries.set(path, {
    path,
    value,
    type: detectType(value),
    source: "page",
    namespace: "",
    tagName: "",
    status: "live",
    lastChanged: Date.now()
  });
  return true;
}
function updateExistingEntry(entry, value) {
  entry.value = value;
  entry.type = detectType(value);
  entry.lastChanged = Date.now();
  entry.status = "live";
}
function assignNamespace(entry, namespace, tag) {
  entry.namespace = namespace;
  entry.tagName = tag;
  if (!entry.source.startsWith("persist:")) {
    entry.source = `component:${tag}`;
  }
}
function detectNamespaces() {
  const nsMap = /* @__PURE__ */ new Map();
  try {
    for (const el of document.querySelectorAll("[data-star-id]")) {
      const id = el.getAttribute("data-star-id");
      if (id && !(debuggerPrefix && id.startsWith(debuggerPrefix))) {
        nsMap.set(id, el.tagName.toLowerCase());
      }
    }
  } catch {
  }
  for (const [path, entry] of entries) {
    let matched = false;
    for (const [prefix, tag] of nsMap) {
      if (path.startsWith(`${prefix}_`) || path === prefix) {
        assignNamespace(entry, prefix, tag);
        matched = true;
        break;
      }
    }
    if (!matched) {
      const m = path.match(/^(_star_\w+_id\d+)_/);
      if (m) {
        const tag = m[1].replace(/^_star_/, "").replace(/_id\d+$/, "").replace(/_/g, "-");
        assignNamespace(entry, m[1], tag);
      } else if (!entry.source.startsWith("persist:")) {
        entry.namespace = "";
        entry.tagName = "";
        entry.source = "page";
      }
    }
  }
}
function detectPersistence() {
  for (const entry of entries.values()) entry.persistStorage = void 0;
  try {
    scanStorage(localStorage, "local");
  } catch {
  }
  try {
    scanStorage(sessionStorage, "session");
  } catch {
  }
}
function scanStorage(storage, type) {
  for (let i = 0; i < storage.length; i++) {
    const key = storage.key(i);
    if (!key || !key.startsWith("starhtml-persist")) continue;
    try {
      const raw = storage.getItem(key);
      if (!raw) continue;
      const data = JSON.parse(raw);
      if (!data || typeof data !== "object") continue;
      for (const signalPath of Object.keys(data)) {
        const entry = entries.get(signalPath);
        if (entry) {
          entry.persistStorage = type;
          if (entry.source === "page") {
            entry.source = `persist:${key}`;
          }
        }
      }
    } catch {
    }
  }
}
function flattenToEntries(obj, prefix, out = []) {
  for (const key of Object.keys(obj)) {
    const fullPath = prefix ? `${prefix}.${key}` : key;
    const val = obj[key];
    if (val && typeof val === "object" && !Array.isArray(val) && !(val instanceof Date)) {
      flattenToEntries(val, fullPath, out);
    } else {
      out.push([fullPath, val]);
    }
  }
  return out;
}
function flattenPaths(obj, prefix) {
  return flattenToEntries(obj, prefix).map(([path]) => path);
}
function detectType(value) {
  if (value == null) return "object";
  if (Array.isArray(value)) return "array";
  const t = typeof value;
  return t === "string" || t === "number" || t === "boolean" ? t : "object";
}
function valuesEqual(a, b) {
  if (a === b) return true;
  if (a == null || b == null) return false;
  if (typeof a !== typeof b) return false;
  if (typeof a === "object") {
    return safeStringify(a) === safeStringify(b);
  }
  return false;
}
function safeStringify(v, pretty = false) {
  try {
    return pretty ? JSON.stringify(v, null, 2) : JSON.stringify(v);
  } catch {
    return String(v);
  }
}
function escapeRegex(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
function notifySubscribers() {
  for (const fn of subscribers) fn();
}
function scheduleNotify() {
  if (pendingNotify) return;
  pendingNotify = true;
  requestAnimationFrame(() => {
    pendingNotify = false;
    notifySubscribers();
  });
}
function stripNamespace(path, namespace) {
  if (!namespace) return path;
  const m = path.match(/^_star_\w+_id\d+_(.+)$/);
  if (m) return m[1];
  const candidates = [namespace.replace(/-/g, "_"), namespace];
  for (const prefix of candidates) {
    if (path.startsWith(`${prefix}_`)) return path.slice(prefix.length + 1);
  }
  return path;
}
function getGroupedEntries(filter) {
  const filterLower = filter.toLowerCase();
  const tagInstances = /* @__PURE__ */ new Map();
  for (const entry of entries.values()) {
    if (entry.tagName && entry.status !== "removed") {
      let arr = tagInstances.get(entry.tagName);
      if (!arr) {
        arr = [];
        tagInstances.set(entry.tagName, arr);
      }
      if (!arr.includes(entry.namespace)) arr.push(entry.namespace);
    }
  }
  for (const arr of tagInstances.values()) arr.sort();
  const groups = /* @__PURE__ */ new Map();
  for (const entry of entries.values()) {
    if (entry.status === "removed" && Date.now() - entry.lastChanged > REMOVED_DISPLAY_MS) continue;
    if (filterLower) {
      const displayName = stripNamespace(entry.path, entry.tagName);
      if (!entry.path.toLowerCase().includes(filterLower) && !displayName.toLowerCase().includes(filterLower)) {
        continue;
      }
    }
    const ns = entry.namespace;
    let group = groups.get(ns);
    if (!group) {
      group = [];
      groups.set(ns, group);
    }
    group.push(entry);
  }
  const result = [];
  const sortedKeys = [...groups.keys()].sort((a, b) => {
    if (a === "" && b !== "") return -1;
    if (b === "" && a !== "") return 1;
    return a.localeCompare(b);
  });
  for (const ns of sortedKeys) {
    const groupEntries = groups.get(ns);
    if (!groupEntries) continue;
    groupEntries.sort((a, b) => {
      const aName = stripNamespace(a.path, a.tagName);
      const bName = stripNamespace(b.path, b.tagName);
      return aName.localeCompare(bName);
    });
    let displayName;
    if (ns === "") {
      displayName = "Page Signals";
    } else {
      const tag = groupEntries[0].tagName;
      const instances = tagInstances.get(tag) || [ns];
      displayName = instances.length > 1 ? `${tag} #${instances.indexOf(ns) + 1}` : tag;
    }
    result.push({ namespace: ns, displayName, entries: groupEntries, count: groupEntries.length });
  }
  return result;
}
function formatSignalValue(value, type) {
  if (value === null || value === void 0) return "null";
  switch (type) {
    case "string": {
      const s = String(value);
      return s.length > MAX_DISPLAY_STRING ? `"${s.slice(0, MAX_DISPLAY_STRING - 3)}…"` : `"${s}"`;
    }
    case "number":
    case "boolean":
      return String(value);
    case "array": {
      const arr = value;
      return `[${arr.length} item${arr.length !== 1 ? "s" : ""}]`;
    }
    case "object": {
      const keys = Object.keys(value);
      return `{${keys.length} key${keys.length !== 1 ? "s" : ""}}`;
    }
    default:
      return String(value);
  }
}
function buildGroupHeaderHtml(group, collapsed) {
  const toggle = collapsed ? "▸" : "▾";
  const esc = escapeHtml;
  return `<div class="signal-group-header" data-ns="${esc(group.namespace)}"><span class="group-toggle">${toggle}</span><span class="group-name">${esc(group.displayName)}</span><span class="group-count">(${group.count})</span></div>`;
}
function buildSignalRowHtml(entry) {
  const esc = escapeHtml;
  const displayName = stripNamespace(entry.path, entry.tagName);
  const formattedValue = formatSignalValue(entry.value, entry.type);
  const typeClass = `sv-${entry.type}`;
  const isChanged = Date.now() - entry.lastChanged < CHANGE_FLASH_MS;
  let classes = "signal-row";
  if (isChanged) classes += " signal-changed";
  if (entry.status === "stale") classes += " signal-stale";
  if (entry.status === "removed") classes += " signal-removed";
  let persistBadge = "";
  if (entry.persistStorage) {
    persistBadge = ` <span class="signal-persist"><iconify-icon icon="material-symbols:lock" width="11" height="11"></iconify-icon> ${entry.persistStorage}</span>`;
  }
  const statusBadge = entry.status === "stale" || entry.status === "removed" ? ` <span class="signal-removed-badge">⚠ ${entry.status}</span>` : "";
  return `<div class="${classes}" data-path="${esc(entry.path)}" title="Click to expand"><span class="signal-name">${esc(displayName)}</span><span class="signal-value ${typeClass}">${esc(formattedValue)}</span>${persistBadge}${statusBadge}</div>`;
}
function buildSignalDetailHtml(entry) {
  const esc = escapeHtml;
  const live = entry.status === "live";
  let html = `<div class="signal-detail">`;
  if (live && (entry.type === "string" || entry.type === "number")) {
    const inputType = entry.type === "number" ? "number" : "text";
    html += `<div class="sd-row"><input class="signal-detail-input" type="${inputType}" data-edit-path="${esc(entry.path)}" value="${esc(String(entry.value))}" /></div>`;
  } else if (live && entry.type === "boolean") {
    html += `<div class="sd-row"><button class="signal-toggle-btn" data-edit-path="${esc(entry.path)}">${entry.value ? "true" : "false"}</button></div>`;
  } else {
    html += `<div class="sd-row"><pre>${esc(safeStringify(entry.value, true))}</pre></div>`;
    if (live && entry.type === "array") {
      html += `<div class="sd-row"><button class="signal-edit-obj-btn" data-edit-path="${esc(entry.path)}">Edit JSON</button></div>`;
    }
  }
  const meta = [entry.type];
  if (entry.source !== "page") meta.push(entry.source);
  if (entry.persistStorage) meta.push(`${entry.persistStorage}Storage`);
  if (entry.status !== "live") meta.push(entry.status);
  html += `<div class="sd-row sd-meta">${esc(entry.path)} · ${meta.map(esc).join(" · ")}</div>`;
  html += "</div>";
  return html;
}
const isPlainObj = (v) => !!v && typeof v === "object" && !Array.isArray(v);
function patchSignal(path, value, previousValue) {
  if (isPlainObj(previousValue) && isPlainObj(value)) {
    const patchObj = { ...value };
    for (const k of Object.keys(previousValue)) {
      if (!(k in patchObj)) patchObj[k] = null;
    }
    mergePatch(dotPathToPatch(path, patchObj));
    return;
  }
  mergePatch(dotPathToPatch(path, value));
}
function dotPathToPatch(path, value) {
  const parts = path.split(".");
  if (parts.length === 1) return { [path]: value };
  const root = {};
  let current = root;
  for (let i = 0; i < parts.length - 1; i++) {
    const next = {};
    current[parts[i]] = next;
    current = next;
  }
  current[parts[parts.length - 1]] = value;
  return root;
}
export {
  buildGroupHeaderHtml,
  buildSignalDetailHtml,
  buildSignalRowHtml,
  cleanup,
  clearPersistedData,
  flattenPaths,
  formatSignalValue,
  getEntries,
  getGroupedEntries,
  getSignalCount,
  init,
  isDebuggerSignal,
  patchSignal,
  stripNamespace,
  subscribe,
  valuesEqual
};
