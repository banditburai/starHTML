/**
 * Throttling utilities for performance optimization
 * RAF-based throttling prevents excessive DOM updates during animations
 * Timer-based throttling reduces API calls and expensive operations
 */

// Type for any callable function
type AnyFunction = (...args: any[]) => any;

// Dynamic delay per call - needed for handlers with configurable throttling
export function createDynamicThrottle(): (func: AnyFunction, delay?: number) => void {
  let timeoutId: number | null = null;
  let lastExecTime = 0;

  return (func: AnyFunction, delay = 150): void => {
    const currentTime = Date.now();
    const timeSinceLastExec = currentTime - lastExecTime;

    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }

    if (timeSinceLastExec >= delay) {
      func();
      lastExecTime = currentTime;
    } else {
      const remainingDelay = delay - timeSinceLastExec;
      timeoutId = setTimeout(() => {
        func();
        lastExecTime = Date.now();
        timeoutId = null;
      }, remainingDelay) as unknown as number;
    }
  };
}

// RAF throttling syncs with display refresh rate for smooth animations
export function createRAFThrottle(func: AnyFunction): AnyFunction {
  let rafId: number | null = null;

  return function (this: any, ...args: any[]) {
    if (rafId !== null) return;

    rafId = requestAnimationFrame(() => {
      try {
        func.apply(this, args);
      } finally {
        // Prevent memory leak if func throws
        rafId = null;
      }
    });
  };
}

// Timer-based throttling for configurable delays
export function createTimerThrottle(func: AnyFunction, delay: number): AnyFunction {
  let timeoutId: number;
  let lastExecTime = 0;

  return function (this: any, ...args: any[]) {
    const currentTime = Date.now();

    if (currentTime - lastExecTime > delay) {
      func.apply(this, args);
      lastExecTime = currentTime;
    } else {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(
        () => {
          func.apply(this, args);
          lastExecTime = Date.now();
        },
        delay - (currentTime - lastExecTime)
      ) as unknown as number;
    }
  };
}

// WeakMap ensures throttle state is garbage collected with elements
export function createElementThrottle(): (
  element: Element,
  func: AnyFunction,
  delay?: number
) => any {
  interface ThrottleConfig {
    lastExec: number;
    timeoutId: number | null;
  }

  const throttleConfigs = new WeakMap<Element, ThrottleConfig>();

  return (element: Element, func: AnyFunction, delay = 150): any => {
    let config = throttleConfigs.get(element);
    if (!config) {
      config = { lastExec: 0, timeoutId: null };
      throttleConfigs.set(element, config);
    }

    const now = Date.now();
    const timeSinceLastExec = now - config.lastExec;

    if (config.timeoutId) {
      clearTimeout(config.timeoutId);
      config.timeoutId = null;
    }

    if (timeSinceLastExec >= delay) {
      config.lastExec = now;
      return func.call(element);
    }
    const remainingDelay = delay - timeSinceLastExec;
    config.timeoutId = setTimeout(() => {
      config.lastExec = Date.now();
      config.timeoutId = null;
      func.call(element);
    }, remainingDelay) as unknown as number;
  };
}

// Debouncing waits for events to stop - useful for search input, resize events
export function createDebounce(func: AnyFunction, delay: number): AnyFunction {
  let timeoutId: number | null = null;

  return function (this: any, ...args: any[]) {
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }

    timeoutId = setTimeout(() => {
      func.apply(this, args);
      timeoutId = null;
    }, delay) as unknown as number;
  };
}
