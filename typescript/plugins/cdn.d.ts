/**
 * Type declarations for CDN modules (resolved at runtime).
 */

declare module "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js" {
  export function parse(src: string): string;
  export const marked: { parse: typeof parse };
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

  interface AnimationOptions {
    duration?: number;
    delay?: number;
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
    callback: (element: Element, entry: IntersectionObserverEntry) => void | ((leaveEntry: IntersectionObserverEntry) => void),
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
    callback: (element: Element, startEvent: PointerEvent) => void | ((endEvent: PointerEvent) => void),
    options?: GestureOptions
  ): () => void;

  /**
   * Detects press/tap gestures with automatic keyboard accessibility.
   * Filters out right clicks and secondary touch points.
   * Returns a cancel function that removes all event listeners.
   */
  export function press(
    target: AnimationTarget,
    callback: (element: Element, startEvent: PointerEvent) => void | ((endEvent: PointerEvent) => void),
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
