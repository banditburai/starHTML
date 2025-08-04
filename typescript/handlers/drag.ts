import { createRAFThrottle } from "./throttle.js";

interface AttributePlugin {
  type: "attribute";
  name: string;
  keyReq: "allowed" | "denied" | "starts" | "exact";
  valReq?: "allowed" | "denied" | "must";
  shouldEvaluate?: boolean;
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

interface DragConfig {
  signal: string;
  mode: "freeform" | "sortable";
  throttleMs: number;
  constrainToParent: boolean;
  touchEnabled: boolean;
}

interface DragState {
  isDragging: boolean;
  element: HTMLElement | null;
  hasMoved: boolean;
  startPoint: { x: number; y: number };
  offset: { x: number; y: number };
  current: { x: number; y: number };
  dimensions: { width: number; height: number };
}

const argNames = ["isDragging", "elementId", "x", "y", "dropZone", "zoneItems"];

const DEFAULT_THROTTLE = 16;

const parseTransform = (transform: string): { pan: { x: number; y: number }; scale: number } => {
  if (!transform || transform === "none") {
    return { pan: { x: 0, y: 0 }, scale: 1 };
  }

  const matches = transform.match(/translate\(([^,]+),\s*([^)]+)\)\s*scale\(([^)]+)\)/);
  if (!matches) {
    return { pan: { x: 0, y: 0 }, scale: 1 };
  }

  return {
    pan: {
      x: Number.parseFloat(matches[1]),
      y: Number.parseFloat(matches[2]),
    },
    scale: Number.parseFloat(matches[3]),
  };
};

const calculateCanvasPosition = (
  screenX: number,
  screenY: number,
  viewportRect: DOMRect,
  transform: { pan: { x: number; y: number }; scale: number },
  offset: { x: number; y: number }
): { x: number; y: number } => {
  return {
    x:
      (screenX - viewportRect.left - transform.pan.x) / transform.scale -
      offset.x / transform.scale,
    y:
      (screenY - viewportRect.top - transform.pan.y) / transform.scale - offset.y / transform.scale,
  };
};

const applyConstraints = (
  x: number,
  y: number,
  parent: HTMLElement,
  dimensions: { width: number; height: number }
): { x: number; y: number } => {
  const maxX = parent.offsetWidth - dimensions.width;
  const maxY = parent.offsetHeight - dimensions.height;

  return {
    x: Math.max(0, Math.min(maxX, x)),
    y: Math.max(0, Math.min(maxY, y)),
  };
};

const findDropZone = (x: number, y: number): Element | null => {
  const elementUnder = document.elementFromPoint(x, y);
  return elementUnder?.closest("[data-drop-zone]") ?? null;
};

const getDropZoneItems = (zone: Element): string[] => {
  return Array.from(zone.querySelectorAll("[data-draggable]"))
    .map((el) => el.id || el.getAttribute("data-id"))
    .filter((id): id is string => Boolean(id));
};

const findInsertPosition = (
  dropZone: Element,
  mouseY: number,
  _draggedElement: HTMLElement
): Element | null => {
  const draggableElements = Array.from(
    dropZone.querySelectorAll("[data-draggable]:not(.is-dragging)")
  );

  for (const element of draggableElements) {
    const rect = element.getBoundingClientRect();
    const midpoint = rect.top + rect.height / 2;

    if (mouseY < midpoint) {
      return element as Element;
    }
  }

  return null;
};

const updateDropZoneTracking = (_config: DragConfig, mergePatch: RuntimeContext["mergePatch"]) => {
  const allZones = document.querySelectorAll("[data-drop-zone]");

  for (const zone of allZones) {
    const zoneName = zone.getAttribute("data-drop-zone");
    if (!zoneName) continue;

    const zoneRect = zone.getBoundingClientRect();
    const items: string[] = [];

    for (const draggable of document.querySelectorAll("[data-draggable]")) {
      const rect = draggable.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;

      if (
        centerX >= zoneRect.left &&
        centerX <= zoneRect.right &&
        centerY >= zoneRect.top &&
        centerY <= zoneRect.bottom
      ) {
        const id = draggable.id || draggable.getAttribute("data-id");
        if (id) items.push(id);
      }
    }

    mergePatch({
      [`zone_${zoneName}_items`]: items,
    });
  }
};

const findRelativeParent = (element: HTMLElement): HTMLElement | null => {
  let parent = element.parentElement;
  while (parent && parent !== document.body) {
    if (window.getComputedStyle(parent).position === "relative") return parent;
    parent = parent.parentElement;
  }
  return null;
};

const dragAttributePlugin: AttributePlugin = {
  type: "attribute",
  name: "draggable",
  keyReq: "starts",
  valReq: "allowed",
  shouldEvaluate: false,

  onLoad(ctx: RuntimeContext): OnRemovalFn | void {
    const { el, mergePatch, startBatch, endBatch } = ctx;

    const config: DragConfig = {
      signal: (window as any).__starhtml_drag_config?.signal ?? "drag",
      mode: (window as any).__starhtml_drag_config?.mode ?? "freeform",
      throttleMs: (window as any).__starhtml_drag_config?.throttleMs ?? DEFAULT_THROTTLE,
      constrainToParent: (window as any).__starhtml_drag_config?.constrainToParent ?? false,
      touchEnabled: (window as any).__starhtml_drag_config?.touchEnabled ?? true,
    };

    const initializeSignals = () => {
      mergePatch({
        isDragging: false,
        elementId: null,
        x: 0,
        y: 0,
        dropZone: null,
      });

      const dropZoneName = el.getAttribute("data-drop-zone");
      if (dropZoneName) {
        mergePatch({
          [`zone_${dropZoneName}_items`]: getDropZoneItems(el),
        });
      }
    };

    initializeSignals();

    const state: DragState & { placeholder?: HTMLElement | null } = {
      isDragging: false,
      element: null,
      hasMoved: false,
      startPoint: { x: 0, y: 0 },
      offset: { x: 0, y: 0 },
      current: { x: 0, y: 0 },
      dimensions: { width: 0, height: 0 },
    };

    const updateDragSignals = (updates: Record<string, any>) => {
      startBatch();
      try {
        mergePatch(updates);
      } catch (error) {
        console.error("Error updating drag signals:", error);
      } finally {
        endBatch();
      }
    };

    const updateDragPosition = () => {
      if (!state.element || !state.isDragging) return;

      const { x, y } = state.current;

      const canvasContainer = state.element.closest("[data-canvas-container]");
      const canvasViewport = document.querySelector("[data-canvas-viewport]");

      let finalX: number;
      let finalY: number;

      if (canvasContainer && canvasViewport) {
        const viewportRect = canvasViewport.getBoundingClientRect();
        const transform = parseTransform(window.getComputedStyle(canvasContainer).transform);
        const canvasPos = calculateCanvasPosition(x, y, viewportRect, transform, state.offset);

        finalX = Math.round(canvasPos.x);
        finalY = Math.round(canvasPos.y);

        Object.assign(state.element.style, {
          left: `${canvasPos.x}px`,
          top: `${canvasPos.y}px`,
          position: "absolute",
          zIndex: "1000",
          transform: transform.scale !== 1 ? `scale(${1 / transform.scale})` : "",
          transformOrigin: "top left",
        });
      } else {
        const relativeParent = findRelativeParent(state.element);

        if (relativeParent && relativeParent !== document.body) {
          const parentRect = relativeParent.getBoundingClientRect();
          let relativePos = {
            x: x - parentRect.left - state.offset.x,
            y: y - parentRect.top - state.offset.y,
          };

          if (config.constrainToParent) {
            relativePos = applyConstraints(
              relativePos.x,
              relativePos.y,
              relativeParent,
              state.dimensions
            );
          }

          finalX = Math.round(relativePos.x);
          finalY = Math.round(relativePos.y);

          Object.assign(state.element.style, {
            left: `${relativePos.x}px`,
            top: `${relativePos.y}px`,
            position: "absolute",
            zIndex: "1000",
          });
        } else {
          let transformX = x - state.offset.x;
          let transformY = y - state.offset.y;

          if (config.constrainToParent && state.element.parentElement) {
            const parentRect = state.element.parentElement.getBoundingClientRect();

            const minX = parentRect.left - state.offset.x;
            const minY = parentRect.top - state.offset.y;
            const maxX = parentRect.right - state.dimensions.width - state.offset.x;
            const maxY = parentRect.bottom - state.dimensions.height - state.offset.y;

            transformX = Math.max(minX, Math.min(maxX, transformX));
            transformY = Math.max(minY, Math.min(maxY, transformY));
          }

          finalX = Math.round(transformX + state.offset.x);
          finalY = Math.round(transformY + state.offset.y);

          Object.assign(state.element.style, {
            position: "fixed",
            transform: `translate(${transformX}px, ${transformY}px)`,
            left: "0",
            top: "0",
            zIndex: "9999",
            pointerEvents: "none",
            willChange: "transform",
          });
        }
      }

      if (state.element) {
        state.element.style.pointerEvents = "none";
        const dropZone = findDropZone(state.current.x, state.current.y);
        state.element.style.pointerEvents = "";

        const dropZoneName = dropZone?.getAttribute("data-drop-zone") ?? null;
        const elementId = state.element.id || state.element.dataset.id || null;

        updateDragSignals({
          isDragging: true,
          elementId: elementId,
          x: finalX,
          y: finalY,
          dropZone: dropZoneName,
        });

        for (const zone of document.querySelectorAll("[data-drop-zone]")) {
          zone.classList.toggle("drop-zone-active", zone === dropZone);
        }

        if (config.mode === "sortable" && dropZone) {
          if (state.placeholder) {
            state.placeholder.remove();
          }

          state.placeholder = document.createElement("div");
          state.placeholder.className = "drag-placeholder";
          state.placeholder.style.height = `${state.dimensions.height}px`;
          state.placeholder.style.margin = window.getComputedStyle(state.element).margin;
          state.placeholder.style.opacity = "0.5";
          state.placeholder.style.border = "2px dashed #3b82f6";
          state.placeholder.style.borderRadius = "8px";
          state.placeholder.style.boxSizing = "border-box";

          const insertBefore = findInsertPosition(dropZone, state.current.y, state.element);

          if (insertBefore) {
            dropZone.insertBefore(state.placeholder, insertBefore);
          } else {
            dropZone.appendChild(state.placeholder);
          }
        }
      }

      if (state.isDragging && config.mode === "freeform") {
        updateDropZoneTracking(config, mergePatch);
      }
    };

    const throttledUpdatePosition = createRAFThrottle(updateDragPosition);

    let boundPointerMove: ((evt: PointerEvent) => void) | null = null;
    let boundPointerUp: (() => void) | null = null;

    const handlePointerDown = (evt: PointerEvent) => {
      const target = evt.target as HTMLElement;
      const draggableElement = target.closest("[data-draggable]") as HTMLElement;

      const isDirectHandler = el.hasAttribute("data-draggable");
      if (!draggableElement || (isDirectHandler && draggableElement !== el)) return;

      evt.preventDefault();

      state.element = draggableElement;
      state.startPoint = { x: evt.clientX, y: evt.clientY };
      state.current = { x: evt.clientX, y: evt.clientY };
      state.hasMoved = false;

      const rect = draggableElement.getBoundingClientRect();

      const canvasContainer = draggableElement.closest("[data-canvas-container]");
      const canvasViewport = document.querySelector("[data-canvas-viewport]");

      if (canvasContainer && canvasViewport) {
        const viewportRect = canvasViewport.getBoundingClientRect();
        const transform = parseTransform(window.getComputedStyle(canvasContainer).transform);

        const canvasClickPos = calculateCanvasPosition(
          evt.clientX,
          evt.clientY,
          viewportRect,
          transform,
          { x: 0, y: 0 }
        );

        const elementStyle = window.getComputedStyle(draggableElement);
        const elementCanvasX = Number.parseFloat(elementStyle.left) || 0;
        const elementCanvasY = Number.parseFloat(elementStyle.top) || 0;

        state.offset = {
          x: canvasClickPos.x - elementCanvasX,
          y: canvasClickPos.y - elementCanvasY,
        };
      } else {
        state.offset = {
          x: evt.clientX - rect.left,
          y: evt.clientY - rect.top,
        };
      }
      state.dimensions = {
        width: rect.width,
        height: rect.height,
      };

      boundPointerMove = handlePointerMove;
      boundPointerUp = handlePointerUp;
      document.addEventListener("pointermove", boundPointerMove);
      document.addEventListener("pointerup", boundPointerUp);
    };

    const handlePointerMove = (evt: PointerEvent) => {
      if (!state.element) return;

      state.current = { x: evt.clientX, y: evt.clientY };

      const deltaX = state.current.x - state.startPoint.x;
      const deltaY = state.current.y - state.startPoint.y;
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

      if (!state.hasMoved && distance < 5) return;

      if (!state.hasMoved) {
        state.hasMoved = true;
        state.isDragging = true;

        const elementId = state.element.id || state.element.dataset.id || null;

        updateDragSignals({
          isDragging: true,
          elementId: elementId,
        });

        state.element.classList.add("is-dragging");
        document.body.classList.add("is-drag-active");

        state.element.style.width = `${state.dimensions.width}px`;
        state.element.style.height = `${state.dimensions.height}px`;
      }

      throttledUpdatePosition();
    };

    const handlePointerUp = () => {
      if (!state.element) {
        cleanup();
        return;
      }

      if (state.isDragging) {
        updateDragSignals({
          isDragging: false,
          elementId: null,
          dropZone: null,
        });

        if (config.mode === "sortable") {
          const dropZone = document.querySelector("[data-drop-zone].drop-zone-active");
          if (dropZone && state.element) {
            const sourceZone = state.element.parentElement?.closest("[data-drop-zone]");
            const sourceZoneName = sourceZone?.getAttribute("data-drop-zone");

            const insertBefore = findInsertPosition(dropZone, state.current.y, state.element);

            if (insertBefore) {
              dropZone.insertBefore(state.element, insertBefore);
            } else {
              dropZone.appendChild(state.element);
            }

            if (sourceZoneName && sourceZone) {
              mergePatch({
                [`zone_${sourceZoneName}_items`]: getDropZoneItems(sourceZone),
              });
            }

            const targetZoneName = dropZone.getAttribute("data-drop-zone");
            if (targetZoneName) {
              mergePatch({
                [`zone_${targetZoneName}_items`]: getDropZoneItems(dropZone),
              });
            }
          }
        } else if (config.mode === "freeform") {
          updateDropZoneTracking(config, mergePatch);
        }
      }

      cleanup();
    };

    const cleanup = () => {
      if (boundPointerMove) {
        document.removeEventListener("pointermove", boundPointerMove);
        boundPointerMove = null;
      }
      if (boundPointerUp) {
        document.removeEventListener("pointerup", boundPointerUp);
        boundPointerUp = null;
      }

      if (state.element) {
        state.element.classList.remove("is-dragging");

        const canvasContainer = state.element.closest("[data-canvas-container]");

        const baseStyles = {
          zIndex: "",
          pointerEvents: "",
          willChange: "",
          width: "",
          height: "",
        };

        if (canvasContainer) {
          Object.assign(state.element.style, baseStyles);
        } else {
          const relativeParent = findRelativeParent(state.element);

          Object.assign(
            state.element.style,
            relativeParent && relativeParent !== document.body
              ? baseStyles
              : { ...baseStyles, position: "", transform: "", left: "", top: "" }
          );
        }
      }

      document.body.classList.remove("is-drag-active");
      for (const el of document.querySelectorAll(".drop-zone-active")) {
        el.classList.remove("drop-zone-active");
      }

      if (state.placeholder) {
        state.placeholder.remove();
        state.placeholder = null;
      }

      state.element = null;
      state.isDragging = false;
      state.hasMoved = false;
    };

    document.addEventListener("pointerdown", handlePointerDown);

    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      cleanup();
    };
  },
};

const dragPlugin = {
  ...dragAttributePlugin,
  argNames,
  setConfig(config: any) {
    (window as any).__starhtml_drag_config = config;
  },
};

export default dragPlugin;
