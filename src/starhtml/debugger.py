"""StarHTML Debugger - auto-injected when debug=True.

The StarElements component (StarHTMLDebugger) is defined at module level
but only available when starelements is installed. setup_debugger() handles
the graceful fallback.
"""
# ruff: noqa: F841

import sys

from .xtend import NotStr, Script


_HAS_STARELEMENTS = False


def setup_debugger(app):
    """Register the StarElements debugger with the app.

    Falls back to a warning if starelements is not installed.
    The component setup script also calls capture.init() as a no-op
    safeguard — the early hdrs script ensures capture starts first.
    """
    if not _HAS_STARELEMENTS:
        print(
            "WARNING: starelements not installed — debugger disabled. "
            "Install with: uv pip install 'starhtml[debug]'",
            file=sys.stderr,
        )
        return

    app.register(StarHTMLDebugger)

    # Early capture init — start intercepting SSE events before component mounts
    app.hdrs.append(
        Script(
            "import {init} from '/_pkg/starhtml/plugins/debugger-capture.js'; init();",
            type="module",
        )
    )

    # Component tag in footer — instantiates the debugger panel
    app.ftrs.append(NotStr("<starhtml-debugger></starhtml-debugger>"))


# ============================================================
# Component definition (requires starelements)
# ============================================================

try:
    from starelements import Local, element

    from .tags import Button, Div, Input, Span
    from .xtend import Style

    _HAS_STARELEMENTS = True
except ImportError:
    # starelements not installed — component will not be defined.
    # setup_debugger() handles this gracefully via the sentinel check.
    pass
else:
    DEBUGGER_CSS = """
  :host {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 99999;
    font-family: ui-monospace, 'SF Mono', Monaco, 'Cascadia Mono', monospace;
    font-size: 12px;
    line-height: 1.5;
    color-scheme: dark;
  }
  :host, :host * { box-sizing: border-box; }
  .debugger-tab {
    position: absolute;
    bottom: 100%;
    right: 20px;
    background: #1e1e2e;
    color: #cdd6f4;
    padding: 4px 16px;
    border-radius: 6px 6px 0 0;
    cursor: pointer;
    font-size: 11px;
    user-select: none;
    border: 1px solid #45475a;
    border-bottom: none;
  }
  .debugger-tab .badge {
    background: #f38ba8;
    color: #1e1e2e;
    border-radius: 8px;
    padding: 0 5px;
    margin-left: 6px;
    font-size: 10px;
  }
  .debugger-panel {
    background: #1e1e2e;
    color: #cdd6f4;
    border-top: 2px solid #89b4fa;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  .resize-handle {
    height: 6px;
    cursor: ns-resize;
    background: transparent;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  .resize-handle::after {
    content: '';
    width: 36px;
    height: 3px;
    border-radius: 2px;
    background: #45475a;
  }
  .resize-handle:hover::after { background: #89b4fa; }
  .tab-bar {
    display: flex;
    border-bottom: 1px solid #45475a;
    padding: 0 8px;
    cursor: ns-resize;
    user-select: none;
  }
  .tab-btn {
    padding: 6px 16px;
    background: none;
    border: none;
    color: #9399b2;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    font-family: inherit;
    font-size: 11px;
    transition: color 0.1s ease, border-color 0.1s ease;
  }
  .tab-btn.active {
    color: #89b4fa;
    border-bottom-color: #89b4fa;
  }
  .tab-btn:hover { color: #cdd6f4; }
  .tab-btn:focus-visible { outline: 2px solid #89b4fa; outline-offset: -2px; }
  .tab-content {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
    position: relative;
    scrollbar-width: thin;
    scrollbar-color: #45475a transparent;
  }
  .tab-content::-webkit-scrollbar { width: 8px; }
  .tab-content::-webkit-scrollbar-track { background: transparent; }
  .tab-content::-webkit-scrollbar-thumb { background: #45475a; border-radius: 4px; }
  .tab-content::-webkit-scrollbar-thumb:hover { background: #585b70; }
  .toolbar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 8px;
    user-select: none;
    border-bottom: 1px solid #313244;
  }
  .toolbar input {
    background: #313244;
    border: 1px solid #45475a;
    color: #cdd6f4;
    padding: 4px 8px;
    border-radius: 4px;
    font-family: inherit;
    font-size: 11px;
  }
  .toolbar input::placeholder { color: #585b70; opacity: 1; }
  .toolbar input:focus-visible { outline: 2px solid #89b4fa; outline-offset: -1px; }
  .toolbar button {
    background: #313244;
    border: 1px solid #45475a;
    color: #cdd6f4;
    padding: 4px 8px;
    border-radius: 4px;
    cursor: pointer;
    font-family: inherit;
    font-size: 11px;
  }
  .toolbar button:hover { background: #45475a; }
  .toolbar button:focus-visible { outline: 2px solid #89b4fa; outline-offset: -1px; }
  .toolbar .clear-events-btn { color: #a6adc8; }
  .toolbar .clear-events-btn:hover { color: #f38ba8; background: #3e1525; border-color: #f38ba8; }
  .filter-wrap { position: relative; display: flex; align-items: center; }
  .filter-wrap .clear-filter-btn {
    position: absolute; right: 4px; top: 50%; transform: translateY(-50%);
    background: none; border: none; color: #9399b2; cursor: pointer;
    font-size: 14px; padding: 0 4px; line-height: 1;
  }
  .filter-wrap .clear-filter-btn:hover { color: #cdd6f4; }
  .toolbar .count { color: #9399b2; margin-left: auto; }
  .event-list { display: flex; flex-direction: column; }
  .event-row {
    display: flex;
    align-items: baseline;
    gap: 8px;
    padding: 4px 8px;
    border-bottom: 1px solid #11111b;
    cursor: pointer;
    white-space: nowrap;
  }
  .event-row::before {
    content: '\\25B8';
    color: #585b70;
    flex-shrink: 0;
    width: 12px;
    text-align: center;
    font-size: 10px;
  }
  .event-row.expanded::before {
    content: '\\25BE';
    color: #9399b2;
  }
  .event-row:hover { background: #2a2b3d; }
  .event-row.expanded { background: #313244; border-bottom-color: transparent; }
  .event-time { color: #9399b2; flex-shrink: 0; }
  .event-type {
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: 600;
    flex-shrink: 0;
    min-width: 56px;
    text-align: center;
  }
  .type-signals { background: #1e3a5f; color: #89b4fa; }
  .type-elements { background: #1e3f2a; color: #a6e3a1; }
  .type-script { background: #2e1f5e; color: #cba6f7; }
  .type-lifecycle { background: #313244; color: #bac2de; }
  .type-error { background: #3e1525; color: #f38ba8; }
  .event-handler { color: #f9e2af; flex-shrink: 0; }
  .event-route { color: #9399b2; overflow: hidden; text-overflow: ellipsis; min-width: 0; }
  .event-detail {
    padding: 6px 8px 6px 24px;
    background: #181825;
    border-bottom: 1px solid #11111b;
    border-left: 2px solid #89b4fa;
    white-space: pre-wrap;
    word-break: break-word;
    overflow-wrap: break-word;
    font-size: 11px;
    color: #a6adc8;
    max-height: 200px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: #45475a transparent;
  }
  .event-detail::-webkit-scrollbar { width: 6px; }
  .event-detail::-webkit-scrollbar-track { background: transparent; }
  .event-detail::-webkit-scrollbar-thumb { background: #45475a; border-radius: 3px; }
  .jump-btn {
    position: sticky;
    bottom: 8px;
    float: right;
    margin-right: 8px;
    background: #89b4fa;
    color: #1e1e2e;
    border: none;
    padding: 4px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-family: inherit;
    font-size: 11px;
    font-weight: 600;
    z-index: 1;
  }
  .jump-btn:hover { background: #b4d0fb; }
  .detail-section { margin-bottom: 6px; }
  .detail-section:last-child { margin-bottom: 0; }
  .detail-header { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
  .detail-header .mode-badge {
    background: #313244; color: #cba6f7; padding: 1px 6px; border-radius: 3px;
    font-size: 10px; font-weight: 600; text-transform: uppercase;
  }
  .detail-header .target { color: #89b4fa; }
  .detail-label { color: #585b70; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }
  .html-block {
    background: #11111b; padding: 6px 8px; border-radius: 3px; border: 1px solid #313244;
    overflow-x: auto; white-space: pre-wrap; word-break: break-word;
  }
  .html-block .ht { color: #89b4fa; }
  .html-block .ha { color: #f9e2af; }
  .html-block .hv { color: #a6e3a1; }
  .html-block .hx { color: #9399b2; }
  .morph-summary { color: #a6e3a1; margin-bottom: 4px; }
  .morph-list { padding-left: 12px; }
  .morph-item { padding: 1px 0; }
  .morph-item .added { color: #a6e3a1; }
  .morph-item .removed { color: #f38ba8; }
  .morph-item .changed { color: #f9e2af; }
  .morph-item .selector { color: #89b4fa; }
  .morph-item .old-val { color: #f38ba8; text-decoration: line-through; }
  .morph-item .new-val { color: #a6e3a1; }
  .morph-item .flash-warn { color: #f9e2af; }
  .event-preview { color: #9399b2; overflow: hidden; text-overflow: ellipsis; min-width: 0; flex: 1; }
  .morph-badge { color: #a6e3a1; flex-shrink: 0; font-size: 10px; }
  .type-chips { display: flex; gap: 4px; align-items: center; }
  .type-chip {
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 600;
    cursor: pointer;
    border: 1px solid transparent;
    opacity: 0.4;
    transition: opacity 0.1s ease;
    user-select: none;
  }
  .type-chip:hover { opacity: 0.7; }
  .type-chip.active { opacity: 1; }
  .chip-signals { background: #1e3a5f; color: #89b4fa; border-color: #1e3a5f; }
  .chip-signals.active { border-color: #89b4fa; }
  .chip-elements { background: #1e3f2a; color: #a6e3a1; border-color: #1e3f2a; }
  .chip-elements.active { border-color: #a6e3a1; }
  .chip-script { background: #2e1f5e; color: #cba6f7; border-color: #2e1f5e; }
  .chip-script.active { border-color: #cba6f7; }
  .chip-lifecycle { background: #313244; color: #bac2de; border-color: #313244; }
  .chip-lifecycle.active { border-color: #bac2de; }
  .toolbar-sep { width: 1px; height: 16px; background: #45475a; flex-shrink: 0; }
  .group-0 { border-left: 2px solid #89b4fa; }
  .group-1 { border-left: 2px solid #a6e3a1; }
  .group-2 { border-left: 2px solid #cba6f7; }
  .event-duration { color: #9399b2; flex-shrink: 0; font-size: 10px; }
  .copy-btn {
    background: #313244; border: 1px solid #45475a; color: #9399b2;
    padding: 2px 8px; border-radius: 3px; cursor: pointer;
    font-family: inherit; font-size: 10px; float: right;
  }
  .copy-btn:hover { background: #45475a; color: #cdd6f4; }
  .copy-btn.copied { color: #a6e3a1; border-color: #a6e3a1; }
  /* --- Signals tab --- */
  .signal-list { display: flex; flex-direction: column; }
  .signal-group-header {
    display: flex; align-items: center; gap: 6px;
    padding: 6px 8px; cursor: pointer; user-select: none;
    color: #cdd6f4; font-weight: 600; font-size: 11px;
    border-bottom: 1px solid #11111b;
  }
  .signal-group-header:hover { background: #2a2b3d; }
  .signal-group-header .group-toggle {
    color: #585b70; width: 12px; text-align: center; font-size: 10px;
  }
  .signal-group-header .group-count { color: #9399b2; font-weight: 400; }
  .signal-row {
    display: flex; align-items: baseline; gap: 8px;
    padding: 3px 8px 3px 28px;
    border-bottom: 1px solid #11111b; cursor: pointer;
  }
  .signal-row:hover { background: #2a2b3d; }
  .signal-name {
    color: #cdd6f4; flex-shrink: 0; min-width: 120px;
    overflow: hidden; text-overflow: ellipsis;
  }
  .signal-value {
    flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
  .signal-persist { color: #9399b2; flex-shrink: 0; font-size: 10px; }
  .sv-string { color: #a6e3a1; }
  .sv-number { color: #89b4fa; }
  .sv-boolean { color: #fab387; }
  .sv-object, .sv-array { color: #9399b2; }
  @keyframes signal-flash {
    0% { background: #2a3f1e; }
    100% { background: transparent; }
  }
  .signal-changed { animation: signal-flash 2s ease-out; }
  .signal-stale .signal-name { color: #585b70; }
  .signal-stale .signal-value { color: #585b70; }
  .signal-removed { opacity: 0.4; text-decoration: line-through; }
  .signal-removed-badge { color: #f9e2af; font-size: 10px; }
  .signal-detail {
    padding: 6px 8px 6px 28px; background: #181825;
    border-bottom: 1px solid #11111b; border-left: 2px solid #89b4fa;
    font-size: 11px; color: #a6adc8;
  }
  .signal-detail .sd-row { padding: 2px 0; }
  .signal-detail .sd-label {
    color: #585b70; font-size: 10px; text-transform: uppercase; margin-right: 8px;
  }
  .signal-detail pre {
    margin: 2px 0; padding: 4px 6px; background: #11111b;
    border-radius: 3px; border: 1px solid #313244;
    white-space: pre-wrap; word-break: break-word; max-height: 150px;
    overflow-y: auto; scrollbar-width: thin; scrollbar-color: #45475a transparent;
  }
  .sd-meta { color: #585b70; font-size: 10px; }
  /* Detail panel input for string/number editing */
  .signal-detail-input {
    background: #11111b; border: 1px solid #45475a; color: #cdd6f4;
    padding: 4px 8px; border-radius: 3px; font-family: inherit; font-size: 12px;
    min-width: 80px; max-width: 100%; outline: none;
  }
  .signal-detail-input:focus { border-color: #89b4fa; }
  /* Boolean toggle button */
  .signal-toggle-btn {
    background: #313244; border: 1px solid #45475a; color: #fab387;
    padding: 3px 12px; border-radius: 3px; cursor: pointer;
    font-family: inherit; font-size: 11px; font-weight: 600;
  }
  .signal-toggle-btn:hover { background: #45475a; border-color: #89b4fa; }
  /* Inline edit input (string/number) */
  .signal-edit-input {
    background: #313244; border: 1px solid #89b4fa; color: #cdd6f4;
    padding: 1px 6px; border-radius: 3px; font-family: inherit; font-size: 11px;
    width: 100%; outline: none;
  }
  /* JSON textarea (array editing) */
  .signal-edit-textarea {
    background: #11111b; border: 1px solid #45475a; color: #cdd6f4;
    padding: 6px 8px; border-radius: 3px; font-family: inherit; font-size: 11px;
    width: 100%; min-height: 80px; resize: vertical; white-space: pre; tab-size: 2;
  }
  .signal-edit-textarea:focus { border-color: #89b4fa; outline: none; }
  /* Editor action buttons */
  .signal-json-editor { margin-top: 4px; }
  .signal-edit-actions { display: flex; gap: 6px; margin-top: 4px; align-items: center; }
  .signal-edit-save {
    background: #89b4fa; color: #1e1e2e; border: none;
    padding: 3px 10px; border-radius: 3px; cursor: pointer;
    font-family: inherit; font-size: 10px; font-weight: 600;
  }
  .signal-edit-save:hover { background: #b4d0fb; }
  .signal-edit-cancel {
    background: #313244; border: 1px solid #45475a; color: #cdd6f4;
    padding: 3px 10px; border-radius: 3px; cursor: pointer;
    font-family: inherit; font-size: 10px;
  }
  .signal-edit-cancel:hover { background: #45475a; }
  .signal-edit-error { font-size: 10px; color: #f38ba8; margin-left: 4px; }
  /* Edit JSON button in detail panel */
  .signal-edit-obj-btn {
    background: #313244; border: 1px solid #45475a; color: #9399b2;
    padding: 2px 8px; border-radius: 3px; cursor: pointer;
    font-family: inherit; font-size: 10px;
  }
  .signal-edit-obj-btn:hover { background: #45475a; color: #cdd6f4; }
"""

    DEBUGGER_SETUP = """
// --- Lifecycle + persistence ---

capture.init();

const unsub = capture.subscribe((ev) => {
    $$event_count = capture.getEventCount();
    if (!$$is_open) {
        const allowed = capture.buildAllowedTypes(activeTypeFilters);
        if (!allowed || allowed.has(ev.type)) $$unseen_count = $$unseen_count + 1;
    }
});
onCleanup(unsub);

try {
    const storedOpen = sessionStorage.getItem('starhtml-debug-open');
    if (storedOpen === 'true') $$is_open = true;
    const storedHeight = Number(sessionStorage.getItem('starhtml-debug-height'));
    if (storedHeight > 0) $$panel_height = storedHeight;
    const storedTab = sessionStorage.getItem('starhtml-debug-tab');
    if (storedTab) $$active_tab = storedTab;
} catch(e) { /* sessionStorage unavailable */ }

effect(() => sessionStorage.setItem('starhtml-debug-open', String($$is_open)));
effect(() => sessionStorage.setItem('starhtml-debug-height', String($$panel_height)));
effect(() => sessionStorage.setItem('starhtml-debug-tab', $$active_tab));

effect(() => {
    if ($$is_open) capture.startObserving();
    else capture.stopObserving();
});
onCleanup(() => capture.stopObserving());

// Push page content above the panel
effect(() => {
    document.documentElement.style.paddingBottom = $$is_open ? $$panel_height + 'px' : '';
});
onCleanup(() => { document.documentElement.style.paddingBottom = ''; });

effect(() => { if ($$is_open) $$unseen_count = 0; });

// --- Render pipeline ---

// Plain vars, not signals — no reactivity needed
let lastRenderedIds = [];
let needsFullRender = true;
let rafPending = false;
let userAtBottom = true;
let activeTypeFilters = new Set(['signals', 'elements', 'script']);

const eventListEl = refs('event_list');
const eventCountLabel = refs('event_count_label');
const copyAllBtn = refs('copy_all_btn');
const clearEventsBtn = refs('clear_events_btn');
const tabContentEl = refs('tab_content');
const jumpBtn = refs('jump_btn');

if (tabContentEl) {
    tabContentEl.addEventListener('scroll', () => {
        userAtBottom = tabContentEl.scrollTop + tabContentEl.clientHeight >= tabContentEl.scrollHeight - 20;
    });
}

const chipRefs = {
    signals: refs('chip_signals'),
    elements: refs('chip_elements'),
    script: refs('chip_script'),
    lifecycle: refs('chip_lifecycle'),
};

// Only trigger full render if the active set actually changed
// (Datastar data-class:active bindings can re-trigger this effect spuriously)
effect(() => {
    const newFilters = new Set();
    if ($$chip_signals_on) newFilters.add('signals');
    if ($$chip_elements_on) newFilters.add('elements');
    if ($$chip_script_on) newFilters.add('script');
    if ($$chip_lifecycle_on) newFilters.add('lifecycle');
    const changed = newFilters.size !== activeTypeFilters.size ||
        [...newFilters].some(t => !activeTypeFilters.has(t));
    activeTypeFilters = newFilters;
    if (changed) {
        $$expanded_id = -1;
        needsFullRender = true;
        scheduleRender();
    }
});

if (clearEventsBtn) {
    clearEventsBtn.addEventListener('click', () => {
        const evts = capture.getEvents();
        const latest = evts[evts.length - 1];
        $$visible_since_id = latest ? latest.id + 1 : 0;
        $$expanded_id = -1;
    });
}

if (jumpBtn) {
    jumpBtn.addEventListener('click', () => {
        if (tabContentEl) tabContentEl.scrollTop = tabContentEl.scrollHeight;
        userAtBottom = true;
        $$show_jump_btn = false;
    });
}

if (copyAllBtn) {
    copyAllBtn.addEventListener('click', () => {
        const allowedTypes = capture.buildAllowedTypes(activeTypeFilters);
        const filtered = capture.getFilteredEvents($$visible_since_id, allowedTypes, $$filter_text);
        const text = capture.formatAllEventsForExport(filtered);
        navigator.clipboard.writeText(text).then(() => {
            copyAllBtn.textContent = 'Copied!';
            copyAllBtn.classList.add('copied');
            setTimeout(() => { copyAllBtn.textContent = 'Copy All'; copyAllBtn.classList.remove('copied'); }, 1500);
        }).catch(() => {
            copyAllBtn.textContent = 'Failed';
            setTimeout(() => { copyAllBtn.textContent = 'Copy All'; }, 1500);
        });
    });
}

if (eventListEl) {
    eventListEl.addEventListener('click', (e) => {
        const target = e.target;

        const copyBtn = target.closest('.copy-btn[data-copy-eid]');
        if (copyBtn) {
            e.stopPropagation();
            const eid = Number(copyBtn.dataset.copyEid);
            const evts = capture.getEvents();
            const ev = evts.find(ev => ev.id === eid);
            if (!ev) return;
            const text = capture.formatSingleEventForExport(ev);
            navigator.clipboard.writeText(text).then(() => {
                copyBtn.textContent = 'Copied!';
                copyBtn.classList.add('copied');
                setTimeout(() => { copyBtn.textContent = 'Copy'; copyBtn.classList.remove('copied'); }, 1500);
            }).catch(() => {
                copyBtn.textContent = 'Failed';
                setTimeout(() => { copyBtn.textContent = 'Copy'; }, 1500);
            });
            return;
        }

        const row = target.closest('.event-row');
        if (!row) return;
        const eid = Number(row.dataset.eid);
        const wasExpanded = $$expanded_id === eid;
        const prevExpandedId = $$expanded_id;
        $$expanded_id = wasExpanded ? -1 : eid;

        if (prevExpandedId !== -1) {
            const prevRow = eventListEl.querySelector('.event-row[data-eid="' + prevExpandedId + '"]');
            if (prevRow) {
                prevRow.classList.remove('expanded');
                const prevDetail = prevRow.nextElementSibling;
                if (prevDetail && prevDetail.classList.contains('event-detail')) prevDetail.remove();
            }
        }

        if (!wasExpanded) {
            row.classList.add('expanded');
            const evts = capture.getEvents();
            const ev = evts.find(ev => ev.id === eid);
            if (ev) {
                const detail = document.createElement('div');
                detail.className = 'event-detail';
                detail.innerHTML = '<button class="copy-btn" data-copy-eid="' + ev.id + '">Copy</button>' + capture.formatEventDetail(ev);
                row.insertAdjacentElement('afterend', detail);
            }
        }
    });
}

function scheduleRender() {
    if (rafPending) return;
    rafPending = true;
    requestAnimationFrame(() => {
        rafPending = false;
        if ($$is_open && $$active_tab === 'sse') renderSSETab();
    });
}

function renderSSETab() {
    if (!eventListEl) return;

    const allowedTypes = capture.buildAllowedTypes(activeTypeFilters);
    const filtered = capture.getFilteredEvents($$visible_since_id, allowedTypes, $$filter_text);

    const visible = capture.getFilteredEvents($$visible_since_id, null, '');
    for (const chip of capture.CHIP_CATEGORIES) {
        const count = visible.filter(ev => chip.types.includes(ev.type)).length;
        const chipEl = chipRefs[chip.key];
        if (chipEl) chipEl.textContent = chip.label.charAt(0).toUpperCase() + chip.label.slice(1) + ' (' + count + ')';
    }

    if (eventCountLabel) {
        eventCountLabel.textContent = filtered.length + ' event' + (filtered.length !== 1 ? 's' : '');
    }

    const wasAtBottom = userAtBottom;
    const filteredIds = filtered.map(ev => ev.id);

    if (!needsFullRender && filteredIds.length >= lastRenderedIds.length) {
        let canIncrement = true;
        for (let i = 0; i < lastRenderedIds.length; i++) {
            if (lastRenderedIds[i] !== filteredIds[i]) { canIncrement = false; break; }
        }
        if (canIncrement) {
            if (filteredIds.length > lastRenderedIds.length) {
                const newEvents = filtered.slice(lastRenderedIds.length);
                let appendHtml = '';
                for (const ev of newEvents) appendHtml += capture.buildRowHtml(ev);
                eventListEl.insertAdjacentHTML('beforeend', appendHtml);
                lastRenderedIds = filteredIds;
                if (wasAtBottom && tabContentEl) tabContentEl.scrollTop = tabContentEl.scrollHeight;
                $$show_jump_btn = !userAtBottom && filtered.length > 0;
            }
            return;
        }
    }

    // innerHTML wipes detail divs, so reset expand state
    $$expanded_id = -1;
    let html = '';
    for (const ev of filtered) html += capture.buildRowHtml(ev);
    eventListEl.innerHTML = html;
    lastRenderedIds = filteredIds;
    needsFullRender = false;

    if (wasAtBottom && tabContentEl) tabContentEl.scrollTop = tabContentEl.scrollHeight;
    $$show_jump_btn = !userAtBottom && filtered.length > 0;
}

// $$expanded_id deliberately excluded — expand/collapse is imperative (click handler)
effect(() => {
    void $$event_count;
    void $$filter_text;
    void $$visible_since_id;
    if ($$is_open && $$active_tab === 'sse') scheduleRender();
});

// Guard against spurious fires from Datastar data-bind processing
let _lastFilterText = $$filter_text;
let _lastVisibleSinceId = $$visible_since_id;
effect(() => {
    const ft = $$filter_text;
    const vsid = $$visible_since_id;
    if (ft !== _lastFilterText || vsid !== _lastVisibleSinceId) {
        _lastFilterText = ft;
        _lastVisibleSinceId = vsid;
        needsFullRender = true;
    }
});

// --- Resize + keyboard ---

const resizeHandle = refs('resize_handle');
const tabBar = refs('tab_bar');

const startResize = (e) => {
    const startY = e.clientY;
    const startH = $$panel_height;
    const onMove = (e) => {
        $$panel_height = Math.max(150, Math.min(window.innerHeight * 0.8, startH - (e.clientY - startY)));
    };
    const onUp = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
    };
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
};

if (resizeHandle) resizeHandle.addEventListener('mousedown', startResize);

// Drag from empty tab-bar space, not tab buttons
if (tabBar) {
    tabBar.addEventListener('mousedown', (e) => {
        if (e.target.closest('.tab-btn')) return;
        startResize(e);
    });
}

// Ctrl+Shift+. (or Cmd+Shift+.)
const onKeydown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.code === 'Period') {
        e.preventDefault();
        $$is_open = !$$is_open;
    }
};
document.addEventListener('keydown', onKeydown);
onCleanup(() => document.removeEventListener('keydown', onKeydown));

// --- Signals tab ---

const debuggerNs = el.getAttribute('data-star-id') || '_star_starhtml_debugger_';
// Local() signal names exist un-namespaced in the Datastar store (via data-bind)
const debuggerSignalNames = [
    'is_open', 'panel_height', 'active_tab', 'unseen_count',
    'filter_text', 'visible_since_id', 'expanded_id', 'event_count',
    'chip_signals_on', 'chip_elements_on', 'chip_script_on', 'chip_lifecycle_on',
    'show_jump_btn', 'signal_count', 'signal_filter', 'signal_expanded_path',
];
signals.init(debuggerNs, debuggerSignalNames);
onCleanup(() => signals.cleanup());

const signalListEl = refs('signal_list');
const signalCountLabel = refs('signal_count_label');
const signalTabCount = refs('signal_tab_count');
const signalEmpty = refs('signal_empty');
const clearPersistBtn = refs('clear_persist_btn');

let signalRafPending = false;
let collapsedGroups = new Set();
let editingPath = '';
let editingPending = false;

const signalUnsub = signals.subscribe(() => {
    const totalCount = signals.getSignalCount();
    $$signal_count = totalCount;
    if (signalCountLabel) signalCountLabel.textContent = totalCount + ' signal' + (totalCount !== 1 ? 's' : '');
    if (signalTabCount) signalTabCount.textContent = totalCount > 0 ? '(' + totalCount + ')' : '';
    if ($$is_open && $$active_tab === 'signals') scheduleSignalRender();
});
onCleanup(signalUnsub);

function scheduleSignalRender() {
    if (signalRafPending) return;
    signalRafPending = true;
    requestAnimationFrame(() => {
        signalRafPending = false;
        if ($$is_open && $$active_tab === 'signals') renderSignalsTab();
    });
}

function finishEditing() {
    editingPath = '';
    if (editingPending) { editingPending = false; renderSignalsTab(); }
}

function checkEntryLive(path) {
    const entry = signals.getEntries().get(path);
    return entry && entry.status === 'live';
}

function renderSignalsTab() {
    if (!signalListEl) return;
    if (editingPath) { editingPending = true; return; }
    const groups = signals.getGroupedEntries($$signal_filter);
    const totalCount = signals.getSignalCount();

    if (signalEmpty) signalEmpty.style.display = totalCount === 0 ? '' : 'none';

    let html = '';
    for (const group of groups) {
        const isCollapsed = collapsedGroups.has(group.namespace);
        html += signals.buildGroupHeaderHtml(group, isCollapsed);
        if (!isCollapsed) {
            for (const entry of group.entries) {
                html += signals.buildSignalRowHtml(entry);
                if ($$signal_expanded_path === entry.path) {
                    html += signals.buildSignalDetailHtml(entry);
                }
            }
        }
    }
    signalListEl.innerHTML = html;
}

if (signalListEl) {
    signalListEl.addEventListener('click', (e) => {
        const target = e.target;

        // Boolean toggle in detail panel
        const toggleBtn = target.closest('.signal-toggle-btn');
        if (toggleBtn) {
            e.stopPropagation();
            const path = toggleBtn.dataset.editPath;
            if (path && checkEntryLive(path)) {
                const entry = signals.getEntries().get(path);
                if (entry) signals.patchSignal(path, !entry.value);
                renderSignalsTab();
            }
            return;
        }

        // Edit JSON button for arrays
        const editBtn = target.closest('.signal-edit-obj-btn');
        if (editBtn) {
            e.stopPropagation();
            const path = editBtn.dataset.editPath;
            const entry = signals.getEntries().get(path);
            if (!entry) return;

            editingPath = path;
            const json = JSON.stringify(entry.value, null, 2);
            const editor = document.createElement('div');
            editor.className = 'signal-json-editor';
            editor.innerHTML =
                '<textarea class="signal-edit-textarea"></textarea>' +
                '<div class="signal-edit-actions">' +
                '<button class="signal-edit-save">Save</button>' +
                '<button class="signal-edit-cancel">Cancel</button>' +
                '<span class="signal-edit-error"></span></div>';

            const textarea = editor.querySelector('textarea');
            textarea.value = json;
            editBtn.replaceWith(editor);
            textarea.focus();

            const saveBtn = editor.querySelector('.signal-edit-save');
            const cancelBtn = editor.querySelector('.signal-edit-cancel');
            const errorSpan = editor.querySelector('.signal-edit-error');

            saveBtn.addEventListener('click', () => {
                if (!checkEntryLive(path)) { finishEditing(); return; }
                try {
                    const parsed = JSON.parse(textarea.value);
                    signals.patchSignal(path, parsed, entry.value);
                    finishEditing();
                } catch (err) {
                    errorSpan.textContent = 'Invalid JSON';
                }
            });
            cancelBtn.addEventListener('click', () => finishEditing());

            textarea.addEventListener('keydown', (ke) => {
                if (ke.key === 'Escape') { ke.preventDefault(); finishEditing(); }
                if (ke.key === 'Enter' && (ke.metaKey || ke.ctrlKey)) {
                    ke.preventDefault(); saveBtn.click();
                }
            });
            textarea.addEventListener('blur', (be) => {
                if (!editingPath) return;
                const related = be.relatedTarget;
                if (related && (related.classList.contains('signal-edit-save') ||
                        related.classList.contains('signal-edit-cancel'))) return;
                finishEditing();
            });
            return;
        }

        const header = target.closest('.signal-group-header');
        if (header) {
            const ns = header.dataset.ns ?? '';
            if (collapsedGroups.has(ns)) collapsedGroups.delete(ns);
            else collapsedGroups.add(ns);
            renderSignalsTab();
            return;
        }

        const row = target.closest('.signal-row');
        if (row) {
            const path = row.dataset.path;
            if (path) {
                $$signal_expanded_path = $$signal_expanded_path === path ? '' : path;
                renderSignalsTab();
            }
            return;
        }
    });

    // Double-click to edit primitives
    signalListEl.addEventListener('dblclick', (e) => {
        const row = e.target.closest('.signal-row');
        if (!row) return;
        const path = row.dataset.path;
        if (!path) return;
        const entry = signals.getEntries().get(path);
        if (!entry || entry.status !== 'live') return;

        // Force expand (undo click's toggle from the preceding click event)
        $$signal_expanded_path = path;

        if (entry.type === 'boolean') {
            signals.patchSignal(path, !entry.value);
            return;
        }

        if (entry.type === 'string' || entry.type === 'number') {
            editingPath = path;
            const valueSpan = row.querySelector('.signal-value');
            if (!valueSpan) return;

            const input = document.createElement('input');
            input.type = entry.type === 'number' ? 'number' : 'text';
            input.className = 'signal-edit-input';
            input.value = String(entry.value);
            valueSpan.textContent = '';
            valueSpan.appendChild(input);
            input.focus();
            input.select();

            const commit = () => {
                if (!checkEntryLive(path)) { finishEditing(); return; }
                if (entry.type === 'number') {
                    const n = Number(input.value);
                    if (!isNaN(n)) signals.patchSignal(path, n);
                } else {
                    signals.patchSignal(path, input.value);
                }
                finishEditing();
            };

            input.addEventListener('keydown', (ke) => {
                if (ke.key === 'Enter') { ke.preventDefault(); commit(); }
                if (ke.key === 'Escape') { ke.preventDefault(); finishEditing(); }
            });
            input.addEventListener('blur', () => {
                if (!editingPath) return;
                finishEditing();
            });
        }
    });

    // Detail-panel input: focus/blur to pause re-renders
    signalListEl.addEventListener('focusin', (e) => {
        const input = e.target.closest('.signal-detail-input');
        if (input) editingPath = input.dataset.editPath || '';
    });
    signalListEl.addEventListener('focusout', (e) => {
        const input = e.target.closest('.signal-detail-input');
        if (!input) return;
        const path = input.dataset.editPath;
        if (path && checkEntryLive(path)) {
            const entry = signals.getEntries().get(path);
            if (entry) {
                if (entry.type === 'number') {
                    const n = Number(input.value);
                    if (!isNaN(n)) signals.patchSignal(path, n);
                } else {
                    signals.patchSignal(path, input.value);
                }
            }
        }
        finishEditing();
    });

    // Detail-panel input: Enter to commit, Escape to collapse
    signalListEl.addEventListener('keydown', (ke) => {
        const input = ke.target.closest('.signal-detail-input');
        if (!input) return;
        const path = input.dataset.editPath;
        if (!path) return;
        if (ke.key === 'Enter') {
            ke.preventDefault();
            if (!checkEntryLive(path)) return;
            const entry = signals.getEntries().get(path);
            if (!entry) return;
            if (entry.type === 'number') {
                const n = Number(input.value);
                if (!isNaN(n)) signals.patchSignal(path, n);
            } else {
                signals.patchSignal(path, input.value);
            }
            finishEditing();
        }
        if (ke.key === 'Escape') {
            ke.preventDefault();
            $$signal_expanded_path = '';
            finishEditing();
        }
    });

    // Detail-panel input: live update for numbers (stepper arrows + typing)
    signalListEl.addEventListener('input', (e) => {
        const input = e.target.closest('.signal-detail-input');
        if (!input) return;
        const path = input.dataset.editPath;
        if (!path || !checkEntryLive(path)) return;
        const entry = signals.getEntries().get(path);
        if (entry && entry.type === 'number') {
            const n = Number(input.value);
            if (!isNaN(n)) signals.patchSignal(path, n);
        }
    });
}

if (clearPersistBtn) {
    clearPersistBtn.addEventListener('click', () => {
        signals.clearPersistedData();
        clearPersistBtn.textContent = 'Cleared!';
        setTimeout(() => { clearPersistBtn.textContent = 'Clear Persisted'; }, 1500);
    });
}

effect(() => {
    void $$signal_count;
    void $$signal_filter;
    void $$signal_expanded_path;
    if ($$is_open && $$active_tab === 'signals') scheduleSignalRender();
});
"""

    CHIP_DEFS = (
        ("Signals", "signals"),
        ("Elements", "elements"),
        ("Script", "script"),
        ("Lifecycle", "lifecycle"),
    )

    @element(
        "starhtml-debugger",
        shadow=True,
        imports={
            "capture": "/_pkg/starhtml/plugins/debugger-capture.js",
            "signals": "/_pkg/starhtml/plugins/debugger-signals.js",
        },
    )
    def StarHTMLDebugger():
        is_open = Local("is_open", False)
        panel_height = Local("panel_height", 300)
        active_tab = Local("active_tab", "sse")
        unseen_count = Local("unseen_count", 0)
        filter_text = Local("filter_text", "")
        visible_since_id = Local("visible_since_id", 0)
        expanded_id = Local("expanded_id", -1)
        event_count = Local("event_count", 0)
        chips = {key: Local(f"chip_{key}_on", key != "lifecycle") for _, key in CHIP_DEFS}
        show_jump_btn = Local("show_jump_btn", False)
        signal_count = Local("signal_count", 0)
        signal_filter = Local("signal_filter", "")
        signal_expanded_path = Local("signal_expanded_path", "")

        return Div(
            Style(DEBUGGER_CSS),
            Script(DEBUGGER_SETUP),
            Div(
                "StarHTML Debug",
                Span(
                    data_show=unseen_count > 0,
                    data_text=unseen_count,
                    cls="badge",
                ),
                data_on_click=is_open.toggle(),
                cls="debugger-tab",
            ),
            Div(
                Div(data_ref="resize_handle", cls="resize-handle"),
                Div(
                    Button(
                        "SSE Events",
                        data_on_click=active_tab.set("sse"),
                        data_class_active=active_tab == "sse",
                        cls="tab-btn",
                    ),
                    Button(
                        Span("Signals"),
                        Span(
                            data_ref="signal_tab_count",
                            style="margin-left:4px;color:#9399b2;",
                        ),
                        data_on_click=active_tab.set("signals"),
                        data_class_active=active_tab == "signals",
                        cls="tab-btn",
                    ),
                    Button(
                        "Timeline",
                        data_on_click=active_tab.set("timeline"),
                        data_class_active=active_tab == "timeline",
                        cls="tab-btn",
                    ),
                    data_ref="tab_bar",
                    cls="tab-bar",
                ),
                # SSE tab
                Div(
                    Div(
                        Div(
                            *[Span(
                                label,
                                data_ref=f"chip_{key}",
                                data_on_click=chips[key].toggle(),
                                data_class_active=chips[key],
                                cls=f"type-chip chip-{key}",
                            ) for label, key in CHIP_DEFS],
                            cls="type-chips",
                        ),
                        Div(cls="toolbar-sep"),
                        Div(
                            Input(
                                type="text",
                                placeholder="Filter...",
                                data_bind=filter_text,
                                style="width:160px;padding-right:20px",
                            ),
                            Button(
                                "\u00d7",
                                data_show=filter_text != "",
                                data_on_click=filter_text.set(""),
                                cls="clear-filter-btn",
                                title="Clear filter",
                            ),
                            cls="filter-wrap",
                        ),
                        Button(
                            "Clear Events",
                            data_ref="clear_events_btn",
                            cls="clear-events-btn",
                            title="Clear visible events",
                        ),
                        Button(
                            "Copy All",
                            data_ref="copy_all_btn",
                            title="Copy all visible events for LLM context",
                        ),
                        Span(data_ref="event_count_label", cls="count"),
                        cls="toolbar",
                    ),
                    Div(data_ref="event_list", cls="event-list"),
                    Button(
                        "Jump to latest",
                        data_show=show_jump_btn,
                        data_ref="jump_btn",
                        cls="jump-btn",
                    ),
                    data_ref="tab_content",
                    data_show=active_tab == "sse",
                    cls="tab-content",
                ),
                # Signals tab
                Div(
                    Div(
                        Div(
                            Input(
                                type="text",
                                placeholder="Filter signals...",
                                data_bind=signal_filter,
                                style="width:160px;padding-right:20px",
                            ),
                            Button(
                                "\u00d7",
                                data_show=signal_filter != "",
                                data_on_click=signal_filter.set(""),
                                cls="clear-filter-btn",
                                title="Clear filter",
                            ),
                            cls="filter-wrap",
                        ),
                        Span(data_ref="signal_count_label", cls="count"),
                        Button(
                            "Clear Persisted",
                            data_ref="clear_persist_btn",
                            cls="clear-events-btn",
                            title="Clear all persisted signal data",
                        ),
                        cls="toolbar",
                    ),
                    Div(data_ref="signal_list", cls="signal-list"),
                    Div(
                        "No signals detected",
                        data_ref="signal_empty",
                        style="color:#6c7086;padding:16px;text-align:center;",
                    ),
                    data_show=active_tab == "signals",
                    cls="tab-content",
                ),
                # Timeline tab (placeholder)
                Div(
                    Div("Coming in Phase 3", style="color:#6c7086;padding:16px;"),
                    data_show=active_tab == "timeline",
                    cls="tab-content",
                ),
                data_ref="panel",
                data_show=is_open,
                data_style_height=panel_height + "px",
                cls="debugger-panel",
            ),
        )
