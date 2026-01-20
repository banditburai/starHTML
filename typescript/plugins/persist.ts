import { effect, getPath, mergePatch } from "datastar";
import { createDebounce } from "./throttle.js";
import type { AttributeContext, AttributePlugin, OnRemovalFn } from "./types.js";

const DEFAULT_STORAGE_KEY = "starhtml-persist";
const DEFAULT_THROTTLE = 500;

function getStorage(isSession: boolean): Storage | null {
  try {
    const storage = isSession ? sessionStorage : localStorage;
    storage.setItem("__test__", "1");
    storage.removeItem("__test__");
    return storage;
  } catch {
    return null;
  }
}

function getModValue(mods: Map<string, any>, key: string): any {
  const val = mods.get(key);
  return val instanceof Set ? Array.from(val)[0] : val;
}

function parseSignals(value: string): string[] {
  // Support both comma and semicolon separators (Python lists use semicolon)
  return value
    .split(/[,;]/)
    .map((s) => s.trim())
    .map((s) => (s.startsWith("$") ? s.slice(1) : s))
    .filter(Boolean);
}

function loadFromStorage(storage: Storage, key: string, signals: string[]): void {
  try {
    const stored = storage.getItem(key);
    if (!stored) return;

    const data = JSON.parse(stored);
    if (!data || typeof data !== "object") return;

    if (signals.length === 0) return;

    const patch = Object.fromEntries(
      signals.filter((signal) => signal in data).map((signal) => [signal, data[signal]])
    );
    if (Object.keys(patch).length > 0) {
      mergePatch(patch);
    }
  } catch {}
}

function saveToStorage(storage: Storage, key: string, data: Record<string, any>): void {
  if (Object.keys(data).length === 0) return;

  try {
    const stored = storage.getItem(key);
    const existing = stored ? JSON.parse(stored) : {};
    storage.setItem(key, JSON.stringify({ ...existing, ...data }));
  } catch {}
}

const persistAttributePlugin: AttributePlugin = {
  name: "persist",
  requirement: {
    key: "allowed",
    value: "allowed",
  },

  apply(ctx: AttributeContext): OnRemovalFn | void {
    const { el, key, value, mods } = ctx;
    const storage = getStorage(mods.has("session"));
    if (!storage) {
      el.setAttribute("data-persist-ready", "");
      return;
    }

    const customKey = key || getModValue(mods, "key");
    const storageKey = customKey
      ? `${DEFAULT_STORAGE_KEY}-${String(customKey)}`
      : DEFAULT_STORAGE_KEY;

    const trimmed = value?.trim();
    const signals = trimmed ? parseSignals(trimmed) : [];

    if (signals.length > 0) {
      loadFromStorage(storage, storageKey, signals);
    }

    // Mark element ready to prevent flash of default values
    el.setAttribute("data-persist-ready", "");

    const throttleMs = mods.has("immediate")
      ? 0
      : Number.parseInt(String(getModValue(mods, "throttle") ?? DEFAULT_THROTTLE));

    let cachedData: Record<string, any> = {};
    let lastSavedData: Record<string, any> | null = null;
    const isShallowEqual = (a: Record<string, any> | null, b: Record<string, any>): boolean => {
      if (!a) return false;
      const aKeys = Object.keys(a);
      const bKeys = Object.keys(b);
      if (aKeys.length !== bKeys.length) return false;
      for (const k of aKeys) {
        if (a[k] !== b[k]) return false;
      }
      return true;
    };
    const persist = () => {
      if (Object.keys(cachedData).length === 0) return;
      if (isShallowEqual(lastSavedData, cachedData)) return;
      saveToStorage(storage, storageKey, cachedData);
      lastSavedData = { ...cachedData };
    };
    const throttledPersist = throttleMs > 0 ? createDebounce(persist, throttleMs) : persist;

    if (signals.length === 0) return;

    return effect(() => {
      const data: Record<string, any> = {};
      for (const signal of signals) {
        try {
          data[signal] = getPath(signal);
        } catch {}
      }
      cachedData = data;
      throttledPersist();
    });
  },
};

export default persistAttributePlugin;
