/**
 * StarHTML Debugger - Phase 1
 * Captures SSE events, signal patches, and DOM mutations.
 * Renders a bottom-drawer debug panel in Shadow DOM.
 */

// Types
export interface DebugSSEEvent {
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

    if (this.isOpen) this.panel.classList.add("open");

    this.setupEventListeners();
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
    }
  }

  private switchTab(tabId: string): void {
    this.activeTab = tabId;
    sessionStorage.setItem("starhtml-debug-tab", tabId);
    for (const btn of this.shadow.querySelectorAll(".tab-btn")) {
      btn.classList.toggle("active", (btn as HTMLElement).dataset.tab === tabId);
    }
    // Re-render tab content (implemented in Task 6)
  }

  // Called by event capture (Task 5) when new events arrive
  public notifyNewEvent(): void {
    if (!this.isOpen) {
      this.unseenCount++;
      this.badge.textContent = String(this.unseenCount);
      this.badge.style.display = "";
    }
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
