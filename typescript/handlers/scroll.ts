/**
 * StarHTML Scroll Handler - Datastar AttributePlugin Implementation
 * Handles data-on-scroll attributes with reactive signal updates
 */

import { SmoothScroll } from "./smooth-scroll.js";
import { createRAFThrottle, createTimerThrottle } from "./throttle.js";

interface AttributePlugin {
  type: "attribute";
  name: string;
  keyReq: "allowed" | "denied" | "starts" | "exact";
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
const DIRECTION_THRESHOLD = 5;
const VISIBILITY_CHECK_INTERVAL = 100; // Check visibility every 100px of scroll

const SCROLL_ARG_NAMES = [
  "scrollX",
  "scrollY",
  "direction",
  "velocity",
  "delta",
  "visible",
  "visiblePercent",
  "progress",
  "pageProgress",
  "elementTop",
  "elementBottom",
  "isTop",
  "isBottom",
] as const;

interface ScrollData {
  scrollX: number;
  scrollY: number;
  direction: string;
  velocity: number;
  delta: number;
  visible: boolean;
  visiblePercent: number;
  progress: number;
  pageProgress: number;
  elementTop: number;
  elementBottom: number;
  isTop: boolean;
  isBottom: boolean;
}

function calculateVisiblePercent(rect: DOMRect, viewportHeight: number): number {
  if (rect.bottom < 0 || rect.top > viewportHeight) return 0;

  const visibleTop = Math.max(0, rect.top);
  const visibleBottom = Math.min(viewportHeight, rect.bottom);
  const visibleHeight = visibleBottom - visibleTop;

  return Math.round((visibleHeight / rect.height) * 100);
}

function getScrollData(el: HTMLElement, lastScrollY: number): ScrollData {
  const currentY = window.scrollY;
  const currentX = window.scrollX;
  const delta = currentY - lastScrollY;
  const direction = Math.abs(delta) > DIRECTION_THRESHOLD ? (delta > 0 ? "down" : "up") : "none";
  const velocity = Math.abs(delta);

  const rect = el.getBoundingClientRect();
  const elementTop = rect.top + window.scrollY;
  const elementBottom = elementTop + rect.height;
  const viewportHeight = window.innerHeight;

  const docHeight = document.documentElement.scrollHeight - window.innerHeight;
  const pageProgress = docHeight > 0 ? Math.round((window.scrollY / docHeight) * 100) : 0;

  let elProgress = pageProgress;
  if (el.scrollHeight > el.clientHeight + 1) {
    elProgress = Math.round((el.scrollTop / (el.scrollHeight - el.clientHeight)) * 100);
  }

  const visiblePercent = calculateVisiblePercent(rect, viewportHeight);
  const isInViewport = rect.top < viewportHeight && rect.bottom > 0;
  const isTop = currentY <= 0;
  const isBottom = currentY >= docHeight;

  return {
    scrollX: currentX,
    scrollY: currentY,
    direction,
    velocity,
    delta,
    visible: isInViewport,
    visiblePercent,
    progress: elProgress,
    pageProgress,
    elementTop,
    elementBottom,
    isTop,
    isBottom,
  };
}

function getThrottleMs(mods: Map<string, any>): number {
  const throttleValue = mods.get("throttle");
  if (throttleValue !== undefined) {
    if (throttleValue instanceof Set) {
      return Number.parseInt(String(Array.from(throttleValue)[0])) || DEFAULT_THROTTLE;
    }
    return Number.parseInt(String(throttleValue)) || DEFAULT_THROTTLE;
  }
  return DEFAULT_THROTTLE;
}

interface AnchoredElementState {
  anchorElement: HTMLElement;
  targetSignalPrefix: string;
  initialScrollY: number;
  initialScrollX: number;
  lastVisibilityCheck: number;
  hideAction?: string;
  hideWhenOffscreen: boolean;
}

function detectAnchoredElements(
  el: HTMLElement,
  value: string,
  mods: Map<string, any>,
  getPath: (path: string) => any
): AnchoredElementState | null {
  // Check for anchor_to modifier
  const anchorTo = mods.get("anchor_to");
  if (!anchorTo) return null;

  // Parse the anchor element ID or reference
  const anchorId = anchorTo instanceof Set ? Array.from(anchorTo)[0] : anchorTo;
  const anchorElement = document.getElementById(anchorId) || document.querySelector(anchorId);
  if (!anchorElement) {
    console.warn(`Anchor element not found: ${anchorId}`);
    return null;
  }

  // Try to detect signal prefix from the anchor element ID
  let signalPrefix = "";
  if (typeof anchorId === "string") {
    // Extract signal prefix from patterns like "${signal}Trigger" or "popoverTrigger"
    const match = anchorId.match(/^\$\{(.+?)\}|^(.+?)(?:Trigger|Button|Toggle)?$/i);
    if (match) {
      signalPrefix = match[1] || match[2] || "";
    }
  }

  // Override with explicit signal_prefix if provided
  const explicitPrefix = mods.get("signal_prefix");
  if (explicitPrefix) {
    signalPrefix = explicitPrefix instanceof Set ? Array.from(explicitPrefix)[0] : explicitPrefix;
  }

  if (!signalPrefix) {
    console.warn("Could not determine signal prefix for anchored element");
    return null;
  }

  // Get hide action from modifiers or detect from element
  let hideAction = mods.get("hide_action");
  if (hideAction instanceof Set) {
    hideAction = Array.from(hideAction)[0];
  }
  
  const hideWhenOffscreen = mods.has("hide_when_offscreen") || mods.get("hide_when_offscreen") === true;

  // Auto-detect hide action if not specified
  if (!hideAction && hideWhenOffscreen) {
    // Check if there's a popover element
    const contentEl = document.querySelector(`[popover]:has(#${signalPrefix}Content)`) || 
                     document.getElementById(`${signalPrefix}Content`);
    if (contentEl && contentEl.hasAttribute("popover")) {
      hideAction = "hidePopover()";
    } else {
      // Default to setting _open signal to false
      hideAction = `$${signalPrefix}_open = false`;
    }
  }

  return {
    anchorElement: anchorElement as HTMLElement,
    targetSignalPrefix: signalPrefix,
    initialScrollY: window.scrollY,
    initialScrollX: window.scrollX,
    lastVisibilityCheck: window.scrollY,
    hideAction,
    hideWhenOffscreen,
  };
}

function updateAnchoredPosition(
  state: AnchoredElementState,
  currentScrollY: number,
  currentScrollX: number,
  mergePatch: (patch: Record<string, any>) => void,
  getPath: (path: string) => any,
  rx: (...args: any[]) => any
): void {
  const deltaY = currentScrollY - state.initialScrollY;
  const deltaX = currentScrollX - state.initialScrollX;

  // Get current position values
  const topSignal = `${state.targetSignalPrefix}_top`;
  const leftSignal = `${state.targetSignalPrefix}_left`;
  const openSignal = `${state.targetSignalPrefix}_open`;

  const currentTop = getPath(topSignal);
  const currentLeft = getPath(leftSignal);
  const isOpen = getPath(openSignal);

  if (!isOpen) return;

  // Update positions with inverse delta
  if (currentTop !== undefined && currentLeft !== undefined) {
    const newTop = currentTop - deltaY;
    const newLeft = currentLeft - deltaX;
    
    mergePatch({
      [topSignal]: newTop,
      [leftSignal]: newLeft,
    });
  }

  // Update initial scroll position for next frame
  state.initialScrollY = currentScrollY;
  state.initialScrollX = currentScrollX;

  // Check visibility at intervals
  if (state.hideWhenOffscreen && 
      Math.abs(currentScrollY - state.lastVisibilityCheck) > VISIBILITY_CHECK_INTERVAL) {
    const rect = state.anchorElement.getBoundingClientRect();
    const isVisible = rect.bottom > 0 && 
                     rect.top < window.innerHeight && 
                     rect.right > 0 && 
                     rect.left < window.innerWidth;
    
    if (!isVisible && state.hideAction) {
      // Execute hide action
      try {
        rx(state.hideAction);
      } catch (e) {
        console.error("Error executing hide action:", e);
      }
    }
    
    state.lastVisibilityCheck = currentScrollY;
  }
}

const scrollAttributePlugin: AttributePlugin = {
  type: "attribute",
  name: "onScroll",
  keyReq: "starts",
  argNames: [...SCROLL_ARG_NAMES],

  onLoad(ctx: RuntimeContext): OnRemovalFn | void {
    const { el, value, mods, rx, mergePatch, startBatch, endBatch, getPath } = ctx;

    // Allow empty value for anchored mode
    if (!value?.trim() && !mods.has("anchor_to")) {
      return;
    }

    const throttleMs = getThrottleMs(mods);

    let lastScrollY = window.scrollY;
    let isUpdating = false;
    let smoothScroll: SmoothScroll | null = null;
    
    // Check for anchored element configuration
    const anchoredState = detectAnchoredElements(el, value, mods, getPath);

    if (mods.has("smooth")) {
      smoothScroll = new SmoothScroll(el, () => {
        if (!isUpdating) {
          updateScroll();
        }
      });
      smoothScroll.start();
    }

    const updateScroll = () => {
      if (isUpdating) {
        return;
      }
      isUpdating = true;

      const rawScrollData = getScrollData(el, lastScrollY);

      let scrollData = rawScrollData;
      if (smoothScroll) {
        const smoothedValues = smoothScroll.getSmoothData({
          scrollY: rawScrollData.scrollY,
          velocity: rawScrollData.velocity,
          progress: rawScrollData.progress,
          pageProgress: rawScrollData.pageProgress,
          visiblePercent: rawScrollData.visiblePercent,
        });

        scrollData = {
          ...rawScrollData,
          scrollY: smoothedValues.scrollY,
          velocity: smoothedValues.velocity,
          progress: smoothedValues.progress,
          pageProgress: smoothedValues.pageProgress,
          visiblePercent: smoothedValues.visiblePercent,
        };
      }

      startBatch();
      try {
        // Handle anchored element positioning first
        if (anchoredState) {
          updateAnchoredPosition(
            anchoredState,
            rawScrollData.scrollY,
            rawScrollData.scrollX,
            mergePatch,
            getPath,
            rx
          );
        }
        
        // Only execute custom expression and merge scroll data if there's a custom expression
        // or if we're not in pure anchor mode
        if (value?.trim() || !anchoredState) {
          mergePatch({
            scrollX: scrollData.scrollX,
            scrollY: scrollData.scrollY,
            direction: scrollData.direction,
            velocity: scrollData.velocity,
            delta: scrollData.delta,
            visible: scrollData.visible,
            visiblePercent: scrollData.visiblePercent,
            progress: scrollData.progress,
            pageProgress: scrollData.pageProgress,
            elementTop: scrollData.elementTop,
            elementBottom: scrollData.elementBottom,
            isTop: scrollData.isTop,
            isBottom: scrollData.isBottom,
          });
          
          if (value?.trim()) {
            rx(
              scrollData.scrollX,
              scrollData.scrollY,
              scrollData.direction,
              scrollData.velocity,
              scrollData.delta,
              scrollData.visible,
              scrollData.visiblePercent,
              scrollData.progress,
              scrollData.pageProgress,
              scrollData.elementTop,
              scrollData.elementBottom,
              scrollData.isTop,
              scrollData.isBottom
            );
          }
        }
      } catch (error) {
        console.error("Error executing scroll handler:", error);
      } finally {
        endBatch();
        lastScrollY = rawScrollData.scrollY; // Use raw value for direction calculation
        isUpdating = false;
      }
    };

    const throttledUpdate =
      throttleMs <= 16
        ? createRAFThrottle(updateScroll)
        : createTimerThrottle(updateScroll, throttleMs);

    updateScroll();

    const handleScroll = () => {
      throttledUpdate();
    };
    window.addEventListener("scroll", handleScroll, { passive: true });

    let elementScrollCleanup: (() => void) | null = null;
    if (el.scrollHeight > el.clientHeight) {
      const handleElementScroll = () => throttledUpdate();
      el.addEventListener("scroll", handleElementScroll, { passive: true });
      elementScrollCleanup = () => el.removeEventListener("scroll", handleElementScroll);
    }

    return () => {
      window.removeEventListener("scroll", handleScroll);
      elementScrollCleanup?.();
      smoothScroll?.cleanup();
    };
  },
};

export default scrollAttributePlugin;
