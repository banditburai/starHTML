import { animate, inView, scroll, stagger } from "https://cdn.jsdelivr.net/npm/motion@11/+esm";
import type { AnimationControls, Keyframes } from "https://cdn.jsdelivr.net/npm/motion@11/+esm";
import { mergePatch, effect, getPath } from "datastar";
import type {
  ActionContext,
  ActionPlugin,
  AttributeContext,
  AttributePlugin,
  OnRemovalFn,
} from "./types.js";

// Motion plugin for declarative animations

interface AnimationEntry {
  anim: AnimationControls;
  el: HTMLElement;
}

const animationRegistry = new Map<string, AnimationEntry>();

// WeakMap for storing exit animation config on elements (avoids memory leaks, proper typing)
const exitConfigMap = new WeakMap<HTMLElement, MotionConfig>();

const SPRING_PRESETS: Record<string, { stiffness: number; damping: number }> = {
  gentle: { stiffness: 120, damping: 14 },
  bouncy: { stiffness: 300, damping: 10 },
  tight: { stiffness: 400, damping: 30 },
  slow: { stiffness: 50, damping: 20 },
};

const ANIMATION_PRESETS: Record<string, Keyframes> = {
  fade: { opacity: [0, 1] },
  "slide-up": { y: [20, 0], opacity: [0, 1] },
  "slide-down": { y: [-20, 0], opacity: [0, 1] },
  scale: { scale: [0.9, 1], opacity: [0, 1] },
  bounce: { y: [-10, 0], opacity: [0, 1] },
};

type AnimationType = "enter" | "exit" | "hover" | "press" | "tap" | "in-view" | "scroll" | "resize" | "visibility";

interface MotionConfig {
  type: AnimationType;
  name?: string;
  x?: number;
  y?: number;
  scale?: number;
  rotate?: number;
  opacity?: number;
  duration?: number;
  delay?: number;
  ease?: string;
  spring?: keyof typeof SPRING_PRESETS;
  preset?: keyof typeof ANIMATION_PRESETS;
  threshold?: number;
  once?: boolean;
  stagger?: number;
  repeat?: number | "infinite";
  [key: string]: string | number | boolean | undefined;
}

interface AnimationOpts {
  duration?: number;
  delay?: number;
  ease?: string;
  repeat?: number;
  repeatType?: "loop" | "reverse" | "mirror";
  type?: "spring";
  stiffness?: number;
  damping?: number;
}

interface VisibilityConfig {
  signal: string;
  enter: MotionConfig;
  exit: MotionConfig;
}

function parseMotionAttribute(value: string): MotionConfig {
  const config: MotionConfig = { type: "enter" };

  for (const part of value.split(" ")) {
    const colonIdx = part.indexOf(":");
    if (colonIdx === -1) continue;

    const key = part.slice(0, colonIdx);
    const val = part.slice(colonIdx + 1);

    if (key === "type") {
      config.type = val as AnimationType;
    } else if (key === "name") {
      config.name = val;
    } else if (key === "preset" || key === "ease" || key === "spring") {
      config[key] = val;
    } else if (key === "once") {
      config.once = val === "true";
    } else if (key === "repeat") {
      config.repeat = val === "infinite" ? Number.POSITIVE_INFINITY : Number(val);
    } else if (val.includes(",")) {
      config[key] = val.split(",").map(Number) as unknown as number;
    } else {
      const numVal = Number(val);
      config[key] = Number.isNaN(numVal) ? val : numVal;
    }
  }

  return config;
}

function parseVisibilityConfig(value: string): VisibilityConfig {
  const enterConfig: MotionConfig = { type: "enter" };
  const exitConfig: MotionConfig = { type: "exit" };
  let signal = "";

  for (const part of value.split(" ")) {
    const colonIdx = part.indexOf(":");
    if (colonIdx === -1) continue;

    const key = part.slice(0, colonIdx);
    const val = part.slice(colonIdx + 1);

    if (key === "signal") {
      signal = val;
    } else if (key.startsWith("enter_")) {
      const subKey = key.slice(6); // Remove "enter_" prefix
      parseConfigValue(enterConfig, subKey, val);
    } else if (key.startsWith("exit_")) {
      const subKey = key.slice(5); // Remove "exit_" prefix
      parseConfigValue(exitConfig, subKey, val);
    }
  }

  return { signal, enter: enterConfig, exit: exitConfig };
}

function parseConfigValue(config: MotionConfig, key: string, val: string): void {
  if (key === "preset" || key === "ease" || key === "spring") {
    config[key] = val;
  } else if (key === "once") {
    config.once = val === "true";
  } else if (key === "repeat") {
    config.repeat = val === "infinite" ? Number.POSITIVE_INFINITY : Number(val);
  } else if (val.includes(",")) {
    config[key] = val.split(",").map(Number) as unknown as number;
  } else {
    const numVal = Number(val);
    config[key] = Number.isNaN(numVal) ? val : numVal;
  }
}

function getKeyframes(config: MotionConfig): Keyframes {
  const preset = config.preset && ANIMATION_PRESETS[config.preset];
  if (preset) return { ...preset };

  const keyframes: Keyframes = {};
  if (config.x !== undefined) keyframes.x = [config.x, 0];
  if (config.y !== undefined) keyframes.y = [config.y, 0];
  if (config.scale !== undefined) keyframes.scale = [config.scale, 1];
  if (config.rotate !== undefined) keyframes.rotate = [config.rotate, 0];
  if (config.opacity !== undefined) keyframes.opacity = [config.opacity, 1];
  return keyframes;
}

function getExitKeyframes(config: MotionConfig): Keyframes {
  const preset = config.preset && ANIMATION_PRESETS[config.preset];
  if (preset) {
    const exitKeyframes: Keyframes = {};
    for (const [key, val] of Object.entries(preset)) {
      if (Array.isArray(val) && val.length >= 2) {
        exitKeyframes[key] = [val[1] as number, val[0] as number];
      }
    }
    return exitKeyframes;
  }

  const keyframes: Keyframes = {};
  if (config.x !== undefined) keyframes.x = [0, config.x];
  if (config.y !== undefined) keyframes.y = [0, config.y];
  if (config.scale !== undefined) keyframes.scale = [1, config.scale];
  if (config.rotate !== undefined) keyframes.rotate = [0, config.rotate];
  if (config.opacity !== undefined) keyframes.opacity = [1, config.opacity];
  return keyframes;
}

function getAnimationOptions(config: MotionConfig): AnimationOpts {
  const options: AnimationOpts = {
    duration: (config.duration ?? 300) / 1000,
  };

  if (config.delay) options.delay = config.delay / 1000;
  if (config.ease) options.ease = config.ease;
  if (config.repeat !== undefined) {
    options.repeat =
      config.repeat === "infinite" ? Number.POSITIVE_INFINITY : (config.repeat as number);
  }

  const springPreset = config.spring && SPRING_PRESETS[config.spring];
  if (springPreset) {
    options.type = "spring";
    options.stiffness = springPreset.stiffness;
    options.damping = springPreset.damping;
  }

  return options;
}

function dispatchMotionEvent(
  el: HTMLElement,
  eventName: "motion-start" | "motion-complete" | "motion-cancel",
  detail: { name: string | undefined; type: string }
): void {
  // Use microtask to ensure Datastar has attached event listeners
  queueMicrotask(() => {
    el.dispatchEvent(
      new CustomEvent(eventName, {
        bubbles: true,
        detail: { name: detail.name, type: detail.type, element: el },
      })
    );
  });
}

function registerAnimation(
  name: string | undefined,
  anim: AnimationControls,
  el: HTMLElement
): void {
  if (name) {
    // Cancel any existing animation with this name before registering
    const existing = animationRegistry.get(name);
    if (existing && existing.anim !== anim) {
      existing.anim.cancel();
    }
    animationRegistry.set(name, { anim, el });
  }
}

function unregisterAnimation(name: string | undefined, anim?: AnimationControls): void {
  if (name) {
    // Only unregister if it's the same animation instance (prevents race condition)
    const entry = animationRegistry.get(name);
    if (!anim || entry?.anim === anim) {
      animationRegistry.delete(name);
    }
  }
}

/** Creates handler for SSE-triggered motion actions (remove/replace) */
function createMotionTriggerHandler(el: HTMLElement): (e: Event) => void {
  return (e: Event) => {
    const detail = (e as CustomEvent).detail;
    if (detail.op === "remove") {
      playExitAndThen(el, () => el.remove());
    } else if (detail.op === "replace" && detail.html) {
      playExitAndThen(el, () => {
        el.outerHTML = detail.html;
      });
    }
  };
}

/**
 * Plays exit animation on element, then executes callback.
 * If no exit config exists, executes callback immediately.
 * Includes isConnected check before callback execution.
 */
function playExitAndThen(
  el: HTMLElement,
  callback: () => void
): void | Promise<void> {
  const exitConfig = exitConfigMap.get(el);
  if (!exitConfig) {
    callback();
    return;
  }

  const keyframes = getExitKeyframes(exitConfig);
  const options = getAnimationOptions(exitConfig);

  dispatchMotionEvent(el, "motion-start", { name: exitConfig.name, type: "exit" });
  const exitAnim = animate(el, keyframes, options);
  registerAnimation(exitConfig.name, exitAnim, el);

  return exitAnim.finished.then(() => {
    dispatchMotionEvent(el, "motion-complete", { name: exitConfig.name, type: "exit" });
    unregisterAnimation(exitConfig.name, exitAnim);
    // Check element is still in DOM before modifying
    if (el.isConnected) {
      callback();
    }
  });
}

const motionAttributePlugin: AttributePlugin = {
  name: "motion",
  requirement: { key: "allowed", value: "allowed" },

  apply(ctx: AttributeContext): OnRemovalFn | void {
    const { el, value } = ctx;
    if (!value) return;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      el.setAttribute("data-motion-ready", "true");
      return;
    }

    const config = parseMotionAttribute(value);
    let cleanup: (() => void) | null = null;
    const animType = config.type === "tap" ? "press" : config.type;

    switch (animType) {
      case "enter": {
        const keyframes = getKeyframes(config);
        const options = getAnimationOptions(config);

        el.setAttribute("data-motion-ready", "true");
        dispatchMotionEvent(el, "motion-start", { name: config.name, type: "enter" });

        const anim = animate(el, keyframes, options);
        registerAnimation(config.name, anim, el);

        anim.finished.then(() => {
          dispatchMotionEvent(el, "motion-complete", { name: config.name, type: "enter" });
          unregisterAnimation(config.name, anim);
        });

        cleanup = () => {
          anim.cancel();
          dispatchMotionEvent(el, "motion-cancel", { name: config.name, type: "enter" });
          unregisterAnimation(config.name, anim);
        };
        break;
      }

      case "exit": {
        el.setAttribute("data-motion-ready", "true");
        const originalDisplay = el.style.display || getComputedStyle(el).display;
        let isAnimating = false;

        const playExitAnimation = () => {
          if (isAnimating) return;
          isAnimating = true;

          el.style.display = originalDisplay === "none" ? "block" : originalDisplay;
          el.hidden = false;

          const keyframes = getExitKeyframes(config);
          const options = getAnimationOptions(config);

          dispatchMotionEvent(el, "motion-start", { name: config.name, type: "exit" });
          const exitAnim = animate(el, keyframes, options);
          registerAnimation(config.name, exitAnim, el);

          exitAnim.finished.then(() => {
            if (el.isConnected) {
              el.style.display = "none";
            }
            dispatchMotionEvent(el, "motion-complete", { name: config.name, type: "exit" });
            unregisterAnimation(config.name, exitAnim);
            isAnimating = false;
          });
        };

        const observer = new MutationObserver((mutations) => {
          for (const mutation of mutations) {
            if (mutation.type === "attributes") {
              const isHiding =
                (mutation.attributeName === "style" && el.style.display === "none") ||
                (mutation.attributeName === "hidden" && el.hidden);
              if (isHiding) {
                playExitAnimation();
              }
            }
          }
        });

        observer.observe(el, { attributes: true, attributeFilter: ["style", "hidden"] });
        cleanup = () => observer.disconnect();
        break;
      }

      case "hover": {
        el.setAttribute("data-motion-ready", "true");
        const duration = (config.duration ?? 200) / 1000;
        const hoverKeyframes: Keyframes = {};
        const restKeyframes: Keyframes = {};

        for (const key of ["scale", "y", "rotate"] as const) {
          const val = config[key];
          if (val !== undefined) {
            hoverKeyframes[key] = val;
            restKeyframes[key] = key === "scale" ? 1 : 0;
          }
        }

        let currentAnim: AnimationControls | null = null;

        const onEnter = () => {
          currentAnim?.cancel();
          dispatchMotionEvent(el, "motion-start", { name: config.name, type: "hover" });
          currentAnim = animate(el, hoverKeyframes, { duration });
          currentAnim.finished.then(() => {
            dispatchMotionEvent(el, "motion-complete", { name: config.name, type: "hover" });
          });
        };

        const onLeave = () => {
          currentAnim?.cancel();
          currentAnim = animate(el, restKeyframes, { duration });
        };

        el.addEventListener("mouseenter", onEnter);
        el.addEventListener("mouseleave", onLeave);

        cleanup = () => {
          el.removeEventListener("mouseenter", onEnter);
          el.removeEventListener("mouseleave", onLeave);
          currentAnim?.cancel();
        };
        break;
      }

      case "press": {
        el.setAttribute("data-motion-ready", "true");
        const duration = (config.duration ?? 100) / 1000;
        const pressKeyframes: Keyframes = {};
        const restKeyframes: Keyframes = {};

        for (const key of ["scale", "y"] as const) {
          const val = config[key];
          if (val !== undefined) {
            pressKeyframes[key] = val;
            restKeyframes[key] = key === "scale" ? 1 : 0;
          }
        }

        let currentAnim: AnimationControls | null = null;
        let isPressed = false;

        const onDown = () => {
          isPressed = true;
          currentAnim?.cancel();
          dispatchMotionEvent(el, "motion-start", { name: config.name, type: "press" });
          currentAnim = animate(el, pressKeyframes, { duration });
        };

        const onUp = () => {
          if (!isPressed) return;
          isPressed = false;
          currentAnim?.cancel();
          currentAnim = animate(el, restKeyframes, { duration });
          currentAnim.finished.then(() => {
            dispatchMotionEvent(el, "motion-complete", { name: config.name, type: "press" });
          });
        };

        el.addEventListener("pointerdown", onDown);
        el.addEventListener("pointerup", onUp);
        el.addEventListener("pointerleave", onUp);

        cleanup = () => {
          el.removeEventListener("pointerdown", onDown);
          el.removeEventListener("pointerup", onUp);
          el.removeEventListener("pointerleave", onUp);
          currentAnim?.cancel();
        };
        break;
      }

      case "resize": {
        el.setAttribute("data-motion-ready", "true");
        const duration = (config.duration ?? 200) / 1000;
        let currentAnim: AnimationControls | null = null;
        let initialSize: { width: number; height: number } | null = null;

        const resizeObserver = new ResizeObserver((entries) => {
          for (const entry of entries) {
            const { width, height } = entry.contentRect;

            if (!initialSize) {
              initialSize = { width, height };
              return;
            }

            if (width !== initialSize.width || height !== initialSize.height) {
              currentAnim?.cancel();

              const keyframes: Keyframes = {};
              if (config.scale !== undefined) keyframes.scale = [config.scale, 1];
              if (config.opacity !== undefined) keyframes.opacity = [config.opacity, 1];

              dispatchMotionEvent(el, "motion-start", { name: config.name, type: "resize" });
              currentAnim = animate(el, keyframes, { duration });
              currentAnim.finished.then(() => {
                dispatchMotionEvent(el, "motion-complete", { name: config.name, type: "resize" });
              });

              initialSize = { width, height };
            }
          }
        });

        resizeObserver.observe(el);
        cleanup = () => {
          resizeObserver.disconnect();
          currentAnim?.cancel();
        };
        break;
      }

      case "in-view": {
        const keyframes = getKeyframes(config);
        const options = getAnimationOptions(config);

        const initialState: Keyframes = {};
        for (const [key, val] of Object.entries(keyframes)) {
          initialState[key] = Array.isArray(val) ? val[0] : val;
        }
        animate(el, initialState, { duration: 0 });

        const stopObserving = inView(
          el,
          () => {
            el.setAttribute("data-motion-ready", "true");
            dispatchMotionEvent(el, "motion-start", { name: config.name, type: "in-view" });

            const anim = animate(el, keyframes, options);
            registerAnimation(config.name, anim, el);

            anim.finished.then(() => {
              dispatchMotionEvent(el, "motion-complete", { name: config.name, type: "in-view" });
              unregisterAnimation(config.name, anim);
            });

            if (config.once === false) {
              return () => animate(el, initialState, { duration: 0 });
            }
            return undefined;
          },
          { amount: config.threshold ?? 0.1 }
        );

        cleanup = stopObserving;
        break;
      }

      case "scroll": {
        el.setAttribute("data-motion-ready", "true");
        const scrollKeyframes: Keyframes = {};

        for (const prop of ["x", "y", "scale", "opacity", "rotate"]) {
          const val = config[prop];
          if (Array.isArray(val) && val.length === 2) {
            scrollKeyframes[prop] = val;
          }
        }

        const anim = animate(el, scrollKeyframes, { duration: 1 });
        anim.pause();

        const progressSignal = config.name ? `${config.name}_progress` : null;

        // Use element-relative scroll tracking: animate as element moves through viewport
        const stopScrolling = scroll(
          (progress: number) => {
            anim.time = progress;
            if (progressSignal) {
              mergePatch({ [progressSignal]: Math.round(progress * 100) });
            }
          },
          { target: el, offset: ["start end", "end start"] }
        );

        cleanup = () => {
          stopScrolling();
          anim.cancel();
        };
        break;
      }

      case "visibility": {
        const visConfig = parseVisibilityConfig(value);
        if (!visConfig.signal) {
          console.warn("data-motion visibility requires a signal");
          el.setAttribute("data-motion-ready", "true");
          return;
        }

        // Store exit config in WeakMap for SSE-driven remove/replace
        if (visConfig.exit) {
          visConfig.exit.type = "exit";
          exitConfigMap.set(el, visConfig.exit);
        }

        const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        const originalDisplay = el.style.display || getComputedStyle(el).display || "block";
        let isAnimating = false;
        let currentlyVisible: boolean | null = null;

        const playEnterAnimation = (): void => {
          el.style.display = originalDisplay;
          el.setAttribute("data-motion-ready", "true");

          if (prefersReducedMotion) {
            isAnimating = false;
            return;
          }

          const enterKeyframes = getKeyframes(visConfig.enter);
          if (Object.keys(enterKeyframes).length === 0) {
            isAnimating = false;
            return;
          }

          isAnimating = true;
          const options = getAnimationOptions(visConfig.enter);
          dispatchMotionEvent(el, "motion-start", { name: visConfig.enter.name, type: "enter" });
          const enterAnim = animate(el, enterKeyframes, options);
          registerAnimation(visConfig.enter.name, enterAnim, el);

          enterAnim.finished.then(() => {
            dispatchMotionEvent(el, "motion-complete", { name: visConfig.enter.name, type: "enter" });
            unregisterAnimation(visConfig.enter.name, enterAnim);
            isAnimating = false;
          });
        };

        const playExitAnimation = (): Promise<void> => {
          if (prefersReducedMotion) {
            el.style.display = "none";
            return Promise.resolve();
          }

          const exitKeyframes = getExitKeyframes(visConfig.exit);
          if (Object.keys(exitKeyframes).length === 0 || isAnimating) {
            el.style.display = "none";
            return Promise.resolve();
          }

          isAnimating = true;
          const options = getAnimationOptions(visConfig.exit);
          dispatchMotionEvent(el, "motion-start", { name: visConfig.exit.name, type: "exit" });
          const exitAnim = animate(el, exitKeyframes, options);
          registerAnimation(visConfig.exit.name, exitAnim, el);

          return exitAnim.finished.then(() => {
            if (el.isConnected) {
              el.style.display = "none";
            }
            dispatchMotionEvent(el, "motion-complete", { name: visConfig.exit.name, type: "exit" });
            unregisterAnimation(visConfig.exit.name, exitAnim);
            isAnimating = false;
          });
        };

        const handleTrigger = createMotionTriggerHandler(el);
        el.addEventListener("motion-trigger", handleTrigger);

        const signalName = visConfig.signal.startsWith("$")
          ? visConfig.signal.slice(1)
          : visConfig.signal;

        const dispose = effect(() => {
          try {
            // Use getPath to read signal value directly (not rx which evaluates expressions)
            const shouldBeVisible = Boolean(getPath(signalName));

            // Initial render - just set display without animation
            if (currentlyVisible === null) {
              currentlyVisible = shouldBeVisible;
              el.style.display = shouldBeVisible ? originalDisplay : "none";
              if (shouldBeVisible) {
                el.setAttribute("data-motion-ready", "true");
              }
              return;
            }

            if (shouldBeVisible && !currentlyVisible) {
              currentlyVisible = true;
              playEnterAnimation();
            } else if (!shouldBeVisible && currentlyVisible) {
              currentlyVisible = false;
              playExitAnimation();
            }
          } catch (err) {
            console.warn("data-motion visibility: Failed to evaluate signal expression:", err);
          }
        });

        cleanup = () => {
          dispose();
          el.removeEventListener("motion-trigger", handleTrigger);
          exitConfigMap.delete(el);
        };
        break;
      }
    }

    return () => cleanup?.();
  },
};

const OPTION_KEYS = new Set([
  "duration",
  "delay",
  "ease",
  "spring",
  "stagger",
  "repeat",
  "repeatType",
  "name",
  "at",
]);

function extractOptions(props: Record<string, unknown>): AnimationOpts {
  const options: AnimationOpts = {
    duration: ((props.duration as number) ?? 300) / 1000,
  };

  if (props.delay !== undefined) options.delay = (props.delay as number) / 1000;
  if (props.ease) options.ease = props.ease as string;

  if (props.spring) {
    const springPreset = SPRING_PRESETS[props.spring as string];
    if (springPreset) {
      options.type = "spring";
      options.stiffness = springPreset.stiffness;
      options.damping = springPreset.damping;
    }
  }

  if (props.stagger !== undefined) {
    options.delay = stagger((props.stagger as number) / 1000) as unknown as number;
  }

  if (props.repeat !== undefined) {
    options.repeat = props.repeat === "infinite" ? Infinity : Number(props.repeat);
  }

  if (props.repeatType) {
    options.repeatType = props.repeatType as "loop" | "reverse" | "mirror";
  }

  return options;
}

function extractKeyframes(props: Record<string, unknown>): Keyframes {
  const keyframes: Keyframes = {};
  for (const [key, value] of Object.entries(props)) {
    if (!OPTION_KEYS.has(key)) {
      keyframes[key] = value as number | string | number[] | string[];
    }
  }
  return keyframes;
}

function resolveElement(
  ctx: ActionContext,
  selectorOrProps: string | Record<string, unknown>,
  maybeProps?: Record<string, unknown>
): { el: HTMLElement | null; props: Record<string, unknown> } {
  if (typeof selectorOrProps === "string") {
    const el =
      selectorOrProps === "el" ? ctx.el : document.querySelector<HTMLElement>(selectorOrProps);
    return { el, props: maybeProps ?? {} };
  }
  return { el: ctx.el, props: selectorOrProps ?? {} };
}

const motionActionPlugin: ActionPlugin = {
  name: "motion",
  apply: (ctx: ActionContext, operation: string, ...args: unknown[]): void | Promise<void> => {
    switch (operation) {
      case "animate": {
        const { el, props } = resolveElement(
          ctx,
          ...(args as [string | Record<string, unknown>, Record<string, unknown>?])
        );
        if (!el) {
          console.warn(`@motion('animate'): Element not found`);
          return;
        }

        const keyframes = extractKeyframes(props);
        const options = extractOptions(props);
        const name = props.name as string | undefined;

        // Handle infinite repeat
        const isInfinite = props.repeat === "infinite";

        // If animation with this name already exists, don't create a new one
        // User should click Cancel first, then Start again
        if (name) {
          const existing = animationRegistry.get(name);
          if (existing) {
            return;
          }
        }

        const animOptions: Record<string, unknown> = { ...options };
        if (isInfinite) {
          animOptions.repeat = Infinity;
        }

        dispatchMotionEvent(el, "motion-start", { name, type: "animate" });
        const anim = animate(el, keyframes, animOptions);
        registerAnimation(name, anim, el);

        // Note: finished promise NEVER resolves for infinite animations, which is correct
        // The animation stays in the registry until manually stopped/cancelled
        return anim.finished
          .then(() => {
            dispatchMotionEvent(el, "motion-complete", { name, type: "animate" });
            unregisterAnimation(name, anim);
          })
          .catch(() => {
            // Animation was cancelled - expected, cancel handler already cleaned up registry
          });
      }

      case "sequence": {
        const [steps] = args as [
          Array<[string, Record<string, unknown>, Record<string, unknown>?]>,
        ];
        if (!Array.isArray(steps) || steps.length === 0) {
          console.warn(`@motion('sequence'): Invalid steps array`);
          return;
        }

        let chain = Promise.resolve();
        let lastAt = 0;

        for (const step of steps) {
          const [selector, keyframeProps, stepOptions = {}] = step;
          const el = selector === "el" ? ctx.el : document.querySelector<HTMLElement>(selector);

          if (!el) {
            console.warn(`@motion('sequence'): Element not found: ${selector}`);
            continue;
          }

          const options = extractOptions({ ...keyframeProps, ...stepOptions });
          const kf = extractKeyframes(keyframeProps);

          const atValue = stepOptions.at as string | number | undefined;
          let delayOffset = 0;

          if (typeof atValue === "string" && atValue.startsWith("+")) {
            delayOffset = Number.parseFloat(atValue.slice(1));
          } else if (typeof atValue === "number") {
            delayOffset = atValue - lastAt;
            lastAt = atValue;
          }

          if (delayOffset > 0) {
            options.delay = (options.delay ?? 0) + delayOffset;
          }

          const capturedEl = el;
          chain = chain.then(() => {
            dispatchMotionEvent(capturedEl, "motion-start", { name: undefined, type: "sequence" });
            const anim = animate(capturedEl, kf, options);
            return anim.finished.then(() => {
              dispatchMotionEvent(capturedEl, "motion-complete", {
                name: undefined,
                type: "sequence",
              });
            });
          });
        }

        return chain;
      }

      case "set": {
        const { el, props } = resolveElement(
          ctx,
          ...(args as [string | Record<string, unknown>, Record<string, unknown>?])
        );
        if (!el) {
          console.warn(`@motion('set'): Element not found`);
          return;
        }
        animate(el, extractKeyframes(props), { duration: 0 });
        return;
      }

      case "pause":
      case "play":
      case "stop":
      case "cancel": {
        const [name] = args as [string];
        const entry = animationRegistry.get(name);

        if (!entry) {
          return;
        }

        entry.anim[operation as "pause" | "play" | "stop" | "cancel"]();

        if (operation === "stop" || operation === "cancel") {
          if (operation === "cancel") {
            dispatchMotionEvent(entry.el, "motion-cancel", { name, type: "cancel" });
          }
          animationRegistry.delete(name);
        }
        return;
      }

      case "remove": {
        const [selector] = args as [string];
        const el = selector === "el" ? ctx.el : document.querySelector<HTMLElement>(selector);
        if (!el) {
          console.warn(`@motion('remove'): Element not found: ${selector}`);
          return;
        }
        return playExitAndThen(el, () => el.remove());
      }

      case "replace": {
        const [selector, html] = args as [string, string];
        const el = selector === "el" ? ctx.el : document.querySelector<HTMLElement>(selector);
        if (!el) {
          console.warn(`@motion('replace'): Element not found: ${selector}`);
          return;
        }
        return playExitAndThen(el, () => {
          el.outerHTML = html;
        });
      }

      default:
        console.warn(`@motion: Unknown operation: ${operation}`);
    }
  },
};

// Separate plugin for exit animations - handles data-motion-exit attribute
// This parses exit animation config for use by @motion("remove/replace") actions
// Also listens for "motion-trigger" events for SSE-driven remove/replace
const motionExitAttributePlugin: AttributePlugin = {
  name: "motion-exit",
  requirement: { key: "allowed", value: "allowed" },

  apply(ctx: AttributeContext): OnRemovalFn | void {
    const { el, value } = ctx;
    if (!value) return;

    const config = parseMotionAttribute(value);
    config.type = "exit";
    exitConfigMap.set(el, config);

    const handleTrigger = createMotionTriggerHandler(el);
    el.addEventListener("motion-trigger", handleTrigger);

    return () => {
      el.removeEventListener("motion-trigger", handleTrigger);
      exitConfigMap.delete(el);
    };
  },
};

export default motionAttributePlugin;
export { motionActionPlugin, motionExitAttributePlugin, stagger, animationRegistry };
