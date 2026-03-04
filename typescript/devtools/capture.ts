import { drainRecords, isDevtoolsMutation, subscribeCapture } from "./dom-observer";

export interface DatastarFetchDetail {
  type: string;
  el: HTMLElement | null;
  argsRaw: Record<string, unknown>;
}

export interface DebugMeta {
  seq: number;
  ts: number;
  handler: string;
  route: string;
}

export function parseDatastarFetchDetail(e: Event): DatastarFetchDetail {
  return (e as CustomEvent<DatastarFetchDetail>).detail;
}

export function extractDebugMeta(argsRaw: Record<string, unknown>): DebugMeta | undefined {
  if (argsRaw["x-debug-seq"] == null) return undefined;
  return {
    seq: Number(argsRaw["x-debug-seq"]),
    ts: Number(argsRaw["x-debug-ts"]),
    handler: String(argsRaw["x-debug-handler"] ?? ""),
    route: String(argsRaw["x-debug-route"] ?? ""),
  };
}

export function stripDebugKeys(argsRaw: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(argsRaw)) {
    if (!k.startsWith("x-debug-")) out[k] = v;
  }
  return out;
}

interface SerializedMorph {
  type: "childList" | "attributes" | "characterData";
  targetSelector: string;
  attributeName?: string;
  oldValue?: string;
  newValue?: string;
  added?: string[];
  removed?: string[];
  flash?: boolean;
}

export interface DebugSSEEvent {
  id: number;
  type: string;
  timestamp: number;
  el: HTMLElement | null;
  argsRaw: Record<string, unknown>;
  debugMeta?: DebugMeta;
  morphs?: SerializedMorph[];
  groupId?: number;
  duration?: number;
}

const TYPE_CONFIG: Record<string, { label: string; cls: string }> = {
  "datastar-patch-signals": { label: "signals", cls: "type-signals" },
  "datastar-patch-elements": { label: "elements", cls: "type-elements" },
  "datastar-execute-script": { label: "script", cls: "type-script" },
  started: { label: "start", cls: "type-lifecycle" },
  finished: { label: "done", cls: "type-lifecycle" },
  error: { label: "error", cls: "type-error" },
  retrying: { label: "retry", cls: "type-lifecycle" },
  "retries-failed": { label: "failed", cls: "type-error" },
  "sse-malformed": { label: "malformed", cls: "type-malformed" },
};

export const CHIP_CATEGORIES: { key: string; label: string; cls: string; types: string[] }[] = [
  { key: "signals", label: "signals", cls: "chip-signals", types: ["datastar-patch-signals"] },
  { key: "elements", label: "elements", cls: "chip-elements", types: ["datastar-patch-elements"] },
  { key: "script", label: "script", cls: "chip-script", types: ["datastar-execute-script"] },
  {
    key: "lifecycle",
    label: "lifecycle",
    cls: "chip-lifecycle",
    types: ["started", "finished", "retrying"],
  },
];

/** Always shown regardless of chip filter state. */
export const ERROR_TYPES = new Set(["sse-malformed", "error", "retries-failed"]);

const MAX_EVENTS = 3000;
const PRESERVE_INITIAL = 200;
const EVICT_BATCH = 500;
const events: DebugSSEEvent[] = [];
let nextEventId = 0;

const subscribers = new Set<() => void>();

export function subscribe(fn: () => void): () => void {
  subscribers.add(fn);
  return () => {
    subscribers.delete(fn);
  };
}

export function getEvents(): readonly DebugSSEEvent[] {
  return events;
}

export function getEventCount(): number {
  return events.length;
}

const LIFECYCLE_TYPES = new Set(["started", "finished", "retrying"]);

/** Excludes lifecycle bookends (started/finished/retrying). */
export function getDataEventCount(): number {
  let count = 0;
  for (const ev of events) {
    if (!LIFECYCLE_TYPES.has(ev.type)) count++;
  }
  return count;
}

export function getFilteredEvents(
  sinceId: number,
  typeFilter: Set<string> | null,
  textFilter: string
): DebugSSEEvent[] {
  const needle = textFilter.toLowerCase();
  return events.filter((ev) => {
    if (ev.id < sinceId) return false;
    if (typeFilter && !typeFilter.has(ev.type) && !ERROR_TYPES.has(ev.type)) return false;
    if (needle) {
      const haystack = [
        TYPE_CONFIG[ev.type]?.label ?? ev.type,
        ev.debugMeta?.handler ?? "",
        ev.debugMeta?.route ?? "",
        ev.type,
      ];
      if (!haystack.some((s) => s.toLowerCase().includes(needle))) return false;
    }
    return true;
  });
}

export function buildAllowedTypes(activeChipKeys: Set<string>): Set<string> | null {
  if (activeChipKeys.size === 0) return null;
  const allowed = new Set<string>();
  for (const chip of CHIP_CATEGORIES) {
    if (activeChipKeys.has(chip.key)) {
      for (const t of chip.types) allowed.add(t);
    }
  }
  return allowed;
}

let morphWindow: { records: MutationRecord[] } | null = null;
let unsubObserver: (() => void) | null = null;
const MAX_MORPH_RECORDS = 500;

function handleMutationRecords(records: MutationRecord[]): void {
  if (!morphWindow) return;
  for (const r of records) {
    if (morphWindow.records.length >= MAX_MORPH_RECORDS) break;
    if (isDevtoolsMutation(r)) continue;
    morphWindow.records.push(r);
  }
}

export function startObserving(): void {
  if (unsubObserver) return;
  unsubObserver = subscribeCapture(handleMutationRecords);
}

export function stopObserving(): void {
  if (!unsubObserver) return;
  // Dispatches to all active consumers (including timeline) before we unsubscribe
  drainRecords();
  unsubObserver();
  unsubObserver = null;
}

function deepDecodeJsonStrings(val: unknown): unknown {
  if (typeof val === "string") {
    const trimmed = val.trim();
    if (
      (trimmed.startsWith("{") && trimmed.endsWith("}")) ||
      (trimmed.startsWith("[") && trimmed.endsWith("]"))
    ) {
      try {
        return deepDecodeJsonStrings(JSON.parse(trimmed));
      } catch {
        /* not JSON */
      }
    }
    return val;
  }
  if (Array.isArray(val)) return val.map(deepDecodeJsonStrings);
  if (val && typeof val === "object") {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(val)) out[k] = deepDecodeJsonStrings(v);
    return out;
  }
  return val;
}

export function selectorPath(el: Element): string {
  if (el.id) return `#${el.id}`;
  let path = el.tagName.toLowerCase();
  if (el.className && typeof el.className === "string") {
    path += `.${el.className.trim().split(/\s+/).slice(0, 2).join(".")}`;
  }
  return path;
}

function serializeMorphRecords(records: MutationRecord[]): SerializedMorph[] {
  const elementIds = new WeakMap<Element, number>();
  const attrChanges = new Map<string, number>();
  let nextElId = 0;

  for (const r of records) {
    if (r.type === "attributes" && r.target instanceof Element) {
      // setAttribute fires MutationObserver even when the value is unchanged
      const oldVal = r.oldValue ?? "";
      const curVal = r.target.getAttribute(r.attributeName ?? "") ?? "";
      if (oldVal === curVal) continue;
      if (!elementIds.has(r.target)) elementIds.set(r.target, nextElId++);
      const key = `${elementIds.get(r.target)}[${r.attributeName}]`;
      attrChanges.set(key, (attrChanges.get(key) ?? 0) + 1);
    }
  }

  const morphs: SerializedMorph[] = [];
  for (const r of records) {
    if (r.type === "childList") {
      const parent = r.target instanceof Element ? selectorPath(r.target) : r.target.nodeName;
      const added: string[] = [];
      for (const node of r.addedNodes) {
        if (node instanceof Element) added.push(`<${selectorPath(node)}>`);
        else if (node.nodeType === Node.TEXT_NODE)
          added.push(`"${(node.textContent ?? "").slice(0, 40)}"`);
      }
      const removed: string[] = [];
      for (const node of r.removedNodes) {
        if (node instanceof Element) removed.push(`<${selectorPath(node)}>`);
        else if (node.nodeType === Node.TEXT_NODE)
          removed.push(`"${(node.textContent ?? "").slice(0, 40)}"`);
      }
      if (added.length > 0 || removed.length > 0) {
        morphs.push({ type: "childList", targetSelector: parent, added, removed });
      }
    } else if (r.type === "attributes" && r.target instanceof Element) {
      const sel = selectorPath(r.target);
      const attr = r.attributeName ?? "";
      const oldVal = r.oldValue ?? "";
      const newVal = r.target.getAttribute(attr) ?? "";
      if (oldVal === newVal) continue;
      const elId = elementIds.get(r.target);
      const key = `${elId}[${attr}]`;
      const flash = (attrChanges.get(key) ?? 0) > 1;
      morphs.push({
        type: "attributes",
        targetSelector: sel,
        attributeName: attr,
        oldValue: oldVal,
        newValue: newVal,
        flash,
      });
    } else if (r.type === "characterData") {
      const parent = r.target.parentElement;
      const sel = parent ? selectorPath(parent) : "#text";
      morphs.push({ type: "characterData", targetSelector: sel, oldValue: r.oldValue ?? "" });
    }
  }
  return morphs;
}

let nextGroupId = 0;
const openGroups = new WeakMap<HTMLElement, { groupId: number; startTime: number }>();

let sseListener: ((e: Event) => void) | null = null;

function captureSSEEvents(): void {
  sseListener = (e: Event) => {
    const { type, el, argsRaw } = parseDatastarFetchDetail(e);
    const debugMeta = extractDebugMeta(argsRaw);

    const event: DebugSSEEvent = {
      id: nextEventId++,
      type,
      timestamp: Date.now(),
      el,
      argsRaw: { ...argsRaw },
      ...(debugMeta && { debugMeta }),
    };

    // Request grouping: started opens a group, finished closes it
    if (type === "started" && el) {
      const gid = nextGroupId++;
      openGroups.set(el, { groupId: gid, startTime: event.timestamp });
      event.groupId = gid;
    } else if (el) {
      const group = openGroups.get(el);
      if (group) {
        event.groupId = group.groupId;
        if (type === "finished" || type === "error" || type === "retries-failed") {
          event.duration = event.timestamp - group.startTime;
          openGroups.delete(el);
        }
      }
    }

    addEvent(event);

    if (type === "datastar-patch-elements") {
      morphWindow = { records: [] };
      setTimeout(() => {
        if (morphWindow) {
          event.morphs = serializeMorphRecords(morphWindow.records);
          morphWindow = null;
        }
      }, 0);
    }
  };
  document.addEventListener("datastar-fetch", sseListener);
}

let pendingNotify = false;

function scheduleNotify(): void {
  if (pendingNotify) return;
  pendingNotify = true;
  queueMicrotask(() => {
    pendingNotify = false;
    for (const fn of subscribers) fn();
  });
}

function addEvent(event: DebugSSEEvent): void {
  events.push(event);
  if (events.length > MAX_EVENTS) {
    events.splice(PRESERVE_INITIAL, EVICT_BATCH);
  }
  scheduleNotify();
}

export function injectEvent(partial: Omit<DebugSSEEvent, "id">): void {
  addEvent({ ...partial, id: nextEventId++ });
}

function splitArgs(argsRaw: Record<string, unknown>): {
  args: Record<string, unknown>;
  htmlStrings: [string, string][];
} {
  const args: Record<string, unknown> = {};
  const htmlStrings: [string, string][] = [];
  for (const [k, v] of Object.entries(argsRaw)) {
    if (k.startsWith("x-debug-")) continue;
    if (typeof v === "string" && v.trimStart().startsWith("<")) {
      htmlStrings.push([k, v]);
    } else {
      args[k] = v;
    }
  }
  return { args, htmlStrings };
}

export function formatDuration(ms: number | undefined): string {
  if (ms == null) return "";
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${Math.round(ms)}ms`;
}

export function formatTime(ts: number): string {
  const d = new Date(ts);
  return `${d.toTimeString().slice(0, 8)}.${String(d.getMilliseconds()).padStart(3, "0")}`;
}

const ESCAPE_MAP: Record<string, string> = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
};
export function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) => ESCAPE_MAP[c]);
}

function highlightHtml(raw: string): string {
  return raw.replace(
    /(<\/?)([\w-]+)((?:\s+[\w-]+(?:=(?:"[^"]*"|'[^']*'|[^\s>]*))?)*)\s*(\/?>)|([^<]+)/g,
    (
      _match,
      open: string | undefined,
      tag: string | undefined,
      attrs: string | undefined,
      close: string | undefined,
      text: string | undefined
    ) => {
      if (text !== undefined) {
        return `<span class="hx">${escapeHtml(text)}</span>`;
      }
      let out = `<span class="ht">${escapeHtml(open ?? "")}${escapeHtml(tag ?? "")}</span>`;
      if (attrs) {
        out += attrs
          .replace(
            /([\w-]+)(=)("[^"]*"|'[^']*'|[^\s>]*)/g,
            (_m: string, name: string, eq: string, val: string) =>
              `<span class="ha">${escapeHtml(name)}</span>${eq}<span class="hv">${escapeHtml(val)}</span>`
          )
          .replace(
            /(?:^|\s)([\w-]+)(?=\s|$)/g,
            (_m: string, name: string) => ` <span class="ha">${escapeHtml(name)}</span>`
          );
      }
      out += `<span class="ht">${escapeHtml(close ?? "")}</span>`;
      return out;
    }
  );
}

function eventPreview(ev: DebugSSEEvent): string {
  const args = ev.argsRaw;
  if (ev.type === "datastar-patch-signals") {
    const raw = args.signals;
    if (typeof raw === "string") {
      try {
        const obj = JSON.parse(raw);
        return Object.entries(obj)
          .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
          .join(", ")
          .slice(0, 60);
      } catch {
        /* fall through */
      }
    }
    return "";
  }
  if (ev.type === "datastar-patch-elements") {
    return `${String(args.mode ?? "outer")} ${String(args.selector ?? "")}`;
  }
  if (ev.type === "datastar-execute-script") {
    return String(args.script ?? "").slice(0, 40);
  }
  if (ev.type === "started") {
    const route = ev.debugMeta?.route ?? "";
    if (route) return route;
    if (ev.el) {
      for (const attr of ev.el.attributes) {
        if (attr.name.startsWith("data-on-") && attr.value) {
          const match = attr.value.match(/(?:get|post|put|patch|delete)\s*\(\s*['"]([^'"]+)/i);
          if (match) return match[1];
        }
      }
    }
  }
  if (ev.type === "sse-malformed") {
    const code = String(ev.argsRaw.code ?? "");
    const msg = String(ev.argsRaw.message ?? "");
    return code ? `${code}: ${msg}`.slice(0, 80) : msg.slice(0, 80);
  }
  return "";
}

function countMorphs(morphs: SerializedMorph[]): {
  added: number;
  removed: number;
  attrs: number;
  char: number;
} {
  let added = 0;
  let removed = 0;
  let attrs = 0;
  let char = 0;
  for (const m of morphs) {
    if (m.type === "childList") {
      if ((m.added?.length ?? 0) > 0) added++;
      if ((m.removed?.length ?? 0) > 0) removed++;
    } else if (m.type === "attributes") attrs++;
    else if (m.type === "characterData") char++;
  }
  return { added, removed, attrs, char };
}

function morphBadge(ev: DebugSSEEvent): string {
  if (!ev.morphs || ev.morphs.length === 0) return "";
  const { added, removed, attrs } = countMorphs(ev.morphs);
  return `+${added} -${removed} ~${attrs}`;
}

export function buildRowHtml(ev: DebugSSEEvent): string {
  const cfg = TYPE_CONFIG[ev.type] ?? {
    label: ev.type.replace("datastar-", ""),
    cls: "type-lifecycle",
  };
  const handler = ev.debugMeta?.handler ?? "";
  const route = ev.debugMeta?.route ?? "";
  const preview = eventPreview(ev);
  const badge = morphBadge(ev);
  const groupCls = ev.groupId != null ? ` group-${ev.groupId % 3}` : "";
  const errorCls = ERROR_TYPES.has(ev.type) ? " event-row-error" : "";
  const dur = formatDuration(ev.duration);

  return `<div class="event-row${groupCls}${errorCls}" data-eid="${ev.id}">
    <span class="event-time">${formatTime(ev.timestamp)}</span>
    <span class="event-type ${cfg.cls}">${escapeHtml(cfg.label)}</span>
    ${dur ? `<span class="event-duration">(${dur})</span>` : ""}
    ${handler ? `<span class="event-handler">${escapeHtml(handler)}</span>` : ""}
    ${preview ? `<span class="event-preview">${escapeHtml(preview)}</span>` : ""}
    ${badge ? `<span class="morph-badge">${escapeHtml(badge)}</span>` : ""}
    ${!preview && route ? `<span class="event-route">${escapeHtml(route)}</span>` : ""}
  </div>`;
}

export function formatEventDetail(ev: DebugSSEEvent): string {
  const sections: string[] = [];

  if (ev.debugMeta) {
    sections.push(
      `<div class="detail-section"><b>seq:</b> ${ev.debugMeta.seq}  <b>ts:</b> ${ev.debugMeta.ts}  <b>handler:</b> ${escapeHtml(ev.debugMeta.handler)}  <b>route:</b> ${escapeHtml(ev.debugMeta.route)}</div>`
    );
  }

  const { args: allArgs, htmlStrings } = splitArgs(ev.argsRaw);
  const { mode: rawMode, selector: rawSel, ...args } = allArgs;

  if (ev.type === "datastar-patch-elements" && (rawMode || rawSel)) {
    const mode = String(rawMode ?? "morph");
    const sel = String(rawSel ?? "");
    sections.push(
      `<div class="detail-section"><div class="detail-header"><span class="mode-badge">${escapeHtml(mode)}</span><span class="ht">→</span> <span class="target">${escapeHtml(sel)}</span></div></div>`
    );
  }

  if (Object.keys(args).length > 0) {
    const decoded = deepDecodeJsonStrings(args);
    sections.push(
      `<div class="detail-section">${escapeHtml(JSON.stringify(decoded, null, 2))}</div>`
    );
  }

  for (const [key, html] of htmlStrings) {
    sections.push(
      `<div class="detail-section"><div class="detail-label">${escapeHtml(key)}</div><div class="html-block">${highlightHtml(html)}</div></div>`
    );
  }

  if (ev.morphs && ev.morphs.length > 0) {
    const {
      added: addedCount,
      removed: removedCount,
      attrs: attrsCount,
      char: charCount,
    } = countMorphs(ev.morphs);

    let summary = `<div class="morph-summary"><b>morphs:</b> ${addedCount} added, ${removedCount} removed, ${attrsCount} attributes`;
    if (charCount > 0) summary += `, ${charCount} text`;
    summary += "</div>";

    let items = "";
    for (const m of ev.morphs) {
      if (m.type === "childList") {
        for (const desc of m.added ?? []) {
          items += `<div class="morph-item"><span class="added">+</span> Added <span class="selector">${escapeHtml(desc)}</span> to <span class="selector">${escapeHtml(m.targetSelector)}</span></div>`;
        }
        for (const desc of m.removed ?? []) {
          items += `<div class="morph-item"><span class="removed">-</span> Removed <span class="selector">${escapeHtml(desc)}</span> from <span class="selector">${escapeHtml(m.targetSelector)}</span></div>`;
        }
      } else if (m.type === "attributes") {
        const flash = m.flash ? ` <span class="flash-warn">&#9888; flash</span>` : "";
        const diff = diffAttrValue(m.attributeName ?? "", m.oldValue ?? "", m.newValue ?? "");
        const diffHtml = renderDiffHtml(diff);
        items += `<div class="morph-item"><span class="changed">~</span> <span class="selector">${escapeHtml(m.targetSelector)}</span> [${escapeHtml(m.attributeName ?? "")}] ${diffHtml}${flash}</div>`;
      } else if (m.type === "characterData") {
        items += `<div class="morph-item">~ text in <span class="selector">${escapeHtml(m.targetSelector)}</span></div>`;
      }
    }

    sections.push(
      `<div class="detail-section">${summary}${items ? `<div class="morph-list">${items}</div>` : ""}</div>`
    );
  }

  return sections.join("");
}

export function formatSingleEventForExport(ev: DebugSSEEvent): string {
  const cfg = TYPE_CONFIG[ev.type] ?? { label: ev.type.replace("datastar-", "") };
  const durStr = formatDuration(ev.duration);
  const dur = durStr ? ` (${durStr})` : "";
  const preview = eventPreview(ev);
  let out = `[${formatTime(ev.timestamp)}] ${cfg.label}${dur}${preview ? `  ${preview}` : ""}`;

  if (ev.debugMeta) {
    out += `\n  handler: ${ev.debugMeta.handler}  route: ${ev.debugMeta.route}`;
  }

  const { args, htmlStrings } = splitArgs(ev.argsRaw);
  if (Object.keys(args).length > 0) {
    const decoded = deepDecodeJsonStrings(args);
    out += `\n  ${JSON.stringify(decoded, null, 2).replace(/\n/g, "\n  ")}`;
  }
  for (const [key, html] of htmlStrings) {
    out += `\n  ${key}:\n    ${html.replace(/\n/g, "\n    ")}`;
  }

  if (ev.morphs && ev.morphs.length > 0) {
    const { added, removed, attrs } = countMorphs(ev.morphs);
    out += `\n  morphs: ${added} added, ${removed} removed, ${attrs} attributes`;
    for (const m of ev.morphs) {
      if (m.type === "childList") {
        for (const desc of m.added ?? []) out += `\n    + Added ${desc} to ${m.targetSelector}`;
        for (const desc of m.removed ?? [])
          out += `\n    - Removed ${desc} from ${m.targetSelector}`;
      } else if (m.type === "attributes") {
        out += `\n    ~ ${m.targetSelector} [${m.attributeName}] ${m.oldValue} → ${m.newValue}${m.flash ? " ⚠ flash" : ""}`;
      }
    }
  }
  return out;
}

export function formatAllEventsForExport(filteredEvents: DebugSSEEvent[]): string {
  const header = `=== StarHTML DevTools Events (${filteredEvents.length} events) ===`;
  return `${header}\n\n${filteredEvents.map(formatSingleEventForExport).join("\n")}`;
}

let initialized = false;

export function init(): void {
  if (initialized) return;
  initialized = true;
  captureSSEEvents();
  console.log("[starhtml-devtools] initialized");
}

export function cleanup(): void {
  if (sseListener) {
    document.removeEventListener("datastar-fetch", sseListener);
    sseListener = null;
  }
  stopObserving();
  subscribers.clear();
  events.length = 0;
  nextEventId = 0;
  nextGroupId = 0;
  morphWindow = null;
  pendingNotify = false;
  initialized = false;
}

// ─── Attribute Diff ───────────────────────────────────────────────

interface DiffSegment {
  text: string;
  type: "added" | "removed";
}

interface AttrDiff {
  isTokenDiff: boolean;
  segments: DiffSegment[];
}

export function diffAttrValue(attrName: string, oldValue: string, newValue: string): AttrDiff {
  if (oldValue === newValue) return { isTokenDiff: false, segments: [] };
  if (attrName === "class") return tokenDiff(oldValue, newValue);
  return rawDiff(oldValue, newValue);
}

function rawDiff(old: string, cur: string): AttrDiff {
  const segments: DiffSegment[] = [];
  if (old) segments.push({ text: old, type: "removed" });
  if (cur) segments.push({ text: cur, type: "added" });
  return { isTokenDiff: false, segments };
}

function tokenDiff(old: string, cur: string): AttrDiff {
  const oldSet = new Set(old.split(/\s+/).filter(Boolean));
  const newSet = new Set(cur.split(/\s+/).filter(Boolean));

  const segments: DiffSegment[] = [];
  for (const t of oldSet) {
    if (!newSet.has(t)) segments.push({ text: t, type: "removed" });
  }
  for (const t of newSet) {
    if (!oldSet.has(t)) segments.push({ text: t, type: "added" });
  }

  // Same tokens in different order — no semantic change for class lists
  if (segments.length === 0) return { isTokenDiff: false, segments: [] };

  return { isTokenDiff: true, segments };
}

/** CSS classes tl-ev-old/tl-ev-new are shared with the Timeline tab. */
export function renderDiffHtml(diff: AttrDiff): string {
  if (diff.segments.length === 0) return "";

  if (!diff.isTokenDiff) {
    return diff.segments
      .map((s) => {
        const cls = s.type === "removed" ? "tl-ev-old" : "tl-ev-new";
        return `<span class="${cls}">${escapeHtml(s.text)}</span>`;
      })
      .join(" \u2192 ");
  }

  return diff.segments
    .map((s) =>
      s.type === "removed"
        ? `<span class="tl-ev-old">\u2212${escapeHtml(s.text)}</span>`
        : `<span class="tl-ev-new">+${escapeHtml(s.text)}</span>`
    )
    .join(" ");
}

export function renderDiffText(diff: AttrDiff): string {
  if (diff.segments.length === 0) return "";
  if (!diff.isTokenDiff) {
    return diff.segments.map((s) => s.text).join(" \u2192 ");
  }
  return diff.segments
    .map((s) => (s.type === "removed" ? `\u2212${s.text}` : `+${s.text}`))
    .join(" ");
}
