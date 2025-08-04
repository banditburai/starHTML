/**
 * StarHTML Resize Handler - Datastar AttributePlugin Implementation
 * Handles data-on-resize attributes with throttling, debouncing, and signal integration
 */

import { createDebounce, createRAFThrottle, createTimerThrottle } from "./throttle.js";

interface AttributePlugin {
  type: "attribute";
  name: string;
  keyReq: "starts" | "exact";
  argNames?: string[];
  onLoad: (ctx: RuntimeContext) => OnRemovalFn | void;
}

interface RuntimeContext {
  el: HTMLElement;
  key: string;
  value: string;
  mods: Map<string, any>;
  rx: (...args: any[]) => any;
  effect: (fn: () => void) => () => void;
  mergePatch: (patch: Record<string, any>) => void;
  getPath: (path: string) => any;
  startBatch: () => void;
  endBatch: () => void;
}

type OnRemovalFn = () => void;

interface ResizeConfig {
  debug?: boolean;
}

const DEFAULT_THROTTLE = 150;

const BREAKPOINT_THRESHOLDS = {
  xs: 640,
  sm: 768,
  md: 1024,
  lg: 1280,
  xl: 1536,
} as const;

const RESIZE_ARG_NAMES = [
  "width",
  "height",
  "windowWidth",
  "windowHeight",
  "aspectRatio",
  "isMobile",
  "isTablet",
  "isDesktop",
  "currentBreakpoint",
] as const;

const hasResizeObserver = typeof ResizeObserver !== "undefined";

function parseTimingValue(value: any): number {
  let actualValue = value;
  if (value instanceof Set) {
    actualValue = Array.from(value)[0];
  }
  const parsed = Number.parseInt(String(actualValue).replace("ms", ""));
  return Number.isNaN(parsed) ? DEFAULT_THROTTLE : parsed;
}

function parseModifiers(mods: Map<string, any>): { throttle: number; isDebounce: boolean } {
  const debounceValue = mods.get("debounce");
  if (debounceValue !== undefined) {
    return { throttle: parseTimingValue(debounceValue), isDebounce: true };
  }

  const throttleValue = mods.get("throttle");
  if (throttleValue !== undefined) {
    return { throttle: parseTimingValue(throttleValue), isDebounce: false };
  }

  return { throttle: DEFAULT_THROTTLE, isDebounce: false };
}

function getBreakpoint(width: number): string {
  if (width < BREAKPOINT_THRESHOLDS.xs) return "xs";
  if (width < BREAKPOINT_THRESHOLDS.sm) return "sm";
  if (width < BREAKPOINT_THRESHOLDS.md) return "md";
  if (width < BREAKPOINT_THRESHOLDS.lg) return "lg";
  if (width < BREAKPOINT_THRESHOLDS.xl) return "xl";
  return "2xl";
}

function createResizeContext(el: HTMLElement, windowWidth: number, windowHeight: number) {
  const rect = el.getBoundingClientRect();
  const width = Math.round(rect.width);
  const height = Math.round(rect.height);

  return {
    width,
    height,
    windowWidth,
    windowHeight,
    aspectRatio: width > 0 ? Math.round((width / height) * 100) / 100 : 0,
    isMobile: windowWidth < BREAKPOINT_THRESHOLDS.sm,
    isTablet: windowWidth >= BREAKPOINT_THRESHOLDS.sm && windowWidth < BREAKPOINT_THRESHOLDS.md,
    isDesktop: windowWidth >= BREAKPOINT_THRESHOLDS.md,
    currentBreakpoint: getBreakpoint(windowWidth),
  };
}

const resizeAttributePlugin: AttributePlugin = {
  type: "attribute",
  name: "onResize",
  keyReq: "starts",
  argNames: [...RESIZE_ARG_NAMES],

  onLoad(ctx: RuntimeContext): OnRemovalFn | void {
    const { el, value, mods, rx, mergePatch, startBatch, endBatch } = ctx;

    if (!value) {
      return;
    }

    const { throttle, isDebounce } = parseModifiers(mods);

    const handleResize = () => {
      const context = createResizeContext(el, window.innerWidth, window.innerHeight);

      startBatch();
      try {
        mergePatch(context);
        rx(
          context.width,
          context.height,
          context.windowWidth,
          context.windowHeight,
          context.aspectRatio,
          context.isMobile,
          context.isTablet,
          context.isDesktop,
          context.currentBreakpoint
        );
      } catch (error) {
        console.error("Error during resize handler:", error);
      } finally {
        endBatch();
      }
    };

    const throttledHandler = isDebounce
      ? createDebounce(handleResize, throttle)
      : throttle > 16
        ? createTimerThrottle(handleResize, throttle)
        : createRAFThrottle(handleResize);

    let resizeObserver: ResizeObserver | null = null;

    if (hasResizeObserver) {
      resizeObserver = new ResizeObserver(() => throttledHandler());
      resizeObserver.observe(el);
    }

    const handleWindowResize = () => throttledHandler();
    window.addEventListener("resize", handleWindowResize, { passive: true });

    handleResize();

    return () => {
      resizeObserver?.disconnect();
      window.removeEventListener("resize", handleWindowResize);
    };
  },
};

let globalConfig: ResizeConfig = { debug: false };

const resizePlugin = {
  ...resizeAttributePlugin,

  setConfig(config: ResizeConfig) {
    globalConfig = { ...globalConfig, ...config };
  },
};

export default resizePlugin;
