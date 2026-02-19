export const DEBUGGER_TAG = "STARHTML-DEBUGGER";

type RecordConsumer = (records: MutationRecord[]) => void;

let captureConsumer: RecordConsumer | null = null;
let timelineConsumer: RecordConsumer | null = null;
let observer: MutationObserver | null = null;

const OBSERVER_CONFIG: MutationObserverInit = {
  childList: true,
  attributes: true,
  attributeOldValue: true,
  characterData: true,
  characterDataOldValue: true,
  subtree: true,
};

function ensureObserver(): void {
  if (observer) return;
  observer = new MutationObserver((records) => {
    if (captureConsumer) captureConsumer(records);
    if (timelineConsumer) timelineConsumer(records);
  });
  observer.observe(document.body, OBSERVER_CONFIG);
}

function maybeDisconnect(): void {
  if (observer && captureConsumer === null && timelineConsumer === null) {
    observer.disconnect();
    observer = null;
  }
}

export function subscribeCapture(fn: RecordConsumer): () => void {
  captureConsumer = fn;
  ensureObserver();
  return () => {
    captureConsumer = null;
    maybeDisconnect();
  };
}

export function subscribeTimeline(fn: RecordConsumer): () => void {
  timelineConsumer = fn;
  ensureObserver();
  return () => {
    timelineConsumer = null;
    maybeDisconnect();
  };
}

export function isDebuggerMutation(r: MutationRecord): boolean {
  if (r.target instanceof Element && r.target.tagName === DEBUGGER_TAG) return true;
  if (r.type === "childList") {
    for (const node of r.addedNodes) {
      if (node instanceof Element && node.tagName === DEBUGGER_TAG) return true;
    }
    for (const node of r.removedNodes) {
      if (node instanceof Element && node.tagName === DEBUGGER_TAG) return true;
    }
  }
  return false;
}

/** Delivers drained records to all active consumers so no data is silently lost. */
export function drainRecords(): void {
  if (!observer) return;
  const records = observer.takeRecords();
  if (records.length > 0) {
    if (captureConsumer) captureConsumer(records);
    if (timelineConsumer) timelineConsumer(records);
  }
}
