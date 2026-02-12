/**
 * Type declarations for CDN modules (resolved at runtime).
 */

declare module "https://cdn.jsdelivr.net/npm/@floating-ui/dom@1/+esm" {
  type Side = "top" | "bottom" | "left" | "right";
  type Alignment = "start" | "end";
  export type Placement = Side | `${Side}-${Alignment}`;
  export type Strategy = "absolute" | "fixed";

  export interface Middleware {
    name: string;
    fn(state: MiddlewareState): Promise<MiddlewareReturn> | MiddlewareReturn;
    options?: any;
  }

  interface MiddlewareState {
    x: number;
    y: number;
    placement: Placement;
    strategy: Strategy;
    elements: { reference: Element; floating: HTMLElement };
    rects: { reference: Rect; floating: Rect };
    middlewareData: Record<string, any>;
  }

  interface MiddlewareReturn {
    x?: number;
    y?: number;
    data?: Record<string, any>;
    reset?: boolean | { placement?: Placement };
  }

  interface Rect {
    x: number;
    y: number;
    width: number;
    height: number;
  }

  interface ComputePositionReturn {
    x: number;
    y: number;
    placement: Placement;
    strategy: Strategy;
    middlewareData: Record<string, any>;
  }

  interface ComputePositionConfig {
    placement?: Placement;
    strategy?: Strategy;
    middleware?: Middleware[];
  }

  export function computePosition(
    reference: Element | { getBoundingClientRect(): DOMRect; contextElement?: Element },
    floating: HTMLElement,
    config?: ComputePositionConfig
  ): Promise<ComputePositionReturn>;

  interface AutoUpdateOptions {
    ancestorScroll?: boolean;
    ancestorResize?: boolean;
    elementResize?: boolean;
    layoutShift?: boolean;
    animationFrame?: boolean;
  }

  export function autoUpdate(
    reference: Element,
    floating: HTMLElement,
    update: () => void,
    options?: AutoUpdateOptions
  ): () => void;

  export function offset(
    value?: number | { mainAxis?: number; crossAxis?: number }
  ): Middleware;

  export function flip(options?: { padding?: number; fallbackPlacements?: Placement[] }): Middleware;

  export function shift(options?: { padding?: number; limiter?: any }): Middleware;

  export function hide(options?: { strategy?: "referenceHidden" | "escaped" }): Middleware;

  export function size(options?: {
    apply?: (state: {
      availableWidth: number;
      availableHeight: number;
      elements: { floating: HTMLElement };
    }) => void;
    padding?: number;
  }): Middleware;
}

declare module "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js" {
  export function parse(src: string): string;
  export function parseInline(src: string): string;
  export const marked: { parse: typeof parse; parseInline: typeof parseInline };
}

declare module "https://cdn.jsdelivr.net/npm/katex/dist/katex.mjs" {
  interface RenderOptions {
    throwOnError?: boolean;
    displayMode?: boolean;
    output?: "html" | "mathml" | "htmlAndMathml";
    trust?: boolean;
  }
  export function renderToString(tex: string, options?: RenderOptions): string;
  const katex: { renderToString: typeof renderToString };
  export default katex;
}

declare module "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs" {
  interface MermaidConfig {
    startOnLoad?: boolean;
    theme?: string;
    securityLevel?: string;
    flowchart?: {
      useMaxWidth?: boolean;
      useMaxHeight?: boolean;
      htmlLabels?: boolean;
      curve?: string;
    };
  }
  export function initialize(config: MermaidConfig): void;
  export function render(
    id: string,
    definition: string
  ): Promise<{ svg: string; bindFunctions?: (el: Element) => void }>;
  const mermaid: { initialize: typeof initialize; render: typeof render };
  export default mermaid;
}

declare module "https://cdn.jsdelivr.net/npm/motion@11/+esm" {
  type Easing = string | [number, number, number, number];

  type StaggerFunction = (index: number, total: number) => number;

  interface AnimationOptions {
    duration?: number;
    delay?: number | StaggerFunction;
    ease?: Easing;
    type?: "tween" | "spring" | "inertia";
    stiffness?: number;
    damping?: number;
    mass?: number;
    bounce?: number;
    velocity?: number;
    repeat?: number;
    repeatType?: "loop" | "reverse" | "mirror";
    repeatDelay?: number;
  }

  interface AnimationControls {
    play(): void;
    pause(): void;
    stop(): void;
    cancel(): void;
    complete(): void;
    finished: Promise<void>;
    time: number;
    speed: number;
  }

  type AnimationTarget = string | Element | Element[] | NodeListOf<Element>;
  type Keyframes = Record<string, number | string | number[] | string[]>;

  export function animate(
    target: AnimationTarget,
    keyframes: Keyframes,
    options?: AnimationOptions
  ): AnimationControls;

  export function stagger(
    duration: number,
    options?: { start?: number; from?: number | "first" | "last" | "center" }
  ): (index: number, total: number) => number;

  interface ScrollOptions {
    target?: Element;
    offset?: [string, string];
    smooth?: number;
  }

  export function scroll(
    animation: AnimationControls | ((progress: number) => void),
    options?: ScrollOptions
  ): () => void;

  /**
   * Detects when elements enter/leave the viewport using IntersectionObserver.
   * Returns a cancel function that removes the observer.
   */
  export function inView(
    target: AnimationTarget,
    callback: (
      element: Element,
      entry: IntersectionObserverEntry
    ) => void | ((leaveEntry: IntersectionObserverEntry) => void),
    options?: { margin?: string; amount?: "some" | "all" | number }
  ): () => void;

  interface GestureOptions {
    passive?: boolean;
    once?: boolean;
  }

  /**
   * Detects hover gestures, filtering out fake events from touch devices.
   * Returns a cancel function that removes all event listeners.
   */
  export function hover(
    target: AnimationTarget,
    callback: (
      element: Element,
      startEvent: PointerEvent
    ) => void | ((endEvent: PointerEvent) => void),
    options?: GestureOptions
  ): () => void;

  /**
   * Detects press/tap gestures with automatic keyboard accessibility.
   * Filters out right clicks and secondary touch points.
   * Returns a cancel function that removes all event listeners.
   */
  export function press(
    target: AnimationTarget,
    callback: (
      element: Element,
      startEvent: PointerEvent
    ) => void | ((endEvent: PointerEvent) => void),
    options?: GestureOptions
  ): () => void;

  interface ResizeInfo {
    width: number;
    height: number;
  }

  /**
   * Observes element size changes using ResizeObserver.
   * Returns a cancel function that removes the observer.
   */
  export function resize(
    target: AnimationTarget,
    callback: (element: Element, info: ResizeInfo) => void
  ): () => void;

  export const spring: AnimationOptions;
}

declare module "https://cdn.jsdelivr.net/npm/flubber@0.4.2/+esm" {
  type Shape = string | number[][];

  interface InterpolateOptions {
    /** Return path string (true) or coordinate array (false). Default: true */
    string?: boolean;
    /** Smoothing parameter in pixels. Lower = smoother but slower. Default: 10 */
    maxSegmentLength?: number;
  }

  /** Interpolate between two shapes (path strings or point arrays) */
  export function interpolate(
    fromShape: Shape,
    toShape: Shape,
    options?: InterpolateOptions
  ): (t: number) => string;

  /** Morph from a shape to a circle */
  export function toCircle(
    fromShape: Shape,
    cx: number,
    cy: number,
    r: number,
    options?: InterpolateOptions
  ): (t: number) => string;

  /** Morph from a circle to a shape */
  export function fromCircle(
    cx: number,
    cy: number,
    r: number,
    toShape: Shape,
    options?: InterpolateOptions
  ): (t: number) => string;

  /** Morph from a shape to a rectangle */
  export function toRect(
    fromShape: Shape,
    x: number,
    y: number,
    width: number,
    height: number,
    options?: InterpolateOptions
  ): (t: number) => string;

  /** Morph from a rectangle to a shape */
  export function fromRect(
    x: number,
    y: number,
    width: number,
    height: number,
    toShape: Shape,
    options?: InterpolateOptions
  ): (t: number) => string;

  interface MultiShapeOptions extends InterpolateOptions {
    /** Return single combined interpolator (true) or array of interpolators (false) */
    single?: boolean;
  }

  /** Split one shape into multiple shapes */
  export function separate(
    fromShape: Shape,
    toShapes: Shape[],
    options?: MultiShapeOptions
  ): ((t: number) => string) | ((t: number) => string)[];

  /** Combine multiple shapes into one */
  export function combine(
    fromShapes: Shape[],
    toShape: Shape,
    options?: MultiShapeOptions
  ): ((t: number) => string) | ((t: number) => string)[];

  /** Interpolate between two arrays of shapes */
  export function interpolateAll(
    fromShapes: Shape[],
    toShapes: Shape[],
    options?: MultiShapeOptions
  ): ((t: number) => string) | ((t: number) => string)[];

  /** Convert point array to SVG path string */
  export function toPathString(ring: number[][]): string;

  /** Split multi-shape path string into array of single-shape strings */
  export function splitPathString(pathString: string): string[];
}
