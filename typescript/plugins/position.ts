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
} from "https://cdn.jsdelivr.net/npm/@floating-ui/dom@1/+esm";
import { effect, getPath } from "datastar";

import type { AttributeContext, AttributePlugin, OnRemovalFn } from "./types.js";

const SHOW_DELAY_MS = 10;
const SETTLE_MS = 100;
const SECONDARY_UPDATE_MS = 150;

type PositionDefaults = {
  padding?: number;
  verticalGapPx?: number;
  horizontalOverlapPx?: number;
};

const DEFAULTS: Required<PositionDefaults> = {
  padding: 10,
  verticalGapPx: 3,
  horizontalOverlapPx: -4,
};

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
};

interface VirtualReference {
  getBoundingClientRect(): DOMRect;
  contextElement: HTMLElement;
}

type Position = { x: number; y: number; placement: string };

const VALID_PLACEMENTS = new Set<Placement>([
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
]);

const VALID_CONTAINERS = new Set(["auto", "none", "parent"]);

const ORIGIN_MAP: Record<string, string> = {
  bottom: "top",
  top: "bottom",
  left: "right",
  right: "left",
};
const placementOrigin = (p: string) => ORIGIN_MAP[p.split("-")[0]] ?? "center";

function resolveReferenceEl(
  el: HTMLElement,
  anchor: HTMLElement | null,
  config: PositionConfig
): HTMLElement | null {
  if (!anchor?.isConnected) return null;
  const parentPopover = el.parentElement?.closest("[popover]:popover-open") as HTMLElement | null;
  const side = config.placement.split("-")[0];
  if (config.container === "parent" && parentPopover) return parentPopover;
  if (config.container === "auto" && parentPopover && (side === "top" || side === "bottom"))
    return parentPopover;
  return anchor;
}

function computeDefaultOffset(
  reference: HTMLElement,
  config: PositionConfig,
  defaults: Required<PositionDefaults>
): number {
  let offsetValue = config.offset;
  const side = config.placement.split("-")[0] as "top" | "bottom" | "left" | "right";

  const parentPopover = reference.parentElement?.closest(
    "[popover]:popover-open"
  ) as HTMLElement | null;
  const needsEdgeDistance =
    parentPopover &&
    (config.container === "parent" ||
      (config.container === "auto" && (side === "left" || side === "right")));

  if (needsEdgeDistance) {
    const parentRect = parentPopover.getBoundingClientRect();
    const refRect = reference.getBoundingClientRect();
    const distanceToEdge = (
      {
        right: parentRect.right - refRect.right,
        left: refRect.left - parentRect.left,
        bottom: parentRect.bottom - refRect.bottom,
        top: refRect.top - parentRect.top,
      } as const
    )[side];
    const adjust =
      side === "top" || side === "bottom" ? defaults.verticalGapPx : defaults.horizontalOverlapPx;
    offsetValue = distanceToEdge + (config.hasCustomOffset ? config.offset : adjust);
  } else if (parentPopover && config.container !== "none" && !config.hasCustomOffset) {
    offsetValue =
      side === "top" || side === "bottom" ? defaults.verticalGapPx : defaults.horizontalOverlapPx;
  }

  return offsetValue;
}

function buildVirtualRef(pageX: number, pageY: number, el: HTMLElement): VirtualReference {
  const x = pageX - window.scrollX;
  const y = pageY - window.scrollY;
  return {
    getBoundingClientRect: () =>
      ({ x, y, left: x, top: y, right: x, bottom: y, width: 0, height: 0 }) as DOMRect,
    contextElement: el,
  };
}

async function computeFloatingPosition(
  reference: HTMLElement | VirtualReference,
  floating: HTMLElement,
  config: PositionConfig,
  resolvedDefaults: Required<PositionDefaults> = DEFAULTS
): Promise<Position> {
  const { padding } = resolvedDefaults;
  const offsetValue =
    reference instanceof HTMLElement
      ? computeDefaultOffset(reference, config, resolvedDefaults)
      : config.offset;

  const mainAxis = config.offsetMain ?? offsetValue;
  const middleware: Middleware[] = [
    config.offsetCross != null
      ? offset({ mainAxis, crossAxis: config.offsetCross })
      : offset(mainAxis),
  ];
  if (config.flip) middleware.push(flip({ padding }));
  if (config.shift) middleware.push(shift({ padding }));
  if (config.hide) middleware.push(hide());
  if (config.autoSize) {
    middleware.push(
      size({
        padding: 10,
        apply: ({ availableWidth, availableHeight, elements }) =>
          Object.assign(elements.floating.style, {
            maxWidth: `${availableWidth}px`,
            maxHeight: `${availableHeight}px`,
          }),
      })
    );
  }

  const strategy: Strategy = floating.hasAttribute("popover") ? "fixed" : config.strategy;
  const { x, y, placement } = await computePosition(
    reference as Parameters<typeof computePosition>[0],
    floating,
    { placement: config.placement, strategy, middleware }
  );

  if (x === 0 && y === 0) {
    const { width, height } = reference.getBoundingClientRect();
    if (width === 0 || height === 0) return { x: -9999, y: -9999, placement };
  }

  return { x: Math.round(x), y: Math.round(y), placement };
}

const shouldUpdatePosition = (current: Position, last: Position, threshold = 2): boolean =>
  Math.abs(current.x - last.x) > threshold ||
  Math.abs(current.y - last.y) > threshold ||
  current.placement !== last.placement;

const extract = (value: unknown): string => {
  if (typeof value === "string") return value;
  if (value instanceof Set) {
    return value.size === 0 ? "true" : String([...value][0]) || "";
  }
  return "";
};

const extractPlacement = (value: unknown): Placement => {
  const str = (extract(value) || "bottom").replace(
    /^(top|bottom|left|right)(start|end)$/i,
    "$1-$2"
  );
  return VALID_PLACEMENTS.has(str as Placement) ? (str as Placement) : "bottom";
};

const boolMod = (mods: Map<string, unknown>, name: string, defaultVal: boolean): boolean =>
  mods.has(name) ? extract(mods.get(name)) !== "false" : defaultVal;

function getPositionArgNames(signal = "position") {
  return [
    `${signal}_x`,
    `${signal}_y`,
    `${signal}_placement`,
    `${signal}_visible`,
    `${signal}_is_positioning`,
  ];
}

function getGlobalConfig(): {
  defaults?: PositionDefaults;
  autoUpdate?: { elementResize?: boolean; layoutShift?: boolean };
} {
  const cfg = (window as any).__starhtml_position_config || {};
  return { defaults: cfg.defaults, autoUpdate: cfg.autoUpdate };
}

const positionAttributePlugin: AttributePlugin = {
  name: "position",
  requirement: { key: "must", value: "allowed" },

  apply({ el, value, mods }: AttributeContext): OnRemovalFn | void {
    let offsetValue = extract(mods.get("offset"));
    if (offsetValue?.startsWith("n")) offsetValue = `-${offsetValue.substring(1)}`;
    const hasCustomOffset = !!offsetValue;
    const offsetMain = extract(mods.get("offset_main"));
    const offsetCross = extract(mods.get("offset_cross"));

    const rawContainer = extract(mods.get("container")) || "auto";
    if (!VALID_CONTAINERS.has(rawContainer)) {
      console.warn(`Invalid container parameter: ${rawContainer}. Using 'auto'.`);
    }
    const container = VALID_CONTAINERS.has(rawContainer) ? rawContainer : "auto";

    const config = {
      anchor: extract(mods.get("anchor")) || (value?.split(" ")[0].trim() ?? ""),
      placement: extractPlacement(mods.get("placement")),
      strategy: (extract(mods.get("strategy")) || "absolute") as Strategy,
      offset: offsetValue ? Number(offsetValue) : 8,
      hasCustomOffset,
      offsetMain: offsetMain ? Number(offsetMain) : null,
      offsetCross: offsetCross ? Number(offsetCross) : null,
      flip: boolMod(mods, "flip", true),
      shift: boolMod(mods, "shift", true),
      hide: boolMod(mods, "hide", false),
      autoSize: boolMod(mods, "auto_size", false),
      container,
    };

    const cursorXPath = extract(mods.get("cursor_x"))?.replace(/^\$/, "");
    const cursorYPath = extract(mods.get("cursor_y"))?.replace(/^\$/, "");
    const isCursorMode = Boolean(cursorXPath && cursorYPath);
    const anchor = config.anchor ? document.getElementById(config.anchor) : null;

    if (!isCursorMode && !anchor && !el.hasAttribute("popover")) return;

    let cleanup: (() => void) | null = null;
    let lastPos: Position = { x: -999, y: -999, placement: "" };
    let hasPositioned = false;
    let showTimer: number | null = null;
    let settlementTimer: number | null = null;
    let domHistory: Array<{ x: number; y: number; timestamp: number }> = [];
    let lockUntil = 0;

    const isPopover = el.hasAttribute("popover");
    const hasAnimateCSS = el.hasAttribute("data-popover-animate");
    const hasDataShow = el.hasAttribute("data-show");
    const d = getGlobalConfig().defaults;
    const resolvedDefaults: Required<PositionDefaults> = {
      padding: Number(d?.padding ?? DEFAULTS.padding),
      verticalGapPx: Number(d?.verticalGapPx ?? DEFAULTS.verticalGapPx),
      horizontalOverlapPx: Number(d?.horizontalOverlapPx ?? DEFAULTS.horizontalOverlapPx),
    };
    const exitDurationMs = hasAnimateCSS
      ? Number.parseFloat(getComputedStyle(el).getPropertyValue("--_dur-out")) || 100
      : 0;
    let closeGuard = 0;
    const effStrategy: Strategy =
      (hasDataShow || isPopover || isCursorMode) && !mods.has("strategy")
        ? "fixed"
        : config.strategy;

    const prepareHiddenState = () => {
      if (isPopover) {
        el.style.visibility = "hidden";
        return;
      }
      if (config.hide) {
        Object.assign(el.style, {
          visibility: "hidden",
          opacity: "0",
          transition: "opacity 150ms ease-out",
        });
      }
    };

    prepareHiddenState();

    const setPopoverOrigin = (placement: string) =>
      el.style.setProperty("--popover-origin", placementOrigin(placement));

    const checkDOMOscillation = (x: number, y: number): boolean => {
      const now = Date.now();
      domHistory.push({ x, y, timestamp: now });
      domHistory = domHistory.filter((h) => now - h.timestamp < 1000);

      if (domHistory.length >= 4) {
        const recent = domHistory.slice(-4);
        const positions = new Set(recent.map((p) => `${p.x},${p.y}`));
        if (positions.size === 2 && now - recent[0].timestamp < 300) {
          lockUntil = now + 2000;
          return true;
        }
      }

      return now < lockUntil;
    };

    const setPositioning = (state: "true" | "false") => {
      el.setAttribute("data-positioning", state);
    };

    const getTargetElement = (): HTMLElement | null => {
      if (isCursorMode) return null;
      const target = anchor || document.getElementById(config.anchor);
      if (!target?.isConnected) return null;
      return resolveReferenceEl(el, target, config);
    };

    const updatePosition = async () => {
      let reference: HTMLElement | VirtualReference | null = null;
      if (isCursorMode) {
        let pageX = 0;
        let pageY = 0;
        try {
          pageX = Number(getPath(cursorXPath as string)) || 0;
          pageY = Number(getPath(cursorYPath as string)) || 0;
        } catch {}
        reference = buildVirtualRef(pageX, pageY, el);
      } else {
        reference = getTargetElement();
        if (!reference) return;
      }

      try {
        const result = await computeFloatingPosition(
          reference,
          el,
          { ...config, strategy: effStrategy },
          resolvedDefaults
        );

        if (shouldUpdatePosition(result, lastPos)) {
          if (!checkDOMOscillation(result.x, result.y)) {
            if (!hasPositioned) {
              Object.assign(el.style, {
                position: effStrategy,
                left: "0px",
                top: "0px",
                willChange: hasAnimateCSS ? "translate" : "transform",
              });
            }

            if (hasAnimateCSS) {
              el.style.translate = `${result.x}px ${result.y}px`;
              if (lastPos.placement !== result.placement || !hasPositioned) {
                setPopoverOrigin(result.placement);
              }
            } else {
              el.style.transform = `translate3d(${result.x}px, ${result.y}px, 0)`;
            }

            lastPos = result;

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
          if (isPopover) {
            el.style.removeProperty("visibility");
          } else if (config.hide) {
            el.style.visibility = "visible";
            showTimer = window.setTimeout(() => {
              el.style.opacity = "1";
            }, SHOW_DELAY_MS);
          }
        }
      } catch {
        /* computeFloatingPosition errors are non-fatal */
      }
    };

    const start = () => {
      if (isCursorMode) {
        updatePosition();
        window.addEventListener("scroll", updatePosition, true);
        cleanup = () => window.removeEventListener("scroll", updatePosition, true);
        return;
      }

      const target = getTargetElement();
      if (!target || cleanup) return;

      if (isPopover) requestAnimationFrame(updatePosition);

      const au = getGlobalConfig().autoUpdate || {};
      cleanup = autoUpdate(target, el, updatePosition, {
        ancestorScroll: true,
        ancestorResize: true,
        elementResize: au.elementResize ?? isPopover,
        layoutShift: au.layoutShift ?? false,
      });
    };

    const stop = () => {
      cleanup?.();
      cleanup = null;
      hasPositioned = false;

      if (showTimer) clearTimeout(showTimer);
      if (settlementTimer) clearTimeout(settlementTimer);
      showTimer = settlementTimer = null;

      domHistory = [];
      lockUntil = 0;
      el.removeAttribute("data-positioning");

      if (isPopover) {
        const props = hasAnimateCSS
          ? ["translate", "will-change", "--popover-origin"]
          : ["visibility", "opacity", "will-change"];
        for (const p of props) el.style.removeProperty(p);
      } else if (config.hide) {
        prepareHiddenState();
      }

      lastPos = { x: -999, y: -999, placement: "" };
    };

    const handleManualUpdate: EventListener = () => {
      if (!cleanup) start();
      requestAnimationFrame(updatePosition);
    };
    el.addEventListener("position-update", handleManualUpdate);

    const dataShowAttr = el.getAttribute("data-show") || "";
    const showSignalMatch = dataShowAttr.match(/\$([a-zA-Z_][\w]*)/);
    let cleanupEffect: (() => void) | null = null;
    let isPositioning = false;
    if (!isPopover && (showSignalMatch || isCursorMode)) {
      const showSignal = showSignalMatch ? showSignalMatch[1] : null;
      cleanupEffect = effect(() => {
        const isShown = showSignal ? Boolean(getPath(showSignal)) : false;
        if (isShown && !isPositioning) {
          isPositioning = true;
          setPositioning("true");
          start();
          if (isCursorMode) {
            updatePosition();
            setTimeout(updatePosition, 0);
          } else {
            setTimeout(() => {
              updatePosition();
              setTimeout(updatePosition, SECONDARY_UPDATE_MS);
            }, SHOW_DELAY_MS);
          }
        } else if (!isShown && isPositioning) {
          isPositioning = false;
          stop();
        }
      });
    }

    const dispose = () => {
      el.removeEventListener("position-update", handleManualUpdate);
      cleanupEffect?.();
      stop();
    };

    if (isPopover) {
      const handleToggle = (e: Event) => {
        const { newState } = e as ToggleEvent;
        if (newState === "open") {
          // Remove visibility:hidden synchronously — toggle fires before first paint,
          // so @starting-style { opacity: 0 } provides anti-flash from here on.
          if (hasAnimateCSS) el.style.removeProperty("visibility");
          const isNested = el.parentElement?.closest("[popover]:popover-open") !== null;
          const startFn = () => el.matches(":popover-open") && start();
          if (isNested) setTimeout(startFn, 20);
          else requestAnimationFrame(startFn);
        } else if (newState === "closed") {
          if (hasAnimateCSS) {
            cleanup?.();
            cleanup = null;
            const id = ++closeGuard;
            setTimeout(() => {
              if (closeGuard === id && !el.matches(":popover-open")) stop();
            }, exitDurationMs + 10);
          } else {
            stop();
          }
        }
      };

      const handleBeforeToggle = (e: Event) => {
        if ((e as ToggleEvent).newState === "open") {
          Object.assign(el.style, { margin: "0", inset: "unset" });
          if (hasAnimateCSS) setPopoverOrigin(config.placement);
          prepareHiddenState();
        }
      };

      el.addEventListener("toggle", handleToggle);
      el.addEventListener("beforetoggle", handleBeforeToggle);

      return () => {
        el.removeEventListener("toggle", handleToggle);
        el.removeEventListener("beforetoggle", handleBeforeToggle);
        dispose();
      };
    }

    const { display, visibility } = getComputedStyle(el);
    if (
      display !== "none" &&
      visibility !== "hidden" &&
      el.offsetWidth > 0 &&
      el.offsetHeight > 0
    ) {
      start();
    }

    return dispose;
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
