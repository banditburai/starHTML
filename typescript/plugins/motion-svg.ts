import { interpolate as flubberInterpolate } from "https://cdn.jsdelivr.net/npm/flubber@0.4.2/+esm";
import { animate } from "https://cdn.jsdelivr.net/npm/motion@11/+esm";
import type { AnimationControls } from "https://cdn.jsdelivr.net/npm/motion@11/+esm";
import { effect, getPath } from "datastar";
import type { AttributeContext, AttributePlugin, OnRemovalFn } from "./types.js";

const SPRING_PRESETS: Record<string, { stiffness: number; damping: number }> = {
  gentle: { stiffness: 120, damping: 14 },
  bouncy: { stiffness: 300, damping: 10 },
  tight: { stiffness: 400, damping: 30 },
  slow: { stiffness: 50, damping: 20 },
  snappy: { stiffness: 500, damping: 25 },
};

const OPTION_KEYS = new Set(["duration", "delay", "ease", "spring", "name"]);

// Map kebab-case keys to correct SVG attribute casing (camelCase exceptions)
const SVG_ATTR_CASE: Record<string, string> = {
  "std-deviation": "stdDeviation",
  "base-frequency": "baseFrequency",
  "num-octaves": "numOctaves",
  "marker-width": "markerWidth",
  "marker-height": "markerHeight",
  "ref-x": "refX",
  "ref-y": "refY",
};

const NUMERIC_SVG_ATTRS = new Set([
  "height",
  "width",
  "x",
  "y",
  "x1",
  "x2",
  "y1",
  "y2",
  "cx",
  "cy",
  "r",
  "rx",
  "ry",
  "rotate",
  "scale",
  "translate-x",
  "translate-y",
  "skew-x",
  "skew-y",
  "stroke-width",
  "stroke-dashoffset",
  "stroke-dasharray",
  "stroke-miterlimit",
  "opacity",
  "fill-opacity",
  "stroke-opacity",
  "font-size",
  "font-weight",
  "letter-spacing",
  "word-spacing",
  "stop-offset",
  "offset",
  "viewbox-x",
  "viewbox-y",
  "viewbox-width",
  "viewbox-height",
  "stdDeviation",
  "baseFrequency",
  "numOctaves",
  "dx",
  "dy",
  "markerWidth",
  "markerHeight",
  "refX",
  "refY",
]);

interface SvgMotionConfig {
  duration: number;
  delay: number;
  /** Signal name for reactive duration (if set, reads from signal instead of duration) */
  durationSignal?: string;
  /** Signal name for reactive delay (if set, reads from signal instead of delay) */
  delaySignal?: string;
  ease?: string;
  spring?: string;
  name?: string;
  /** Map of SVG attribute -> signal name for numeric properties */
  properties: Map<string, string>;
  /** Signal name for path morphing (d attribute) */
  morphPath?: string;
}

interface AnimationState {
  currentValues: Map<string, number>;
  targetValues: Map<string, number>;
  activeAnimation: AnimationControls | null;
  proxyElement: HTMLDivElement | null;
  rafId: number | null;
  isAnimating: boolean;
}

interface MorphState {
  currentPath: string;
  targetPath: string;
  interpolator: ((t: number) => string) | null;
  activeAnimation: AnimationControls | null;
  proxyElement: HTMLDivElement | null;
  rafId: number | null;
  isAnimating: boolean;
}

interface AnimationLifecycle {
  activeAnimation: AnimationControls | null;
  proxyElement: HTMLDivElement | null;
  rafId: number | null;
  isAnimating: boolean;
}

function cancelActiveAnimation(state: AnimationLifecycle): void {
  if (state.activeAnimation) {
    state.activeAnimation.cancel();
    state.activeAnimation = null;
  }
  if (state.rafId) {
    cancelAnimationFrame(state.rafId);
    state.rafId = null;
  }
}

function ensureProxyElement(state: AnimationLifecycle): HTMLDivElement {
  if (!state.proxyElement) {
    state.proxyElement = document.createElement("div");
    state.proxyElement.style.cssText =
      "position:absolute;visibility:hidden;pointer-events:none;width:0;height:0;";
    document.body.appendChild(state.proxyElement);
  }
  return state.proxyElement;
}

function stopAnimationLoop(state: AnimationLifecycle): void {
  state.isAnimating = false;
  if (state.rafId) {
    cancelAnimationFrame(state.rafId);
    state.rafId = null;
  }
}

function parseMotionSvgAttribute(value: string): SvgMotionConfig {
  const config: SvgMotionConfig = {
    duration: 300,
    delay: 0,
    properties: new Map(),
  };

  const parts = value.match(/([a-zA-Z_-]+):([^\s]+)/g) || [];

  for (const part of parts) {
    const colonIdx = part.indexOf(":");
    if (colonIdx === -1) continue;

    const rawKey = part.slice(0, colonIdx).toLowerCase();
    const key = SVG_ATTR_CASE[rawKey] || rawKey;
    const val = part.slice(colonIdx + 1);

    if (OPTION_KEYS.has(key)) {
      if (key === "duration") {
        if (val.startsWith("$")) {
          config.durationSignal = val.slice(1);
        } else {
          config.duration = Number(val) || 300;
        }
      } else if (key === "delay") {
        if (val.startsWith("$")) {
          config.delaySignal = val.slice(1);
        } else {
          config.delay = Number(val) || 0;
        }
      } else if (key === "ease") config.ease = val;
      else if (key === "spring") config.spring = val;
      else if (key === "name") config.name = val;
    } else if (key === "d") {
      // Path morphing via Flubber
      config.morphPath = val.startsWith("$") ? val.slice(1) : val;
    } else if (NUMERIC_SVG_ATTRS.has(key)) {
      const signalName = val.startsWith("$") ? val.slice(1) : val;
      config.properties.set(key, signalName);
    } else {
      console.warn(`[motion-svg] Unknown or unsupported property: ${key}`);
    }
  }

  return config;
}

function getSignalValue(signalName: string): number {
  const value = getPath(signalName);
  return typeof value === "number" ? value : 0;
}

function getSignalStringValue(signalName: string): string {
  const value = getPath(signalName);
  return typeof value === "string" ? value : "";
}

function buildAnimationOptions(config: SvgMotionConfig): Record<string, unknown> {
  // Resolve duration from signal if specified, otherwise use static value
  const duration = config.durationSignal
    ? getSignalValue(config.durationSignal) || config.duration
    : config.duration;
  const options: Record<string, unknown> = { duration: duration / 1000 };

  // Resolve delay from signal if specified, otherwise use static value
  const delay = config.delaySignal
    ? getSignalValue(config.delaySignal) || config.delay
    : config.delay;
  if (delay > 0) options.delay = delay / 1000;

  if (config.spring && SPRING_PRESETS[config.spring]) {
    const preset = SPRING_PRESETS[config.spring];
    Object.assign(options, { type: "spring", ...preset });
  } else if (config.ease) {
    options.ease = config.ease;
  }

  return options;
}

function getCurrentAttributeValue(el: SVGElement, attr: string): number {
  const value = el.getAttribute(attr);
  if (value === null) return 0;

  if (attr === "stroke-dasharray") {
    return Number.parseFloat(value.split(/[\s,]+/)[0]) || 0;
  }
  if (attr === "font-weight") {
    const weights: Record<string, number> = { normal: 400, bold: 700, lighter: 300, bolder: 800 };
    return weights[value] || Number.parseFloat(value) || 400;
  }
  if (attr === "stop-offset" || attr === "offset") {
    return value.endsWith("%") ? Number.parseFloat(value) / 100 : Number.parseFloat(value) || 0;
  }

  return Number.parseFloat(value) || 0;
}

function setAttributeValue(el: SVGElement, attr: string, value: number): void {
  if (attr === "stroke-dasharray") {
    const current = el.getAttribute(attr) || "0";
    const parts = current.split(/[\s,]+/);
    parts[0] = String(value);
    el.setAttribute(attr, parts.join(" "));
    return;
  }
  if (attr === "stop-offset" || attr === "offset") {
    el.setAttribute(attr, `${value * 100}%`);
    return;
  }
  if (attr === "font-weight") {
    el.setAttribute(attr, String(Math.round(value / 100) * 100));
    return;
  }
  if (
    attr === "rotate" ||
    attr === "scale" ||
    attr === "translate-x" ||
    attr === "translate-y" ||
    attr === "skew-x" ||
    attr === "skew-y"
  ) {
    updateTransform(el, attr, value);
    return;
  }

  el.setAttribute(attr, String(value));
}

function updateTransform(el: SVGElement, component: string, value: number): void {
  const currentTransform = el.getAttribute("transform") || "";
  const transforms: Record<string, string> = {};

  for (const match of currentTransform.matchAll(/(\w+)\s*\(([^)]+)\)/g)) {
    transforms[match[1]] = match[2];
  }

  if (component === "translate-x") {
    const y = transforms.translate?.split(/[\s,]+/)[1] || "0";
    transforms.translate = `${value} ${y}`;
  } else if (component === "translate-y") {
    const x = transforms.translate?.split(/[\s,]+/)[0] || "0";
    transforms.translate = `${x} ${value}`;
  } else if (component === "skew-x") {
    transforms.skewX = String(value);
  } else if (component === "skew-y") {
    transforms.skewY = String(value);
  } else if (component === "rotate") {
    // Preserve rotation center point if present (e.g., "0 100 100" -> "45 100 100")
    const parts = transforms.rotate?.split(/[\s,]+/) || [];
    if (parts.length >= 3) {
      transforms.rotate = `${value} ${parts[1]} ${parts[2]}`;
    } else {
      transforms.rotate = String(value);
    }
  } else if (component === "scale") {
    transforms.scale = String(value);
  }

  const parts: string[] = [];
  if (transforms.translate) parts.push(`translate(${transforms.translate})`);
  if (transforms.rotate) parts.push(`rotate(${transforms.rotate})`);
  if (transforms.scale) parts.push(`scale(${transforms.scale})`);
  if (transforms.skewX) parts.push(`skewX(${transforms.skewX})`);
  if (transforms.skewY) parts.push(`skewY(${transforms.skewY})`);

  el.setAttribute("transform", parts.join(" "));
}

function animateSvgAttributes(
  el: SVGElement,
  state: AnimationState,
  config: SvgMotionConfig
): void {
  const attrs = Array.from(state.targetValues.keys());
  if (attrs.length === 0) return;

  cancelActiveAnimation(state);
  const proxy = ensureProxyElement(state);

  const keyframes: Record<string, number[]> = {};
  for (const attr of attrs) {
    const from = state.currentValues.get(attr) ?? 0;
    const to = state.targetValues.get(attr) ?? 0;
    keyframes[`--svg-${attr}`] = [from, to];
    proxy.style.setProperty(`--svg-${attr}`, String(from));
  }

  const options = buildAnimationOptions(config);
  state.isAnimating = true;

  const anim = animate(proxy, keyframes, options);
  state.activeAnimation = anim;

  const updateFrame = () => {
    if (!state.isAnimating) return;

    const style = getComputedStyle(proxy);
    for (const attr of attrs) {
      const value = style.getPropertyValue(`--svg-${attr}`);
      if (value) {
        const numValue = Number.parseFloat(value);
        setAttributeValue(el, attr, numValue);
        state.currentValues.set(attr, numValue);
      }
    }

    state.rafId = requestAnimationFrame(updateFrame);
  };

  state.rafId = requestAnimationFrame(updateFrame);

  anim.finished
    .then(() => {
      stopAnimationLoop(state);
      for (const attr of attrs) {
        const finalValue = state.targetValues.get(attr) ?? 0;
        setAttributeValue(el, attr, finalValue);
        state.currentValues.set(attr, finalValue);
      }
    })
    .catch(() => stopAnimationLoop(state));
}

function animatePathMorph(el: SVGElement, state: MorphState, config: SvgMotionConfig): void {
  const fromPath = state.currentPath;
  const toPath = state.targetPath;

  if (!fromPath || !toPath || fromPath === toPath) return;

  cancelActiveAnimation(state);

  // Create Flubber interpolator for this transition
  // Lower maxSegmentLength = smoother curves but more computation
  try {
    state.interpolator = flubberInterpolate(fromPath, toPath, { maxSegmentLength: 2 });
  } catch (e) {
    console.warn("[motion-svg] Failed to create path interpolator:", e);
    el.setAttribute("d", toPath);
    state.currentPath = toPath;
    return;
  }

  const proxy = ensureProxyElement(state);
  proxy.style.setProperty("--morph-progress", "0");

  const options = buildAnimationOptions(config);
  state.isAnimating = true;

  const anim = animate(proxy, { "--morph-progress": [0, 1] }, options);
  state.activeAnimation = anim;

  const updateFrame = () => {
    if (!state.isAnimating || !state.interpolator) return;

    const style = getComputedStyle(proxy);
    const progress = Number.parseFloat(style.getPropertyValue("--morph-progress")) || 0;
    const pathString = state.interpolator(Math.min(1, Math.max(0, progress)));
    el.setAttribute("d", pathString);

    state.rafId = requestAnimationFrame(updateFrame);
  };

  state.rafId = requestAnimationFrame(updateFrame);

  anim.finished
    .then(() => {
      stopAnimationLoop(state);
      el.setAttribute("d", toPath);
      state.currentPath = toPath;
      state.interpolator = null;
    })
    .catch(() => stopAnimationLoop(state));
}

const motionSvgAttributePlugin: AttributePlugin = {
  name: "motion-svg",
  requirement: { key: "allowed", value: "allowed" },
  argNames: [],

  apply(ctx: AttributeContext): OnRemovalFn | void {
    const { el: htmlEl, value } = ctx;
    if (!value) return;

    if (!(htmlEl instanceof SVGElement)) {
      console.warn("[motion-svg] data-motion-svg requires an SVG element");
      return;
    }
    const el = htmlEl;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return setupWithoutAnimation(el, value);
    }

    const config = parseMotionSvgAttribute(value);
    const hasNumericProps = config.properties.size > 0;
    const hasMorphPath = !!config.morphPath;

    if (!hasNumericProps && !hasMorphPath) {
      console.warn("[motion-svg] No properties to animate:", value);
      return;
    }

    const cleanupFns: (() => void)[] = [];

    // Numeric attribute animation
    if (hasNumericProps) {
      const state: AnimationState = {
        currentValues: new Map(),
        targetValues: new Map(),
        activeAnimation: null,
        proxyElement: null,
        rafId: null,
        isAnimating: false,
      };

      for (const [attr] of config.properties) {
        state.currentValues.set(attr, getCurrentAttributeValue(el, attr));
      }

      let isInitialRender = true;

      const dispose = effect(() => {
        const newTargets = new Map<string, number>();
        for (const [attr, signalName] of config.properties) {
          newTargets.set(attr, getSignalValue(signalName));
        }

        let hasChanges = false;
        for (const [attr, newValue] of newTargets) {
          const current = state.targetValues.get(attr);
          if (current === undefined || Math.abs(current - newValue) > 0.001) {
            hasChanges = true;
            break;
          }
        }

        if (!hasChanges && !isInitialRender) return;

        state.targetValues = newTargets;

        if (isInitialRender) {
          isInitialRender = false;
          for (const [attr, val] of newTargets) {
            setAttributeValue(el, attr, val);
            state.currentValues.set(attr, val);
          }
        } else {
          animateSvgAttributes(el, state, config);
        }
      });

      cleanupFns.push(() => {
        dispose();
        if (state.activeAnimation) state.activeAnimation.cancel();
        if (state.rafId) cancelAnimationFrame(state.rafId);
        if (state.proxyElement) state.proxyElement.remove();
      });
    }

    // Path morphing animation
    if (hasMorphPath && config.morphPath) {
      const morphSignal = config.morphPath;
      const morphState: MorphState = {
        currentPath: el.getAttribute("d") || "",
        targetPath: "",
        interpolator: null,
        activeAnimation: null,
        proxyElement: null,
        rafId: null,
        isAnimating: false,
      };

      let isInitialMorphRender = true;

      const dispose = effect(() => {
        const newPath = getSignalStringValue(morphSignal);
        if (!newPath || newPath === morphState.targetPath) return;

        morphState.targetPath = newPath;

        if (isInitialMorphRender) {
          isInitialMorphRender = false;
          el.setAttribute("d", newPath);
          morphState.currentPath = newPath;
        } else {
          animatePathMorph(el, morphState, config);
        }
      });

      cleanupFns.push(() => {
        dispose();
        if (morphState.activeAnimation) morphState.activeAnimation.cancel();
        if (morphState.rafId) cancelAnimationFrame(morphState.rafId);
        if (morphState.proxyElement) morphState.proxyElement.remove();
      });
    }

    return () => {
      for (const cleanup of cleanupFns) cleanup();
    };
  },
};

function setupWithoutAnimation(el: SVGElement, value: string): OnRemovalFn {
  const config = parseMotionSvgAttribute(value);
  const cleanupFns: (() => void)[] = [];

  // Numeric properties
  if (config.properties.size > 0) {
    const dispose = effect(() => {
      for (const [attr, signalName] of config.properties) {
        setAttributeValue(el, attr, getSignalValue(signalName));
      }
    });
    cleanupFns.push(dispose);
  }

  // Path morphing
  if (config.morphPath) {
    const morphSignal = config.morphPath;
    const dispose = effect(() => {
      const path = getSignalStringValue(morphSignal);
      if (path) el.setAttribute("d", path);
    });
    cleanupFns.push(dispose);
  }

  return () => {
    for (const cleanup of cleanupFns) cleanup();
  };
}

export default motionSvgAttributePlugin;
export { SPRING_PRESETS, NUMERIC_SVG_ATTRS };
