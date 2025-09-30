import { createRAFThrottle, createTimerThrottle } from "./throttle.js";

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

// Dynamic signal names based on config.signal
function getDragArgNames(signal = "drag"): string[] {
  return [
    `${signal}_is_dragging`,
    `${signal}_element_id`,
    `${signal}_x`,
    `${signal}_y`,
    `${signal}_drop_zone`,
  ];
}

const DEFAULT_THROTTLE = 16;

const parseTransform = (transform: string): { pan: { x: number; y: number }; scale: number } => {
  if (!transform || transform === "none") {
    return { pan: { x: 0, y: 0 }, scale: 1 };
  }

  // Try to match translate(x, y) scale(z) format first
  let matches = transform.match(/translate\(([^,]+),\s*([^)]+)\)\s*scale\(([^)]+)\)/);
  if (matches) {
    return {
      pan: {
        x: Number.parseFloat(matches[1]),
        y: Number.parseFloat(matches[2]),
      },
      scale: Number.parseFloat(matches[3]),
    };
  }

  // Try to match matrix format: matrix(a, b, c, d, tx, ty)
  // where a = scale x, d = scale y, tx = translate x, ty = translate y
  matches = transform.match(/matrix\(([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^)]+)\)/);
  if (matches) {
    return {
      pan: {
        x: Number.parseFloat(matches[5]), // tx
        y: Number.parseFloat(matches[6]), // ty
      },
      scale: Number.parseFloat(matches[1]), // a (scale x)
    };
  }

  return { pan: { x: 0, y: 0 }, scale: 1 };
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

    const sig = _config.signal ?? "drag";
    mergePatch({
      [`${sig}_zone_${zoneName}_items`]: items,
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

function ensureAndPlacePlaceholder(state: DragState & { placeholder?: HTMLElement | null }, dropZone: Element) {
  if (!state.element) return;
  if (!state.placeholder) {
    state.placeholder = document.createElement("div");
    state.placeholder.className = "drag-placeholder";
    state.placeholder.style.opacity = "0.5";
    state.placeholder.style.border = "2px dashed #3b82f6";
    state.placeholder.style.borderRadius = "8px";
    state.placeholder.style.boxSizing = "border-box";
  }
  const height = `${state.dimensions.height}px`;
  if (state.placeholder.style.height !== height) {
    state.placeholder.style.height = height;
  }
  state.placeholder.style.margin = window.getComputedStyle(state.element).margin;

  const insertBefore = findInsertPosition(dropZone, state.current.y, state.element);
  if (insertBefore) {
    dropZone.insertBefore(state.placeholder, insertBefore);
  } else if (state.placeholder.parentElement !== dropZone) {
    dropZone.appendChild(state.placeholder);
  }
}

// Global drag manager: single delegated pointerdown, shared active state
type Registration = {
  el: HTMLElement;
  mods: Map<string, any>;
  mergePatch: RuntimeContext["mergePatch"];
  startBatch: RuntimeContext["startBatch"];
  endBatch: RuntimeContext["endBatch"];
};

type ActiveDrag = {
  ctx: Registration;
  sig: string;
  debug: boolean;
  config: DragConfig;
  state: DragState & { placeholder?: HTMLElement | null };
  lastSent: Record<string, any>;
  throttledUpdatePosition: () => void;
  throttledZoneScan: () => void;
};

const registrations: Registration[] = [];
let globalPointerDownAttached = false;
let active: ActiveDrag | null = null;

function getGlobalConfig(): DragConfig {
  const cfg = (window as any).__starhtml_drag_config || {};
  return {
    signal: cfg.signal ?? "drag",
    mode: cfg.mode ?? "freeform",
    throttleMs: cfg.throttleMs ?? DEFAULT_THROTTLE,
    constrainToParent: cfg.constrainToParent ?? false,
  } as DragConfig;
}

function findRegistrationFor(draggableEl: HTMLElement): Registration | null {
  let node: HTMLElement | null = draggableEl;
  while (node && node !== document.body) {
    const reg = registrations.find(r => r.el === node) || null;
    if (reg) {
      const isDirectHandler = reg.el.hasAttribute("data-draggable");
      if (!isDirectHandler || reg.el === draggableEl) {
        return reg;
      }
    }
    node = node.parentElement;
  }
  return null;
}

function computeAndMergeIfChanged(ctx: Registration, _debug: boolean, last: Record<string, any>, updates: Record<string, any>) {
  const patch: Record<string, any> = {};
  for (const k of Object.keys(updates)) {
    if (last[k] !== updates[k]) {
      patch[k] = updates[k];
      last[k] = updates[k];
    }
  }
  if (Object.keys(patch).length === 0) return;
  ctx.startBatch();
  try {
    ctx.mergePatch(patch);
        
      } finally {
    ctx.endBatch();
  }
      }

function updateDragPositionActive() {
  if (!active) return;
  const { ctx, state, sig, config } = active;
      if (!state.element || !state.isDragging) return;

      const { x, y } = state.current;

      const canvasContainer = state.element.closest("[data-canvas-container]");
      const canvasViewport = document.querySelector("[data-canvas-viewport]");

      let finalX: number;
      let finalY: number;

  const useCanvas = Boolean(canvasContainer && canvasViewport);
  const relativeParent = useCanvas ? null : findRelativeParent(state.element);
  const useRelative = Boolean(!useCanvas && relativeParent && relativeParent !== document.body);

  if (useCanvas && canvasContainer && canvasViewport) {
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
          transform: "",
          transformOrigin: "top left",
        });
  } else if (useRelative && relativeParent) {
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

      if (state.element) {
        state.element.style.pointerEvents = "none";
        const dropZone = findDropZone(state.current.x, state.current.y);
        state.element.style.pointerEvents = "";

        const dropZoneName = dropZone?.getAttribute("data-drop-zone") ?? null;
        const elementId = state.element.id || state.element.dataset.id || null;

    computeAndMergeIfChanged(
      ctx,
      active.debug,
      active.lastSent,
      {
          [`${sig}_is_dragging`]: true,
          [`${sig}_element_id`]: elementId,
          [`${sig}_x`]: finalX,
          [`${sig}_y`]: finalY,
          [`${sig}_drop_zone`]: dropZoneName,
      }
    );

        for (const zone of document.querySelectorAll("[data-drop-zone]")) {
          zone.classList.toggle("drop-zone-active", zone === dropZone);
        }

        if (config.mode === "sortable" && dropZone) {
          ensureAndPlacePlaceholder(state, dropZone);
        }
      }

      if (state.isDragging && config.mode === "freeform") {
    active.throttledZoneScan();
  }
}

function cleanupActiveDrag() {
  if (!active) return;

  document.removeEventListener("pointermove", handleGlobalPointerMove);
  document.removeEventListener("pointerup", handleGlobalPointerUp);

  const { state } = active;
  if (state.element) {
    state.element.classList.remove("is-dragging");

    const canvasContainer = state.element.closest("[data-canvas-container]");

    const baseStyles = {
      zIndex: "",
      pointerEvents: "",
      willChange: "",
      width: "",
      height: "",
    } as Record<string, string>;

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

  active = null;
}

function handleGlobalPointerMove(evt: PointerEvent) {
  if (!active || !active.state.element) return;
  const { state } = active;
      state.current = { x: evt.clientX, y: evt.clientY };

      const deltaX = state.current.x - state.startPoint.x;
      const deltaY = state.current.y - state.startPoint.y;
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

      if (!state.hasMoved && distance < 5) return;

      if (!state.hasMoved) {
        state.hasMoved = true;
        state.isDragging = true;

    const element = state.element as HTMLElement;
    const elementId = element.id || element.dataset.id || null;

    computeAndMergeIfChanged(
      active.ctx,
      active.debug,
      active.lastSent,
      {
        [`${active.sig}_is_dragging`]: true,
        [`${active.sig}_element_id`]: elementId,
      }
    );

    element.classList.add("is-dragging");
        document.body.classList.add("is-drag-active");

    // Don't set explicit dimensions for canvas elements
    const isCanvasElement = Boolean(element.closest("[data-canvas-container]"));
    if (!isCanvasElement) {
      element.style.width = `${state.dimensions.width}px`;
      element.style.height = `${state.dimensions.height}px`;
    }
      }

  active.throttledUpdatePosition();
}

function handleGlobalPointerUp() {
  if (!active) {
    cleanupActiveDrag();
        return;
      }

  const { ctx, state, config, sig } = active;

      if (state.isDragging) {
    computeAndMergeIfChanged(ctx, active.debug, active.lastSent, {
          [`${sig}_is_dragging`]: false,
          [`${sig}_element_id`]: null,
          [`${sig}_drop_zone`]: null,
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
              const srcPatch = { [`${sig}_zone_${sourceZoneName}_items`]: getDropZoneItems(sourceZone) } as Record<string, any>;
          ctx.mergePatch(srcPatch);
          
            }

            const targetZoneName = dropZone.getAttribute("data-drop-zone");
            if (targetZoneName) {
              const tgtPatch = { [`${sig}_zone_${targetZoneName}_items`]: getDropZoneItems(dropZone) } as Record<string, any>;
          ctx.mergePatch(tgtPatch);
          
            }
          }
        } else if (config.mode === "freeform") {
      updateDropZoneTracking(config, ctx.mergePatch);
    }
  }

  cleanupActiveDrag();
}

function handleGlobalPointerDown(evt: PointerEvent) {
  const target = evt.target as HTMLElement;
  const draggableElement = target.closest?.("[data-draggable]") as HTMLElement | null;
  if (!draggableElement) return;

  const reg = findRegistrationFor(draggableElement);
  if (!reg) return;

  evt.preventDefault();

  const config = getGlobalConfig();
  const sig = config.signal ?? "drag";
  const debug = reg.mods.has("debug");

  const rect = draggableElement.getBoundingClientRect();

  const canvasContainer = draggableElement.closest("[data-canvas-container]");
  const canvasViewport = document.querySelector("[data-canvas-viewport]");

  let offset: { x: number; y: number };
  if (canvasContainer && canvasViewport) {
    const viewportRect = canvasViewport.getBoundingClientRect();
    const transform = parseTransform(window.getComputedStyle(canvasContainer).transform);        
    const elementStyle = window.getComputedStyle(draggableElement);
    const elementCanvasX = Number.parseFloat(elementStyle.left) || 0;
    const elementCanvasY = Number.parseFloat(elementStyle.top) || 0;
    
    const clickInCanvas = calculateCanvasPosition(
      evt.clientX,
      evt.clientY,
      viewportRect,
      transform,
      { x: 0, y: 0 }
    );
    
    offset = { 
      x: (clickInCanvas.x - elementCanvasX) * transform.scale, 
      y: (clickInCanvas.y - elementCanvasY) * transform.scale 
    };
  } else {
    offset = { x: evt.clientX - rect.left, y: evt.clientY - rect.top };
  }

  const state: DragState & { placeholder?: HTMLElement | null } = {
    isDragging: false,
    element: draggableElement,
    hasMoved: false,
    startPoint: { x: evt.clientX, y: evt.clientY },
    offset: offset,
    current: { x: evt.clientX, y: evt.clientY },
    dimensions: { width: rect.width, height: rect.height },
  };

  const throttledUpdatePosition = createRAFThrottle(updateDragPositionActive);
  const zoneThrottle = Math.max(100, Number(config.throttleMs || 0) || 0);
  const throttledZoneScan = createTimerThrottle(() => updateDropZoneTracking(config, reg.mergePatch), zoneThrottle);

  active = {
    ctx: reg,
    sig,
    debug,
    config,
    state,
    lastSent: {},
    throttledUpdatePosition,
    throttledZoneScan,
  };

  document.addEventListener("pointermove", handleGlobalPointerMove);
  document.addEventListener("pointerup", handleGlobalPointerUp);
}

function attachGlobalPointerDown() {
  if (globalPointerDownAttached) return;
  document.addEventListener("pointerdown", handleGlobalPointerDown);
  globalPointerDownAttached = true;
}

function detachGlobalPointerDown() {
  if (!globalPointerDownAttached) return;
  document.removeEventListener("pointerdown", handleGlobalPointerDown);
  globalPointerDownAttached = false;
}

const dragAttributePlugin: AttributePlugin = {
  type: "attribute",
  name: "draggable",
  keyReq: "starts",
  valReq: "allowed",
  shouldEvaluate: false,

  onLoad(ctx: RuntimeContext): OnRemovalFn | void {
    const { el, mergePatch, mods, startBatch, endBatch } = ctx;

    const config = getGlobalConfig();
    const sig = config.signal ?? "drag";
  

    const initPatch = {
      [`${sig}_is_dragging`]: false,
      [`${sig}_element_id`]: null,
      [`${sig}_x`]: 0,
      [`${sig}_y`]: 0,
      [`${sig}_drop_zone`]: null,
    } as Record<string, any>;
    mergePatch(initPatch);
    

    const dropZoneName = el.getAttribute("data-drop-zone");
    if (dropZoneName) {
      const zonePatch = { [`${sig}_zone_${dropZoneName}_items`]: getDropZoneItems(el) } as Record<string, any>;
      mergePatch(zonePatch);
      
    }

    const registration: Registration = { el, mods, mergePatch, startBatch, endBatch };
    registrations.push(registration);
    attachGlobalPointerDown();

    return () => {
      const idx = registrations.findIndex(r => r.el === el);
      if (idx >= 0) registrations.splice(idx, 1);
      if (registrations.length === 0) {
        detachGlobalPointerDown();
      }
    };
  },
};

const dragPlugin = {
  ...dragAttributePlugin,
  argNames: [] as string[],
  setConfig(config: any) {
    (window as any).__starhtml_drag_config = config;
    const signal = config?.signal ? String(config.signal) : "drag";
    (this as any).argNames = getDragArgNames(signal);
  },
};

export default dragPlugin;
