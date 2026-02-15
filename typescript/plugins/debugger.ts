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

// Ring buffer for events (eviction logic in Task 5)
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
  }
  .debugger-tab {
    position: absolute;
    bottom: 0;
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
    gap: 0;
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

  constructor() {
    super();
    this.shadow = this.attachShadow({ mode: "open" });

    // Restore state from sessionStorage
    this.isOpen = sessionStorage.getItem("starhtml-debug-open") === "true";
    this.panelHeight = parseInt(sessionStorage.getItem("starhtml-debug-height") || "300");
    this.activeTab = sessionStorage.getItem("starhtml-debug-tab") || "sse";

    this.render();
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

    // Keyboard shortcut: Ctrl/Cmd + Shift + .
    document.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === ".") {
        e.preventDefault();
        this.toggle();
      }
    });
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

export function init(): void {
  console.log("[starhtml-debugger] initialized");
}
