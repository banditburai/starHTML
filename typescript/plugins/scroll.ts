import { getPath, mergePatch } from "datastar";
import { SmoothScroll } from "./smooth-scroll.js";
import { createRAFThrottle, createTimerThrottle } from "./throttle.js";
import type { AttributeContext, AttributePlugin, OnRemovalFn } from "./types.js";

const DEFAULT_THROTTLE = 100;
const VELOCITY_DECAY_MS = 50;
const DIRECTION_THRESHOLD = 3; // Minimum delta to change direction (filters momentum bounce)

const SCROLL_ARG_NAMES = [
  "scroll_x",
  "scroll_y",
  "scroll_direction",
  "scroll_page_progress",
  "scroll_is_top",
  "scroll_is_bottom",
  "scroll_visible_percent",
  "scroll_progress",
] as const;

let globalRefCount = 0;
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
  name: "scroll",
  requirement: {
    key: "allowed",
    value: "allowed",
  },
  argNames: [...SCROLL_ARG_NAMES],

  apply(ctx: AttributeContext): OnRemovalFn | void {
    const { el, value, mods, rx } = ctx;

    globalRefCount++;
    if (globalRefCount === 1) {
      mergePatch({
        scroll_x: window.scrollX || 0,
        scroll_y: window.scrollY || 0,
        scroll_direction: "none",
        scroll_page_progress: 0,
        scroll_is_top: true,
        scroll_is_bottom: false,
      });

      let lastScrollY = window.scrollY;
      let direction = "none";
      let decayTimer: number | null = null;

      const updateGlobalScroll = () => {
        const currentY = window.scrollY;
        const currentX = window.scrollX;
        const delta = currentY - lastScrollY;

        // Only change direction for significant movement (filters momentum bounce)
        if (Math.abs(delta) >= DIRECTION_THRESHOLD) {
          direction = delta > 0 ? "down" : "up";
        }

        // Reset decay timer on any scroll activity
        if (delta !== 0) {
          if (decayTimer) clearTimeout(decayTimer);
          decayTimer = setTimeout(() => {
            direction = "none";
            mergePatch({ scroll_direction: "none" });
          }, VELOCITY_DECAY_MS) as unknown as number;
        }

        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const pageProgress = docHeight > 0 ? Math.round((currentY / docHeight) * 100) : 0;

        mergePatch({
          scroll_x: currentX,
          scroll_y: currentY,
          scroll_direction: direction,
          scroll_page_progress: pageProgress,
          scroll_is_top: currentY <= 0,
          scroll_is_bottom: currentY >= docHeight,
        });

        lastScrollY = currentY;
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
      const viewportHeight = window.innerHeight;
      const visiblePercent = calculateVisiblePercent(rect, viewportHeight);

      let elProgress = scrollPageProgress;
      if (el.scrollHeight > el.clientHeight + 1) {
        elProgress = Math.round((el.scrollTop / (el.scrollHeight - el.clientHeight)) * 100);
      }

      let patchedVisiblePercent = visiblePercent;
      let patchedProgress = elProgress;

      if (smoothScroll) {
        const globalY = Number(getPath("scroll_y")) || 0;
        const globalPage = Number(scrollPageProgress) || 0;
        const smoothed = smoothScroll.getSmoothData({
          scrollY: globalY,
          velocity: 0,
          progress: Number(elProgress) || 0,
          pageProgress: globalPage,
          visiblePercent: Number(visiblePercent) || 0,
        });
        patchedVisiblePercent = Math.round(smoothed.visiblePercent);
        patchedProgress = Math.round(smoothed.progress);
      }

      mergePatch({
        scroll_visible_percent: patchedVisiblePercent,
        scroll_progress: patchedProgress,
      });

      if (hasExpression) {
        try {
          rx?.(value);
        } catch (error) {
          console.error("Error executing scroll expression:", error);
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

    // Attach unconditionally: a mount-time scrollable check misses elements
    // that become scrollable later (streaming chat, infinite lists).
    const handleInternalScroll = () => throttledElementUpdate();
    el.addEventListener("scroll", handleInternalScroll, { passive: true });
    const elementScrollCleanup = () => el.removeEventListener("scroll", handleInternalScroll);

    return () => {
      window.removeEventListener("scroll", handleElementScroll);
      elementScrollCleanup();
      smoothScroll?.cleanup();

      globalRefCount--;
      if (globalRefCount === 0 && globalScrollManager) {
        globalScrollManager();
        globalScrollManager = null;
      }
    };
  },
};

export default scrollAttributePlugin;
