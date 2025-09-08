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

class OscillationDetector {
  private history: Array<Position & { timestamp: number }> = [];
  private lockedPosition: Position | null = null;
  private lockUntil = 0;
  private lastPosition: Position | null = null;

  addPosition(pos: Position): void {
    const now = Date.now();
    if (this.lastPosition?.x === pos.x && this.lastPosition?.y === pos.y) return;

    this.history.push({ ...pos, timestamp: now });
    this.lastPosition = pos;
    this.history = this.history.filter((h) => now - h.timestamp < 1000);

    if (this.history.length >= 3) {
      const recent = this.history.slice(-3);
      const positions = new Set(recent.map((p) => `${p.x},${p.y}`));

      if (positions.size === 2 && now - recent[0].timestamp < 500) {
        this.lockedPosition = { ...pos };
        this.lockUntil = now + 2000;
      }
    }
  }

  getPosition(computed: Position): Position {
    const now = Date.now();
    if (now >= this.lockUntil) this.lockedPosition = null;
    return this.lockedPosition && now < this.lockUntil ? this.lockedPosition : computed;
  }

  reset(): void {
    Object.assign(this, {
      history: [],
      lockedPosition: null,
      lockUntil: 0,
      lastPosition: null,
    });
  }
}

type PositionConfig = {
  placement: Placement;
  strategy: Strategy;
  offset: number;
  hasCustomOffset: boolean;
  flip: boolean;
  shift: boolean;
  hide: boolean;
  autoSize: boolean;
};

async function computeFloatingPosition(
  reference: HTMLElement,
  floating: HTMLElement,
  config: PositionConfig,
  detector?: OscillationDetector
): Promise<Position> {
  const padding = 10;
  const parentPopover = floating.parentElement?.closest(
    "[popover]:popover-open"
  ) as HTMLElement | null;

  let offsetValue = config.offset;

  // Submenus need offset relative to parent menu edge, not trigger element
  if (parentPopover) {
    const parentRect = parentPopover.getBoundingClientRect();
    const refRect = reference.getBoundingClientRect();

    const edgeDistances = {
      right: parentRect.right - refRect.right,
      left: refRect.left - parentRect.left,
      bottom: parentRect.bottom - refRect.bottom,
      top: refRect.top - parentRect.top,
    };

    const edge = config.placement.split("-")[0] as keyof typeof edgeDistances;
    if (edge in edgeDistances) {
      offsetValue = edgeDistances[edge] + (config.hasCustomOffset ? config.offset : -2);
    }
  }

  const middleware: Middleware[] = [offset(offsetValue)];
  if (config.flip) middleware.push(flip({ padding }));
  if (config.shift) middleware.push(shift({ padding }));
  if (config.hide) middleware.push(hide());
  if (config.autoSize) {
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

  const strategy = floating.hasAttribute("popover") ? "fixed" : config.strategy;
  const { x, y, placement } = await computePosition(reference, floating, {
    placement: config.placement,
    strategy: strategy as Strategy,
    middleware,
  });

  if (x === 0 && y === 0) {
    const { width, height } = reference.getBoundingClientRect();
    if (width === 0 || height === 0) {
      return { x: -9999, y: -9999, placement };
    }
  }

  const position = { x: Math.round(x), y: Math.round(y), placement };

  if (detector) {
    detector.addPosition(position);
    return detector.getPosition(position);
  }

  return position;
}

const shouldUpdatePosition = (current: Position, last: Position, threshold = 2): boolean =>
  Math.abs(current.x - last.x) > threshold ||
  Math.abs(current.y - last.y) > threshold ||
  current.placement !== last.placement;

const extract = (value: unknown): string => {
  if (typeof value === "string") return value;
  if (value instanceof Set) return Array.from(value)[0] || "";
  return "";
};

const extractPlacement = (value: unknown): Placement => {
  let str = extract(value) || "bottom";

  str = str.replace(/^(top|bottom|left|right)(start|end)$/i, "$1-$2");

  const hyphenMap: Record<string, Placement> = {
    topstart: "top-start",
    topend: "top-end",
    bottomstart: "bottom-start",
    bottomend: "bottom-end",
    leftstart: "left-start",
    leftend: "left-end",
    rightstart: "right-start",
    rightend: "right-end",
  };

  const normalized = hyphenMap[str.toLowerCase()] || str;
  return VALID_PLACEMENTS.includes(normalized as Placement) ? (normalized as Placement) : "bottom";
};

const injectPositioningCSS = () => {
  const styleId = "starhtml-positioning-css";
  if (document.getElementById(styleId)) return;

  const style = document.createElement("style");
  style.id = styleId;
  style.textContent = `
    [data-positioning="true"]:not([popover]) {
      visibility: hidden !important;
      opacity: 0 !important;
    }
    [data-positioning="false"]:not([popover]) {
      visibility: visible !important;
      opacity: 1 !important;
      transition: opacity 150ms ease-out;
    }
  `;
  document.head.appendChild(style);
};

export default {
  type: "attribute",
  name: "position",
  keyReq: "starts",

  onLoad({ el, value, mods, startBatch, endBatch }: RuntimeContext): OnRemovalFn | void {
    injectPositioningCSS();

    const offsetValue = extract(mods.get("offset"));
    const config = {
      anchor: extract(mods.get("anchor") || value),
      placement: extractPlacement(mods.get("placement")),
      strategy: (extract(mods.get("strategy")) || "absolute") as Strategy,
      offset: offsetValue ? Number(offsetValue) : 8,
      hasCustomOffset: !!offsetValue,
      flip: extract(mods.get("flip")) !== "false",
      shift: extract(mods.get("shift")) !== "false",
      hide: extract(mods.get("hide")) === "true",
      autoSize: extract(mods.get("auto_size")) === "true",
    };

    const anchor = document.getElementById(config.anchor);
    if (!anchor && !el.hasAttribute("popover")) return;

    let cleanup: (() => void) | null = null;
    let lastPos: Position = { x: -999, y: -999, placement: "" };
    let hasPositioned = false;
    let showTimer: number | null = null;
    let settlementTimer: number | null = null;
    let domHistory: Array<{ x: number; y: number; timestamp: number }> = [];
    let isLocked = false;
    let lockUntil = 0;

    const prepareHiddenState = () => {
      const baseStyle = { visibility: "hidden" as const, opacity: "0" };
      const style = config.hide
        ? { ...baseStyle, transition: "opacity 150ms ease-out" }
        : baseStyle;

      if (config.hide || el.hasAttribute("popover")) {
        Object.assign(el.style, style);
      }
    };

    prepareHiddenState();

    const checkDOMOscillation = (x: number, y: number): boolean => {
      const now = Date.now();
      domHistory.push({ x, y, timestamp: now });
      domHistory = domHistory.filter((h) => now - h.timestamp < 1000);

      if (domHistory.length >= 4) {
        const recent = domHistory.slice(-4);
        const positions = new Set(recent.map((p) => `${p.x},${p.y}`));

        if (positions.size === 2 && now - recent[0].timestamp < 300) {
          isLocked = true;
          lockUntil = now + 2000;
          return true;
        }
      }

      if (now > lockUntil) isLocked = false;
      return isLocked;
    };

    const setPositioning = (state: "true" | "false") => {
      el.setAttribute("data-positioning", state);
    };

    const getTargetElement = (): HTMLElement | null => {
      const target = anchor || document.getElementById(config.anchor);
      if (!target?.isConnected) return null;

      const parentPopover = el.parentElement?.closest(
        "[popover]:popover-open"
      ) as HTMLElement | null;
      const isVertical =
        config.placement.startsWith("top") || config.placement.startsWith("bottom");

      return parentPopover && isVertical ? parentPopover : target;
    };

    const updatePosition = async () => {
      const target = getTargetElement();
      if (!target) return;

      startBatch();
      try {
        const result = await computeFloatingPosition(target, el, config);

        if (shouldUpdatePosition(result, lastPos)) {
          if (!checkDOMOscillation(result.x, result.y)) {
            const strategy = el.hasAttribute("popover") ? "fixed" : config.strategy;
            Object.assign(el.style, {
              position: strategy,
              left: `${result.x}px`,
              top: `${result.y}px`,
            });
            lastPos = result;

            if (settlementTimer) clearTimeout(settlementTimer);
            settlementTimer = window.setTimeout(() => setPositioning("false"), 100);
          } else {
            setPositioning("false");
          }
        }

        const isValidPosition =
          result.x !== 0 && result.y !== 0 && result.x > -1000 && result.y > -1000;
        if (!hasPositioned && isValidPosition) {
          hasPositioned = true;

          if (config.hide || el.hasAttribute("popover")) {
            el.style.visibility = "visible";
            if (config.hide) {
              showTimer = window.setTimeout(() => {
                el.style.opacity = "1";
              }, 10);
            } else {
              el.style.opacity = "1";
            }
          }
        }
      } finally {
        endBatch();
      }
    };

    const isVisible = (): boolean => {
      const { display, visibility } = getComputedStyle(el);
      return (
        display !== "none" && visibility !== "hidden" && el.offsetWidth > 0 && el.offsetHeight > 0
      );
    };

    const start = () => {
      const target = getTargetElement();
      if (!target || cleanup) return;

      if (el.hasAttribute("popover")) {
        requestAnimationFrame(updatePosition);
      }

      cleanup = autoUpdate(target, el, updatePosition, {
        ancestorScroll: true,
        ancestorResize: true,
        elementResize: true,
        layoutShift: true,
      });
    };

    const stop = () => {
      cleanup?.();
      cleanup = null;
      hasPositioned = false;

      for (const timer of [showTimer, settlementTimer]) {
        if (timer) clearTimeout(timer);
      }
      showTimer = settlementTimer = null;

      domHistory = [];
      isLocked = false;
      lockUntil = 0;
      el.removeAttribute("data-positioning");

      if (config.hide || el.hasAttribute("popover")) {
        prepareHiddenState();
      }

      lastPos = { x: -999, y: -999, placement: "" };
    };

    if (el.hasAttribute("popover")) {
      const handleToggle = (e: any) => {
        if (e.newState === "open") {
          config.strategy = "fixed" as Strategy;
          Object.assign(el.style, { margin: "0", inset: "unset" });
          prepareHiddenState();

          const isNested = el.parentElement?.closest("[popover]:popover-open") !== null;
          const startFn = () => el.matches(":popover-open") && start();

          if (isNested) {
            setTimeout(startFn, 20);
          } else {
            requestAnimationFrame(startFn);
          }
        } else if (e.newState === "closed") {
          stop();
        }
      };

      const handleBeforeToggle = (e: any) => {
        if (e.newState === "open") {
          Object.assign(el.style, { margin: "0", inset: "unset" });
          prepareHiddenState();
        }
      };

      el.addEventListener("toggle", handleToggle);
      el.addEventListener("beforetoggle", handleBeforeToggle);

      return () => {
        el.removeEventListener("toggle", handleToggle);
        el.removeEventListener("beforetoggle", handleBeforeToggle);
        stop();
      };
    }

    const observer = new MutationObserver(() => {
      if (isVisible() && !cleanup) {
        setPositioning("true");
        start();
      } else if (!isVisible() && cleanup) {
        stop();
      }
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
