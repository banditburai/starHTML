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

function extractValue(value: any): string {
  if (!value) return "";
  if (typeof value === "string") return value;
  if (value instanceof Set) {
    return Array.from(value)[0] || "";
  }
  return "";
}

function extractPlacementValue(value: any): string {
  if (value instanceof Set) {
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

      if (validPlacements.includes(singleValue)) {
        return singleValue;
      }

      // Handle Datastar's hyphen removal in compound placements
      const mergedCompoundPlacements: Record<string, string> = {
        topstart: "top-start",
        topend: "top-end",
        bottomstart: "bottom-start",
        bottomend: "bottom-end",
        leftstart: "left-start",
        leftend: "left-end",
        rightstart: "right-start",
        rightend: "right-end",
      };

      const mapped = mergedCompoundPlacements[singleValue.toLowerCase()];
      if (mapped) return mapped;
    }

    const validParts = ["top", "bottom", "left", "right", "start", "end"];
    const placementParts = values.filter((v) => validParts.includes(v));
    if (placementParts.length === 0) {
      return "bottom";
    }
    return placementParts.join("-");
  }
  return value || "bottom";
}

function parseConfig(el: HTMLElement, value: string, mods: Map<string, Set<string>>) {
  let signalPrefix = "";
  if (el.id) {
    const match = el.id.match(/^(.+?)(Content|Panel|Menu|Dropdown|Tooltip|Popover)?$/i);
    if (match) signalPrefix = match[1];
  }

  const explicitPrefix = mods.get("signal_prefix");
  if (explicitPrefix) {
    signalPrefix = extractValue(explicitPrefix);
  }

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
}

/**
 * Position handler for dynamically positioning elements relative to anchor elements using Floating UI.
 *
 * Supports modifiers:
 * - anchor: ID of the element to position relative to
 * - placement: Position (top, bottom, left, right, top-start, etc.)
 * - strategy: Positioning strategy (absolute or fixed)
 * - offset: Distance from anchor element (default: 8)
 * - flip: Enable position flipping when space is limited (default: true)
 * - shift: Enable position shifting to stay in viewport (default: true)
 * - hide: Hide element when reference is not visible (default: false)
 * - auto_size: Automatically size element to available space (default: false)
 * - signal_prefix: Prefix for reactive signal updates
 */
const positionAttributePlugin: AttributePlugin = {
  type: "attribute",
  name: "position",
  keyReq: "starts",

  onLoad(ctx: RuntimeContext): OnRemovalFn | void {
    const { el, value, mods, startBatch, endBatch } = ctx;

    const config = parseConfig(el, value, mods);

    const initialAnchor = document.getElementById(config.anchor);
    if (!initialAnchor) {
      return;
    }

    const middleware: Middleware[] = [offset(config.offsetValue)];

    if (config.flipEnabled) {
      middleware.push(flip());
    }

    if (config.shiftEnabled) {
      middleware.push(shift({ padding: 10 }));
    }

    if (config.hideEnabled) {
      middleware.push(hide());
    }

    if (config.autoSize) {
      middleware.push(
        size({
          apply({ availableWidth, availableHeight, elements }) {
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
    let visibilityObserver: MutationObserver | null = null;

    function isElementVisible(element: HTMLElement): boolean {
      const style = getComputedStyle(element);
      return (
        style.display !== "none" &&
        style.visibility !== "hidden" &&
        element.offsetWidth > 0 &&
        element.offsetHeight > 0
      );
    }

    function waitForValidBounds(element: HTMLElement, maxAttempts = 3): Promise<DOMRect | null> {
      return new Promise((resolve) => {
        let attempts = 0;

        const checkBounds = () => {
          attempts++;
          const bounds = element.getBoundingClientRect();

          const hasValidDimensions =
            (typeof bounds.width === "number" && bounds.width > 0) ||
            (typeof bounds.height === "number" && bounds.height > 0);
          const hasValidPosition = typeof bounds.x === "number" && typeof bounds.y === "number";
          const isValid = hasValidDimensions && hasValidPosition;

          if (isValid) {
            resolve(bounds);
          } else if (attempts >= maxAttempts) {
            resolve(null);
          } else {
            setTimeout(checkBounds, 16);
          }
        };

        checkBounds();
      });
    }

    const updatePosition = async (passedReferenceEl?: HTMLElement) => {
      startBatch();
      try {
        const currentAnchor = document.getElementById(config.anchor);
        if (!currentAnchor?.isConnected) {
          return;
        }

        const referenceEl = passedReferenceEl || currentAnchor;

        if (!referenceEl.isConnected) {
          cleanup?.();
          cleanup = null;
          return;
        }

        const bounds = referenceEl.getBoundingClientRect();

        // Basic validation for element bounds
        if (bounds.width === 0 && bounds.height === 0) {
          return;
        }

        let result: Awaited<ReturnType<typeof computePosition>>;
        try {
          result = await computePosition(referenceEl, el, {
            placement: config.placement,
            strategy: config.strategy,
            middleware,
          });
        } catch (_error) {
          return;
        }

        const positionChanged =
          Math.abs(result.x - lastPosition.x) > 0.1 ||
          Math.abs(result.y - lastPosition.y) > 0.1 ||
          result.placement !== lastPosition.placement;

        if (positionChanged) {
          Object.assign(el.style, {
            position: config.strategy,
            left: `${result.x}px`,
            top: `${result.y}px`,
          });

          lastPosition = { x: result.x, y: result.y, placement: result.placement };
        }
      } finally {
        endBatch();
      }
    };

    async function setupPositioning() {
      const currentAnchor = document.getElementById(config.anchor);
      if (!currentAnchor) {
        return;
      }

      const validBounds = await waitForValidBounds(currentAnchor);
      if (!validBounds) {
        return;
      }

      cleanup = autoUpdate(currentAnchor, el, () => updatePosition(), {
        ancestorScroll: true,
        ancestorResize: true,
        elementResize: true,
        layoutShift: true,
        animationFrame: false,
      });
    }

    function teardownPositioning() {
      cleanup?.();
      cleanup = null;
    }

    visibilityObserver = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (
          mutation.type === "attributes" &&
          (mutation.attributeName === "style" ||
            mutation.attributeName === "class" ||
            mutation.attributeName === "data-show")
        ) {
          const isVisible = isElementVisible(el);
          const wasVisible = cleanup !== null;

          if (isVisible && !wasVisible) {
            setupPositioning();
          } else if (!isVisible && wasVisible) {
            teardownPositioning();
          }
        }
      }
    });

    visibilityObserver.observe(el, {
      attributes: true,
      attributeFilter: ["style", "class", "data-show"],
    });

    if (isElementVisible(el)) {
      setupPositioning();
    }

    return () => {
      teardownPositioning();
      visibilityObserver?.disconnect();
      visibilityObserver = null;
    };
  },
};

export { positionAttributePlugin };
export default positionAttributePlugin;
