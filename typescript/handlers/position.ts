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

function extractValue(value: any): any {
  return value instanceof Set ? Array.from(value)[0] : value;
}

function parseConfig(
  el: HTMLElement,
  mods: Map<string, any>,
  value: string
): PositionConfig | null {
  const anchorValue = mods.get("anchor") || value;
  if (!anchorValue) {
    console.warn("Position handler requires an anchor element");
    return null;
  }

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
    anchor: extractValue(anchorValue),
    placement: extractValue(mods.get("placement")) || "bottom",
    strategy: extractValue(mods.get("strategy")) || "absolute",
    offsetValue: mods.has("offset") ? Number(extractValue(mods.get("offset"))) : 8,
    flipEnabled: mods.has("flip") ? mods.get("flip") !== false : true,
    shiftEnabled: mods.has("shift") ? mods.get("shift") !== false : true,
    hideEnabled: mods.get("hide") === true,
    autoSize: mods.get("auto_size") === true,
    signalPrefix,
  };
}

const positionAttributePlugin: AttributePlugin = {
  type: "attribute",
  name: "position",
  keyReq: "starts",

  onLoad(ctx: RuntimeContext): OnRemovalFn | void {
    const { el, value, mods, mergePatch, startBatch, endBatch, getPath } = ctx;

    const config = parseConfig(el, mods, value);
    if (!config) return;

    const domAnchor = document.getElementById(config.anchor);
    if (!domAnchor) {
      console.warn(`Anchor element not found: ${config.anchor}`);
      return;
    }

    const middleware: Middleware[] = [];

    if (config.offsetValue) {
      middleware.push(offset(config.offsetValue));
    }

    if (config.flipEnabled) {
      middleware.push(
        flip({
          fallbackPlacements: ["top", "bottom", "left", "right"],
          padding: 5,
        })
      );
    }

    if (config.shiftEnabled) {
      middleware.push(
        shift({
          padding: 5,
          limiter: {
            fn: ({ x, y, rects }) => {
              const { width, height } = rects.floating;
              const viewportWidth = window.innerWidth;
              const viewportHeight = window.innerHeight;
              return {
                x: Math.min(Math.max(0, x), viewportWidth - width),
                y: Math.min(Math.max(0, y), viewportHeight - height),
              };
            },
          },
        })
      );
    }

    if (config.hideEnabled) {
      middleware.push(hide({ strategy: "referenceHidden" }));
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

    const updatePosition = async (referenceEl: any) => {
      startBatch();
      try {
        const result = await computePosition(referenceEl, el, {
          placement: config.placement,
          strategy: config.strategy,
          middleware,
        });

        Object.assign(el.style, {
          position: config.strategy,
          left: `${result.x}px`,
          top: `${result.y}px`,
        });

        if (config.signalPrefix) {
          mergePatch({
            [`${config.signalPrefix}_x`]: result.x,
            [`${config.signalPrefix}_y`]: result.y,
            [`${config.signalPrefix}_placement`]: result.placement,
          });

          if (config.hideEnabled && result.middlewareData.hide?.referenceHidden) {
            const currentOpen = getPath(`${config.signalPrefix}_open`);
            if (currentOpen) {
              mergePatch({ [`${config.signalPrefix}_open`]: false });
            }
          }
        }

        el.dispatchEvent(
          new CustomEvent("position-update", {
            detail: {
              x: result.x,
              y: result.y,
              placement: result.placement,
              strategy: config.strategy,
            },
            bubbles: true,
          })
        );
      } catch (error) {
        console.error("Error computing position:", error);
      } finally {
        endBatch();
      }
    };

    const cleanup = autoUpdate(domAnchor, el, () => updatePosition(domAnchor), {
      ancestorScroll: true,
      ancestorResize: true,
      elementResize: true,
      layoutShift: true,
      animationFrame: false,
    });

    const handleVirtualElement = () => {
      const virtualElement = (window as any)[`${el.id}VirtualAnchor`];
      updatePosition(virtualElement || domAnchor);
    };

    el.addEventListener("position-update-virtual", handleVirtualElement);

    return () => {
      cleanup();
      el.removeEventListener("position-update-virtual", handleVirtualElement);
    };
  },
};

export default positionAttributePlugin;
