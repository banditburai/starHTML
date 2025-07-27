/**
 * StarHTML Persist Handler - Datastar AttributePlugin Implementation
 * Handles data-persist attributes for automatic signal persistence to storage
 */

import { createDebounce } from "./throttle.js";

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
  effect: (fn: () => void) => () => void;
  getPath: (path: string) => any;
  hasPath: (path: string) => boolean;
  mergePatch: (patch: Record<string, any>) => void;
  startBatch: () => void;
  endBatch: () => void;
}

type OnRemovalFn = () => void;

interface PersistConfig {
  storage: Storage;
  storageKey: string;
  signals: string[];
  isWildcard: boolean;
}

const DEFAULT_STORAGE_KEY = "starhtml-persist";
const DEFAULT_THROTTLE = 500;
const WILDCARD = "*";

function getStorage(isSession: boolean): Storage | null {
  try {
    const storage = isSession ? sessionStorage : localStorage;
    const testKey = "__test__";
    storage.setItem(testKey, "1");
    storage.removeItem(testKey);
    return storage;
  } catch {
    return null;
  }
}

function parseConfig(ctx: RuntimeContext): PersistConfig | null {
  const { key, value, mods } = ctx;

  const isSession = mods.has("session");
  const storage = getStorage(isSession);
  if (!storage) return null;

  const customKey = mods.get("as");
  const storageKey = customKey ? `${DEFAULT_STORAGE_KEY}-${customKey}` : DEFAULT_STORAGE_KEY;

  let signals: string[] = [];
  let isWildcard = false;

  if (key) {
    signals = [key];
  } else if (value) {
    const trimmed = value.trim();
    if (trimmed === WILDCARD) {
      isWildcard = true;
    } else if (trimmed) {
      signals = trimmed
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
    }
  }

  // Default to wildcard if nothing specified
  if (signals.length === 0 && !isWildcard) {
    isWildcard = true;
  }

  return { storage, storageKey, signals, isWildcard };
}

function loadFromStorage(config: PersistConfig, ctx: RuntimeContext): void {
  try {
    const stored = config.storage.getItem(config.storageKey);
    if (!stored) return;

    const data = JSON.parse(stored);
    if (!data || typeof data !== "object") return;

    ctx.startBatch();
    try {
      if (config.isWildcard) {
        ctx.mergePatch(data);
      } else {
        const patch = Object.fromEntries(
          config.signals.filter((signal) => signal in data).map((signal) => [signal, data[signal]])
        );

        if (Object.keys(patch).length > 0) {
          ctx.mergePatch(patch);
        }
      }
    } finally {
      ctx.endBatch();
    }
  } catch {
    // Storage errors are expected in some environments
  }
}

function getSignalsFromElement(el: HTMLElement): string[] {
  const signalsAttr = el.getAttribute("data-signals");
  if (!signalsAttr) return [];

  try {
    const signals = JSON.parse(signalsAttr);
    return Object.keys(signals);
  } catch {
    return [];
  }
}

function saveToStorage(
  config: PersistConfig,
  _ctx: RuntimeContext,
  signalData: Record<string, any>
): void {
  try {
    const stored = config.storage.getItem(config.storageKey);
    const existing = stored ? JSON.parse(stored) : {};
    const merged = { ...existing, ...signalData };

    if (Object.keys(merged).length > 0) {
      config.storage.setItem(config.storageKey, JSON.stringify(merged));
    }
  } catch {
    // Storage quota exceeded or other storage errors
  }
}

const persistAttributePlugin: AttributePlugin = {
  type: "attribute",
  name: "persist",
  keyReq: "allowed",
  valReq: "allowed",
  shouldEvaluate: false,

  onLoad(ctx: RuntimeContext): OnRemovalFn | void {
    const config = parseConfig(ctx);
    if (!config) return;

    loadFromStorage(config, ctx);

    const throttleMs = ctx.mods.has("immediate")
      ? 0
      : Number.parseInt(String(ctx.mods.get("throttle") ?? DEFAULT_THROTTLE));

    let cachedSignalData: Record<string, any> = {};

    const persistData = () => {
      if (Object.keys(cachedSignalData).length > 0) {
        saveToStorage(config, ctx, cachedSignalData);
      }
    };

    const throttledPersist = throttleMs > 0 ? createDebounce(persistData, throttleMs) : persistData;

    // Single-pass signal tracking with data collection
    const cleanup = ctx.effect(() => {
      const signals = config.isWildcard ? getSignalsFromElement(ctx.el) : config.signals;

      const data: Record<string, any> = {};

      // Single pass: create dependencies and collect values
      for (const signal of signals) {
        if (ctx.hasPath(signal)) {
          data[signal] = ctx.getPath(signal);
        }
      }

      cachedSignalData = data;
      throttledPersist();
    });

    return cleanup;
  },
};

export default persistAttributePlugin;
