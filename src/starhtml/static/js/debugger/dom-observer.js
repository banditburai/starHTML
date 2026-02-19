const DEBUGGER_TAG = "STARHTML-DEBUGGER";
let captureConsumer = null;
let timelineConsumer = null;
let observer = null;
const OBSERVER_CONFIG = {
  childList: true,
  attributes: true,
  attributeOldValue: true,
  characterData: true,
  characterDataOldValue: true,
  subtree: true
};
function ensureObserver() {
  if (observer) return;
  observer = new MutationObserver((records) => {
    if (captureConsumer) captureConsumer(records);
    if (timelineConsumer) timelineConsumer(records);
  });
  observer.observe(document.body, OBSERVER_CONFIG);
}
function maybeDisconnect() {
  if (observer && captureConsumer === null && timelineConsumer === null) {
    observer.disconnect();
    observer = null;
  }
}
function subscribeCapture(fn) {
  captureConsumer = fn;
  ensureObserver();
  return () => {
    captureConsumer = null;
    maybeDisconnect();
  };
}
function subscribeTimeline(fn) {
  timelineConsumer = fn;
  ensureObserver();
  return () => {
    timelineConsumer = null;
    maybeDisconnect();
  };
}
function isDebuggerMutation(r) {
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
function drainRecords() {
  if (!observer) return;
  const records = observer.takeRecords();
  if (records.length > 0) {
    if (captureConsumer) captureConsumer(records);
    if (timelineConsumer) timelineConsumer(records);
  }
}
export {
  DEBUGGER_TAG,
  drainRecords,
  isDebuggerMutation,
  subscribeCapture,
  subscribeTimeline
};
