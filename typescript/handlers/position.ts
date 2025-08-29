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

    if (validPlacements.includes(singleValue)) return singleValue;

    // Datastar removes hyphens in compound placements
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
      // Native popover might need to wait for anchor to appear in DOM
      const observer = new MutationObserver(() => {
        const anchor = document.getElementById(config.anchor);
        if (anchor) {
          observer.disconnect();
          initializeWithAnchor(anchor);
        }
      });

      observer.observe(document.body, { childList: true, subtree: true });

      // Also poll for a limited time as fallback
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
      // Position off-screen initially to prevent flash at 0,0
      if (!el.hasAttribute("data-positioned")) {
        el.style.position = config.strategy;
        el.style.left = "-9999px";
        el.style.top = "-9999px";
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
            if (
              (bounds.width > 0 || bounds.height > 0) &&
              typeof bounds.x === "number" &&
              typeof bounds.y === "number"
            ) {
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

            // Mark as positioned
            if (!el.hasAttribute("data-positioned")) {
              el.setAttribute("data-positioned", "true");
            }
          }
        } catch {
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
            setupPositioning();
          } else if (e.newState === "closed") {
            teardownPositioning();
            el.removeAttribute("data-positioned");
          }
        };
        el.addEventListener("toggle", toggleHandler);
      } else {
        visibilityObserver = new MutationObserver(() => {
          const visible = isVisible(el);
          const wasVisible = cleanup !== null;
          if (visible && !wasVisible) setupPositioning();
          else if (!visible && wasVisible) teardownPositioning();
        });

        visibilityObserver.observe(el, {
          attributes: true,
          attributeFilter: ["style", "class", "data-show"],
        });

        if (isVisible(el)) setupPositioning();
      }

      return () => {
        teardownPositioning();
        if (toggleHandler) el.removeEventListener("toggle", toggleHandler);
        visibilityObserver?.disconnect();
      };
    }
  },
};

export { positionAttributePlugin };
export default positionAttributePlugin;
