// debugger-signals.ts — Signal tracking data layer for the StarHTML debugger.

import { filtered, getPath, mergePatch } from "datastar";

export interface SignalEntry {
  path: string;
  value: unknown;
  previousValue: unknown;
  type: "string" | "number" | "boolean" | "object" | "array";
  source: string;
  namespace: string;
  tagName: string;
  status: "live" | "stale" | "removed";
  lastChanged: number;
  persistStorage?: "local" | "session";
}

export interface SignalGroup {
  namespace: string;
  displayName: string;
  entries: SignalEntry[];
  count: number;
}

const POLL_INTERVAL_MS = 2000;
const CHANGE_FLASH_MS = 2000;
const REMOVED_CLEANUP_MS = 6000;
const REMOVED_DISPLAY_MS = 4000;
const MAX_DISPLAY_STRING = 40;
const MAX_PREV_VALUE_SIZE = 1024;

const entries: Map<string, SignalEntry> = new Map();
let debuggerPrefix = "";
let debuggerSignalNames: Set<string> = new Set();
let pollInterval: ReturnType<typeof setInterval> | null = null;
const subscribers = new Set<() => void>();
let pendingNotify = false;
let initialized = false;

/** excludePrefix filters namespaced signals; excludeNames filters
 *  un-namespaced Local() signal names created by data-bind. */
export function init(excludePrefix: string, excludeNames?: string[]): void {
  if (initialized) return;
  initialized = true;
  debuggerPrefix = excludePrefix;
  debuggerSignalNames = new Set(excludeNames || []);
  document.addEventListener("datastar-signal-patch", onSignalPatch as EventListener);
  structuralPoll();
  pollInterval = setInterval(structuralPoll, POLL_INTERVAL_MS);
}

export function cleanup(): void {
  document.removeEventListener("datastar-signal-patch", onSignalPatch as EventListener);
  if (pollInterval !== null) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
  entries.clear();
  subscribers.clear();
  initialized = false;
}

export function subscribe(fn: () => void): () => void {
  subscribers.add(fn);
  return () => { subscribers.delete(fn); };
}

export function getEntries(): Map<string, SignalEntry> {
  return entries;
}

/** Excludes entries with status "removed". */
export function getSignalCount(): number {
  let count = 0;
  for (const entry of entries.values()) {
    if (entry.status !== "removed") count++;
  }
  return count;
}

export function clearPersistedData(): void {
  for (const storage of [localStorage, sessionStorage]) {
    const keysToRemove: string[] = [];
    try {
      for (let i = 0; i < storage.length; i++) {
        const key = storage.key(i);
        if (key?.startsWith("starhtml-persist")) keysToRemove.push(key);
      }
      keysToRemove.forEach(k => storage.removeItem(k));
    } catch { /* storage unavailable */ }
  }
  for (const entry of entries.values()) entry.persistStorage = undefined;
  notifySubscribers();
}

function isDebuggerSignal(path: string): boolean {
  if (debuggerPrefix && path.startsWith(debuggerPrefix)) return true;
  if (debuggerSignalNames.has(path)) return true;
  return false;
}

function onSignalPatch(e: CustomEvent): void {
  const detail = e.detail;
  if (!detail || typeof detail !== "object") return;

  const paths = flattenNestedObject(detail, "");
  let changed = false;

  for (const path of paths) {
    if (isDebuggerSignal(path)) continue;
    try {
      const value = getPath(path);
      if (updateOrCreateEntry(path, value)) changed = true;
    } catch { /* signal may have been removed */ }
  }

  if (changed) scheduleNotify();
}

function structuralPoll(): void {
  const excludeRe = debuggerPrefix ? new RegExp("^" + escapeRegex(debuggerPrefix)) : undefined;
  let result: Record<string, unknown>;
  try {
    // filtered() returns a nested object (not an array), via Datastar's Me() function
    result = filtered(excludeRe ? { exclude: excludeRe } : undefined) as unknown as Record<string, unknown>;
  } catch { return; }

  const allSignals = flattenToEntries(result, "");
  const seenPaths = new Set<string>();

  for (const [path, value] of allSignals) {
    if (isDebuggerSignal(path)) continue;
    seenPaths.add(path);
    if (!entries.has(path)) {
      updateOrCreateEntry(path, value);
    } else {
      // Poll catches changes missed by patch events
      const entry = entries.get(path)!;
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
  }

  for (const [path, entry] of entries) {
    if (entry.status === "removed" && Date.now() - entry.lastChanged > REMOVED_CLEANUP_MS) {
      entries.delete(path);
    }
  }

  detectNamespaces();
  detectPersistence();
  notifySubscribers();
}

function updateOrCreateEntry(path: string, value: unknown): boolean {
  const existing = entries.get(path);
  if (existing) {
    if (valuesEqual(existing.value, value)) return false;
    updateExistingEntry(existing, value);
    return true;
  }

  entries.set(path, {
    path,
    value,
    previousValue: null,
    type: detectType(value),
    source: "page",
    namespace: "",
    tagName: "",
    status: "live",
    lastChanged: Date.now(),
  });
  return true;
}

function updateExistingEntry(entry: SignalEntry, value: unknown): void {
  const prevStr = safeStringify(entry.value);
  entry.previousValue = prevStr.length <= MAX_PREV_VALUE_SIZE ? entry.value : "[too large]";
  entry.value = value;
  entry.type = detectType(value);
  entry.lastChanged = Date.now();
  entry.status = "live";
}

function detectNamespaces(): void {
  const nsMap = new Map<string, string>();
  try {
    document.querySelectorAll("[data-star-id]").forEach(el => {
      const id = el.getAttribute("data-star-id");
      if (id && !(debuggerPrefix && id.startsWith(debuggerPrefix))) {
        nsMap.set(id, el.tagName.toLowerCase());
      }
    });
  } catch { /* DOM query failed */ }

  for (const [path, entry] of entries) {
    let matched = false;

    for (const [prefix, tag] of nsMap) {
      if (path.startsWith(prefix + "_") || path === prefix) {
        entry.namespace = prefix;     // full instance ID: "_star_demo_counter_id0"
        entry.tagName = tag;          // component tag: "demo-counter"
        if (!entry.source.startsWith("persist:")) {
          entry.source = `component:${tag}`;
        }
        matched = true;
        break;
      }
    }

    if (!matched) {
      // Fallback: _star_{tag}_id{N}_ pattern when DOM element is gone
      const m = path.match(/^(_star_\w+_id\d+)_/);
      if (m) {
        const tag = m[1].replace(/^_star_/, "").replace(/_id\d+$/, "").replace(/_/g, "-");
        entry.namespace = m[1];       // full instance prefix
        entry.tagName = tag;          // derived tag name
        if (!entry.source.startsWith("persist:")) {
          entry.source = `component:${tag}`;
        }
      } else if (!entry.source.startsWith("persist:")) {
        entry.namespace = "";
        entry.tagName = "";
        entry.source = "page";
      }
    }
  }
}

function detectPersistence(): void {
  for (const entry of entries.values()) entry.persistStorage = undefined;
  try { scanStorage(localStorage, "local"); } catch { /* unavailable */ }
  try { scanStorage(sessionStorage, "session"); } catch { /* unavailable */ }
}

function scanStorage(storage: Storage, type: "local" | "session"): void {
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
    } catch { /* parse error */ }
  }
}

/** Walk a nested object (from filtered()) back to [dot-path, leaf-value] tuples. */
function flattenToEntries(obj: Record<string, unknown>, prefix: string): [string, unknown][] {
  const result: [string, unknown][] = [];
  for (const key of Object.keys(obj)) {
    const fullPath = prefix ? `${prefix}.${key}` : key;
    const val = obj[key];
    if (val && typeof val === "object" && !Array.isArray(val) && !(val instanceof Date)) {
      result.push(...flattenToEntries(val as Record<string, unknown>, fullPath));
    } else {
      result.push([fullPath, val]);
    }
  }
  return result;
}

function flattenNestedObject(obj: Record<string, unknown>, prefix: string): string[] {
  const paths: string[] = [];
  for (const key of Object.keys(obj)) {
    const fullPath = prefix ? `${prefix}.${key}` : key;
    const val = obj[key];
    if (val && typeof val === "object" && !Array.isArray(val) && !(val instanceof Date)) {
      paths.push(...flattenNestedObject(val as Record<string, unknown>, fullPath));
    } else {
      paths.push(fullPath);
    }
  }
  return paths;
}

function detectType(value: unknown): SignalEntry["type"] {
  if (value === null || value === undefined) return "object";
  if (Array.isArray(value)) return "array";
  const t = typeof value;
  if (t === "string") return "string";
  if (t === "number") return "number";
  if (t === "boolean") return "boolean";
  return "object";
}

function valuesEqual(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (a === null || b === null || a === undefined || b === undefined) return false;
  if (typeof a !== typeof b) return false;
  if (typeof a === "object") {
    return safeStringify(a) === safeStringify(b);
  }
  return false;
}

function safeStringify(v: unknown): string {
  try { return JSON.stringify(v); } catch { return String(v); }
}

function prettyStringify(v: unknown): string {
  try { return JSON.stringify(v, null, 2); } catch { return String(v); }
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function notifySubscribers(): void {
  for (const fn of subscribers) fn();
}

function scheduleNotify(): void {
  if (pendingNotify) return;
  pendingNotify = true;
  requestAnimationFrame(() => {
    pendingNotify = false;
    notifySubscribers();
  });
}

export function stripNamespace(path: string, namespace: string): string {
  if (!namespace) return path;
  const m = path.match(/^_star_\w+_id\d+_(.+)$/);
  if (m) return m[1];
  const candidates = [namespace.replace(/-/g, "_"), namespace];
  for (const prefix of candidates) {
    if (path.startsWith(prefix + "_")) return path.slice(prefix.length + 1);
  }
  return path;
}

export function getGroupedEntries(filter: string): SignalGroup[] {
  const filterLower = filter.toLowerCase();

  // Build stable instance numbering from ALL live entries (before filtering)
  const tagInstances = new Map<string, string[]>();
  for (const entry of entries.values()) {
    if (entry.tagName && entry.status !== "removed") {
      let arr = tagInstances.get(entry.tagName);
      if (!arr) { arr = []; tagInstances.set(entry.tagName, arr); }
      if (!arr.includes(entry.namespace)) arr.push(entry.namespace);
    }
  }
  for (const arr of tagInstances.values()) arr.sort();

  // Group filtered entries by namespace (instance-unique)
  const groups = new Map<string, SignalEntry[]>();
  for (const entry of entries.values()) {
    if (entry.status === "removed" && Date.now() - entry.lastChanged > REMOVED_DISPLAY_MS) continue;

    if (filterLower) {
      const displayName = stripNamespace(entry.path, entry.tagName);
      if (!entry.path.toLowerCase().includes(filterLower) &&
          !displayName.toLowerCase().includes(filterLower)) {
        continue;
      }
    }

    const ns = entry.namespace;
    if (!groups.has(ns)) groups.set(ns, []);
    groups.get(ns)!.push(entry);
  }

  // Page first, then components alphabetically
  const result: SignalGroup[] = [];
  const sortedKeys = [...groups.keys()].sort((a, b) => {
    if (a === "" && b !== "") return -1;
    if (b === "" && a !== "") return 1;
    return a.localeCompare(b);
  });

  for (const ns of sortedKeys) {
    const groupEntries = groups.get(ns)!;
    groupEntries.sort((a, b) => {
      const aName = stripNamespace(a.path, a.tagName);
      const bName = stripNamespace(b.path, b.tagName);
      return aName.localeCompare(bName);
    });

    let displayName: string;
    if (ns === "") {
      displayName = "Page Signals";
    } else {
      const tag = groupEntries[0].tagName;
      const instances = tagInstances.get(tag) || [ns];
      displayName = instances.length > 1
        ? `${tag} #${instances.indexOf(ns) + 1}`
        : tag;
    }

    result.push({ namespace: ns, displayName, entries: groupEntries, count: groupEntries.length });
  }

  return result;
}

export function formatSignalValue(value: unknown, type: SignalEntry["type"]): string {
  if (value === null || value === undefined) return "null";
  switch (type) {
    case "string": {
      const s = String(value);
      return s.length > MAX_DISPLAY_STRING ? `"${s.slice(0, MAX_DISPLAY_STRING - 3)}…"` : `"${s}"`;
    }
    case "number":
    case "boolean":
      return String(value);
    case "array": {
      const arr = value as unknown[];
      return `[${arr.length} item${arr.length !== 1 ? "s" : ""}]`;
    }
    case "object": {
      const keys = Object.keys(value as object);
      return `{${keys.length} key${keys.length !== 1 ? "s" : ""}}`;
    }
    default:
      return String(value);
  }
}

export function buildGroupHeaderHtml(group: SignalGroup, collapsed: boolean): string {
  const toggle = collapsed ? "\u25B8" : "\u25BE";
  const esc = escapeHtml;
  return `<div class="signal-group-header" data-ns="${esc(group.namespace)}">` +
    `<span class="group-toggle">${toggle}</span>` +
    `<span class="group-name">${esc(group.displayName)}</span>` +
    `<span class="group-count">(${group.count})</span>` +
    `</div>`;
}

export function buildSignalRowHtml(entry: SignalEntry): string {
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
    const icon = entry.persistStorage === "local" ? "\uD83D\uDD12 local" : "\uD83D\uDD12 session";
    persistBadge = ` <span class="signal-persist">${icon}</span>`;
  }

  let statusBadge = "";
  if (entry.status === "stale") {
    statusBadge = ` <span class="signal-removed-badge">\u26A0 stale</span>`;
  } else if (entry.status === "removed") {
    statusBadge = ` <span class="signal-removed-badge">\u26A0 removed</span>`;
  }

  return `<div class="${classes}" data-path="${escapeHtml(entry.path)}" title="Click to expand">` +
    `<span class="signal-name">${escapeHtml(displayName)}</span>` +
    `<span class="signal-value ${typeClass}">${escapeHtml(formattedValue)}</span>` +
    persistBadge + statusBadge +
    `</div>`;
}

export function buildSignalDetailHtml(entry: SignalEntry): string {
  const esc = escapeHtml;
  const live = entry.status === "live";
  let html = `<div class="signal-detail">`;

  // Value row — editable input for live scalars, pre block for complex/non-live
  if (live && (entry.type === "string" || entry.type === "number")) {
    const inputType = entry.type === "number" ? "number" : "text";
    html += `<div class="sd-row sd-edit-row">` +
      `<input class="signal-detail-input" type="${inputType}" data-edit-path="${esc(entry.path)}" value="${esc(String(entry.value))}" />` +
      `</div>`;
  } else if (live && entry.type === "boolean") {
    html += `<div class="sd-row sd-edit-row">` +
      `<button class="signal-toggle-btn" data-edit-path="${esc(entry.path)}">${entry.value ? "true" : "false"}</button>` +
      `</div>`;
  } else if (live && entry.type === "array") {
    html += `<div class="sd-row"><pre>${esc(prettyStringify(entry.value))}</pre></div>`;
    html += `<div class="sd-row"><button class="signal-edit-obj-btn" data-edit-path="${esc(entry.path)}">Edit JSON</button></div>`;
  } else {
    html += `<div class="sd-row"><pre>${esc(prettyStringify(entry.value))}</pre></div>`;
  }

  // Compact metadata line: path · type · source · storage · status
  const meta: string[] = [entry.type];
  if (entry.source !== "page") meta.push(entry.source);
  if (entry.persistStorage) meta.push(`${entry.persistStorage}Storage`);
  if (entry.status !== "live") meta.push(entry.status);
  html += `<div class="sd-row sd-meta">${esc(entry.path)} · ${meta.map(esc).join(" · ")}</div>`;

  html += `</div>`;
  return html;
}

export function patchSignal(path: string, value: unknown, previousValue?: unknown): void {
  // For objects: detect removed keys and null them out (merge patch semantics)
  if (previousValue && typeof previousValue === "object" && !Array.isArray(previousValue) &&
      value && typeof value === "object" && !Array.isArray(value)) {
    const patchObj = { ...(value as Record<string, unknown>) };
    for (const k of Object.keys(previousValue as Record<string, unknown>)) {
      if (!(k in patchObj)) patchObj[k] = null;
    }
    mergePatch(dotPathToPatch(path, patchObj));
    return;
  }
  // For arrays: direct replacement (merge patch replaces arrays wholesale)
  mergePatch(dotPathToPatch(path, value));
}

function dotPathToPatch(path: string, value: unknown): Record<string, unknown> {
  const parts = path.split(".");
  if (parts.length === 1) return { [path]: value };
  const root: Record<string, unknown> = {};
  let current = root;
  for (let i = 0; i < parts.length - 1; i++) {
    const next: Record<string, unknown> = {};
    current[parts[i]] = next;
    current = next;
  }
  current[parts[parts.length - 1]] = value;
  return root;
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
