// debugger.ts — Legacy web component UI for the StarHTML debugger.
// Data layer and rendering helpers are in debugger-capture.ts.

import {
  type DebugSSEEvent,
  TYPE_CONFIG, CHIP_CATEGORIES,
  getEvents, clearEvents, startObserving, stopObserving,
  subscribe, getFilteredEvents, buildAllowedTypes,
  buildRowHtml, formatEventDetail, formatSingleEventForExport, formatAllEventsForExport,
  init,
} from './debugger-capture';

// Re-export public API so existing imports from 'debugger' still work
export { type DebugSSEEvent, getEvents, clearEvents, getMorphWindow, init } from './debugger-capture';

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
    cursor: ns-resize;
    user-select: none;
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
    user-select: none;
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
    position: sticky;
    bottom: 8px;
    float: right;
    margin-right: 8px;
    background: #89b4fa;
    color: #1e1e2e;
    border: none;
    padding: 4px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-family: inherit;
    font-size: 11px;
    font-weight: 600;
    z-index: 1;
  }
  .jump-btn:hover { background: #b4d0fb; }
  .detail-section { margin-bottom: 6px; }
  .detail-section:last-child { margin-bottom: 0; }
  .detail-header { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
  .detail-header .mode-badge {
    background: #313244; color: #cba6f7; padding: 1px 6px; border-radius: 3px;
    font-size: 10px; font-weight: 600; text-transform: uppercase;
  }
  .detail-header .target { color: #89b4fa; }
  .detail-label { color: #585b70; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }
  .html-block {
    background: #11111b; padding: 6px 8px; border-radius: 3px; border: 1px solid #313244;
    overflow-x: auto; white-space: pre-wrap; word-break: break-word;
  }
  .html-block .ht { color: #89b4fa; }
  .html-block .ha { color: #f9e2af; }
  .html-block .hv { color: #a6e3a1; }
  .html-block .hx { color: #9399b2; }
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
  .event-preview { color: #9399b2; overflow: hidden; text-overflow: ellipsis; min-width: 0; flex: 1; }
  .morph-badge { color: #a6e3a1; flex-shrink: 0; font-size: 10px; }
  .type-chips { display: flex; gap: 4px; align-items: center; }
  .type-chip {
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 600;
    cursor: pointer;
    border: 1px solid transparent;
    opacity: 0.4;
    transition: opacity 0.1s ease;
    user-select: none;
  }
  .type-chip:hover { opacity: 0.7; }
  .type-chip.active { opacity: 1; }
  .chip-signals { background: #1e3a5f; color: #89b4fa; border-color: #1e3a5f; }
  .chip-signals.active { border-color: #89b4fa; }
  .chip-elements { background: #1e3f2a; color: #a6e3a1; border-color: #1e3f2a; }
  .chip-elements.active { border-color: #a6e3a1; }
  .chip-script { background: #2e1f5e; color: #cba6f7; border-color: #2e1f5e; }
  .chip-script.active { border-color: #cba6f7; }
  .chip-lifecycle { background: #313244; color: #bac2de; border-color: #313244; }
  .chip-lifecycle.active { border-color: #bac2de; }
  .toolbar-sep { width: 1px; height: 16px; background: #45475a; flex-shrink: 0; }
  .group-0 { border-left: 2px solid #89b4fa; }
  .group-1 { border-left: 2px solid #a6e3a1; }
  .group-2 { border-left: 2px solid #cba6f7; }
  .event-duration { color: #9399b2; flex-shrink: 0; font-size: 10px; }
  .copy-btn {
    background: #313244; border: 1px solid #45475a; color: #9399b2;
    padding: 2px 8px; border-radius: 3px; cursor: pointer;
    font-family: inherit; font-size: 10px; float: right;
  }
  .copy-btn:hover { background: #45475a; color: #cdd6f4; }
  .copy-btn.copied { color: #a6e3a1; border-color: #a6e3a1; }
`;

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
  private visibleSinceId: number = 0;
  private expandedId: number = -1;
  private rafPending: boolean = false;
  private userAtBottom: boolean = true;
  private sseToolbar: HTMLDivElement | null = null;
  private sseEventList: HTMLDivElement | null = null;
  private activeTypeFilters: Set<string> = new Set();
  private lastRenderedIds: number[] = [];
  private needsFullRender: boolean = true;
  private unsubscribe: (() => void) | null = null;

  constructor() {
    super();
    this.shadow = this.attachShadow({ mode: "open" });
    this.isOpen = sessionStorage.getItem("starhtml-debug-open") === "true";
    const stored = Number(sessionStorage.getItem("starhtml-debug-height"));
    this.panelHeight = Number.isNaN(stored) || stored <= 0 ? 300 : stored;
    this.activeTab = sessionStorage.getItem("starhtml-debug-tab") || "sse";
    this.unsubscribe = subscribe(() => this.notifyNewEvent());
    this.render();
  }

  disconnectedCallback(): void {
    if (this.unsubscribe) {
      this.unsubscribe();
      this.unsubscribe = null;
    }
    if (this.keydownHandler) {
      document.removeEventListener("keydown", this.keydownHandler);
      this.keydownHandler = null;
    }
    document.documentElement.style.paddingBottom = "";
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
        <div class="tab-content" id="tab-content"></div>
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
    this.updatePageInset();

    if (this.isOpen) {
      this.renderTabContent();
    }
  }

  private setupEventListeners(): void {
    this.tab.addEventListener("click", () => this.toggle());

    this.shadow.querySelector(".tab-bar")!.addEventListener("click", (e) => {
      const btn = (e.target as HTMLElement).closest<HTMLElement>(".tab-btn");
      if (!btn) return;
      this.switchTab(btn.dataset.tab!);
    });

    const startResize = (e: Event) => {
      const me = e as MouseEvent;
      const startY = me.clientY;
      const startH = this.panelHeight;
      const onMove = (e: MouseEvent) => {
        this.panelHeight = Math.max(150, Math.min(window.innerHeight * 0.8, startH - (e.clientY - startY)));
        this.panel.style.height = `${this.panelHeight}px`;
        this.updatePageInset();
      };
      const onUp = () => {
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
        sessionStorage.setItem("starhtml-debug-height", String(this.panelHeight));
      };
      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    };

    this.shadow.querySelector(".resize-handle")!.addEventListener("mousedown", startResize);

    this.shadow.querySelector(".tab-bar")!.addEventListener("mousedown", (e: Event) => {
      if ((e.target as HTMLElement).closest(".tab-btn")) return;
      startResize(e);
    });

    this.keydownHandler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.code === "Period") {
        e.preventDefault();
        this.toggle();
      }
    };
    document.addEventListener("keydown", this.keydownHandler);
  }

  private updatePageInset(): void {
    document.documentElement.style.paddingBottom =
      this.isOpen ? `${this.panelHeight}px` : "";
  }

  private toggle(): void {
    this.isOpen = !this.isOpen;
    this.panel.classList.toggle("open", this.isOpen);
    sessionStorage.setItem("starhtml-debug-open", String(this.isOpen));
    this.updatePageInset();
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
    for (const btn of this.shadow.querySelectorAll<HTMLElement>(".tab-btn")) {
      btn.classList.toggle("active", btn.dataset.tab === tabId);
    }
    this.expandedId = -1;
    this.sseToolbar = null;
    this.sseEventList = null;
    this.renderTabContent();
  }

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
      this.shadow.getElementById("tab-content")!.innerHTML =
        `<div style="color:#6c7086;padding:16px;">Coming in Phase 2</div>`;
    }
  }

  private ensureSSEStructure(): void {
    const content = this.shadow.getElementById("tab-content")!;
    if (!this.sseToolbar || !content.contains(this.sseToolbar)) {
      content.innerHTML = "";

      this.sseToolbar = document.createElement("div");
      this.sseToolbar.className = "toolbar";
      const chipsHtml = CHIP_CATEGORIES.map(c =>
        `<span class="type-chip ${c.cls}${this.activeTypeFilters.has(c.key) ? " active" : ""}" data-chip="${c.key}">${c.label}</span>`
      ).join("");
      this.sseToolbar.innerHTML = `
        <div class="type-chips">${chipsHtml}</div>
        <div class="toolbar-sep"></div>
        <div class="filter-wrap">
          <input type="text" placeholder="Filter..." class="filter-input" style="width:160px;padding-right:20px">
          <button class="clear-filter-btn" style="display:none" title="Clear filter">&times;</button>
        </div>
        <button class="clear-events-btn" title="Clear visible events">Clear Events</button>
        <button class="copy-all-btn" title="Copy all visible events for LLM context">Copy All</button>
        <span class="count"></span>
      `;

      this.sseEventList = document.createElement("div");
      this.sseEventList.className = "event-list";

      content.appendChild(this.sseToolbar);
      content.appendChild(this.sseEventList);

      const filterInput = this.sseToolbar.querySelector(".filter-input") as HTMLInputElement;
      const clearFilterBtn = this.sseToolbar.querySelector(".clear-filter-btn") as HTMLButtonElement;

      filterInput.addEventListener("input", () => {
        this.filterText = filterInput.value;
        clearFilterBtn.style.display = this.filterText ? "" : "none";
        this.expandedId = -1;
        this.needsFullRender = true;
        this.renderSSETab();
      });

      clearFilterBtn.addEventListener("click", () => {
        this.filterText = "";
        filterInput.value = "";
        clearFilterBtn.style.display = "none";
        this.expandedId = -1;
        this.needsFullRender = true;
        this.renderSSETab();
      });

      this.sseToolbar.querySelector(".clear-events-btn")!.addEventListener("click", () => {
        const evts = getEvents();
        const latest = evts[evts.length - 1];
        this.visibleSinceId = latest ? latest.id + 1 : 0;
        this.expandedId = -1;
        this.needsFullRender = true;
        this.renderSSETab();
      });

      this.sseToolbar.querySelector(".type-chips")!.addEventListener("click", (e) => {
        const chip = (e.target as HTMLElement).closest<HTMLElement>(".type-chip");
        if (!chip) return;
        const key = chip.dataset.chip!;
        if (this.activeTypeFilters.has(key)) {
          this.activeTypeFilters.delete(key);
          chip.classList.remove("active");
        } else {
          this.activeTypeFilters.add(key);
          chip.classList.add("active");
        }
        this.expandedId = -1;
        this.needsFullRender = true;
        this.renderSSETab();
      });

      // Event delegation: single click handler for all rows and copy buttons
      this.sseEventList.addEventListener("click", (e) => {
        const target = e.target as HTMLElement;

        const copyBtn = target.closest<HTMLButtonElement>(".copy-btn[data-copy-eid]");
        if (copyBtn) {
          e.stopPropagation();
          const eid = Number(copyBtn.dataset.copyEid);
          const evts = getEvents();
          const ev = evts.find(ev => ev.id === eid);
          if (!ev) return;
          const text = formatSingleEventForExport(ev);
          navigator.clipboard.writeText(text).then(() => {
            copyBtn.textContent = "Copied!";
            copyBtn.classList.add("copied");
            setTimeout(() => { copyBtn.textContent = "Copy"; copyBtn.classList.remove("copied"); }, 1500);
          });
          return;
        }

        const row = target.closest<HTMLElement>(".event-row");
        if (!row) return;
        const eid = Number(row.dataset.eid);
        const wasExpanded = this.expandedId === eid;
        const prevExpandedId = this.expandedId;
        this.expandedId = wasExpanded ? -1 : eid;

        if (prevExpandedId !== -1) {
          const prevRow = this.sseEventList!.querySelector<HTMLElement>(`.event-row[data-eid="${prevExpandedId}"]`);
          if (prevRow) {
            prevRow.classList.remove("expanded");
            const prevDetail = prevRow.nextElementSibling;
            if (prevDetail?.classList.contains("event-detail")) prevDetail.remove();
          }
        }

        if (!wasExpanded) {
          row.classList.add("expanded");
          const evts = getEvents();
          const ev = evts.find(ev => ev.id === eid);
          if (ev) {
            const detail = document.createElement("div");
            detail.className = "event-detail";
            detail.innerHTML = `<button class="copy-btn" data-copy-eid="${ev.id}">Copy</button>${formatEventDetail(ev)}`;
            row.insertAdjacentElement("afterend", detail);
          }
        }
      });

      this.sseToolbar.querySelector(".copy-all-btn")!.addEventListener("click", (e) => {
        const btn = e.target as HTMLButtonElement;
        const allowedTypes = buildAllowedTypes(this.activeTypeFilters);
        const filtered = getFilteredEvents(this.visibleSinceId, allowedTypes, this.filterText);
        const text = formatAllEventsForExport(filtered);
        navigator.clipboard.writeText(text).then(() => {
          btn.textContent = "Copied!";
          btn.classList.add("copied");
          setTimeout(() => { btn.textContent = "Copy All"; btn.classList.remove("copied"); }, 1500);
        });
      });

      content.addEventListener("scroll", () => {
        this.userAtBottom = content.scrollTop + content.clientHeight >= content.scrollHeight - 20;
      });
    }
  }

  private renderSSETab(): void {
    this.ensureSSEStructure();
    const content = this.shadow.getElementById("tab-content")!;
    const eventList = this.sseEventList!;

    const allowedTypes = buildAllowedTypes(this.activeTypeFilters);
    const filtered = getFilteredEvents(this.visibleSinceId, allowedTypes, this.filterText);

    // Update chip counts (visible events = all since watermark, regardless of type/text filter)
    const visible = getFilteredEvents(this.visibleSinceId, null, "");
    for (const chip of CHIP_CATEGORIES) {
      const count = visible.filter(ev => chip.types.includes(ev.type)).length;
      const el = this.sseToolbar!.querySelector(`.type-chip[data-chip="${chip.key}"]`);
      if (el) el.textContent = `${chip.label} (${count})`;
    }

    this.sseToolbar!.querySelector(".count")!.textContent =
      `${filtered.length} event${filtered.length !== 1 ? "s" : ""}`;

    const wasAtBottom = this.userAtBottom;
    const filteredIds = filtered.map(ev => ev.id);

    // Incremental append
    if (!this.needsFullRender && filteredIds.length >= this.lastRenderedIds.length) {
      let canIncrement = true;
      for (let i = 0; i < this.lastRenderedIds.length; i++) {
        if (this.lastRenderedIds[i] !== filteredIds[i]) { canIncrement = false; break; }
      }
      if (canIncrement && filteredIds.length > this.lastRenderedIds.length) {
        const newEvents = filtered.slice(this.lastRenderedIds.length);
        let appendHtml = "";
        for (const ev of newEvents) {
          appendHtml += buildRowHtml(ev);
        }
        eventList.insertAdjacentHTML("beforeend", appendHtml);
        this.lastRenderedIds = filteredIds;
        this.needsFullRender = false;

        if (wasAtBottom) content.scrollTop = content.scrollHeight;
        this.updateJumpButton(content, filtered.length);
        return;
      }
    }

    // Full render fallback
    let html = "";
    for (const ev of filtered) {
      html += buildRowHtml(ev);
    }
    eventList.innerHTML = html;
    this.lastRenderedIds = filteredIds;
    this.needsFullRender = false;

    if (wasAtBottom) {
      content.scrollTop = content.scrollHeight;
    }
    this.updateJumpButton(content, filtered.length);
  }

  private updateJumpButton(content: HTMLElement, eventCount: number): void {
    let jumpBtn = content.querySelector(".jump-btn") as HTMLButtonElement | null;
    if (!this.userAtBottom && eventCount > 0) {
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
  }
}

if (!customElements.get("starhtml-debugger")) {
  customElements.define("starhtml-debugger", StarHTMLDebugger);
}
