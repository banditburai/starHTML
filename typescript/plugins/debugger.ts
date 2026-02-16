/**
 * StarHTML Debugger - Phase 1
 * Captures SSE events, signal patches, and DOM mutations.
 * Renders a bottom-drawer debug panel in Shadow DOM.
 */

// Types
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
  morphRecords?: MutationRecord[];
}

let nextEventId = 0;

// Ring buffer for events
const MAX_EVENTS = 3000;
const PRESERVE_INITIAL = 200;
let events: DebugSSEEvent[] = [];

export function getEvents(): readonly DebugSSEEvent[] {
  return events;
}

export function clearEvents(): void {
  events = [];
}

// ============================================================================
// SSE Event Capture
// ============================================================================

let morphWindow: { sseEvent: DebugSSEEvent; records: MutationRecord[] } | null = null;

export function getMorphWindow() { return morphWindow; }

let panelRef: StarHTMLDebugger | null = null;

// ============================================================================
// MutationObserver — morph correlation
// ============================================================================

let observer: MutationObserver | null = null;
const DEBUGGER_TAG = "STARHTML-DEBUGGER";
const MAX_MORPH_RECORDS = 500;

function startObserving(): void {
  if (observer) return;
  observer = new MutationObserver((records) => {
    if (!morphWindow) return;

    // Shadow DOM isolates debugger-internal mutations from this observer.
    // Only filter light-DOM mutations that target or add/remove the debugger element.
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

function stopObserving(): void {
  if (observer) {
    const pending = observer.takeRecords();
    if (morphWindow && pending.length > 0) {
      for (const r of pending) {
        if (morphWindow.records.length >= MAX_MORPH_RECORDS) break;
        morphWindow.records.push(r);
      }
    }
    observer.disconnect();
    observer = null;
  }
}

function captureSSEEvents(): void {
  document.addEventListener("datastar-fetch", (e: Event) => {
    const detail = (e as CustomEvent).detail;
    const { type, el, argsRaw } = detail;

    // Extract debug metadata from argsRaw if present
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

    addEvent(event);

    // If this is a patch-elements event, open a morph window.
    // Use setTimeout(0) to close — MutationObserver callbacks fire after
    // microtasks but before macrotasks, so setTimeout gives the MO callback
    // in Task 7 time to push records into morphWindow.records.
    if (type === "datastar-patch-elements") {
      morphWindow = { sseEvent: event, records: [] };
      setTimeout(() => {
        if (morphWindow) {
          event.morphRecords = morphWindow.records;
          morphWindow = null;
        }
      }, 0);
    }
  });
}

function addEvent(event: DebugSSEEvent): void {
  events.push(event);
  // Two-tier eviction: preserve first PRESERVE_INITIAL, evict oldest middle
  if (events.length > MAX_EVENTS) {
    events.splice(PRESERVE_INITIAL, events.length - MAX_EVENTS);
  }
  // Notify the panel component
  panelRef ??= document.querySelector("starhtml-debugger") as StarHTMLDebugger | null;
  panelRef?.notifyNewEvent();
}

// ============================================================================
// Bottom Drawer Panel (Shadow DOM)
// ============================================================================

const PANEL_STYLES = `
  :host {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 99999;
    font-family: ui-monospace, 'SF Mono', Monaco, 'Cascadia Mono', monospace;
    font-size: 12px;
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
  .debugger-panel.open {
    display: flex;
  }
  .resize-handle {
    height: 4px;
    cursor: ns-resize;
    background: transparent;
  }
  .resize-handle:hover { background: #89b4fa33; }
  .tab-bar {
    display: flex;
    border-bottom: 1px solid #45475a;
    padding: 0 8px;
  }
  .tab-btn {
    padding: 6px 16px;
    background: none;
    border: none;
    color: #6c7086;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    font-family: inherit;
    font-size: 11px;
  }
  .tab-btn.active {
    color: #89b4fa;
    border-bottom-color: #89b4fa;
  }
  .tab-btn:hover { color: #cdd6f4; }
  .tab-content {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
    position: relative;
  }
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
    padding: 2px 8px;
    border-radius: 4px;
    font-family: inherit;
    font-size: 11px;
  }
  .toolbar button {
    background: #313244;
    border: 1px solid #45475a;
    color: #cdd6f4;
    padding: 2px 8px;
    border-radius: 4px;
    cursor: pointer;
    font-family: inherit;
    font-size: 11px;
  }
  .toolbar button:hover { background: #45475a; }
  .toolbar .count { color: #6c7086; margin-left: auto; }
  .event-list { display: flex; flex-direction: column; }
  .event-row {
    display: flex;
    align-items: baseline;
    gap: 8px;
    padding: 3px 4px;
    border-bottom: 1px solid #181825;
    cursor: pointer;
    white-space: nowrap;
  }
  .event-row:hover { background: #313244; }
  .event-row.expanded { background: #313244; }
  .event-time { color: #6c7086; flex-shrink: 0; }
  .event-type {
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 600;
    flex-shrink: 0;
  }
  .type-signals { background: #1e3a5f; color: #89b4fa; }
  .type-elements { background: #1e3f2a; color: #a6e3a1; }
  .type-script { background: #2e1f5e; color: #cba6f7; }
  .type-lifecycle { background: #313244; color: #6c7086; }
  .type-error { background: #3e1525; color: #f38ba8; }
  .event-handler { color: #f9e2af; flex-shrink: 0; }
  .event-route { color: #6c7086; overflow: hidden; text-overflow: ellipsis; min-width: 0; }
  .event-detail {
    padding: 6px 8px 6px 24px;
    background: #181825;
    border-bottom: 1px solid #313244;
    white-space: pre-wrap;
    word-break: break-all;
    font-size: 11px;
    color: #a6adc8;
    max-height: 200px;
    overflow-y: auto;
  }
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
`;

const TYPE_CONFIG: Record<string, { label: string; cls: string }> = {
  "datastar-patch-signals": { label: "signals", cls: "type-signals" },
  "datastar-patch-elements": { label: "elements", cls: "type-elements" },
  "datastar-execute-script": { label: "script", cls: "type-script" },
  "started": { label: "start", cls: "type-lifecycle" },
  "finished": { label: "done", cls: "type-lifecycle" },
  "error": { label: "error", cls: "type-error" },
};

function formatTime(ts: number): string {
  const d = new Date(ts);
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}:${String(d.getSeconds()).padStart(2, "0")}.${String(d.getMilliseconds()).padStart(3, "0")}`;
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

class StarHTMLDebugger extends HTMLElement {
  private shadow: ShadowRoot;
  private panel!: HTMLDivElement;
  private tab!: HTMLDivElement;
  private isOpen: boolean;
  private panelHeight: number;
  private activeTab: string;
  private badge!: HTMLSpanElement;
  private unseenCount: number = 0;
  private keydownHandler: ((e: KeyboardEvent) => void) | null = null;
  private filterText: string = "";
  private expandedId: number = -1;
  private rafPending: boolean = false;
  private userAtBottom: boolean = true;
  private sseToolbar: HTMLDivElement | null = null;
  private sseEventList: HTMLDivElement | null = null;

  constructor() {
    super();
    this.shadow = this.attachShadow({ mode: "open" });

    // Restore state from sessionStorage
    this.isOpen = sessionStorage.getItem("starhtml-debug-open") === "true";
    const stored = Number(sessionStorage.getItem("starhtml-debug-height"));
    this.panelHeight = Number.isNaN(stored) || stored <= 0 ? 300 : stored;
    this.activeTab = sessionStorage.getItem("starhtml-debug-tab") || "sse";

    this.render();
  }

  disconnectedCallback(): void {
    if (this.keydownHandler) {
      document.removeEventListener("keydown", this.keydownHandler);
      this.keydownHandler = null;
    }
    stopObserving();
  }

  private render(): void {
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
        <div class="tab-content" id="tab-content">
          <!-- Tab content rendered here -->
        </div>
      </div>
    `;

    this.panel = this.shadow.querySelector(".debugger-panel")!;
    this.tab = this.shadow.querySelector(".debugger-tab")!;
    this.badge = this.shadow.querySelector(".badge")!;

    if (this.isOpen) {
      this.panel.classList.add("open");
      startObserving();
    }

    this.setupEventListeners();

    if (this.isOpen) {
      this.renderTabContent();
    }
  }

  private setupEventListeners(): void {
    // Toggle panel
    this.tab.addEventListener("click", () => this.toggle());

    // Tab switching
    this.shadow.querySelector(".tab-bar")!.addEventListener("click", (e) => {
      const btn = (e.target as HTMLElement).closest(".tab-btn") as HTMLElement;
      if (!btn) return;
      this.switchTab(btn.dataset.tab!);
    });

    // Resize handle
    const handle = this.shadow.querySelector(".resize-handle")!;
    let startY = 0, startH = 0;
    handle.addEventListener("mousedown", (e: Event) => {
      const me = e as MouseEvent;
      startY = me.clientY;
      startH = this.panelHeight;
      const onMove = (e: MouseEvent) => {
        this.panelHeight = Math.max(150, Math.min(window.innerHeight * 0.8, startH - (e.clientY - startY)));
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

    // Keyboard shortcut: Ctrl/Cmd + Shift + Period
    this.keydownHandler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.code === "Period") {
        e.preventDefault();
        this.toggle();
      }
    };
    document.addEventListener("keydown", this.keydownHandler);
  }

  private toggle(): void {
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

  private switchTab(tabId: string): void {
    this.activeTab = tabId;
    sessionStorage.setItem("starhtml-debug-tab", tabId);
    for (const btn of this.shadow.querySelectorAll(".tab-btn")) {
      btn.classList.toggle("active", (btn as HTMLElement).dataset.tab === tabId);
    }
    this.expandedId = -1;
    this.sseToolbar = null;
    this.sseEventList = null;
    this.renderTabContent();
  }

  // Called by event capture (Task 5) when new events arrive
  public notifyNewEvent(): void {
    if (!this.isOpen) {
      this.unseenCount++;
      this.badge.textContent = String(this.unseenCount);
      this.badge.style.display = "";
    }
    this.scheduleRender();
  }

  private scheduleRender(): void {
    if (this.rafPending) return;
    this.rafPending = true;
    requestAnimationFrame(() => {
      this.rafPending = false;
      if (this.isOpen && this.activeTab === "sse") {
        this.renderSSETab();
      }
    });
  }

  private renderTabContent(): void {
    if (this.activeTab === "sse") {
      this.renderSSETab();
    } else {
      const content = this.shadow.getElementById("tab-content")!;
      content.innerHTML = `<div style="color:#6c7086;padding:16px;">Coming in Phase 2</div>`;
    }
  }

  private ensureSSEStructure(): void {
    const content = this.shadow.getElementById("tab-content")!;

    // Create persistent toolbar and event list if not already present
    if (!this.sseToolbar || !content.contains(this.sseToolbar)) {
      content.innerHTML = "";

      this.sseToolbar = document.createElement("div");
      this.sseToolbar.className = "toolbar";
      this.sseToolbar.innerHTML = `
        <input type="text" placeholder="Filter..." class="filter-input" style="width:160px">
        <button class="clear-btn">Clear</button>
        <span class="count"></span>
      `;

      this.sseEventList = document.createElement("div");
      this.sseEventList.className = "event-list";

      content.appendChild(this.sseToolbar);
      content.appendChild(this.sseEventList);

      // Persistent listeners on toolbar
      const filterInput = this.sseToolbar.querySelector(".filter-input") as HTMLInputElement;
      filterInput.addEventListener("input", () => {
        this.filterText = filterInput.value;
        this.expandedId = -1;
        this.renderSSETab();
      });

      const clearBtn = this.sseToolbar.querySelector(".clear-btn")!;
      clearBtn.addEventListener("click", () => {
        clearEvents();
        this.expandedId = -1;
        this.renderSSETab();
      });

      // Scroll tracking on the content container (the scrollable element)
      content.addEventListener("scroll", () => {
        this.userAtBottom = content.scrollTop + content.clientHeight >= content.scrollHeight - 20;
      });
    }
  }

  private renderSSETab(): void {
    this.ensureSSEStructure();
    const content = this.shadow.getElementById("tab-content")!;
    const eventList = this.sseEventList!;
    const filter = this.filterText.toLowerCase();

    const filtered = filter
      ? events.filter(ev => {
          const typeCfg = TYPE_CONFIG[ev.type];
          const label = typeCfg?.label ?? ev.type;
          const handler = (ev.debugMeta?.handler ?? "").toLowerCase();
          const route = (ev.debugMeta?.route ?? "").toLowerCase();
          return label.includes(filter) || handler.includes(filter) || route.includes(filter) || ev.type.includes(filter);
        })
      : events;

    // Update count
    const countEl = this.sseToolbar!.querySelector(".count")!;
    countEl.textContent = `${filtered.length} event${filtered.length !== 1 ? "s" : ""}`;

    // Check scroll position before re-render
    const wasAtBottom = this.userAtBottom;

    // Build event rows HTML
    let html = "";
    for (let i = 0; i < filtered.length; i++) {
      const ev = filtered[i];
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
        const detail = this.formatEventDetail(ev);
        html += `<div class="event-detail">${detail}</div>`;
      }
    }

    eventList.innerHTML = html;

    // Row click to expand/collapse
    for (const row of eventList.querySelectorAll(".event-row")) {
      row.addEventListener("click", () => {
        const eid = Number((row as HTMLElement).dataset.eid);
        this.expandedId = this.expandedId === eid ? -1 : eid;
        this.renderSSETab();
      });
    }

    // Manage jump-to-latest button
    let jumpBtn = content.querySelector(".jump-btn") as HTMLButtonElement | null;
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

    // Auto-scroll if was at bottom
    if (wasAtBottom) {
      content.scrollTop = content.scrollHeight;
    }
  }

  private formatEventDetail(ev: DebugSSEEvent): string {
    const parts: string[] = [];

    if (ev.debugMeta) {
      parts.push(`<b>seq:</b> ${ev.debugMeta.seq}  <b>ts:</b> ${ev.debugMeta.ts}  <b>handler:</b> ${escapeHtml(ev.debugMeta.handler)}  <b>route:</b> ${escapeHtml(ev.debugMeta.route)}`);
    }

    // Show argsRaw (excluding debug metadata keys)
    const args: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(ev.argsRaw)) {
      if (!k.startsWith("x-debug-")) args[k] = v;
    }
    if (Object.keys(args).length > 0) {
      const json = JSON.stringify(args, null, 2);
      parts.push(escapeHtml(json));
    }

    // Morph records summary (rendered in detail in Task 8)
    if (ev.morphRecords && ev.morphRecords.length > 0) {
      const added = ev.morphRecords.filter(r => r.type === "childList" && r.addedNodes.length > 0).length;
      const removed = ev.morphRecords.filter(r => r.type === "childList" && r.removedNodes.length > 0).length;
      const attrs = ev.morphRecords.filter(r => r.type === "attributes").length;
      parts.push(`<b>morphs:</b> ${added} added, ${removed} removed, ${attrs} attributes`);
    }

    return parts.join("\n");
  }
}

customElements.define("starhtml-debugger", StarHTMLDebugger);

// ============================================================================
// Init
// ============================================================================

let initialized = false;

export function init(): void {
  if (initialized) return;
  initialized = true;
  captureSSEEvents();
  console.log("[starhtml-debugger] initialized");
}
