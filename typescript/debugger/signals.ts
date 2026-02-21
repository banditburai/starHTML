import { filtered, getPath, mergePatch } from "datastar";
import { escapeHtml } from "./capture";

export interface SignalEntry {
  path: string;
  value: unknown;
  type: "string" | "number" | "boolean" | "object" | "array";
  source: string;
  namespace: string;
  tagName: string;
  status: "live" | "stale" | "removed";
  lastChanged: number;
  persistStorage?: "local" | "session" | undefined;
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

const entries: Map<string, SignalEntry> = new Map();
let debuggerPrefix = "";
let excludeRe: RegExp | undefined;
let debuggerSignalNames: Set<string> = new Set();
let pollInterval: ReturnType<typeof setInterval> | null = null;
const subscribers = new Set<() => void>();
let pendingNotify = false;
let initialized = false;
let isVisible: (() => boolean) | null = null;

export function init(
  excludePrefix: string,
  excludeNames?: string[],
  visibilityFn?: () => boolean
): void {
  if (initialized) return;
  initialized = true;
  debuggerPrefix = excludePrefix;
  excludeRe = excludePrefix ? new RegExp(`^${escapeRegex(excludePrefix)}`) : undefined;
  debuggerSignalNames = new Set(excludeNames ?? []);
  if (visibilityFn) isVisible = visibilityFn;
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
  debuggerPrefix = "";
  excludeRe = undefined;
  debuggerSignalNames = new Set();
  pendingNotify = false;
  isVisible = null;
  initialized = false;
}

export function subscribe(fn: () => void): () => void {
  subscribers.add(fn);
  return () => {
    subscribers.delete(fn);
  };
}

export function getEntries(): ReadonlyMap<string, SignalEntry> {
  return entries;
}

export function getSignalCount(): number {
  let count = 0;
  for (const entry of entries.values()) {
    if (entry.status !== "removed") count++;
  }
  return count;
}

export function clearPersistedData(): void {
  const persistedPaths = new Set<string>();
  for (const [path, entry] of entries) {
    if (entry.persistStorage) persistedPaths.add(path);
  }

  for (const storage of [localStorage, sessionStorage]) {
    const keysToRemove: string[] = [];
    try {
      for (let i = 0; i < storage.length; i++) {
        const key = storage.key(i);
        if (key?.startsWith("starhtml-persist")) keysToRemove.push(key);
      }
      for (const k of keysToRemove) storage.removeItem(k);
    } catch {
      /* storage unavailable */
    }
  }

  // Force next page load to re-read DOM defaults instead of cached persist values
  (window as unknown as Record<string, unknown>).__starhtml_pc = undefined;

  // DOM attributes are the only source of truth for original default values
  if (persistedPaths.size > 0) {
    const defaults: Record<string, unknown> = {};
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

export function isDebuggerSignal(path: string): boolean {
  return (!!debuggerPrefix && path.startsWith(debuggerPrefix)) || debuggerSignalNames.has(path);
}

function onSignalPatch(e: CustomEvent): void {
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
      /* noop */
    }
  }

  if (changed) scheduleNotify();
}

function structuralPoll(): void {
  if (isVisible && !isVisible()) return;
  let result: Record<string, unknown>;
  try {
    result = filtered(excludeRe ? { exclude: excludeRe } : undefined);
  } catch {
    return;
  }

  const allSignals = flattenToEntries(result, "");
  const seenPaths = new Set<string>();

  for (const [path, value] of allSignals) {
    if (isDebuggerSignal(path)) continue;
    seenPaths.add(path);
    const entry = entries.get(path);
    if (!entry) {
      updateOrCreateEntry(path, value);
    } else {
      // Poll catches changes missed by patch events
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
  entry.value = value;
  entry.type = detectType(value);
  entry.lastChanged = Date.now();
  entry.status = "live";
}

function assignNamespace(entry: SignalEntry, namespace: string, tag: string): void {
  entry.namespace = namespace;
  entry.tagName = tag;
  if (!entry.source.startsWith("persist:")) {
    entry.source = `component:${tag}`;
  }
}

function detectNamespaces(): void {
  const nsMap = new Map<string, string>();
  try {
    for (const el of document.querySelectorAll("[data-star-id]")) {
      const id = el.getAttribute("data-star-id");
      if (id && !(debuggerPrefix && id.startsWith(debuggerPrefix))) {
        nsMap.set(id, el.tagName.toLowerCase());
      }
    }
  } catch {
    /* noop */
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
      // Fallback when DOM element is gone
      const m = path.match(/^(_star_\w+_id\d+)_/);
      if (m) {
        const tag = m[1]
          .replace(/^_star_/, "")
          .replace(/_id\d+$/, "")
          .replace(/_/g, "-");
        assignNamespace(entry, m[1], tag);
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
  try {
    scanStorage(localStorage, "local");
  } catch {
    /* noop */
  }
  try {
    scanStorage(sessionStorage, "session");
  } catch {
    /* noop */
  }
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
    } catch {
      /* noop */
    }
  }
}

function flattenToEntries(
  obj: Record<string, unknown>,
  prefix: string,
  out: [string, unknown][] = []
): [string, unknown][] {
  for (const key of Object.keys(obj)) {
    const fullPath = prefix ? `${prefix}.${key}` : key;
    const val = obj[key];
    if (val && typeof val === "object" && !Array.isArray(val) && !(val instanceof Date)) {
      flattenToEntries(val as Record<string, unknown>, fullPath, out);
    } else {
      out.push([fullPath, val]);
    }
  }
  return out;
}

export function flattenPaths(obj: Record<string, unknown>, prefix: string): string[] {
  return flattenToEntries(obj, prefix).map(([path]) => path);
}

function detectType(value: unknown): SignalEntry["type"] {
  if (value == null) return "object";
  if (Array.isArray(value)) return "array";
  const t = typeof value;
  return t === "string" || t === "number" || t === "boolean" ? t : "object";
}

export function valuesEqual(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (a == null || b == null) return false;
  if (typeof a !== typeof b) return false;
  if (typeof a === "object") {
    return safeStringify(a) === safeStringify(b);
  }
  return false;
}

function safeStringify(v: unknown, pretty = false): string {
  try {
    return pretty ? JSON.stringify(v, null, 2) : JSON.stringify(v);
  } catch {
    return String(v);
  }
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function notifySubscribers(): void {
  for (const fn of subscribers) fn();
}

// rAF (not microtask) to batch rapid signal-patch bursts into one UI render
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
    if (path.startsWith(`${prefix}_`)) return path.slice(prefix.length + 1);
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
      if (!arr) {
        arr = [];
        tagInstances.set(entry.tagName, arr);
      }
      if (!arr.includes(entry.namespace)) arr.push(entry.namespace);
    }
  }
  for (const arr of tagInstances.values()) arr.sort();

  const groups = new Map<string, SignalEntry[]>();
  for (const entry of entries.values()) {
    if (entry.status === "removed" && Date.now() - entry.lastChanged > REMOVED_DISPLAY_MS) continue;

    if (filterLower) {
      const displayName = stripNamespace(entry.path, entry.tagName);
      if (
        !entry.path.toLowerCase().includes(filterLower) &&
        !displayName.toLowerCase().includes(filterLower)
      ) {
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

  const result: SignalGroup[] = [];
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

    let displayName: string;
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
  return `<div class="signal-group-header" data-ns="${esc(group.namespace)}"><span class="group-toggle">${toggle}</span><span class="group-name">${esc(group.displayName)}</span><span class="group-count">(${group.count})</span></div>`;
}

export function buildSignalRowHtml(entry: SignalEntry): string {
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

  const statusBadge =
    entry.status === "stale" || entry.status === "removed"
      ? ` <span class="signal-removed-badge">\u26A0 ${entry.status}</span>`
      : "";

  return `<div class="${classes}" data-path="${esc(entry.path)}" title="Click to expand"><span class="signal-name">${esc(displayName)}</span><span class="signal-value ${typeClass}">${esc(formattedValue)}</span>${persistBadge}${statusBadge}</div>`;
}

export function buildSignalDetailHtml(entry: SignalEntry): string {
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

  const meta: string[] = [entry.type];
  if (entry.source !== "page") meta.push(entry.source);
  if (entry.persistStorage) meta.push(`${entry.persistStorage}Storage`);
  if (entry.status !== "live") meta.push(entry.status);
  html += `<div class="sd-row sd-meta">${esc(entry.path)} · ${meta.map(esc).join(" · ")}</div>`;

  html += "</div>";
  return html;
}

const isPlainObj = (v: unknown): v is Record<string, unknown> =>
  !!v && typeof v === "object" && !Array.isArray(v);

export function patchSignal(path: string, value: unknown, previousValue?: unknown): void {
  // RFC 7386: null values in merge patch trigger key deletion
  if (isPlainObj(previousValue) && isPlainObj(value)) {
    const patchObj = { ...value };
    for (const k of Object.keys(previousValue)) {
      if (!(k in patchObj)) patchObj[k] = null;
    }
    mergePatch(dotPathToPatch(path, patchObj));
    return;
  }
  // Merge patch replaces arrays wholesale — no per-element diffing
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
