import { mergePatch } from "datastar";
import { createDebounce, createRAFThrottle, createTimerThrottle } from "./throttle.js";
import type { AttributeContext, AttributePlugin, OnRemovalFn } from "./types.js";

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
  "resize_width",
  "resize_height",
  "resize_window_width",
  "resize_window_height",
  "resize_current_breakpoint",
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
  return {
    width: Math.round(rect.width),
    height: Math.round(rect.height),
    window_width: windowWidth,
    window_height: windowHeight,
    current_breakpoint: getBreakpoint(windowWidth),
  };
}

const resizeAttributePlugin: AttributePlugin = {
  name: "resize",
  requirement: {
    key: "allowed",
    value: "allowed",
  },
  argNames: [...RESIZE_ARG_NAMES],

  apply(ctx: AttributeContext): OnRemovalFn | void {
    const { el, value, mods, rx } = ctx;

    const ctx0 = createResizeContext(el, window.innerWidth, window.innerHeight);
    mergePatch({
      resize_width: ctx0.width,
      resize_height: ctx0.height,
      resize_window_width: ctx0.window_width,
      resize_window_height: ctx0.window_height,
      resize_current_breakpoint: ctx0.current_breakpoint,
    });

    const { throttle, isDebounce } = parseModifiers(mods);

    const handleResize = () => {
      const resizeCtx = createResizeContext(el, window.innerWidth, window.innerHeight);

      try {
        mergePatch({
          resize_width: resizeCtx.width,
          resize_height: resizeCtx.height,
          resize_window_width: resizeCtx.window_width,
          resize_window_height: resizeCtx.window_height,
          resize_current_breakpoint: resizeCtx.current_breakpoint,
        });

        if (value) rx?.(value);
      } catch (error) {
        console.error("Error during resize handler:", error);
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
