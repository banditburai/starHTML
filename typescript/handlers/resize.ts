import { createDebounce, createRAFThrottle, createTimerThrottle } from "./throttle.js";

interface AttributePlugin {
  type: "attribute";
  name: string;
  keyReq: "starts" | "exact" | "allowed";
  valReq?: "allowed";
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

// Flattened resize variables like scroll handler
const RESIZE_ARG_NAMES = [
  "resize_width",
  "resize_height",
  "resize_window_width",
  "resize_window_height",
  "resize_aspect_ratio",
  "resize_current_breakpoint",
  "resize_is_mobile",
  "resize_is_tablet",
  "resize_is_desktop",
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
    width: width,
    height: height,
    window_width: windowWidth,
    window_height: windowHeight,
    aspect_ratio: width > 0 && height > 0 ? Math.round((width / height) * 100) / 100 : 0,
    is_mobile: windowWidth < BREAKPOINT_THRESHOLDS.sm,
    is_tablet: windowWidth >= BREAKPOINT_THRESHOLDS.sm && windowWidth < BREAKPOINT_THRESHOLDS.md,
    is_desktop: windowWidth >= BREAKPOINT_THRESHOLDS.md,
    current_breakpoint: getBreakpoint(windowWidth),    
  };
}

const resizeAttributePlugin: AttributePlugin = {
  type: "attribute",
  name: "resize",
  keyReq: "allowed",
  valReq: "allowed",
  argNames: [...RESIZE_ARG_NAMES],

  onLoad(ctx: RuntimeContext): OnRemovalFn | void {
    const { el, value, mods, rx, mergePatch, startBatch, endBatch } = ctx;
        
    const initialContext = createResizeContext(el, window.innerWidth, window.innerHeight);
    const initPatch = {
      resize_width: initialContext.width,
      resize_height: initialContext.height,
      resize_window_width: initialContext.window_width,
      resize_window_height: initialContext.window_height,
      resize_aspect_ratio: initialContext.aspect_ratio,
      resize_current_breakpoint: initialContext.current_breakpoint,
      resize_is_mobile: initialContext.is_mobile,
      resize_is_tablet: initialContext.is_tablet,
      resize_is_desktop: initialContext.is_desktop,
    };
    mergePatch(initPatch);

    const { throttle, isDebounce } = parseModifiers(mods);

    const handleResize = () => {
      const context = createResizeContext(el, window.innerWidth, window.innerHeight);

      startBatch();
      try {        
        const patch = {
          resize_width: context.width,
          resize_height: context.height,
          resize_window_width: context.window_width,
          resize_window_height: context.window_height,
          resize_aspect_ratio: context.aspect_ratio,
          resize_current_breakpoint: context.current_breakpoint,
          resize_is_mobile: context.is_mobile,
          resize_is_tablet: context.is_tablet,
          resize_is_desktop: context.is_desktop,
        };
        mergePatch(patch);
                
        if (value) rx(value);
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
