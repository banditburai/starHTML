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
interface Point {
  x: number;
  y: number;
}
interface Camera {
  x: number;
  y: number;
  z: number;
}
interface CanvasConfig {
  signal: string;
  enablePan: boolean;
  enableZoom: boolean;
  minZoom: number;
  maxZoom: number;
  touchEnabled: boolean;
  contextMenuEnabled: boolean;
  spacebarPan: boolean;
  middleClickPan: boolean;
}
interface GestureState {
  pointers: Map<number, PointerEvent>;
  initialDistance?: number;
  initialCenter?: Point;
  initialCamera?: Camera;
  fixedWorldPoint?: Point;
  isGesturing: boolean;
  mode: "none" | "pan" | "pinch";
}
declare global {
  interface Window {
    __starhtml_canvas_config?: CanvasConfig;
  }
}
function parseConfig(config: any): CanvasConfig {
  return {
    signal: config?.signal || "canvas",
    enablePan: config?.enablePan !== false,
    enableZoom: config?.enableZoom !== false,
    minZoom: config?.minZoom || 0.01,
    maxZoom: config?.maxZoom || 100.0,
    touchEnabled: config?.touchEnabled !== false,
    contextMenuEnabled: config?.contextMenuEnabled !== false,
    spacebarPan: config?.spacebarPan !== false,
    middleClickPan: config?.middleClickPan !== false,
  };
}
const ZOOM_FACTOR = 1.2;
const WHEEL_ZOOM_IN = 1.05;
const WHEEL_ZOOM_OUT = 0.95;

class CanvasController {
  private camera: Camera = { x: 0, y: 0, z: 1.0 };
  private viewport: HTMLElement | null = null;
  private container: HTMLElement | null = null;
  private config: CanvasConfig;
  private gestureState: GestureState = {
    pointers: new Map(),
    isGesturing: false,
    mode: "none",
  };
  private isPanning = false;
  private lastPanPoint: Point | null = null;
  private isSpacePressed = false;
  private rafId: number | null = null;
  private needsRender = false;
  private lastViewportWidth = 0;
  private lastViewportHeight = 0;
  private resizeObserver: ResizeObserver | null = null;
  private boundHandlePointerDown = this.handlePointerDown.bind(this);
  private boundHandleWheel = this.handleWheel.bind(this);
  private boundHandleKeyDown = this.handleKeyDown.bind(this);
  private boundHandleKeyUp = this.handleKeyUp.bind(this);
  private boundHandleContextMenu = this.handleContextMenu.bind(this);
  private boundHandlePointerMove = this.handlePointerMove.bind(this);
  private boundHandlePointerUp = this.handlePointerUp.bind(this);
  constructor(
    private ctx: RuntimeContext,
    config: CanvasConfig
  ) {
    this.config = config;
    this.setupEventListeners();
    this.initializeDOMElements();
    this.startRenderLoop();
  }
  private setupEventListeners() {
    document.addEventListener("pointerdown", this.boundHandlePointerDown);
    document.addEventListener("wheel", this.boundHandleWheel, { passive: false });
    if (this.config.spacebarPan) {
      document.addEventListener("keydown", this.boundHandleKeyDown);
      document.addEventListener("keyup", this.boundHandleKeyUp);
    }
    if (this.config.contextMenuEnabled) {
      document.addEventListener("contextmenu", this.boundHandleContextMenu);
    }
  }
  private initializeDOMElements() {
    requestAnimationFrame(() => {
      this.viewport = document.querySelector("[data-canvas-viewport]") as HTMLElement;
      this.container = document.querySelector("[data-canvas-container]") as HTMLElement;
      if (this.viewport) {
        this.setupViewportStyles();
        this.setupResizeObserver();
        this.centerCanvas();
      }
      this.scheduleRender();
    });
  }
  private centerCanvas() {
    if (!this.viewport) return;
    const rect = this.viewport.getBoundingClientRect();
    const viewportWidth = rect.width;
    const viewportHeight = rect.height;
    this.camera.x = viewportWidth / 2 / this.camera.z;
    this.camera.y = viewportHeight / 2 / this.camera.z;
  }
  private setupResizeObserver() {
    if (!this.viewport) return;
    const rect = this.viewport.getBoundingClientRect();
    this.lastViewportWidth = rect.width;
    this.lastViewportHeight = rect.height;
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        this.handleViewportResize(entry.contentRect);
      }
    });
    resizeObserver.observe(this.viewport);
    this.resizeObserver = resizeObserver;
  }
  private handleViewportResize(rect: DOMRectReadOnly) {
    const newWidth = rect.width;
    const newHeight = rect.height;
    if (newWidth === this.lastViewportWidth && newHeight === this.lastViewportHeight) {
      return;
    }
    if (newWidth === 0 || newHeight === 0) {
      return;
    }
    const oldCenterX = this.lastViewportWidth / 2;
    const oldCenterY = this.lastViewportHeight / 2;
    const worldCenterX = oldCenterX / this.camera.z - this.camera.x;
    const worldCenterY = oldCenterY / this.camera.z - this.camera.y;
    const newCenterX = newWidth / 2;
    const newCenterY = newHeight / 2;
    this.camera.x = newCenterX / this.camera.z - worldCenterX;
    this.camera.y = newCenterY / this.camera.z - worldCenterY;
    this.lastViewportWidth = newWidth;
    this.lastViewportHeight = newHeight;
    this.scheduleRender();
  }
  private setupViewportStyles() {
    if (!this.viewport) return;
    Object.assign(this.viewport.style, {
      userSelect: "none",
      webkitUserSelect: "none",
      touchAction: "none",
      cursor: "grab",
      willChange: "transform",
      ...(window.devicePixelRatio > 1 && { imageRendering: "pixelated" }),
    });
  }
  private handlePointerDown(evt: PointerEvent) {
    const target = evt.target as HTMLElement;
    const draggableElement = target.closest("[data-draggable]");
    if (draggableElement) {
      return;
    }
    const viewport = target.closest("[data-canvas-viewport]") as HTMLElement;
    if (!viewport || !this.config.enablePan) return;
    this.viewport = viewport;
    this.gestureState.pointers.set(evt.pointerId, evt);
    const pointerCount = this.gestureState.pointers.size;
    if (pointerCount === 1) {
      this.handleSinglePointerDown(evt);
    } else if (pointerCount === 2) {
      this.handleMultiTouchStart();
    }
  }
  private handleSinglePointerDown(evt: PointerEvent) {
    const isLeftClick = evt.button === 0;
    const isMiddleClick = evt.button === 1 && this.config.middleClickPan;
    const isSpacePan = this.isSpacePressed && isLeftClick;
    if (!isLeftClick && !isMiddleClick && !isSpacePan) return;
    evt.preventDefault();
    this.startPanning(evt);
  }
  private handleMultiTouchStart() {
    if (!this.config.touchEnabled) return;
    const pointers = Array.from(this.gestureState.pointers.values());
    if (pointers.length !== 2) return;
    this.gestureState.mode = "pinch";
    this.gestureState.isGesturing = true;
    this.gestureState.initialDistance = this.getDistance(pointers[0], pointers[1]);
    this.gestureState.initialCenter = this.getCenter(pointers[0], pointers[1]);
    this.gestureState.initialCamera = { ...this.camera };
    if (this.viewport) {
      const rect = this.viewport.getBoundingClientRect();
      const screenPoint = {
        x: this.gestureState.initialCenter.x - rect.left,
        y: this.gestureState.initialCenter.y - rect.top,
      };
      this.gestureState.fixedWorldPoint = this.screenToCanvas(screenPoint);
    }
    this.stopPanning();
  }
  private startPanning(evt: PointerEvent) {
    this.isPanning = true;
    this.gestureState.mode = "pan";
    this.lastPanPoint = { x: evt.clientX, y: evt.clientY };
    if (this.viewport) {
      this.viewport.style.cursor = "grabbing";
    }
    document.addEventListener("pointermove", this.boundHandlePointerMove);
    document.addEventListener("pointerup", this.boundHandlePointerUp);
    document.addEventListener("pointercancel", this.boundHandlePointerUp);
  }
  private stopPanning() {
    this.isPanning = false;
    this.lastPanPoint = null;
    if (this.viewport) {
      this.viewport.style.cursor = "grab";
    }
    document.removeEventListener("pointermove", this.boundHandlePointerMove);
    document.removeEventListener("pointerup", this.boundHandlePointerUp);
    document.removeEventListener("pointercancel", this.boundHandlePointerUp);
  }
  private handlePointerMove(evt: PointerEvent) {
    this.gestureState.pointers.set(evt.pointerId, evt);
    if (this.gestureState.mode === "pan" && this.isPanning) {
      this.handlePanMove(evt);
    } else if (this.gestureState.mode === "pinch" && this.gestureState.pointers.size === 2) {
      this.handlePinchMove();
    }
  }
  private handlePanMove(evt: PointerEvent) {
    if (!this.lastPanPoint) return;
    const deltaX = evt.clientX - this.lastPanPoint.x;
    const deltaY = evt.clientY - this.lastPanPoint.y;
    this.camera.x += deltaX / this.camera.z;
    this.camera.y += deltaY / this.camera.z;
    this.lastPanPoint = { x: evt.clientX, y: evt.clientY };
    this.scheduleRender();
  }
  private handlePinchMove() {
    const pointers = Array.from(this.gestureState.pointers.values());
    if (pointers.length !== 2) return;
    const currentDistance = this.getDistance(pointers[0], pointers[1]);
    const currentCenter = this.getCenter(pointers[0], pointers[1]);
    if (this.gestureState.initialDistance && this.gestureState.initialCamera && this.viewport) {
      const scaleFactor = currentDistance / this.gestureState.initialDistance;
      const targetZoom = this.clampZoom(this.gestureState.initialCamera.z * scaleFactor);
      const rect = this.viewport.getBoundingClientRect();
      const pinchScreenX = currentCenter.x - rect.left;
      const pinchScreenY = currentCenter.y - rect.top;
      if (targetZoom !== this.camera.z) {
        this.zoomAtPoint(pinchScreenX, pinchScreenY, targetZoom / this.camera.z);
      }
    }
  }
  private handlePointerUp(evt: PointerEvent) {
    this.gestureState.pointers.delete(evt.pointerId);
    if (this.gestureState.pointers.size === 0) {
      this.gestureState.mode = "none";
      this.gestureState.isGesturing = false;
      this.stopPanning();
    } else if (this.gestureState.pointers.size === 1 && this.gestureState.mode === "pinch") {
      const remainingPointer = Array.from(this.gestureState.pointers.values())[0];
      this.startPanning(remainingPointer);
    }
  }
  private handleWheel(evt: WheelEvent) {
    const target = evt.target as HTMLElement;
    const viewport = target.closest("[data-canvas-viewport]") as HTMLElement;
    if (!viewport || !this.config.enableZoom) return;
    evt.preventDefault();
    const rect = viewport.getBoundingClientRect();
    const mouseX = evt.clientX - rect.left;
    const mouseY = evt.clientY - rect.top;
    const zoomFactor = evt.deltaY > 0 ? WHEEL_ZOOM_OUT : WHEEL_ZOOM_IN;
    this.zoomAtPoint(mouseX, mouseY, zoomFactor);
  }
  private handleKeyDown(evt: KeyboardEvent) {
    if (evt.code === "Space" && this.config.spacebarPan) {
      evt.preventDefault();
      if (!this.isSpacePressed) {
        this.isSpacePressed = true;
        if (this.viewport) {
          this.viewport.style.cursor = "grab";
        }
      }
    }
    if ((evt.ctrlKey || evt.metaKey) && this.config.enableZoom) {
      const zoomActions: Record<string, () => void> = {
        "=": () => this.zoomAtCenter(ZOOM_FACTOR),
        "+": () => this.zoomAtCenter(ZOOM_FACTOR),
        "-": () => this.zoomAtCenter(1 / ZOOM_FACTOR),
        "0": () => this.resetView(),
      };

      const action = zoomActions[evt.key];
      if (action) {
        action();
        evt.preventDefault();
      }
    }
  }
  private handleKeyUp(evt: KeyboardEvent) {
    if (evt.code === "Space" && this.config.spacebarPan) {
      evt.preventDefault();
      this.isSpacePressed = false;
      if (this.viewport && !this.isPanning) {
        this.viewport.style.cursor = "grab";
      }
    }
  }
  private handleContextMenu(evt: MouseEvent) {
    const target = evt.target as HTMLElement;
    const viewport = target.closest("[data-canvas-viewport]") as HTMLElement;
    if (!viewport) return;
    evt.preventDefault();
    const rect = viewport.getBoundingClientRect();
    const canvasPoint = this.screenToCanvas({
      x: evt.clientX - rect.left,
      y: evt.clientY - rect.top,
    });
    this.ctx.mergePatch({
      [`${this.config.signal}_context_menu_x`]: canvasPoint.x,
      [`${this.config.signal}_context_menu_y`]: canvasPoint.y,
      [`${this.config.signal}_context_menu_screen_x`]: evt.clientX,
      [`${this.config.signal}_context_menu_screen_y`]: evt.clientY,
    });
  }
  private clampZoom(zoom: number): number {
    return Math.max(this.config.minZoom, Math.min(this.config.maxZoom, zoom));
  }
  private zoomAtPoint(screenX: number, screenY: number, zoomFactor: number) {
    const oldZoom = this.camera.z;
    const newZoom = this.clampZoom(oldZoom * zoomFactor);
    if (newZoom !== oldZoom) {
      const worldX = screenX / oldZoom - this.camera.x;
      const worldY = screenY / oldZoom - this.camera.y;
      this.camera.z = newZoom;
      this.camera.x = screenX / newZoom - worldX;
      this.camera.y = screenY / newZoom - worldY;
      this.scheduleRender();
    }
  }
  private zoomAtCenter(zoomFactor: number) {
    if (!this.viewport) return;
    const rect = this.viewport.getBoundingClientRect();
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    this.zoomAtPoint(centerX, centerY, zoomFactor);
  }
  private resetView() {
    this.camera.z = 1.0;
    this.centerCanvas();
    this.scheduleRender();
  }
  private zoomIn() {
    this.zoomAtCenter(ZOOM_FACTOR);
  }
  private zoomOut() {
    this.zoomAtCenter(1 / ZOOM_FACTOR);
  }
  private screenToCanvas(point: Point): Point {
    return {
      x: point.x / this.camera.z - this.camera.x,
      y: point.y / this.camera.z - this.camera.y,
    };
  }
  private canvasToScreen(point: Point): Point {
    return {
      x: (point.x + this.camera.x) * this.camera.z,
      y: (point.y + this.camera.y) * this.camera.z,
    };
  }
  private getDistance(pointer1: PointerEvent, pointer2: PointerEvent): number {
    return Math.sqrt(
      (pointer2.clientX - pointer1.clientX) ** 2 + (pointer2.clientY - pointer1.clientY) ** 2
    );
  }
  private getCenter(pointer1: PointerEvent, pointer2: PointerEvent): Point {
    return {
      x: (pointer1.clientX + pointer2.clientX) / 2,
      y: (pointer1.clientY + pointer2.clientY) / 2,
    };
  }
  private startRenderLoop() {
    const render = () => {
      if (this.needsRender) {
        this.updateTransform();
        this.updateSignals();
        this.needsRender = false;
      }
      this.rafId = requestAnimationFrame(render);
    };
    this.rafId = requestAnimationFrame(render);
  }
  private scheduleRender() {
    this.needsRender = true;
  }
  private updateTransform() {
    if (!this.container) return;
    const transform = `translate(${this.camera.x * this.camera.z}px, ${this.camera.y * this.camera.z}px) scale(${this.camera.z})`;
    this.container.style.transform = transform;
    this.container.style.transformOrigin = "0 0";
  }
  private updateSignals() {
    this.ctx.startBatch();
    try {
      this.ctx.mergePatch({
        [`${this.config.signal}_pan_x`]: this.camera.x,
        [`${this.config.signal}_pan_y`]: this.camera.y,
        [`${this.config.signal}_zoom`]: this.camera.z,
        [`${this.config.signal}_is_panning`]: this.isPanning,
        [`${this.config.signal}_reset_view`]: this.resetView.bind(this),
        [`${this.config.signal}_zoom_in`]: this.zoomIn.bind(this),
        [`${this.config.signal}_zoom_out`]: this.zoomOut.bind(this),
      });
      this.ctx.rx(this.camera.x, this.camera.y, this.camera.z, this.isPanning);
    } catch (error) {
      console.error("Error executing canvas handler:", error);
    } finally {
      this.ctx.endBatch();
    }
  }
  public destroy() {
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
    }
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
    document.removeEventListener("pointerdown", this.boundHandlePointerDown);
    document.removeEventListener("wheel", this.boundHandleWheel);
    document.removeEventListener("keydown", this.boundHandleKeyDown);
    document.removeEventListener("keyup", this.boundHandleKeyUp);
    document.removeEventListener("contextmenu", this.boundHandleContextMenu);
    this.stopPanning();
  }
}
const canvasAttributePlugin: AttributePlugin = {
  type: "attribute",
  name: "onCanvas",
  keyReq: "starts",
  onLoad(ctx: RuntimeContext): OnRemovalFn | void {
    const { value } = ctx;
    if (!value) return;
    const globalConfig = window.__starhtml_canvas_config;
    const config = parseConfig(globalConfig);
    const controller = new CanvasController(ctx, config);
    return () => {
      controller.destroy();
    };
  },
};
const canvasPlugin = {
  ...canvasAttributePlugin,
  setConfig(config: any) {
    window.__starhtml_canvas_config = config;
  },
};
export default canvasPlugin;
