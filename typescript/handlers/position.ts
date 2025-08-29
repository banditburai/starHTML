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

const extractValue = (value: any): string => {
  if (!value) return "";
  if (typeof value === "string") return value;
  if (value instanceof Set) return Array.from(value)[0] || "";
  return "";
};

const extractPlacementValue = (value: any): string => {
  if (!(value instanceof Set)) return value || "bottom";

  const values = Array.from(value);
  if (values.length === 1) {
    const singleValue = values[0];
    const validPlacements = [
      "top", "bottom", "left", "right",
      "top-start", "top-end", "bottom-start", "bottom-end",
      "left-start", "left-end", "right-start", "right-end",
    ];

    if (validPlacements.includes(singleValue)) return singleValue;

    // Datastar removes hyphens from compound placements
    const dehyphenated: Record<string, string> = {
      topstart: "top-start",
      topend: "top-end",
      bottomstart: "bottom-start",
      bottomend: "bottom-end",
      leftstart: "left-start",
      leftend: "left-end",
      rightstart: "right-start",
      rightend: "right-end",
    };

    return dehyphenated[singleValue.toLowerCase()] || "bottom";
  }

  const validParts = ["top", "bottom", "left", "right", "start", "end"];
  const placementParts = values.filter((v) => validParts.includes(v));
  return placementParts.length ? placementParts.join("-") : "bottom";
};

const parseConfig = (el: HTMLElement, value: string, mods: Map<string, Set<string>>) => {
  const match = el.id?.match(/^(.+?)(Content|Panel|Menu|Dropdown|Tooltip|Popover)?$/i);
  const signalPrefix = extractValue(mods.get("signal_prefix")) || (match?.[1] ?? "");

  return {
    anchor: extractValue(mods.get("anchor") || value),
    placement: extractPlacementValue(mods.get("placement")) as Placement,
    strategy: (extractValue(mods.get("strategy")) || "absolute") as Strategy,
    offsetValue: mods.has("offset") ? Number(extractValue(mods.get("offset"))) : 8,
    flipEnabled: mods.has("flip") ? extractValue(mods.get("flip")) !== "false" : true,
    shiftEnabled: mods.has("shift") ? extractValue(mods.get("shift")) !== "false" : true,
    hideEnabled: extractValue(mods.get("hide")) === "true",
    autoSize: extractValue(mods.get("auto_size")) === "true",
    signalPrefix,
  };
};

const positionAttributePlugin: AttributePlugin = {
  type: "attribute",
  name: "position",
  keyReq: "starts",

  onLoad(ctx: RuntimeContext): OnRemovalFn | void {
    const { el, value, mods, startBatch, endBatch } = ctx;
    const config = parseConfig(el, value, mods);
    const isNativePopover = el.hasAttribute("popover");
    const initialAnchor = document.getElementById(config.anchor);

    if (!initialAnchor && !isNativePopover) return;

    if (!initialAnchor) {
      const observer = new MutationObserver(() => {
        const anchor = document.getElementById(config.anchor);
        if (anchor) {
          observer.disconnect();
          initializeWithAnchor(anchor);
        }
      });

      observer.observe(document.body, { childList: true, subtree: true });

      let attempts = 0;
      const checkInterval = setInterval(() => {
        const anchor = document.getElementById(config.anchor);
        if (anchor || ++attempts > 50) {
          clearInterval(checkInterval);
          observer.disconnect();
          if (anchor) initializeWithAnchor(anchor);
        }
      }, 100);

      return () => {
        clearInterval(checkInterval);
        observer.disconnect();
      };
    }

    return initializeWithAnchor(initialAnchor);

    function initializeWithAnchor(anchorElement: HTMLElement): OnRemovalFn {
      const originalStyles = {
        opacity: el.style.opacity,
        pointerEvents: el.style.pointerEvents,
        transition: el.style.transition,
      };

      const hideElement = () => {
        el.style.transition = "none";
        el.style.opacity = "0";
        el.style.pointerEvents = "none";
        el.style.position = config.strategy;
        el.setAttribute("data-position-state", "initializing");
      };

      const revealElement = () => {
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            el.setAttribute("data-position-state", "positioned");
            el.setAttribute("data-position-initialized", "true");
            el.style.transition = originalStyles.transition || "opacity 0.15s ease-in-out";
            el.style.opacity = originalStyles.opacity || "1";
            el.style.pointerEvents = originalStyles.pointerEvents || "";
            
            setTimeout(() => {
              if (el.style.transition === "opacity 0.15s ease-in-out") {
                el.style.transition = originalStyles.transition || "";
              }
            }, 150);
          });
        });
      };

      if (!el.hasAttribute("data-position-initialized")) {
        hideElement();
      }

      const middleware: Middleware[] = [offset(config.offsetValue)];
      if (config.flipEnabled) middleware.push(flip());
      if (config.shiftEnabled) middleware.push(shift({ padding: 10 }));
      if (config.hideEnabled) middleware.push(hide());
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

      let lastPosition = { x: 0, y: 0, placement: "" };
      let cleanup: (() => void) | null = null;
      let hasPositionedOnce = false;

      const isVisible = (element: HTMLElement) => {
        const style = getComputedStyle(element);
        return (
          style.display !== "none" &&
          style.visibility !== "hidden" &&
          element.offsetWidth > 0 &&
          element.offsetHeight > 0
        );
      };

      const waitForBounds = (element: HTMLElement): Promise<DOMRect | null> =>
        new Promise((resolve) => {
          let attempts = 0;
          const check = () => {
            const bounds = element.getBoundingClientRect();
            if ((bounds.width > 0 || bounds.height > 0) && 
                typeof bounds.x === "number" && 
                typeof bounds.y === "number") {
              resolve(bounds);
            } else if (++attempts >= 3) {
              resolve(null);
            } else {
              setTimeout(check, 16);
            }
          };
          check();
        });

      const updatePosition = async () => {
        const anchor = anchorElement || document.getElementById(config.anchor);
        if (!anchor?.isConnected) return;

        const bounds = anchor.getBoundingClientRect();
        if (bounds.width === 0 && bounds.height === 0) return;

        startBatch();
        try {
          const result = await computePosition(anchor, el, {
            placement: config.placement,
            strategy: config.strategy,
            middleware,
          });

          const changed =
            Math.abs(result.x - lastPosition.x) > 0.1 ||
            Math.abs(result.y - lastPosition.y) > 0.1 ||
            result.placement !== lastPosition.placement;

          if (changed) {
            Object.assign(el.style, {
              position: config.strategy,
              left: `${result.x}px`,
              top: `${result.y}px`,
            });
            lastPosition = { x: result.x, y: result.y, placement: result.placement };
          }

          if (!hasPositionedOnce) {
            hasPositionedOnce = true;
            revealElement();
          }
        } catch (err) {
          console.error("Position update failed:", err);
        } finally {
          endBatch();
        }
      };

      const setupPositioning = async () => {
        const anchor = anchorElement || document.getElementById(config.anchor);
        if (!anchor || !(await waitForBounds(anchor))) return;

        cleanup = autoUpdate(anchor, el, updatePosition, {
          ancestorScroll: true,
          ancestorResize: true,
          elementResize: true,
          layoutShift: true,
          animationFrame: false,
        });
      };

      const teardownPositioning = () => {
        cleanup?.();
        cleanup = null;
      };

      let toggleHandler: ((e: any) => void) | null = null;
      let visibilityObserver: MutationObserver | null = null;

      if (isNativePopover) {
        toggleHandler = (e: any) => {
          if (e.newState === "open") {
            hideElement();
            el.offsetHeight; // Force reflow for rapid toggles
            hasPositionedOnce = false;
            el.removeAttribute("data-position-initialized");
            setupPositioning();
          } else if (e.newState === "closed") {
            teardownPositioning();
            el.removeAttribute("data-position-initialized");
            el.setAttribute("data-position-state", "closed");
            el.style.opacity = "0";
            hasPositionedOnce = false;
          }
        };
        el.addEventListener("toggle", toggleHandler);
      } else {
        visibilityObserver = new MutationObserver(() => {
          const visible = isVisible(el);
          const wasVisible = cleanup !== null;
          if (visible && !wasVisible) {
            if (!hasPositionedOnce) hideElement();
            setupPositioning();
          } else if (!visible && wasVisible) {
            teardownPositioning();
            hasPositionedOnce = false;
          }
        });

        visibilityObserver.observe(el, {
          attributes: true,
          attributeFilter: ["style", "class", "data-show"],
        });

        if (isVisible(el)) setupPositioning();
      }

      return () => {
        teardownPositioning();
        toggleHandler && el.removeEventListener("toggle", toggleHandler);
        visibilityObserver?.disconnect();

        el.style.opacity = originalStyles.opacity || "";
        el.style.pointerEvents = originalStyles.pointerEvents || "";
        el.style.transition = originalStyles.transition || "";
        el.removeAttribute("data-position-state");
        el.removeAttribute("data-position-initialized");
      };
    }
  },
};

export { positionAttributePlugin };
export default positionAttributePlugin;