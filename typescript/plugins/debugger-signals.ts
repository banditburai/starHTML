// debugger-signals.ts — Signal tracking data layer for the StarHTML debugger.
// Standalone module consumed by the StarElements debugger component.

import { filtered, getPath } from "datastar";

// ─── Interfaces ────────────────────────────────────────────────────

export interface SignalEntry {
  path: string;
  value: unknown;
  previousValue: unknown;
  type: "string" | "number" | "boolean" | "object" | "array";
  source: string;        // "page", "component:my-counter", "persist:starhtml-persist"
  namespace: string;     // "" for page-level, component tag, or persist key
  status: "live" | "stale" | "removed";
  lastChanged: number;   // Date.now() timestamp
  persistStorage?: "local" | "session";
}

export interface SignalGroup {
  namespace: string;
  displayName: string;   // "Page Signals", component tag, persist key
  entries: SignalEntry[];
  count: number;
}

// ─── State ─────────────────────────────────────────────────────────

const entries: Map<string, SignalEntry> = new Map();
let debuggerPrefix = "";
let debuggerSignalNames: Set<string> = new Set();
let pollInterval: ReturnType<typeof setInterval> | null = null;
const subscribers = new Set<() => void>();

let pendingNotify = false;
let initialized = false;

// Previous value size cap (1KB serialized)
const MAX_PREV_VALUE_SIZE = 1024;

// ─── Public API ────────────────────────────────────────────────────

/** Initialize signal tracking. excludePrefix filters the debugger's namespaced signals;
 *  excludeNames filters un-namespaced Local() signal names (created by data-bind). */
export function init(excludePrefix: string, excludeNames?: string[]): void {
  if (initialized) return;
  initialized = true;
  debuggerPrefix = excludePrefix;
  debuggerSignalNames = new Set(excludeNames || []);
  document.addEventListener("datastar-signal-patch", onSignalPatch as EventListener);
  structuralPoll();  // initial poll
  pollInterval = setInterval(structuralPoll, 2000);
}

/** Clean up listeners and timers. */
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

/** Subscribe to signal changes. Returns unsubscribe function. */
export function subscribe(fn: () => void): () => void {
  subscribers.add(fn);
  return () => { subscribers.delete(fn); };
}

/** Get all signal entries. */
export function getEntries(): Map<string, SignalEntry> {
  return entries;
}

/** Get total signal count (excluding removed). */
export function getSignalCount(): number {
  let count = 0;
  for (const entry of entries.values()) {
    if (entry.status !== "removed") count++;
  }
  return count;
}

/** Clear all persisted signal data from storage. */
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

// ─── Exclusion ─────────────────────────────────────────────────────

function isDebuggerSignal(path: string): boolean {
  if (debuggerPrefix && path.startsWith(debuggerPrefix)) return true;
  if (debuggerSignalNames.has(path)) return true;
  return false;
}

// ─── Patch Listener ────────────────────────────────────────────────

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

// ─── Structural Poll ───────────────────────────────────────────────

function structuralPoll(): void {
  const excludeRe = debuggerPrefix ? new RegExp("^" + escapeRegex(debuggerPrefix)) : undefined;
  let result: Record<string, unknown>;
  try {
    // filtered() returns a nested object (not an array), e.g. { count: 3, theme: "dark" }
    result = filtered(excludeRe ? { exclude: excludeRe } : undefined) as unknown as Record<string, unknown>;
  } catch { return; }

  // Flatten nested object to [path, value] pairs
  const allSignals = flattenToEntries(result, "");
  const seenPaths = new Set<string>();

  for (const [path, value] of allSignals) {
    seenPaths.add(path);
    if (!entries.has(path)) {
      updateOrCreateEntry(path, value);
    } else {
      // Update value if changed (poll catches changes missed by patch events)
      const entry = entries.get(path)!;
      if (!valuesEqual(entry.value, value)) {
        updateExistingEntry(entry, value);
      }
      if (entry.status === "stale") entry.status = "live";
    }
  }

  // Mark disappeared signals
  for (const [path, entry] of entries) {
    if (!seenPaths.has(path)) {
      if (entry.status === "live") entry.status = "stale";
      else if (entry.status === "stale") entry.status = "removed";
    }
  }

  // Clean up entries that have been "removed" for a full cycle
  for (const [path, entry] of entries) {
    if (entry.status === "removed" && Date.now() - entry.lastChanged > 6000) {
      entries.delete(path);
    }
  }

  detectNamespaces();
  detectPersistence();
  notifySubscribers();
}

// ─── Entry Management ──────────────────────────────────────────────

function updateOrCreateEntry(path: string, value: unknown): boolean {
  const existing = entries.get(path);
  if (existing) {
    if (valuesEqual(existing.value, value)) return false;
    updateExistingEntry(existing, value);
    return true;
  }

  // Create new entry
  entries.set(path, {
    path,
    value,
    previousValue: null,
    type: detectType(value),
    source: "page",
    namespace: "",
    status: "live",
    lastChanged: Date.now(),
  });
  return true;
}

function updateExistingEntry(entry: SignalEntry, value: unknown): void {
  // Cap previousValue size
  const prevStr = safeStringify(entry.value);
  entry.previousValue = prevStr.length <= MAX_PREV_VALUE_SIZE ? entry.value : "[too large]";
  entry.value = value;
  entry.type = detectType(value);
  entry.lastChanged = Date.now();
  entry.status = "live";
}

// ─── Namespace Detection ───────────────────────────────────────────

function detectNamespaces(): void {
  // Phase 1: DOM walk for [data-star-id] elements
  const nsMap = new Map<string, string>();
  try {
    document.querySelectorAll("[data-star-id]").forEach(el => {
      const id = el.getAttribute("data-star-id");
      if (id && !(debuggerPrefix && id.startsWith(debuggerPrefix))) {
        nsMap.set(id, el.tagName.toLowerCase());
      }
    });
  } catch { /* DOM query failed */ }

  // Phase 2: Assign namespaces to entries
  for (const [path, entry] of entries) {
    let matched = false;

    // Check DOM-based namespaces first
    for (const [prefix, tag] of nsMap) {
      if (path.startsWith(prefix + "_") || path === prefix) {
        entry.namespace = tag;
        if (!entry.source.startsWith("persist:")) {
          entry.source = `component:${tag}`;
        }
        matched = true;
        break;
      }
    }

    if (!matched) {
      // Regex fallback for _star_{tag}_id{N}_ pattern
      const m = path.match(/^(_star_\w+_id\d+)_/);
      if (m) {
        const tag = m[1].replace(/^_star_/, "").replace(/_id\d+$/, "").replace(/_/g, "-");
        entry.namespace = tag;
        if (!entry.source.startsWith("persist:")) {
          entry.source = `component:${tag}`;
        }
      } else if (!entry.source.startsWith("persist:")) {
        entry.namespace = "";
        entry.source = "page";
      }
    }
  }
}

// ─── Persistence Detection ─────────────────────────────────────────

function detectPersistence(): void {
  // Clear existing persist flags
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

// ─── Helpers ───────────────────────────────────────────────────────

/** Flatten a nested object into [dot-path, value] tuples (for filtered() results). */
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

/** Flatten a nested object into dot-path keys. */
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

// ─── Notification ──────────────────────────────────────────────────

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

// ─── Render Helpers ────────────────────────────────────────────────

/** Strip namespace prefix from a signal path for display. */
export function stripNamespace(path: string, namespace: string): string {
  if (!namespace) return path;
  // Regex: _star_{tag}_id{N}_ prefix
  const m = path.match(/^_star_\w+_id\d+_(.+)$/);
  if (m) return m[1];
  // DOM-based: try stripping namespace + _
  const candidates = [namespace.replace(/-/g, "_"), namespace];
  for (const prefix of candidates) {
    if (path.startsWith(prefix + "_")) return path.slice(prefix.length + 1);
  }
  return path;
}

/** Get entries grouped by namespace, optionally filtered. */
export function getGroupedEntries(filter: string): SignalGroup[] {
  const filterLower = filter.toLowerCase();
  const groups = new Map<string, SignalEntry[]>();

  for (const entry of entries.values()) {
    if (entry.status === "removed" && Date.now() - entry.lastChanged > 4000) continue;

    // Filter check
    if (filterLower) {
      const displayName = stripNamespace(entry.path, entry.namespace);
      if (!entry.path.toLowerCase().includes(filterLower) &&
          !displayName.toLowerCase().includes(filterLower)) {
        continue;
      }
    }

    const ns = entry.namespace;
    if (!groups.has(ns)) groups.set(ns, []);
    groups.get(ns)!.push(entry);
  }

  // Sort groups: page first, then components alphabetically, then persist
  const result: SignalGroup[] = [];
  const sortedKeys = [...groups.keys()].sort((a, b) => {
    if (a === "" && b !== "") return -1;
    if (b === "" && a !== "") return 1;
    return a.localeCompare(b);
  });

  for (const ns of sortedKeys) {
    const groupEntries = groups.get(ns)!;
    // Sort entries alphabetically by display name within group
    groupEntries.sort((a, b) => {
      const aName = stripNamespace(a.path, a.namespace);
      const bName = stripNamespace(b.path, b.namespace);
      return aName.localeCompare(bName);
    });

    result.push({
      namespace: ns,
      displayName: ns === "" ? "Page Signals" : ns,
      entries: groupEntries,
      count: groupEntries.length,
    });
  }

  return result;
}

/** Format a signal value for display (truncated). */
export function formatSignalValue(value: unknown, type: SignalEntry["type"]): string {
  if (value === null || value === undefined) return "null";
  switch (type) {
    case "string": {
      const s = String(value);
      return s.length > 40 ? `"${s.slice(0, 37)}…"` : `"${s}"`;
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

/** Build HTML for a group header. */
export function buildGroupHeaderHtml(group: SignalGroup, collapsed: boolean): string {
  const toggle = collapsed ? "\u25B8" : "\u25BE";
  const esc = escapeHtml;
  return `<div class="signal-group-header" data-ns="${esc(group.namespace)}">` +
    `<span class="group-toggle">${toggle}</span>` +
    `<span class="group-name">${esc(group.displayName)}</span>` +
    `<span class="group-count">(${group.count})</span>` +
    `</div>`;
}

/** Build HTML for a signal row. */
export function buildSignalRowHtml(entry: SignalEntry): string {
  const displayName = stripNamespace(entry.path, entry.namespace);
  const formattedValue = formatSignalValue(entry.value, entry.type);
  const typeClass = `sv-${entry.type}`;
  const isChanged = Date.now() - entry.lastChanged < 2000;

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

  return `<div class="${classes}" data-path="${escapeHtml(entry.path)}" title="Click to copy path">` +
    `<span class="signal-name">${escapeHtml(displayName)}</span>` +
    `<span class="signal-value ${typeClass}">${escapeHtml(formattedValue)}</span>` +
    persistBadge + statusBadge +
    `</div>`;
}

/** Build HTML for an expanded signal detail view. */
export function buildSignalDetailHtml(entry: SignalEntry): string {
  const esc = escapeHtml;
  let html = `<div class="signal-detail">`;
  html += `<div class="sd-row"><span class="sd-label">Path:</span> ${esc(entry.path)}</div>`;
  html += `<div class="sd-row"><span class="sd-label">Value:</span><pre>${esc(prettyStringify(entry.value))}</pre></div>`;
  if (entry.previousValue !== null) {
    html += `<div class="sd-row"><span class="sd-label">Previous:</span><pre>${esc(prettyStringify(entry.previousValue))}</pre></div>`;
  }
  html += `<div class="sd-row"><span class="sd-label">Type:</span> ${esc(entry.type)}</div>`;
  html += `<div class="sd-row"><span class="sd-label">Source:</span> ${esc(entry.source)}</div>`;
  if (entry.status !== "live") {
    html += `<div class="sd-row"><span class="sd-label">Status:</span> ${esc(entry.status)}</div>`;
  }
  if (entry.persistStorage) {
    html += `<div class="sd-row"><span class="sd-label">Storage:</span> ${entry.persistStorage}Storage</div>`;
  }
  html += `</div>`;
  return html;
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
