let nextEventId = 0;
const MAX_EVENTS = 3e3;
const PRESERVE_INITIAL = 200;
let events = [];
function getEvents() {
  return events;
}
function clearEvents() {
  events.length = 0;
}
let morphWindow = null;
function getMorphWindow() {
  return morphWindow;
}
let panelRef = null;
let observer = null;
const DEBUGGER_TAG = "STARHTML-DEBUGGER";
const MAX_MORPH_RECORDS = 500;
function startObserving() {
  if (observer) return;
  observer = new MutationObserver((records) => {
    if (!morphWindow) return;
    for (const r of records) {
      if (morphWindow.records.length >= MAX_MORPH_RECORDS) break;
      if (r.target.tagName === DEBUGGER_TAG) continue;
      if (r.type === "childList") {
        let skip = false;
        for (const node of r.addedNodes) {
          if (node.tagName === DEBUGGER_TAG) {
            skip = true;
            break;
          }
        }
        if (!skip) {
          for (const node of r.removedNodes) {
            if (node.tagName === DEBUGGER_TAG) {
              skip = true;
              break;
            }
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
    subtree: true
  });
}
function stopObserving() {
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
function deepDecodeJsonStrings(val) {
  if (typeof val === "string") {
    const trimmed = val.trim();
    if (trimmed.startsWith("{") && trimmed.endsWith("}") || trimmed.startsWith("[") && trimmed.endsWith("]")) {
      try {
        return deepDecodeJsonStrings(JSON.parse(trimmed));
      } catch {
      }
    }
    return val;
  }
  if (Array.isArray(val)) return val.map(deepDecodeJsonStrings);
  if (val && typeof val === "object") {
    const out = {};
    for (const [k, v] of Object.entries(val)) out[k] = deepDecodeJsonStrings(v);
    return out;
  }
  return val;
}
function serializeMorphRecords(records) {
  const elementIds = /* @__PURE__ */ new WeakMap();
  const attrChanges = /* @__PURE__ */ new Map();
  let nextElId = 0;
  for (const r of records) {
    if (r.type === "attributes" && r.target instanceof Element) {
      if (!elementIds.has(r.target)) elementIds.set(r.target, nextElId++);
      const key = `${elementIds.get(r.target)}[${r.attributeName}]`;
      attrChanges.set(key, (attrChanges.get(key) ?? 0) + 1);
    }
  }
  const morphs = [];
  for (const r of records) {
    if (r.type === "childList") {
      const parent = r.target instanceof Element ? selectorPath(r.target) : r.target.nodeName;
      const added = [];
      for (const node of r.addedNodes) {
        if (node instanceof Element) added.push(`<${selectorPath(node)}>`);
        else if (node.nodeType === Node.TEXT_NODE) added.push(`"${(node.textContent ?? "").slice(0, 40)}"`);
      }
      const removed = [];
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
function captureSSEEvents() {
  document.addEventListener("datastar-fetch", (e) => {
    const { type, el, argsRaw } = e.detail;
    const debugMeta = argsRaw?.["x-debug-seq"] != null ? {
      seq: Number(argsRaw["x-debug-seq"]),
      ts: Number(argsRaw["x-debug-ts"]),
      handler: String(argsRaw["x-debug-handler"] ?? ""),
      route: String(argsRaw["x-debug-route"] ?? "")
    } : void 0;
    const event = {
      id: nextEventId++,
      type,
      timestamp: Date.now(),
      el,
      argsRaw: { ...argsRaw },
      debugMeta
    };
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
function addEvent(event) {
  events.push(event);
  if (events.length > MAX_EVENTS) {
    events.splice(PRESERVE_INITIAL, events.length - MAX_EVENTS);
  }
  panelRef ?? (panelRef = document.querySelector("starhtml-debugger"));
  panelRef?.notifyNewEvent();
}
const PANEL_STYLES = `
  :host {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 99999;
    font-family: ui-monospace, 'SF Mono', Monaco, 'Cascadia Mono', monospace;
    font-size: 12px;
    line-height: 1.5;
    color-scheme: dark;
  }
  :host, :host * { box-sizing: border-box; }
  .debugger-tab {
    position: absolute;
    bottom: 100%;
    right: 20px;
    background: #1e1e2e;
    color: #cdd6f4;
    padding: 4px 16px;
    border-radius: 6px 6px 0 0;
    cursor: pointer;
    font-size: 11px;
    user-select: none;
    border: 1px solid #45475a;
    border-bottom: none;
  }
  .debugger-tab .badge {
    background: #f38ba8;
    color: #1e1e2e;
    border-radius: 8px;
    padding: 0 5px;
    margin-left: 6px;
    font-size: 10px;
  }
  .debugger-panel {
    background: #1e1e2e;
    color: #cdd6f4;
    border-top: 2px solid #89b4fa;
    display: none;
    flex-direction: column;
    overflow: hidden;
  }
  .debugger-panel.open { display: flex; }
  .resize-handle {
    height: 6px;
    cursor: ns-resize;
    background: transparent;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  .resize-handle::after {
    content: '';
    width: 36px;
    height: 3px;
    border-radius: 2px;
    background: #45475a;
  }
  .resize-handle:hover::after { background: #89b4fa; }
  .tab-bar {
    display: flex;
    border-bottom: 1px solid #45475a;
    padding: 0 8px;
  }
  .tab-btn {
    padding: 6px 16px;
    background: none;
    border: none;
    color: #9399b2;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    font-family: inherit;
    font-size: 11px;
    transition: color 0.1s ease, border-color 0.1s ease;
  }
  .tab-btn.active {
    color: #89b4fa;
    border-bottom-color: #89b4fa;
  }
  .tab-btn:hover { color: #cdd6f4; }
  .tab-btn:focus-visible { outline: 2px solid #89b4fa; outline-offset: -2px; }
  .tab-content {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
    position: relative;
    scrollbar-width: thin;
    scrollbar-color: #45475a transparent;
  }
  .tab-content::-webkit-scrollbar { width: 8px; }
  .tab-content::-webkit-scrollbar-track { background: transparent; }
  .tab-content::-webkit-scrollbar-thumb { background: #45475a; border-radius: 4px; }
  .tab-content::-webkit-scrollbar-thumb:hover { background: #585b70; }
  .toolbar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 8px;
    border-bottom: 1px solid #313244;
  }
  .toolbar input {
    background: #313244;
    border: 1px solid #45475a;
    color: #cdd6f4;
    padding: 4px 8px;
    border-radius: 4px;
    font-family: inherit;
    font-size: 11px;
  }
  .toolbar input::placeholder { color: #585b70; opacity: 1; }
  .toolbar input:focus-visible { outline: 2px solid #89b4fa; outline-offset: -1px; }
  .toolbar button {
    background: #313244;
    border: 1px solid #45475a;
    color: #cdd6f4;
    padding: 4px 8px;
    border-radius: 4px;
    cursor: pointer;
    font-family: inherit;
    font-size: 11px;
  }
  .toolbar button:hover { background: #45475a; }
  .toolbar button:focus-visible { outline: 2px solid #89b4fa; outline-offset: -1px; }
  .toolbar .clear-events-btn { color: #a6adc8; }
  .toolbar .clear-events-btn:hover { color: #f38ba8; background: #3e1525; border-color: #f38ba8; }
  .filter-wrap { position: relative; display: flex; align-items: center; }
  .filter-wrap .clear-filter-btn {
    position: absolute; right: 4px; top: 50%; transform: translateY(-50%);
    background: none; border: none; color: #9399b2; cursor: pointer;
    font-size: 14px; padding: 0 4px; line-height: 1;
  }
  .filter-wrap .clear-filter-btn:hover { color: #cdd6f4; }
  .toolbar .count { color: #9399b2; margin-left: auto; }
  .event-list { display: flex; flex-direction: column; }
  .event-row {
    display: flex;
    align-items: baseline;
    gap: 8px;
    padding: 4px 8px;
    border-bottom: 1px solid #11111b;
    cursor: pointer;
    white-space: nowrap;
  }
  .event-row::before {
    content: '\\25B8';
    color: #585b70;
    flex-shrink: 0;
    width: 12px;
    text-align: center;
    font-size: 10px;
  }
  .event-row.expanded::before {
    content: '\\25BE';
    color: #9399b2;
  }
  .event-row:hover { background: #2a2b3d; }
  .event-row.expanded { background: #313244; border-bottom-color: transparent; }
  .event-time { color: #9399b2; flex-shrink: 0; }
  .event-type {
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: 600;
    flex-shrink: 0;
    min-width: 56px;
    text-align: center;
  }
  .type-signals { background: #1e3a5f; color: #89b4fa; }
  .type-elements { background: #1e3f2a; color: #a6e3a1; }
  .type-script { background: #2e1f5e; color: #cba6f7; }
  .type-lifecycle { background: #313244; color: #bac2de; }
  .type-error { background: #3e1525; color: #f38ba8; }
  .event-handler { color: #f9e2af; flex-shrink: 0; }
  .event-route { color: #9399b2; overflow: hidden; text-overflow: ellipsis; min-width: 0; }
  .event-detail {
    padding: 6px 8px 6px 24px;
    background: #181825;
    border-bottom: 1px solid #11111b;
    border-left: 2px solid #89b4fa;
    white-space: pre-wrap;
    word-break: break-word;
    overflow-wrap: break-word;
    font-size: 11px;
    color: #a6adc8;
    max-height: 200px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: #45475a transparent;
  }
  .event-detail::-webkit-scrollbar { width: 6px; }
  .event-detail::-webkit-scrollbar-track { background: transparent; }
  .event-detail::-webkit-scrollbar-thumb { background: #45475a; border-radius: 3px; }
  .jump-btn {
    position: absolute;
    bottom: 8px;
    right: 16px;
    background: #89b4fa;
    color: #1e1e2e;
    border: none;
    padding: 4px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-family: inherit;
    font-size: 11px;
    font-weight: 600;
  }
  .jump-btn:hover { background: #b4d0fb; }
  .morph-summary { color: #a6e3a1; margin-bottom: 4px; }
  .morph-list { padding-left: 12px; }
  .morph-item { padding: 1px 0; }
  .morph-item .added { color: #a6e3a1; }
  .morph-item .removed { color: #f38ba8; }
  .morph-item .changed { color: #f9e2af; }
  .morph-item .selector { color: #89b4fa; }
  .morph-item .old-val { color: #f38ba8; text-decoration: line-through; }
  .morph-item .new-val { color: #a6e3a1; }
  .morph-item .flash-warn { color: #f9e2af; }
`;
const TYPE_CONFIG = {
  "datastar-patch-signals": { label: "signals", cls: "type-signals" },
  "datastar-patch-elements": { label: "elements", cls: "type-elements" },
  "datastar-execute-script": { label: "script", cls: "type-script" },
  "started": { label: "start", cls: "type-lifecycle" },
  "finished": { label: "done", cls: "type-lifecycle" },
  "error": { label: "error", cls: "type-error" },
  "retrying": { label: "retry", cls: "type-lifecycle" },
  "retries-failed": { label: "failed", cls: "type-error" }
};
function formatTime(ts) {
  const d = new Date(ts);
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}:${String(d.getSeconds()).padStart(2, "0")}.${String(d.getMilliseconds()).padStart(3, "0")}`;
}
const ESCAPE_MAP = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ESCAPE_MAP[c]);
}
function selectorPath(el) {
  if (el.id) return `#${el.id}`;
  let path = el.tagName.toLowerCase();
  if (el.className && typeof el.className === "string") {
    path += "." + el.className.trim().split(/\s+/).slice(0, 2).join(".");
  }
  return path;
}
class StarHTMLDebugger extends HTMLElement {
  constructor() {
    super();
    this.unseenCount = 0;
    this.keydownHandler = null;
    this.filterText = "";
    this.visibleSinceId = 0;
    this.expandedId = -1;
    this.rafPending = false;
    this.userAtBottom = true;
    this.sseToolbar = null;
    this.sseEventList = null;
    this.shadow = this.attachShadow({ mode: "open" });
    this.isOpen = sessionStorage.getItem("starhtml-debug-open") === "true";
    const stored = Number(sessionStorage.getItem("starhtml-debug-height"));
    this.panelHeight = Number.isNaN(stored) || stored <= 0 ? 300 : stored;
    this.activeTab = sessionStorage.getItem("starhtml-debug-tab") || "sse";
    this.render();
  }
  disconnectedCallback() {
    if (panelRef === this) panelRef = null;
    if (this.keydownHandler) {
      document.removeEventListener("keydown", this.keydownHandler);
      this.keydownHandler = null;
    }
    stopObserving();
  }
  render() {
    this.shadow.innerHTML = `
      <style>${PANEL_STYLES}</style>
      <div class="debugger-tab">
        StarHTML Debug<span class="badge" style="display:none"></span>
      </div>
      <div class="debugger-panel" style="height:${this.panelHeight}px">
        <div class="resize-handle"></div>
        <div class="tab-bar">
          <button class="tab-btn ${this.activeTab === "sse" ? "active" : ""}" data-tab="sse">SSE Events</button>
          <button class="tab-btn ${this.activeTab === "signals" ? "active" : ""}" data-tab="signals">Signals</button>
          <button class="tab-btn ${this.activeTab === "timeline" ? "active" : ""}" data-tab="timeline">Timeline</button>
        </div>
        <div class="tab-content" id="tab-content"></div>
      </div>
    `;
    this.panel = this.shadow.querySelector(".debugger-panel");
    this.tab = this.shadow.querySelector(".debugger-tab");
    this.badge = this.shadow.querySelector(".badge");
    if (this.isOpen) {
      this.panel.classList.add("open");
      startObserving();
    }
    this.setupEventListeners();
    if (this.isOpen) {
      this.renderTabContent();
    }
  }
  setupEventListeners() {
    this.tab.addEventListener("click", () => this.toggle());
    this.shadow.querySelector(".tab-bar").addEventListener("click", (e) => {
      const btn = e.target.closest(".tab-btn");
      if (!btn) return;
      this.switchTab(btn.dataset.tab);
    });
    const handle = this.shadow.querySelector(".resize-handle");
    let startY = 0, startH = 0;
    handle.addEventListener("mousedown", (e) => {
      const me = e;
      startY = me.clientY;
      startH = this.panelHeight;
      const onMove = (e2) => {
        this.panelHeight = Math.max(150, Math.min(window.innerHeight * 0.8, startH - (e2.clientY - startY)));
        this.panel.style.height = `${this.panelHeight}px`;
      };
      const onUp = () => {
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
        sessionStorage.setItem("starhtml-debug-height", String(this.panelHeight));
      };
      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    });
    this.keydownHandler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.code === "Period") {
        e.preventDefault();
        this.toggle();
      }
    };
    document.addEventListener("keydown", this.keydownHandler);
  }
  toggle() {
    this.isOpen = !this.isOpen;
    this.panel.classList.toggle("open", this.isOpen);
    sessionStorage.setItem("starhtml-debug-open", String(this.isOpen));
    if (this.isOpen) {
      this.unseenCount = 0;
      this.badge.style.display = "none";
      startObserving();
      this.renderTabContent();
    } else {
      stopObserving();
    }
  }
  switchTab(tabId) {
    this.activeTab = tabId;
    sessionStorage.setItem("starhtml-debug-tab", tabId);
    for (const btn of this.shadow.querySelectorAll(".tab-btn")) {
      btn.classList.toggle("active", btn.dataset.tab === tabId);
    }
    this.expandedId = -1;
    this.sseToolbar = null;
    this.sseEventList = null;
    this.renderTabContent();
  }
  notifyNewEvent() {
    if (!this.isOpen) {
      this.unseenCount++;
      this.badge.textContent = String(this.unseenCount);
      this.badge.style.display = "";
    }
    this.scheduleRender();
  }
  scheduleRender() {
    if (this.rafPending) return;
    this.rafPending = true;
    requestAnimationFrame(() => {
      this.rafPending = false;
      if (this.isOpen && this.activeTab === "sse") {
        this.renderSSETab();
      }
    });
  }
  renderTabContent() {
    if (this.activeTab === "sse") {
      this.renderSSETab();
    } else {
      this.shadow.getElementById("tab-content").innerHTML = `<div style="color:#6c7086;padding:16px;">Coming in Phase 2</div>`;
    }
  }
  ensureSSEStructure() {
    const content = this.shadow.getElementById("tab-content");
    if (!this.sseToolbar || !content.contains(this.sseToolbar)) {
      content.innerHTML = "";
      this.sseToolbar = document.createElement("div");
      this.sseToolbar.className = "toolbar";
      this.sseToolbar.innerHTML = `
        <div class="filter-wrap">
          <input type="text" placeholder="Filter..." class="filter-input" style="width:160px;padding-right:20px">
          <button class="clear-filter-btn" style="display:none" title="Clear filter">&times;</button>
        </div>
        <button class="clear-events-btn" title="Clear visible events">Clear Events</button>
        <span class="count"></span>
      `;
      this.sseEventList = document.createElement("div");
      this.sseEventList.className = "event-list";
      content.appendChild(this.sseToolbar);
      content.appendChild(this.sseEventList);
      const filterInput = this.sseToolbar.querySelector(".filter-input");
      const clearFilterBtn = this.sseToolbar.querySelector(".clear-filter-btn");
      filterInput.addEventListener("input", () => {
        this.filterText = filterInput.value;
        clearFilterBtn.style.display = this.filterText ? "" : "none";
        this.expandedId = -1;
        this.renderSSETab();
      });
      clearFilterBtn.addEventListener("click", () => {
        this.filterText = "";
        filterInput.value = "";
        clearFilterBtn.style.display = "none";
        this.expandedId = -1;
        this.renderSSETab();
      });
      this.sseToolbar.querySelector(".clear-events-btn").addEventListener("click", () => {
        const latest = events[events.length - 1];
        this.visibleSinceId = latest ? latest.id + 1 : 0;
        this.expandedId = -1;
        this.renderSSETab();
      });
      content.addEventListener("scroll", () => {
        this.userAtBottom = content.scrollTop + content.clientHeight >= content.scrollHeight - 20;
      });
    }
  }
  renderSSETab() {
    this.ensureSSEStructure();
    const content = this.shadow.getElementById("tab-content");
    const eventList = this.sseEventList;
    const filter = this.filterText.toLowerCase();
    const visible = events.filter((ev) => ev.id >= this.visibleSinceId);
    const filtered = filter ? visible.filter((ev) => {
      const label = TYPE_CONFIG[ev.type]?.label ?? ev.type;
      const handler = (ev.debugMeta?.handler ?? "").toLowerCase();
      const route = (ev.debugMeta?.route ?? "").toLowerCase();
      return label.includes(filter) || handler.includes(filter) || route.includes(filter) || ev.type.includes(filter);
    }) : visible;
    this.sseToolbar.querySelector(".count").textContent = `${filtered.length} event${filtered.length !== 1 ? "s" : ""}`;
    const wasAtBottom = this.userAtBottom;
    let html = "";
    for (const ev of filtered) {
      const cfg = TYPE_CONFIG[ev.type] ?? { label: ev.type.replace("datastar-", ""), cls: "type-lifecycle" };
      const handler = ev.debugMeta?.handler ?? "";
      const route = ev.debugMeta?.route ?? "";
      const expanded = ev.id === this.expandedId;
      html += `<div class="event-row${expanded ? " expanded" : ""}" data-eid="${ev.id}">
        <span class="event-time">${formatTime(ev.timestamp)}</span>
        <span class="event-type ${cfg.cls}">${escapeHtml(cfg.label)}</span>
        ${handler ? `<span class="event-handler">${escapeHtml(handler)}</span>` : ""}
        ${route ? `<span class="event-route">${escapeHtml(route)}</span>` : ""}
      </div>`;
      if (expanded) {
        html += `<div class="event-detail">${this.formatEventDetail(ev)}</div>`;
      }
    }
    eventList.innerHTML = html;
    for (const row of eventList.querySelectorAll(".event-row")) {
      row.addEventListener("click", () => {
        const eid = Number(row.dataset.eid);
        this.expandedId = this.expandedId === eid ? -1 : eid;
        this.renderSSETab();
      });
    }
    let jumpBtn = content.querySelector(".jump-btn");
    if (!this.userAtBottom && filtered.length > 0) {
      if (!jumpBtn) {
        jumpBtn = document.createElement("button");
        jumpBtn.className = "jump-btn";
        jumpBtn.textContent = "Jump to latest";
        jumpBtn.addEventListener("click", () => {
          content.scrollTop = content.scrollHeight;
          this.userAtBottom = true;
          jumpBtn?.remove();
        });
        content.appendChild(jumpBtn);
      }
    } else if (jumpBtn) {
      jumpBtn.remove();
    }
    if (wasAtBottom) {
      content.scrollTop = content.scrollHeight;
    }
  }
  formatEventDetail(ev) {
    const parts = [];
    if (ev.debugMeta) {
      parts.push(`<b>seq:</b> ${ev.debugMeta.seq}  <b>ts:</b> ${ev.debugMeta.ts}  <b>handler:</b> ${escapeHtml(ev.debugMeta.handler)}  <b>route:</b> ${escapeHtml(ev.debugMeta.route)}`);
    }
    const args = {};
    for (const [k, v] of Object.entries(ev.argsRaw)) {
      if (!k.startsWith("x-debug-")) args[k] = v;
    }
    if (Object.keys(args).length > 0) {
      const decoded = deepDecodeJsonStrings(args);
      parts.push(escapeHtml(JSON.stringify(decoded, null, 2)));
    }
    if (ev.morphs && ev.morphs.length > 0) {
      const addedCount = ev.morphs.filter((m) => m.type === "childList" && (m.added?.length ?? 0) > 0).length;
      const removedCount = ev.morphs.filter((m) => m.type === "childList" && (m.removed?.length ?? 0) > 0).length;
      const attrsCount = ev.morphs.filter((m) => m.type === "attributes").length;
      const charCount = ev.morphs.filter((m) => m.type === "characterData").length;
      let summary = `<div class="morph-summary"><b>morphs:</b> ${addedCount} added, ${removedCount} removed, ${attrsCount} attributes`;
      if (charCount > 0) summary += `, ${charCount} text`;
      summary += `</div>`;
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
          items += `<div class="morph-item"><span class="changed">~</span> <span class="selector">${escapeHtml(m.targetSelector)}</span> [${escapeHtml(m.attributeName ?? "")}] <span class="old-val">${escapeHtml(m.oldValue ?? "")}</span> → <span class="new-val">${escapeHtml(m.newValue ?? "")}</span>${flash}</div>`;
        } else if (m.type === "characterData") {
          items += `<div class="morph-item">~ text in <span class="selector">${escapeHtml(m.targetSelector)}</span></div>`;
        }
      }
      parts.push(summary + (items ? `<div class="morph-list">${items}</div>` : ""));
    }
    return parts.join("\n");
  }
}
if (!customElements.get("starhtml-debugger")) {
  customElements.define("starhtml-debugger", StarHTMLDebugger);
}
let initialized = false;
function init() {
  if (initialized) return;
  initialized = true;
  captureSSEEvents();
  console.log("[starhtml-debugger] initialized");
}
export {
  clearEvents,
  getEvents,
  getMorphWindow,
  init
};
