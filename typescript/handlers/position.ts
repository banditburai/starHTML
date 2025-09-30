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

// Timeouts / delays
const SHOW_DELAY_MS = 10;
const SETTLE_MS = 100;
const SECONDARY_UPDATE_MS = 150;

// Central defaults (tunable via setConfig)
type PositionDefaults = {
  padding?: number;            // Floating UI padding
  verticalGapPx?: number;      // Gap for top/bottom stacks
  horizontalOverlapPx?: number;// Overlap for left/right submenus
};

const DEFAULTS: Required<PositionDefaults> = {
  padding: 10,
  verticalGapPx: 3,
  horizontalOverlapPx: -4,
};

// Container-based reference selection to honor nesting semantics
function resolveReferenceEl(el: HTMLElement, anchor: HTMLElement | null, config: PositionConfig): HTMLElement | null {
  if (!anchor?.isConnected) return null;
  const parentPopover = el.parentElement?.closest("[popover]:popover-open") as HTMLElement | null;
  const side = (config.placement as string).split("-")[0];
  if (config.container === "parent" && parentPopover) return parentPopover;
  if (config.container === "auto" && parentPopover && (side === "top" || side === "bottom")) return parentPopover;
  return anchor;
}

// Default offset policy for nested popovers and submenus
function computeDefaultOffset(reference: HTMLElement, config: PositionConfig, defaults: Required<PositionDefaults>): number {
  let offsetValue = config.offset;
  const side = (config.placement as string).split("-")[0] as "top"|"bottom"|"left"|"right";

  try {
    const htmlRef = reference as HTMLElement;
    const parentPopover = (htmlRef?.parentElement?.closest("[popover]:popover-open") as HTMLElement | null);
    const nested = !!parentPopover;
    const needsEdgeDistance = nested && (
      config.container === "parent" ||
      (config.container === "auto" && (side === "left" || side === "right"))
    );

    if (needsEdgeDistance && parentPopover) {
      const parentRect = parentPopover.getBoundingClientRect();
      const refRect = htmlRef.getBoundingClientRect();
      const edgeDistances = {
        right: parentRect.right - refRect.right,
        left: refRect.left - parentRect.left,
        bottom: parentRect.bottom - refRect.bottom,
        top: refRect.top - parentRect.top,
      } as const;
      const distanceToEdge = edgeDistances[side];
      const adjust = (side === "top" || side === "bottom") ? defaults.verticalGapPx : defaults.horizontalOverlapPx;
      offsetValue = distanceToEdge + (config.hasCustomOffset ? config.offset : adjust);
    } else if (nested && config.container !== "none" && !config.hasCustomOffset) {
      // Parent-referenced with no explicit offset → apply defaults
      offsetValue = (side === "top" || side === "bottom") ? defaults.verticalGapPx : defaults.horizontalOverlapPx;
    }
  } catch {}

  return offsetValue;
}

interface AttributePlugin {
  type: "attribute";
  name: string;
  keyReq: "starts" | "exact";
  valReq?: "allowed" | "denied" | "must";
  shouldEvaluate?: boolean;
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

type PositionConfig = {
  placement: Placement;
  strategy: Strategy;
  offset: number;
  hasCustomOffset: boolean;
  offsetMain?: number | null;
  offsetCross?: number | null;
  flip: boolean;
  shift: boolean;
  hide: boolean;
  autoSize: boolean;
  container: string;
  isVirtual?: boolean;
};

// Helper: adjust Y for fixed strategy to eliminate drift while scrolling
function adjustFixedY(side: string, align: string | undefined, refRect: DOMRect, floatRect: DOMRect, offset: number): number {
  if (side === "left" || side === "right") {
    if (align === "start") return refRect.top;
    if (align === "end") return refRect.bottom - floatRect.height;
    return refRect.y + (refRect.height - floatRect.height) / 2;
  }
  if (side === "top") return refRect.top - floatRect.height - offset;
  if (side === "bottom") return refRect.bottom + offset;
  return refRect.y;
}

function buildVirtualRef(pageX: number, pageY: number, el: HTMLElement) {
  const viewportX = pageX - window.scrollX;
  const viewportY = pageY - window.scrollY;
  return {
    getBoundingClientRect: () => ({
      x: viewportX,
      y: viewportY,
      left: viewportX,
      top: viewportY,
      right: viewportX,
      bottom: viewportY,
      width: 0,
      height: 0,
    } as DOMRect),
    contextElement: el,
  } as any;
}

async function computeFloatingPosition(
  reference: HTMLElement,
  floating: HTMLElement,
  config: PositionConfig
): Promise<Position> {
  const cfgDefaults = getGlobalConfig().defaults || {};
  const padding = Number(cfgDefaults.padding ?? DEFAULTS.padding);
  const offsetValue = computeDefaultOffset(reference, config, {
    padding,
    verticalGapPx: Number(cfgDefaults.verticalGapPx ?? DEFAULTS.verticalGapPx),
    horizontalOverlapPx: Number(cfgDefaults.horizontalOverlapPx ?? DEFAULTS.horizontalOverlapPx),
  });


  const mainAxis = (config.offsetMain ?? null) ?? offsetValue;
  const crossAxis = (config.offsetCross ?? null) ?? undefined;
  const middleware: Middleware[] = [
    crossAxis === undefined ? offset(mainAxis) : offset({ mainAxis, crossAxis })
  ];
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

  // popovers use fixed; otherwise use requested strategy
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

  // For fixed strategy, adjust Y to track scrolling reference
  let finalY = y;
  if (strategy === "fixed" && !config.isVirtual) {
    const refRect = reference.getBoundingClientRect();
    const floatRect = floating.getBoundingClientRect();
    const [side, align] = (config.placement as string).split("-");
    finalY = adjustFixedY(side, align, refRect, floatRect, offsetValue);
  }

  const position = { x: Math.round(x), y: Math.round(finalY), placement };

  return position;
}

const shouldUpdatePosition = (current: Position, last: Position, threshold = 2): boolean =>
  Math.abs(current.x - last.x) > threshold ||
  Math.abs(current.y - last.y) > threshold ||
  current.placement !== last.placement;

const extract = (value: unknown): string => {
  if (typeof value === "string") return value;
  if (value instanceof Set) {
    const arr = Array.from(value);
    // If Set is empty, it's a boolean flag that's present (true)
    if (arr.length === 0) return "true";
    // Otherwise return the first value
    return String(arr[0]) || "";
  }
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

function getPositionArgNames(signal = "position"): string[] {
  return [
    `${signal}_x`,
    `${signal}_y`,
    `${signal}_placement`,
    `${signal}_visible`,
    `${signal}_is_positioning`,
  ];
}

function getGlobalConfig(): { signal: string; defaults?: PositionDefaults; autoUpdate?: { elementResize?: boolean; layoutShift?: boolean } } {
  const cfg = (window as any).__starhtml_position_config || {};
  return { signal: cfg.signal ?? "position", defaults: cfg.defaults, autoUpdate: cfg.autoUpdate } as { signal: string; defaults?: PositionDefaults; autoUpdate?: { elementResize?: boolean; layoutShift?: boolean } };
}

const positionAttributePlugin: AttributePlugin = {
  type: "attribute",
  name: "position",
  keyReq: "starts",
  valReq: "allowed",
  shouldEvaluate: false,

  onLoad({ el, value, mods, startBatch, endBatch, mergePatch, getPath, effect }: RuntimeContext): OnRemovalFn | void {
    injectPositioningCSS();

    const modSigRaw = extract(mods.get("signal_prefix"));
    const fallback = getGlobalConfig().signal;
    const sig = modSigRaw || fallback;
    

    const initPatch = {
      [`${sig}_x`]: 0,
      [`${sig}_y`]: 0,
      [`${sig}_placement`]: "bottom",
      [`${sig}_visible`]: false,
      [`${sig}_is_positioning`]: false,
    } as Record<string, any>;
    mergePatch(initPatch);

    let offsetValue = extract(mods.get("offset"));
    if (offsetValue?.startsWith("n")) {
      offsetValue = `-${offsetValue.substring(1)}`;
    }
    const hasCustomOffset = !!offsetValue;
    const offsetMain = extract(mods.get("offset_main"));
    const offsetCross = extract(mods.get("offset_cross"));

    const containerParam = extract(mods.get("container")) || "auto";
    if (!["auto", "none", "parent"].includes(containerParam)) {
      console.warn(`Invalid container parameter: ${containerParam}. Using 'auto'.`);
    }

    const anchorFromValue = value.split(' ')[0].trim();
    
  
    const config = {
      anchor: extract(mods.get("anchor")) || anchorFromValue,
      placement: extractPlacement(mods.get("placement")),
      strategy: (extract(mods.get("strategy")) || "absolute") as Strategy,
      offset: offsetValue ? Number(offsetValue) : 8,
      hasCustomOffset,
      offsetMain: offsetMain ? Number(offsetMain) : null,
      offsetCross: offsetCross ? Number(offsetCross) : null,
      // For boolean flags: if the modifier exists (even as empty Set), it's true unless explicitly "false"
      flip: mods.has("flip") ? extract(mods.get("flip")) !== "false" : true,
      shift: mods.has("shift") ? extract(mods.get("shift")) !== "false" : true,
      hide: mods.has("hide") ? extract(mods.get("hide")) !== "false" : false,
      autoSize: mods.has("auto_size") ? extract(mods.get("auto_size")) !== "false" : false,
      container: ["auto", "none", "parent"].includes(containerParam) ? containerParam : "auto",
    };
    // Optional cursor-based virtual reference support for context menus
    const cursorXPathRaw = extract(mods.get("cursor_x"));
    const cursorYPathRaw = extract(mods.get("cursor_y"));
    const cursorXPath = cursorXPathRaw?.replace(/^\$/, "");
    const cursorYPath = cursorYPathRaw?.replace(/^\$/, "");
    const isCursorMode = Boolean(cursorXPath && cursorYPath);
    const anchor = config.anchor ? document.getElementById(config.anchor) : null;
    
    if (!isCursorMode && !anchor && !el.hasAttribute("popover")) return;

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
      mergePatch({ [`${sig}_is_positioning`]: state === "true" });
    };

    const getTargetElement = (): HTMLElement | null => {
      if (isCursorMode) return null; // Using virtual reference
      const target = anchor || document.getElementById(config.anchor);
      if (!target?.isConnected) return null;
      return resolveReferenceEl(el, target, config);
    };

    const updatePosition = async () => {
      const useVirtual = isCursorMode;
      
      let reference: any = null;
        if (useVirtual) {
        let pageX = 0;
        let pageY = 0;
        try {
          pageX = Number(getPath(cursorXPath as string)) || 0;
          pageY = Number(getPath(cursorYPath as string)) || 0;
        } catch {}
        reference = buildVirtualRef(pageX, pageY, el);
      } else {
        const target = getTargetElement();
        if (!target) return;
        
        // Use element chosen by getTargetElement(), which already encodes container logic
        reference = target;
      }
      
      if (!reference) return;

      startBatch();
      try {

        // Default to fixed for popover/virtual and for data-show unless overridden
        const hasDataShow = el.hasAttribute("data-show");
        const effStrategy = (hasDataShow && !mods.has("strategy"))
          ? "fixed"
          : ((el.hasAttribute("popover") || useVirtual)
              ? (mods.has("strategy") ? config.strategy : "fixed")
              : config.strategy);
        const result = await computeFloatingPosition(reference, el, { ...config, strategy: effStrategy, isVirtual: useVirtual } as any);
        const patch: Record<string, any> = {};

        if (shouldUpdatePosition(result, lastPos)) {
          if (!checkDOMOscillation(result.x, result.y)) {
            const strategy = effStrategy;
            Object.assign(el.style, {
              position: strategy,
              left: "0px",
              top: "0px",
              transform: `translate3d(${result.x}px, ${result.y}px, 0)`,
              willChange: "transform",
            });
            lastPos = result;
            patch[`${sig}_x`] = result.x;
            patch[`${sig}_y`] = result.y;
            patch[`${sig}_placement`] = result.placement;

            if (settlementTimer) clearTimeout(settlementTimer);
            settlementTimer = window.setTimeout(() => setPositioning("false"), SETTLE_MS);
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
                }, SHOW_DELAY_MS);
            } else {
              el.style.opacity = "1";
            }
          }
          patch[`${sig}_visible`] = true;
        }
        if (Object.keys(patch).length) mergePatch(patch);
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
      const useVirtual = isCursorMode;
      
      // For virtual references, create a virtual anchor element
      if (useVirtual) {
        // Immediately position for cursor mode
        updatePosition();
        // Set up scroll listener for virtual references
        const handleScroll = () => { updatePosition(); };
        window.addEventListener('scroll', handleScroll, true);
        cleanup = () => {
          window.removeEventListener('scroll', handleScroll, true);
        };
        return;
      }
      
      const target = getTargetElement();
      if (!target || cleanup) return;

      if (el.hasAttribute("popover")) {
        requestAnimationFrame(updatePosition);
      }

      const cfg = getGlobalConfig();
      const au = (cfg.autoUpdate || {}) as { elementResize?: boolean; layoutShift?: boolean };
      const elementResize = au.elementResize ?? false;
      const layoutShift = au.layoutShift ?? false;

      cleanup = autoUpdate(target, el, updatePosition, {
        ancestorScroll: true,
        ancestorResize: true,
        elementResize,
        layoutShift,
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
      mergePatch({ [`${sig}_is_positioning`]: false, [`${sig}_visible`]: false });
    };

    // Allow external manual re-positioning triggers (e.g., after ds_show toggles)
    const handleManualUpdate = () => {
      if (!cleanup) {
        // If not started yet, start observing and then position
        start();
      }
      requestAnimationFrame(() => updatePosition());
    };
    el.addEventListener("position-update", handleManualUpdate as any);

    // Reactive watch for data-show toggles on non-popover elements (merged for cursor/non-cursor)
    const dataShowAttr = el.getAttribute("data-show") || "";
    const showSignalMatch = dataShowAttr.match(/\$([a-zA-Z_][\w]*)/);
    let cleanupEffect: (() => void) | null = null;
    let isPositioning = false;
    if (!el.hasAttribute("popover") && (showSignalMatch || isCursorMode)) {
      const showSignal = showSignalMatch ? showSignalMatch[1] : null;
      cleanupEffect = effect(() => {
        const hasSignal = !!showSignal;
        const isShown = hasSignal ? Boolean(getPath(showSignal as string)) : false;
        if (isShown && !isPositioning) {
          isPositioning = true;
          setPositioning("true");
          start();
          if (isCursorMode) {
            // Immediate updates for cursor mode
            updatePosition();
            setTimeout(() => { updatePosition(); }, 0);
          } else {
            // Allow DOM to settle, then position and follow-up after animations
            setTimeout(() => {
              updatePosition();
              setTimeout(() => updatePosition(), SECONDARY_UPDATE_MS);
            }, SHOW_DELAY_MS);
          }
        } else if (!isShown && isPositioning) {
          isPositioning = false;
          stop();
        }
      });
    }

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
        el.removeEventListener("position-update", handleManualUpdate as any);
        cleanupEffect?.();
        stop();
      };
    }

    if (isVisible()) start();

    return () => {
      el.removeEventListener("position-update", handleManualUpdate as any);
      cleanupEffect?.();
      stop();
    };
  },
};

const positionPlugin = {
  ...positionAttributePlugin,
  argNames: [] as string[],
  setConfig(config: any) {
    (window as any).__starhtml_position_config = config;
    const signal = config?.signal ? String(config.signal) : "position";
    (this as any).argNames = getPositionArgNames(signal);
  },
};

export default positionPlugin;
