import { SmoothScroll } from "./smooth-scroll.js";
import { createRAFThrottle, createTimerThrottle } from "./throttle.js";

interface AttributePlugin {
  type: "attribute";
  name: string;
  keyReq: "allowed" | "denied" | "starts" | "exact";
  valReq?: "allowed" | "denied" | "must";
  argNames?: string[];
  onLoad: (ctx: RuntimeContext) => OnRemovalFn | void;
}

interface RuntimeContext {
  el: HTMLElement;
  key: string;
  value: string;
  mods: Map<string, any>;
  rx: (...args: any[]) => any;
  mergePatch: (patch: Record<string, any>) => void;
  startBatch: () => void;
  endBatch: () => void;
  getPath: (path: string) => any;
}

type OnRemovalFn = () => void;

const DEFAULT_THROTTLE = 100;
const VELOCITY_DECAY_MS = 50; // Faster decay for more responsive feel

const SCROLL_ARG_NAMES = [
  "scroll_x",
  "scroll_y",
  "scroll_y_smoothed",
  "scroll_direction",
  "scroll_velocity",
  "scroll_velocity_smoothed",
  "scroll_delta",
  "scroll_page_progress",
  "scroll_is_top",
  "scroll_is_bottom",
  "scroll_visible",
  "scroll_visible_percent",
  "scroll_progress",
  "scroll_element_top",
  "scroll_element_bottom"
] as const;

let globalScrollInitialized = false;
let globalScrollManager: (() => void) | null = null;

function calculateVisiblePercent(rect: DOMRect, viewportHeight: number): number {
  if (rect.bottom < 0 || rect.top > viewportHeight) return 0;
  if (rect.height <= 0) return 0;
  const visibleTop = Math.max(0, rect.top);
  const visibleBottom = Math.min(viewportHeight, rect.bottom);
  const visibleHeight = visibleBottom - visibleTop;
  return Math.round((visibleHeight / rect.height) * 100);
}

function getThrottleMs(mods: Map<string, any>): number {
  const throttleValue = mods.get("throttle");
  if (throttleValue === undefined) return DEFAULT_THROTTLE;
  const value = throttleValue instanceof Set ? Array.from(throttleValue)[0] : throttleValue;
  return Number.parseInt(String(value)) || DEFAULT_THROTTLE;
}

const scrollAttributePlugin: AttributePlugin = {
  type: "attribute",
  name: "scroll",
  keyReq: "allowed",
  valReq: "allowed",
  argNames: [...SCROLL_ARG_NAMES],

  onLoad(ctx: RuntimeContext): OnRemovalFn | void {
    const { el, value, mods, rx, mergePatch, startBatch, endBatch, getPath } = ctx;
    
    const shouldManageGlobal = !globalScrollInitialized;
    if (shouldManageGlobal) {
      globalScrollInitialized = true;
      const initPatch = {
        scroll_x: window.scrollX || 0,
        scroll_y: window.scrollY || 0,
        scroll_direction: "none",
        scroll_velocity: 0,
        scroll_delta: 0,
        scroll_page_progress: 0,
        scroll_is_top: true,
        scroll_is_bottom: false,
      };
      mergePatch(initPatch);
      
      let lastScrollY = window.scrollY;
      let lastScrollTime = Date.now();
      let velocity = 0;
      let direction = "none";
      let decayTimer: number | null = null;
      
      const updateGlobalScroll = () => {
        const now = Date.now();
        const currentY = window.scrollY;
        const currentX = window.scrollX;
        const delta = currentY - lastScrollY;
        const timeDelta = now - lastScrollTime;
        
        if (timeDelta > 0 && delta !== 0) {
          velocity = Math.abs(delta / timeDelta * 1000);
          direction = delta > 0 ? "down" : delta < 0 ? "up" : direction;
          
          if (decayTimer) clearTimeout(decayTimer);
          decayTimer = setTimeout(() => {
            velocity = 0;
            direction = "none";
            mergePatch({
              scroll_velocity: 0,
              scroll_direction: "none",
            });
          }, VELOCITY_DECAY_MS) as unknown as number;
        }
        
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const pageProgress = docHeight > 0 ? Math.round((currentY / docHeight) * 100) : 0;
        
        const patch = {
          scroll_x: currentX,
          scroll_y: currentY,
          scroll_direction: direction,
          scroll_velocity: Math.round(velocity),
          scroll_delta: delta,
          scroll_page_progress: pageProgress,
          scroll_is_top: currentY <= 0,
          scroll_is_bottom: currentY >= docHeight,
        };
        mergePatch(patch);
        
        lastScrollY = currentY;
        lastScrollTime = now;
      };
      
      const throttledGlobalUpdate = createRAFThrottle(updateGlobalScroll);
      updateGlobalScroll();
      
      const handleGlobalScroll = () => throttledGlobalUpdate();
      window.addEventListener("scroll", handleGlobalScroll, { passive: true });
      
      globalScrollManager = () => {
        window.removeEventListener("scroll", handleGlobalScroll);
      };
    }
    
    const hasExpression = value?.trim();
    
    const throttleMs = getThrottleMs(mods);
    let smoothScroll: SmoothScroll | null = null;

    if (mods.has("smooth")) {
      smoothScroll = new SmoothScroll(el, () => {
        executeElementExpression();
      });
      smoothScroll.start();
    }

    const executeElementExpression = () => {
      const scrollPageProgress = getPath("scroll_page_progress") || 0;
      
      const rect = el.getBoundingClientRect();
      const elementTop = rect.top + window.scrollY;
      const elementBottom = elementTop + rect.height;
      const viewportHeight = window.innerHeight;
      const visiblePercent = calculateVisiblePercent(rect, viewportHeight);
      const isInViewport = rect.top < viewportHeight && rect.bottom > 0;
      
      let elProgress = scrollPageProgress;
      if (el.scrollHeight > el.clientHeight + 1) {
        elProgress = Math.round((el.scrollTop / (el.scrollHeight - el.clientHeight)) * 100);
      }
      
      let patchedVisiblePercent = visiblePercent;
      let patchedProgress = elProgress;

      if (smoothScroll) {
        const globalY = Number(getPath("scroll_y")) || 0;
        const globalVelocity = Number(getPath("scroll_velocity")) || 0;
        const globalPage = Number(scrollPageProgress) || 0;
        const smoothed = smoothScroll.getSmoothData({
          scrollY: globalY,
          velocity: globalVelocity,
          progress: Number(elProgress) || 0,
          pageProgress: globalPage,
          visiblePercent: Number(visiblePercent) || 0,
        });
        patchedVisiblePercent = Math.round(smoothed.visiblePercent);
        patchedProgress = Math.round(smoothed.progress);
        // Expose smoothed global signals as optional convenience
        const smoothedY = Math.round(smoothed.scrollY);
        const smoothedVel = Math.round(smoothed.velocity);
        mergePatch({
          scroll_y_smoothed: smoothedY,
          scroll_velocity_smoothed: smoothedVel,
        });
      }
      
      const elementPatch = {
        scroll_visible: isInViewport,
        scroll_visible_percent: patchedVisiblePercent,
        scroll_progress: patchedProgress,
        scroll_element_top: elementTop,
        scroll_element_bottom: elementBottom,
      };
      mergePatch(elementPatch);
      
      if (hasExpression) {
        startBatch();
        try {          
          rx(value);
        } catch (error) {
          console.error("Error executing scroll expression:", error);
        } finally {
          endBatch();
        }
      }
    };

    const throttledElementUpdate =
      throttleMs <= 16
        ? createRAFThrottle(executeElementExpression)
        : createTimerThrottle(executeElementExpression, throttleMs);

    executeElementExpression();
    
    const handleElementScroll = () => throttledElementUpdate();
    window.addEventListener("scroll", handleElementScroll, { passive: true });

    let elementScrollCleanup: (() => void) | null = null;
    if (el.scrollHeight > el.clientHeight) {
      const handleInternalScroll = () => throttledElementUpdate();
      el.addEventListener("scroll", handleInternalScroll, { passive: true });
      elementScrollCleanup = () => el.removeEventListener("scroll", handleInternalScroll);
    }

    return () => {
      window.removeEventListener("scroll", handleElementScroll);
      elementScrollCleanup?.();
      smoothScroll?.cleanup();
      
      if (shouldManageGlobal && globalScrollManager) {
        globalScrollManager();
        globalScrollManager = null;
        globalScrollInitialized = false;
      }
    };
  },
};

export default scrollAttributePlugin;