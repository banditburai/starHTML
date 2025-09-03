import {
  type Middleware,
  type Placement,
  type Strategy,
  autoUpdate,
  computePosition,
  flip,
  hide,
  offset,
  shift,
  size,
} from "@floating-ui/dom";

interface AttributePlugin {
  type: "attribute";
  name: string;
  keyReq: "starts" | "exact";
  onLoad: (ctx: RuntimeContext) => OnRemovalFn | void;
}

interface RuntimeContext {
  el: HTMLElement;
  key: string;
  value: string;
  mods: Map<string, any>;
  rx: (...args: any[]) => any;
  effect: (fn: () => void) => () => void;
  getPath: (path: string) => any;
  mergePatch: (patch: Record<string, any>) => void;
  startBatch: () => void;
  endBatch: () => void;
}

type OnRemovalFn = () => void;

const TIMING = {
  OSCILLATION_WINDOW: 2000,
  OSCILLATION_THRESHOLD: 3,
  STABILIZATION_DURATION: 1500,
  HISTORY_LIMIT: 10,
} as const;

const THRESHOLDS = {
  ZOOM_CHANGE: 0.01,
  BASE_PADDING: 20,
  PADDING_MULTIPLIER: 30,
  MOVEMENT_THRESHOLD: 50,
  RAPID_MOVEMENT_WINDOW: 500,
} as const;

const PLACEMENT_OPPOSITES = {
  left: "right",
  right: "left",
  top: "bottom",
  bottom: "top",
} as const;

class StablePositioner {
  private history: Array<{ x: number; y: number; placement: string; timestamp: number }> = [];
  private lockedPlacement: Placement | null = null;
  private lockUntil = 0;
  private lastZoom = window.devicePixelRatio || 1;

  constructor(
    private reference: HTMLElement,
    private floating: HTMLElement,
    private config: {
      placement: Placement;
      strategy: Strategy;
      offset: number;
      flip: boolean;
      shift: boolean;
      hide: boolean;
      autoSize: boolean;
    }
  ) {}

  async position() {
    const zoom = window.devicePixelRatio || 1;
    if (Math.abs(zoom - this.lastZoom) > THRESHOLDS.ZOOM_CHANGE) {
      this.lastZoom = zoom;
      this.reset();
    }

    const placement = this.getStablePlacement();
    const padding = Math.max(THRESHOLDS.BASE_PADDING, THRESHOLDS.PADDING_MULTIPLIER * zoom);
    
    const middleware: Middleware[] = [offset(this.config.offset)];
    
    if (this.config.flip && !this.isLocked()) {
      middleware.push(flip({ padding, fallbackStrategy: "bestFit" }));
    }
    
    if (this.config.shift) middleware.push(shift({ padding }));
    if (this.config.hide) middleware.push(hide());
    
    if (this.config.autoSize) {
      middleware.push(size({
        apply: ({ availableWidth, availableHeight, elements }) => {
          Object.assign(elements.floating.style, {
            maxWidth: `${availableWidth}px`,
            maxHeight: `${availableHeight}px`,
          });
        },
        padding: 10,
      }));
    }

    const result = await computePosition(this.reference, this.floating, {
      placement,
      strategy: this.config.strategy,
      middleware,
    });

    this.recordHistory(result);
    
    return {
      x: Math.round(result.x),
      y: Math.round(result.y),
      placement: result.placement,
    };
  }

  private getStablePlacement(): Placement {
    if (this.isLocked() && this.lockedPlacement) return this.lockedPlacement;

    if (this.detectOscillation()) {
      const placement = this.findBestPlacement();
      this.lock(placement);
      return placement;
    }

    return this.config.placement;
  }

  private detectOscillation(): boolean {
    const now = Date.now();
    this.history = this.history.filter(h => now - h.timestamp < TIMING.OSCILLATION_WINDOW);
    
    if (this.history.length < TIMING.OSCILLATION_THRESHOLD) return false;

    const placements = this.history.map(h => h.placement);
    const uniquePlacements = new Set(placements);
    
    if (uniquePlacements.size <= 1) return false;

    // Detect opposing placements
    for (const [side, opposite] of Object.entries(PLACEMENT_OPPOSITES)) {
      if (placements.some(p => p.includes(side)) && placements.some(p => p.includes(opposite))) {
        return true;
      }
    }

    // Detect rapid movement
    const recent = this.history.slice(-3);
    if (recent.length < 3) return false;
    
    const movement = recent.reduce((sum, h, i) => {
      if (i === 0) return 0;
      const prev = recent[i - 1];
      return sum + Math.abs(h.x - prev.x) + Math.abs(h.y - prev.y);
    }, 0);

    return movement > THRESHOLDS.MOVEMENT_THRESHOLD && 
           (now - recent[0].timestamp) < THRESHOLDS.RAPID_MOVEMENT_WINDOW;
  }

  private findBestPlacement(): Placement {
    const rect = this.reference.getBoundingClientRect();
    const floatingRect = this.floating.getBoundingClientRect();
    const viewport = { width: window.innerWidth, height: window.innerHeight };
    const padding = Math.max(THRESHOLDS.BASE_PADDING, THRESHOLDS.PADDING_MULTIPLIER * this.lastZoom);
    
    const space = {
      top: rect.top - padding,
      bottom: viewport.height - rect.bottom - padding,
      left: rect.left - padding,
      right: viewport.width - rect.right - padding,
    };

    const scores = {
      top: space.top / floatingRect.height,
      bottom: space.bottom / floatingRect.height,
      left: space.left / floatingRect.width,
      right: space.right / floatingRect.width,
    };

    const [base] = this.config.placement.split("-");
    const alignment = this.config.placement.includes("-") ? this.config.placement.split("-")[1] : "";
    
    // Prefer original placement if space is adequate
    if (scores[base as keyof typeof scores] > 0.8) return this.config.placement;

    const best = Object.entries(scores).reduce((a, b) => b[1] > a[1] ? b : a);
    return (alignment ? `${best[0]}-${alignment}` : best[0]) as Placement;
  }

  private lock(placement: Placement): void {
    const zoom = window.devicePixelRatio || 1;
    this.lockedPlacement = placement;
    this.lockUntil = Date.now() + TIMING.STABILIZATION_DURATION * Math.max(1, zoom / 2);
  }

  private isLocked(): boolean {
    return Date.now() < this.lockUntil;
  }

  private recordHistory(result: { x: number; y: number; placement: Placement }): void {
    this.history.push({
      x: result.x,
      y: result.y,
      placement: result.placement,
      timestamp: Date.now(),
    });

    if (this.history.length > TIMING.HISTORY_LIMIT) {
      this.history = this.history.slice(-TIMING.HISTORY_LIMIT);
    }
  }

  shouldUpdate(x: number, y: number, placement: string, last: { x: number; y: number; placement: string }): boolean {
    const zoom = window.devicePixelRatio || 1;
    const threshold = Math.max(2, 3 * Math.sqrt(zoom));
    
    return Math.abs(x - last.x) > threshold ||
           Math.abs(y - last.y) > threshold ||
           placement !== last.placement;
  }

  reset(): void {
    this.history = [];
    this.lockUntil = 0;
    this.lockedPlacement = null;
  }
}

const extract = (value: unknown): string => {
  if (!value) return "";
  if (typeof value === "string") return value;
  if (value instanceof Set) return Array.from(value)[0] || "";
  return "";
};

const extractPlacement = (value: unknown): Placement => {
  const str = extract(value) || "bottom";
  const valid = ["top", "bottom", "left", "right", "top-start", "top-end", 
                 "bottom-start", "bottom-end", "left-start", "left-end", 
                 "right-start", "right-end"];
  return valid.includes(str) ? str as Placement : "bottom";
};

export default {
  type: "attribute",
  name: "position",
  keyReq: "starts",

  onLoad({ el, value, mods, startBatch, endBatch }: RuntimeContext): OnRemovalFn | void {
    const config = {
      anchor: extract(mods.get("anchor") || value),
      placement: extractPlacement(mods.get("placement")),
      strategy: (extract(mods.get("strategy")) || "absolute") as Strategy,
      offset: Number(extract(mods.get("offset"))) || 8,
      flip: extract(mods.get("flip")) !== "false",
      shift: extract(mods.get("shift")) !== "false",
      hide: extract(mods.get("hide")) === "true",
      autoSize: extract(mods.get("auto_size")) === "true",
    };

    const anchor = document.getElementById(config.anchor);
    if (!anchor && !el.hasAttribute("popover")) return;

    let positioner: StablePositioner | null = null;
    let cleanup: (() => void) | null = null;
    let lastPos = { x: -999, y: -999, placement: "" };

    const updatePosition = async () => {
      const target = anchor || document.getElementById(config.anchor);
      if (!target?.isConnected) return;

      startBatch();
      try {
        positioner ??= new StablePositioner(target, el, config);
        const result = await positioner.position();

        if (positioner.shouldUpdate(result.x, result.y, result.placement, lastPos)) {
          Object.assign(el.style, {
            position: config.strategy,
            left: `${result.x}px`,
            top: `${result.y}px`,
          });
          lastPos = result;
        }
      } finally {
        endBatch();
      }
    };

    const isVisible = () => {
      const style = getComputedStyle(el);
      return style.display !== "none" && 
             style.visibility !== "hidden" && 
             el.offsetWidth > 0 && 
             el.offsetHeight > 0;
    };

    const start = () => {
      const target = anchor || document.getElementById(config.anchor);
      if (!target) return;
      
      cleanup = autoUpdate(target, el, updatePosition, {
        ancestorScroll: true,
        ancestorResize: true,
        elementResize: false,
        layoutShift: false,
      });
    };

    const stop = () => {
      cleanup?.();
      cleanup = null;
      positioner?.reset();
      positioner = null;
    };

    if (el.hasAttribute("popover")) {
      const handleToggle = (e: any) => {
        if (e.newState === "open") start();
        else if (e.newState === "closed") stop();
      };
      el.addEventListener("toggle", handleToggle);
      return () => {
        el.removeEventListener("toggle", handleToggle);
        stop();
      };
    }

    const observer = new MutationObserver(() => {
      if (isVisible() && !cleanup) start();
      else if (!isVisible() && cleanup) stop();
    });

    observer.observe(el, {
      attributes: true,
      attributeFilter: ["style", "class", "data-show"],
    });

    if (isVisible()) start();

    return () => {
      observer.disconnect();
      stop();
    };
  },
} satisfies AttributePlugin;