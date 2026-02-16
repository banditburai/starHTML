// debugger-capture.ts — Data layer, event capture, rendering helpers.
// Standalone data-layer module consumed by the StarElements debugger component.

// ─── Interfaces ────────────────────────────────────────────────────

export interface SerializedMorph {
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
  debugMeta?: {
    seq: number;
    ts: number;
    handler: string;
    route: string;
  };
  morphs?: SerializedMorph[];
  groupId?: number;
  duration?: number;
}

// ─── Constants ─────────────────────────────────────────────────────

export const TYPE_CONFIG: Record<string, { label: string; cls: string }> = {
  "datastar-patch-signals": { label: "signals", cls: "type-signals" },
  "datastar-patch-elements": { label: "elements", cls: "type-elements" },
  "datastar-execute-script": { label: "script", cls: "type-script" },
  "started": { label: "start", cls: "type-lifecycle" },
  "finished": { label: "done", cls: "type-lifecycle" },
  "error": { label: "error", cls: "type-error" },
  "retrying": { label: "retry", cls: "type-lifecycle" },
  "retries-failed": { label: "failed", cls: "type-error" },
};

export const CHIP_CATEGORIES: { key: string; label: string; cls: string; types: string[] }[] = [
  { key: "signals", label: "signals", cls: "chip-signals", types: ["datastar-patch-signals"] },
  { key: "elements", label: "elements", cls: "chip-elements", types: ["datastar-patch-elements"] },
  { key: "script", label: "script", cls: "chip-script", types: ["datastar-execute-script"] },
  { key: "lifecycle", label: "lifecycle", cls: "chip-lifecycle", types: ["started", "finished", "error", "retrying", "retries-failed"] },
];

// ─── Event storage ─────────────────────────────────────────────────

const MAX_EVENTS = 3000;
const PRESERVE_INITIAL = 200;
let events: DebugSSEEvent[] = [];
let nextEventId = 0;

// ─── Subscriber pattern ───────────────────────────────────────────

const subscribers = new Set<() => void>();

/** Subscribe to new-event notifications. Returns an unsubscribe function. */
export function subscribe(fn: () => void): () => void {
  subscribers.add(fn);
  return () => { subscribers.delete(fn); };
}

// ─── Public API ────────────────────────────────────────────────────

export function getEvents(): readonly DebugSSEEvent[] {
  return events;
}

export function getEventCount(): number {
  return events.length;
}

export function clearEvents(): void {
  events.length = 0;
}

/**
 * Filter events by watermark ID, event-type set, and text filter.
 * @param sinceId  Only include events with id >= sinceId (watermark pattern)
 * @param typeFilter  Set of raw event type strings to allow (null = all)
 * @param textFilter  Case-insensitive text to match against label/handler/route/type
 */
export function getFilteredEvents(
  sinceId: number,
  typeFilter: Set<string> | null,
  textFilter: string,
): DebugSSEEvent[] {
  const filter = textFilter.toLowerCase();
  return events.filter(ev => {
    if (ev.id < sinceId) return false;
    if (typeFilter && !typeFilter.has(ev.type)) return false;
    if (filter) {
      const label = TYPE_CONFIG[ev.type]?.label ?? ev.type;
      const handler = (ev.debugMeta?.handler ?? "").toLowerCase();
      const route = (ev.debugMeta?.route ?? "").toLowerCase();
      if (!(label.includes(filter) || handler.includes(filter) || route.includes(filter) || ev.type.includes(filter))) return false;
    }
    return true;
  });
}

/** Build the Set<string> of allowed event type strings from active chip keys. */
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

// ─── MutationObserver ──────────────────────────────────────────────

let morphWindow: { sseEvent: DebugSSEEvent; records: MutationRecord[] } | null = null;
let observer: MutationObserver | null = null;
const DEBUGGER_TAG = "STARHTML-DEBUGGER";
const MAX_MORPH_RECORDS = 500;

export function getMorphWindow() { return morphWindow; }

export function startObserving(): void {
  if (observer) return;
  observer = new MutationObserver((records) => {
    if (!morphWindow) return;
    for (const r of records) {
      if (morphWindow.records.length >= MAX_MORPH_RECORDS) break;
      if ((r.target as Element).tagName === DEBUGGER_TAG) continue;
      if (r.type === "childList") {
        let skip = false;
        for (const node of r.addedNodes) {
          if ((node as Element).tagName === DEBUGGER_TAG) { skip = true; break; }
        }
        if (!skip) {
          for (const node of r.removedNodes) {
            if ((node as Element).tagName === DEBUGGER_TAG) { skip = true; break; }
          }
        }
        if (skip) continue;
      }
      morphWindow.records.push(r);
    }
  });

  observer.observe(document.body, {
    childList: true,
    attributes: true,
    attributeOldValue: true,
    characterData: true,
    characterDataOldValue: true,
    subtree: true,
  });
}

export function stopObserving(): void {
  if (!observer) return;
  const pending = observer.takeRecords();
  if (morphWindow) {
    for (const r of pending) {
      if (morphWindow.records.length >= MAX_MORPH_RECORDS) break;
      morphWindow.records.push(r);
    }
  }
  observer.disconnect();
  observer = null;
}

// ─── Internal helpers ──────────────────────────────────────────────

function deepDecodeJsonStrings(val: unknown): unknown {
  if (typeof val === "string") {
    const trimmed = val.trim();
    if ((trimmed.startsWith("{") && trimmed.endsWith("}")) || (trimmed.startsWith("[") && trimmed.endsWith("]"))) {
      try { return deepDecodeJsonStrings(JSON.parse(trimmed)); } catch { /* not JSON */ }
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

function selectorPath(el: Element): string {
  if (el.id) return `#${el.id}`;
  let path = el.tagName.toLowerCase();
  if (el.className && typeof el.className === "string") {
    path += "." + el.className.trim().split(/\s+/).slice(0, 2).join(".");
  }
  return path;
}

function serializeMorphRecords(records: MutationRecord[]): SerializedMorph[] {
  const elementIds = new WeakMap<Element, number>();
  const attrChanges = new Map<string, number>();
  let nextElId = 0;

  for (const r of records) {
    if (r.type === "attributes" && r.target instanceof Element) {
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
        else if (node.nodeType === Node.TEXT_NODE) added.push(`"${(node.textContent ?? "").slice(0, 40)}"`);
      }
      const removed: string[] = [];
      for (const node of r.removedNodes) {
        if (node instanceof Element) removed.push(`<${selectorPath(node)}>`);
        else if (node.nodeType === Node.TEXT_NODE) removed.push(`"${(node.textContent ?? "").slice(0, 40)}"`);
      }
      if (added.length > 0 || removed.length > 0) {
        morphs.push({ type: "childList", targetSelector: parent, added, removed });
      }
    } else if (r.type === "attributes" && r.target instanceof Element) {
      const sel = selectorPath(r.target);
      const attr = r.attributeName ?? "";
      const oldVal = r.oldValue ?? "";
      const newVal = r.target.getAttribute(attr) ?? "";
      const elId = elementIds.get(r.target);
      const key = `${elId}[${attr}]`;
      const flash = (attrChanges.get(key) ?? 0) > 1;
      morphs.push({ type: "attributes", targetSelector: sel, attributeName: attr, oldValue: oldVal, newValue: newVal, flash });
    } else if (r.type === "characterData") {
      const parent = r.target.parentElement;
      const sel = parent ? selectorPath(parent) : "#text";
      morphs.push({ type: "characterData", targetSelector: sel, oldValue: r.oldValue ?? "" });
    }
  }
  return morphs;
}

// ─── Event capture ─────────────────────────────────────────────────

let nextGroupId = 0;
const openGroups = new WeakMap<HTMLElement, { groupId: number; startTime: number }>();

function captureSSEEvents(): void {
  document.addEventListener("datastar-fetch", (e: Event) => {
    const { type, el, argsRaw } = (e as CustomEvent).detail;

    const debugMeta = argsRaw?.["x-debug-seq"] != null ? {
      seq: Number(argsRaw["x-debug-seq"]),
      ts: Number(argsRaw["x-debug-ts"]),
      handler: String(argsRaw["x-debug-handler"] ?? ""),
      route: String(argsRaw["x-debug-route"] ?? ""),
    } : undefined;

    const event: DebugSSEEvent = {
      id: nextEventId++,
      type,
      timestamp: Date.now(),
      el,
      argsRaw: { ...argsRaw },
      debugMeta,
    };

    // Request grouping: started opens a group, finished closes it
    if (type === "started" && el) {
      const gid = nextGroupId++;
      openGroups.set(el, { groupId: gid, startTime: event.timestamp });
      event.groupId = gid;
    } else if (el && openGroups.has(el)) {
      const group = openGroups.get(el)!;
      event.groupId = group.groupId;
      if (type === "finished" || type === "error" || type === "retries-failed") {
        event.duration = event.timestamp - group.startTime;
        openGroups.delete(el);
      }
    }

    addEvent(event);

    if (type === "datastar-patch-elements") {
      morphWindow = { sseEvent: event, records: [] };
      setTimeout(() => {
        if (morphWindow) {
          event.morphs = serializeMorphRecords(morphWindow.records);
          morphWindow = null;
        }
      }, 0);
    }
  });
}

function addEvent(event: DebugSSEEvent): void {
  events.push(event);
  if (events.length > MAX_EVENTS) {
    events.splice(PRESERVE_INITIAL, events.length - MAX_EVENTS);
  }
  for (const fn of subscribers) fn();
}

// ─── Rendering helpers ─────────────────────────────────────────────

export function formatTime(ts: number): string {
  const d = new Date(ts);
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}:${String(d.getSeconds()).padStart(2, "0")}.${String(d.getMilliseconds()).padStart(3, "0")}`;
}

const ESCAPE_MAP: Record<string, string> = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
export function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, c => ESCAPE_MAP[c]);
}

/** Simple HTML syntax highlighter: tags blue, attrs yellow, values green, text gray */
export function highlightHtml(raw: string): string {
  return raw.replace(/(<\/?)([\w-]+)((?:\s+[\w-]+(?:=(?:"[^"]*"|'[^']*'|[^\s>]*))?)*)\s*(\/?>)|([^<]+)/g,
    (_match, open: string | undefined, tag: string | undefined, attrs: string | undefined, close: string | undefined, text: string | undefined) => {
      if (text !== undefined) {
        return `<span class="hx">${escapeHtml(text)}</span>`;
      }
      let out = `<span class="ht">${escapeHtml(open!)}${escapeHtml(tag!)}</span>`;
      if (attrs) {
        out += attrs.replace(/([\w-]+)(=)("[^"]*"|'[^']*'|[^\s>]*)/g,
          (_m: string, name: string, eq: string, val: string) =>
            `<span class="ha">${escapeHtml(name)}</span>${eq}<span class="hv">${escapeHtml(val)}</span>`
        ).replace(/(?:^|\s)([\w-]+)(?=\s|$)/g,
          (_m: string, name: string) => ` <span class="ha">${escapeHtml(name)}</span>`
        );
      }
      out += `<span class="ht">${escapeHtml(close!)}</span>`;
      return out;
    });
}

export function eventPreview(ev: DebugSSEEvent): string {
  const args = ev.argsRaw;
  if (ev.type === "datastar-patch-signals") {
    const raw = args.signals;
    if (typeof raw === "string") {
      try {
        const obj = JSON.parse(raw);
        return Object.entries(obj).map(([k, v]) => `${k}: ${JSON.stringify(v)}`).join(", ").slice(0, 60);
      } catch { /* fall through */ }
    }
    return "";
  }
  if (ev.type === "datastar-patch-elements") {
    const mode = args.mode ?? "outer";
    const selector = args.selector ?? "";
    return `${mode} ${selector}`;
  }
  if (ev.type === "datastar-execute-script") {
    const script = String(args.script ?? "").slice(0, 40);
    return script;
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
  return "";
}

export function morphBadge(ev: DebugSSEEvent): string {
  if (!ev.morphs || ev.morphs.length === 0) return "";
  const added = ev.morphs.filter(m => m.type === "childList" && (m.added?.length ?? 0) > 0).length;
  const removed = ev.morphs.filter(m => m.type === "childList" && (m.removed?.length ?? 0) > 0).length;
  const changed = ev.morphs.filter(m => m.type === "attributes").length;
  return `+${added} -${removed} ~${changed}`;
}

export function buildRowHtml(ev: DebugSSEEvent): string {
  const cfg = TYPE_CONFIG[ev.type] ?? { label: ev.type.replace("datastar-", ""), cls: "type-lifecycle" };
  const handler = ev.debugMeta?.handler ?? "";
  const route = ev.debugMeta?.route ?? "";
  const preview = eventPreview(ev);
  const badge = morphBadge(ev);
  const groupCls = ev.groupId != null ? ` group-${ev.groupId % 3}` : "";
  const dur = ev.duration != null
    ? ev.duration >= 1000 ? `${(ev.duration / 1000).toFixed(1)}s` : `${ev.duration}ms`
    : "";

  return `<div class="event-row${groupCls}" data-eid="${ev.id}">
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
    sections.push(`<div class="detail-section"><b>seq:</b> ${ev.debugMeta.seq}  <b>ts:</b> ${ev.debugMeta.ts}  <b>handler:</b> ${escapeHtml(ev.debugMeta.handler)}  <b>route:</b> ${escapeHtml(ev.debugMeta.route)}</div>`);
  }

  const args: Record<string, unknown> = {};
  const htmlStrings: [string, string][] = [];
  for (const [k, v] of Object.entries(ev.argsRaw)) {
    if (k.startsWith("x-debug-")) continue;
    if (typeof v === "string" && v.trimStart().startsWith("<")) {
      htmlStrings.push([k, v]);
    } else {
      args[k] = v;
    }
  }

  const isElements = ev.type === "datastar-patch-elements";
  if (isElements && (args.mode || args.selector)) {
    const mode = String(args.mode ?? "morph");
    const sel = String(args.selector ?? "");
    sections.push(`<div class="detail-section"><div class="detail-header"><span class="mode-badge">${escapeHtml(mode)}</span><span class="ht">→</span> <span class="target">${escapeHtml(sel)}</span></div></div>`);
    delete args.mode;
    delete args.selector;
  }

  if (Object.keys(args).length > 0) {
    const decoded = deepDecodeJsonStrings(args);
    sections.push(`<div class="detail-section">${escapeHtml(JSON.stringify(decoded, null, 2))}</div>`);
  }

  for (const [key, html] of htmlStrings) {
    sections.push(`<div class="detail-section"><div class="detail-label">${escapeHtml(key)}</div><div class="html-block">${highlightHtml(html)}</div></div>`);
  }

  if (ev.morphs && ev.morphs.length > 0) {
    const addedCount = ev.morphs.filter(m => m.type === "childList" && (m.added?.length ?? 0) > 0).length;
    const removedCount = ev.morphs.filter(m => m.type === "childList" && (m.removed?.length ?? 0) > 0).length;
    const attrsCount = ev.morphs.filter(m => m.type === "attributes").length;
    const charCount = ev.morphs.filter(m => m.type === "characterData").length;

    let summary = `<div class="morph-summary"><b>morphs:</b> ${addedCount} added, ${removedCount} removed, ${attrsCount} attributes`;
    if (charCount > 0) summary += `, ${charCount} text`;
    summary += `</div>`;

    let items = "";
    for (const m of ev.morphs) {
      if (m.type === "childList") {
        for (const desc of (m.added ?? [])) {
          items += `<div class="morph-item"><span class="added">+</span> Added <span class="selector">${escapeHtml(desc)}</span> to <span class="selector">${escapeHtml(m.targetSelector)}</span></div>`;
        }
        for (const desc of (m.removed ?? [])) {
          items += `<div class="morph-item"><span class="removed">-</span> Removed <span class="selector">${escapeHtml(desc)}</span> from <span class="selector">${escapeHtml(m.targetSelector)}</span></div>`;
        }
      } else if (m.type === "attributes") {
        const flash = m.flash ? ` <span class="flash-warn">&#9888; flash</span>` : "";
        items += `<div class="morph-item"><span class="changed">~</span> <span class="selector">${escapeHtml(m.targetSelector)}</span> [${escapeHtml(m.attributeName ?? "")}] <span class="old-val">${escapeHtml(m.oldValue ?? "")}</span> → <span class="new-val">${escapeHtml(m.newValue ?? "")}</span>${flash}</div>`;
      } else if (m.type === "characterData") {
        items += `<div class="morph-item">~ text in <span class="selector">${escapeHtml(m.targetSelector)}</span></div>`;
      }
    }

    sections.push(`<div class="detail-section">${summary}${items ? `<div class="morph-list">${items}</div>` : ""}</div>`);
  }

  return sections.join("");
}

export function formatSingleEventForExport(ev: DebugSSEEvent): string {
  const cfg = TYPE_CONFIG[ev.type] ?? { label: ev.type.replace("datastar-", "") };
  const dur = ev.duration != null
    ? ev.duration >= 1000 ? ` (${(ev.duration / 1000).toFixed(1)}s)` : ` (${ev.duration}ms)`
    : "";
  const preview = eventPreview(ev);
  let out = `[${formatTime(ev.timestamp)}] ${cfg.label}${dur}${preview ? "  " + preview : ""}`;

  if (ev.debugMeta) {
    out += `\n  handler: ${ev.debugMeta.handler}  route: ${ev.debugMeta.route}`;
  }

  const args: Record<string, unknown> = {};
  const htmlStrings: [string, string][] = [];
  for (const [k, v] of Object.entries(ev.argsRaw)) {
    if (k.startsWith("x-debug-")) continue;
    if (typeof v === "string" && v.trimStart().startsWith("<")) {
      htmlStrings.push([k, v]);
    } else {
      args[k] = v;
    }
  }
  if (Object.keys(args).length > 0) {
    const decoded = deepDecodeJsonStrings(args);
    out += "\n  " + JSON.stringify(decoded, null, 2).replace(/\n/g, "\n  ");
  }
  for (const [key, html] of htmlStrings) {
    out += `\n  ${key}:\n    ${html.replace(/\n/g, "\n    ")}`;
  }

  if (ev.morphs && ev.morphs.length > 0) {
    const added = ev.morphs.filter(m => m.type === "childList" && (m.added?.length ?? 0) > 0).length;
    const removed = ev.morphs.filter(m => m.type === "childList" && (m.removed?.length ?? 0) > 0).length;
    const attrs = ev.morphs.filter(m => m.type === "attributes").length;
    out += `\n  morphs: ${added} added, ${removed} removed, ${attrs} attributes`;
    for (const m of ev.morphs) {
      if (m.type === "childList") {
        for (const desc of (m.added ?? [])) out += `\n    + Added ${desc} to ${m.targetSelector}`;
        for (const desc of (m.removed ?? [])) out += `\n    - Removed ${desc} from ${m.targetSelector}`;
      } else if (m.type === "attributes") {
        out += `\n    ~ ${m.targetSelector} [${m.attributeName}] ${m.oldValue} → ${m.newValue}${m.flash ? " ⚠ flash" : ""}`;
      }
    }
  }
  return out;
}

/** Format an array of (pre-filtered) events for LLM-friendly export. */
export function formatAllEventsForExport(filteredEvents: DebugSSEEvent[]): string {
  const lines = [`=== StarHTML Debug Events (${filteredEvents.length} events) ===`, ""];
  for (const ev of filteredEvents) {
    lines.push(formatSingleEventForExport(ev));
  }
  return lines.join("\n");
}

// ─── Init ──────────────────────────────────────────────────────────

let initialized = false;

export function init(): void {
  if (initialized) return;
  initialized = true;
  captureSSEEvents();
  console.log("[starhtml-debugger] initialized");
}
