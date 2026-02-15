/**
 * StarHTML Debugger - Phase 1
 * Captures SSE events, signal patches, and DOM mutations.
 * Renders a bottom-drawer debug panel in Shadow DOM.
 */

// Types
export interface DebugSSEEvent {
  type: string;
  timestamp: number;
  el: HTMLElement | null;
  argsRaw: Record<string, unknown>;
  debugMeta?: {
    seq: number;
    ts: number;
    handler: string;
    route: string;
  };
  morphRecords?: MutationRecord[];
}

// Ring buffer for events
const MAX_EVENTS = 3000;
const PRESERVE_INITIAL = 200;
let events: DebugSSEEvent[] = [];

export function getEvents(): readonly DebugSSEEvent[] {
  return events;
}

export function clearEvents(): void {
  events = [];
}

// Will be populated in subsequent tasks
export function init(): void {
  console.log("[starhtml-debugger] initialized");
}
