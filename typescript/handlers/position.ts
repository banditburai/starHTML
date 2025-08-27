/**
 * StarHTML Position Handler - Floating UI Integration for Positioned Elements
 * Provides automatic positioning and anchoring for floating elements using Floating UI
 */

import {
  computePosition,
  autoUpdate,
  flip,
  shift,
  offset,
  hide,
  size,
  type Placement,
  type Middleware,
  type Strategy,
} from "@floating-ui/dom";

interface AttributePlugin {
  type: "attribute";
  name: string;
  keyReq: "allowed" | "denied" | "starts" | "exact";
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

interface PositionConfig {
  anchor: string;
  placement: Placement;
  strategy: Strategy;
  offsetValue: number;
  flipEnabled: boolean;
  shiftEnabled: boolean;
  hideEnabled: boolean;
  autoSize: boolean;
  signalPrefix?: string;
}

function parseConfig(el: HTMLElement, mods: Map<string, any>, value: string): PositionConfig | null {
  // Get anchor element ID
  const anchorValue = mods.get("anchor") || value;
  if (!anchorValue) {
    console.warn("Position handler requires an anchor element");
    return null;
  }

  const anchorId = anchorValue instanceof Set ? Array.from(anchorValue)[0] : anchorValue;
  
  // Try to detect signal prefix from element ID
  let signalPrefix = "";
  const elementId = el.id;
  if (elementId) {
    // Extract prefix from patterns like "popoverContent" -> "popover"
    const match = elementId.match(/^(.+?)(Content|Panel|Menu|Dropdown|Tooltip|Popover)?$/i);
    if (match) {
      signalPrefix = match[1];
    }
  }

  // Override with explicit signal prefix if provided
  const explicitPrefix = mods.get("signal_prefix");
  if (explicitPrefix) {
    signalPrefix = explicitPrefix instanceof Set ? Array.from(explicitPrefix)[0] : explicitPrefix;
  }

  // Get placement (default: "bottom")
  const placementValue = mods.get("placement");
  const placement = (placementValue instanceof Set ? Array.from(placementValue)[0] : placementValue) || "bottom";

  // Get strategy (default: "absolute")
  const strategyValue = mods.get("strategy");
  const strategy = (strategyValue instanceof Set ? Array.from(strategyValue)[0] : strategyValue) || "absolute";

  // Get offset (default: 8)
  const offsetMod = mods.get("offset");
  const offsetValue = offsetMod ? Number(offsetMod instanceof Set ? Array.from(offsetMod)[0] : offsetMod) : 8;

  // Get feature flags
  const flipEnabled = mods.has("flip") || mods.get("flip") !== false;
  const shiftEnabled = mods.has("shift") || mods.get("shift") !== false;
  const hideEnabled = mods.has("hide") || mods.get("hide") === true;
  const autoSize = mods.has("auto_size") || mods.get("auto_size") === true;

  return {
    anchor: anchorId,
    placement: placement as Placement,
    strategy: strategy as Strategy,
    offsetValue,
    flipEnabled,
    shiftEnabled,
    hideEnabled,
    autoSize,
    signalPrefix,
  };
}

const positionAttributePlugin: AttributePlugin = {
  type: "attribute",
  name: "position",
  keyReq: "starts",

  onLoad(ctx: RuntimeContext): OnRemovalFn | void {
    const { el, value, mods, mergePatch, startBatch, endBatch, getPath } = ctx;

    // Parse configuration
    const config = parseConfig(el, mods, value);
    if (!config) return;

    // Get anchor element
    const anchorElement = document.getElementById(config.anchor);
    if (!anchorElement) {
      console.warn(`Anchor element not found: ${config.anchor}`);
      return;
    }

    // Build middleware array based on configuration
    const middleware: Middleware[] = [];
    
    // Add offset
    if (config.offsetValue) {
      middleware.push(offset(config.offsetValue));
    }

    // Add flip to automatically flip when there's not enough space
    if (config.flipEnabled) {
      middleware.push(flip({
        fallbackPlacements: ["top", "bottom", "left", "right"],
        padding: 5,
      }));
    }

    // Add shift to slide along the viewport edge
    if (config.shiftEnabled) {
      middleware.push(shift({
        padding: 5,
        limiter: {
          fn: ({ x, y, placement, rects, availableWidth, availableHeight }) => {
            const { width, height } = rects.floating;
            return {
              x: Math.min(Math.max(0, x), availableWidth - width),
              y: Math.min(Math.max(0, y), availableHeight - height),
            };
          },
        },
      }));
    }

    // Add hide detection when reference element is clipped
    if (config.hideEnabled) {
      middleware.push(hide({
        strategy: "referenceHidden",
      }));
    }

    // Add auto-size to constrain floating element size
    if (config.autoSize) {
      middleware.push(size({
        apply({ availableWidth, availableHeight, elements }) {
          Object.assign(elements.floating.style, {
            maxWidth: `${availableWidth}px`,
            maxHeight: `${availableHeight}px`,
          });
        },
        padding: 10,
      }));
    }

    // Setup auto-update for reactive positioning
    const cleanup = autoUpdate(
      anchorElement,
      el,
      async () => {
        startBatch();
        try {
          const result = await computePosition(anchorElement, el, {
            placement: config.placement,
            strategy: config.strategy,
            middleware,
          });

          // Update position styles directly on element
          Object.assign(el.style, {
            position: config.strategy,
            left: `${result.x}px`,
            top: `${result.y}px`,
          });

          // If signal prefix is detected, update position signals for reactive binding
          if (config.signalPrefix) {
            mergePatch({
              [`${config.signalPrefix}_x`]: result.x,
              [`${config.signalPrefix}_y`]: result.y,
              [`${config.signalPrefix}_placement`]: result.placement,
            });

            // If hide middleware detected the reference is hidden, update visibility signal
            if (config.hideEnabled && result.middlewareData.hide) {
              const { referenceHidden } = result.middlewareData.hide;
              const currentOpen = getPath(`${config.signalPrefix}_open`);
              if (referenceHidden && currentOpen) {
                mergePatch({
                  [`${config.signalPrefix}_open`]: false,
                });
              }
            }
          }

          // Dispatch custom event for position updates
          el.dispatchEvent(new CustomEvent("position-update", {
            detail: {
              x: result.x,
              y: result.y,
              placement: result.placement,
              strategy: config.strategy,
            },
            bubbles: true,
          }));

        } catch (error) {
          console.error("Error computing position:", error);
        } finally {
          endBatch();
        }
      },
      {
        // Options for auto-update
        ancestorScroll: true,
        ancestorResize: true,
        elementResize: true,
        layoutShift: true,
        animationFrame: false, // Use event-based updates for better performance
      }
    );

    // Return cleanup function
    return () => {
      cleanup();
    };
  },
};

export default positionAttributePlugin;