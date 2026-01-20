/**
 * Datastar RC.6 Plugin Types for StarHTML Handlers
 */

export type Requirement =
  | "allowed"
  | "must"
  | "denied"
  | "exclusive"
  | {
      key?: "allowed" | "must" | "denied";
      value?: "allowed" | "must" | "denied";
    };

export interface AttributeContext {
  el: HTMLElement;
  key?: string;
  value?: string;
  rawKey: string;
  mods: Map<string, Set<string>>;
  rx?: (...args: any[]) => any;
  evt?: Event;
  error: (name: string, ctx?: Record<string, any>) => Error;
}

export interface AttributePlugin {
  name: string;
  requirement?: Requirement;
  returnsValue?: boolean;
  argNames?: string[];
  apply: (ctx: AttributeContext) => void | (() => void);
}

export type OnRemovalFn = () => void;
