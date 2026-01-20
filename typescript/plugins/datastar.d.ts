/**
 * Type declarations for Datastar (resolved at runtime via import map).
 */

declare module 'datastar' {
  /** Merge a patch object into the reactive signal store. */
  export function mergePatch(patch: Record<string, unknown>): void;

  /** Get a value from the signal store by dot-notation path. */
  export function getPath(path: string): unknown;

  /** Create a reactive effect that re-runs when dependencies change. */
  export function effect(fn: () => void): () => void;

  /** Register an attribute plugin with Datastar. */
  export function attribute(plugin: {
    name: string;
    requirement?: unknown;
    apply: (ctx: unknown) => void | (() => void);
  }): void;

  /** Register an action plugin with Datastar. */
  export function action(plugin: {
    name: string;
    apply: (ctx: unknown, ...args: unknown[]) => void | Promise<void>;
  }): void;
}
