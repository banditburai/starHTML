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
type Position = { x: number; y: number; placement: string };

const OPPOSITES = { left: "right", right: "left", top: "bottom", bottom: "top" };
const VALID_PLACEMENTS: Placement[] = [
  "top",
  "bottom",
  "left",
  "right",
  "top-start",
  "top-end",
  "bottom-start",
  "bottom-end",
  "left-start",
  "left-end",
  "right-start",
  "right-end",
];

class StablePositioner {
  private history: Array<Position & { timestamp: number }> = [];
  private lockedPlacement: Placement | null = null;
  private lockUntil = 0;

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

  async position(): Promise<Position> {
    const placement = this.getStablePlacement();
    const zoom = window.devicePixelRatio || 1;
    const padding = Math.max(20, 30 * zoom);

    const middleware: Middleware[] = [offset(this.config.offset)];

    if (this.config.flip && !this.isLocked()) {
      middleware.push(flip({ padding, fallbackStrategy: "bestFit" }));
    }
    if (this.config.shift) middleware.push(shift({ padding }));
    if (this.config.hide) middleware.push(hide());
    if (this.config.autoSize) {
      middleware.push(
        size({
          apply: ({ availableWidth, availableHeight, elements }) => {
            Object.assign(elements.floating.style, {
              maxWidth: `${availableWidth}px`,
              maxHeight: `${availableHeight}px`,
            });
          },
          padding: 10,
        })
      );
    }

    const {
      x,
      y,
      placement: finalPlacement,
    } = await computePosition(this.reference, this.floating, {
      placement,
      strategy: this.config.strategy,
      middleware,
    });

    const result = {
      x: Math.round(x),
      y: Math.round(y),
      placement: finalPlacement,
    };

    this.recordHistory(result);
    return result;
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
    this.history = this.history.filter((h) => now - h.timestamp < 2000);

    if (this.history.length < 3) return false;

    const placements = this.history.map((h) => h.placement);
    if (new Set(placements).size <= 1) return false;

    // Oscillating between opposite sides?
    const hasOpposites = Object.entries(OPPOSITES).some(
      ([side, opposite]) =>
        placements.some((p) => p.includes(side)) && placements.some((p) => p.includes(opposite))
    );
    if (hasOpposites) return true;

    // Rapid movement?
    const recent = this.history.slice(-3);
    const movement = recent
      .slice(1)
      .reduce((sum, h, i) => sum + Math.abs(h.x - recent[i].x) + Math.abs(h.y - recent[i].y), 0);

    return movement > 50 && now - recent[0].timestamp < 500;
  }

  private findBestPlacement(): Placement {
    const rect = this.reference.getBoundingClientRect();
    const floatingRect = this.floating.getBoundingClientRect();
    const viewport = { width: window.innerWidth, height: window.innerHeight };
    const padding = Math.max(20, 30 * (window.devicePixelRatio || 1));

    const space = {
      top: (rect.top - padding) / floatingRect.height,
      bottom: (viewport.height - rect.bottom - padding) / floatingRect.height,
      left: (rect.left - padding) / floatingRect.width,
      right: (viewport.width - rect.right - padding) / floatingRect.width,
    };

    const [base, align] = this.config.placement.split("-");
    if (space[base as keyof typeof space] > 0.8) return this.config.placement;

    const [best] = Object.entries(space).reduce((a, b) => (b[1] > a[1] ? b : a));
    return (align ? `${best}-${align}` : best) as Placement;
  }

  private lock(placement: Placement): void {
    this.lockedPlacement = placement;
    this.lockUntil = Date.now() + 1500;
  }

  private isLocked(): boolean {
    return Date.now() < this.lockUntil && this.lockedPlacement !== null;
  }

  private recordHistory(position: Position): void {
    this.history.push({ ...position, timestamp: Date.now() });
    if (this.history.length > 10) this.history.shift();
  }

  shouldUpdate(x: number, y: number, placement: string, last: Position): boolean {
    const threshold = Math.max(2, 3 * Math.sqrt(window.devicePixelRatio || 1));
    return (
      Math.abs(x - last.x) > threshold ||
      Math.abs(y - last.y) > threshold ||
      placement !== last.placement
    );
  }

  reset(): void {
    this.history = [];
    this.lockUntil = 0;
    this.lockedPlacement = null;
  }
}

const extract = (value: unknown): string =>
  typeof value === "string" ? value : value instanceof Set ? Array.from(value)[0] || "" : "";

const extractPlacement = (value: unknown): Placement => {
  const str = extract(value) || "bottom";
  return VALID_PLACEMENTS.includes(str as Placement) ? (str as Placement) : "bottom";
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
    let lastPos: Position = { x: -999, y: -999, placement: "" };

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
      return (
        style.display !== "none" &&
        style.visibility !== "hidden" &&
        el.offsetWidth > 0 &&
        el.offsetHeight > 0
      );
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
