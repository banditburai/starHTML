"""StarHTML Debugger - auto-injected when debug=True.

The StarElements component (StarHTMLDebugger) is defined at module level
but only available when starelements is installed. setup_debugger() handles
the graceful fallback.
"""

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
"""

    DEBUGGER_SETUP = """
// --- Lifecycle + persistence ---

// Initialize capture module (SSE event interception)
capture.init();

// Subscribe to new events from capture module
const unsub = capture.subscribe((ev) => {
    $$event_count = capture.getEventCount();
    if (!$$is_open) {
        const allowed = capture.buildAllowedTypes(activeTypeFilters);
        if (!allowed || allowed.has(ev.type)) $$unseen_count = $$unseen_count + 1;
    }
});
onCleanup(unsub);

// Restore state from sessionStorage
try {
    const storedOpen = sessionStorage.getItem('starhtml-debug-open');
    if (storedOpen === 'true') $$is_open = true;
    const storedHeight = Number(sessionStorage.getItem('starhtml-debug-height'));
    if (storedHeight > 0) $$panel_height = storedHeight;
    const storedTab = sessionStorage.getItem('starhtml-debug-tab');
    if (storedTab) $$active_tab = storedTab;
} catch(e) { /* sessionStorage unavailable (sandboxed iframe, privacy mode) */ }

// Persist signal changes to sessionStorage
effect(() => sessionStorage.setItem('starhtml-debug-open', String($$is_open)));
effect(() => sessionStorage.setItem('starhtml-debug-height', String($$panel_height)));
effect(() => sessionStorage.setItem('starhtml-debug-tab', $$active_tab));

// MutationObserver lifecycle — observe when panel is open
effect(() => {
    if ($$is_open) capture.startObserving();
    else capture.stopObserving();
});
onCleanup(() => capture.stopObserving());

// Page inset — push page content above the panel
effect(() => {
    document.documentElement.style.paddingBottom = $$is_open ? $$panel_height + 'px' : '';
});
onCleanup(() => { document.documentElement.style.paddingBottom = ''; });

// Reset unseen count when panel opens
effect(() => { if ($$is_open) $$unseen_count = 0; });

// --- Render pipeline ---

// Local render state (plain vars, not signals — no reactivity needed)
let lastRenderedIds = [];
let needsFullRender = true;
let rafPending = false;
let userAtBottom = true;
let activeTypeFilters = new Set(['signals', 'elements', 'script']);

// DOM refs
const eventListEl = refs('event_list');
const eventCountLabel = refs('event_count_label');
const copyAllBtn = refs('copy_all_btn');
const clearEventsBtn = refs('clear_events_btn');
const tabContentEl = refs('tab_content');
const jumpBtn = refs('jump_btn');

// Scroll tracking
if (tabContentEl) {
    tabContentEl.addEventListener('scroll', () => {
        userAtBottom = tabContentEl.scrollTop + tabContentEl.clientHeight >= tabContentEl.scrollHeight - 20;
    });
}

// Chip refs (for count text updates in renderSSETab)
const chipRefs = {
    signals: refs('chip_signals'),
    elements: refs('chip_elements'),
    script: refs('chip_script'),
    lifecycle: refs('chip_lifecycle'),
};

// Build filter set from chip toggle signals
// Guard: only trigger full render if the active set actually changed
// (Datastar processing data-class:active bindings can re-trigger this effect spuriously)
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

// Clear Events button (needsFullRender + render handled by reactive effects)
if (clearEventsBtn) {
    clearEventsBtn.addEventListener('click', () => {
        const evts = capture.getEvents();
        const latest = evts[evts.length - 1];
        $$visible_since_id = latest ? latest.id + 1 : 0;
        $$expanded_id = -1;
    });
}

// Jump to Latest button
if (jumpBtn) {
    jumpBtn.addEventListener('click', () => {
        if (tabContentEl) tabContentEl.scrollTop = tabContentEl.scrollHeight;
        userAtBottom = true;
        $$show_jump_btn = false;
    });
}

// Copy All button
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

// Event delegation on event list (expand/collapse + copy buttons)
if (eventListEl) {
    eventListEl.addEventListener('click', (e) => {
        const target = e.target;

        // Copy single event button
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

        // Row expand/collapse
        const row = target.closest('.event-row');
        if (!row) return;
        const eid = Number(row.dataset.eid);
        const wasExpanded = $$expanded_id === eid;
        const prevExpandedId = $$expanded_id;
        $$expanded_id = wasExpanded ? -1 : eid;

        // Collapse previous
        if (prevExpandedId !== -1) {
            const prevRow = eventListEl.querySelector('.event-row[data-eid="' + prevExpandedId + '"]');
            if (prevRow) {
                prevRow.classList.remove('expanded');
                const prevDetail = prevRow.nextElementSibling;
                if (prevDetail && prevDetail.classList.contains('event-detail')) prevDetail.remove();
            }
        }

        // Expand new
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

// Schedule render via RAF
function scheduleRender() {
    if (rafPending) return;
    rafPending = true;
    requestAnimationFrame(() => {
        rafPending = false;
        if ($$is_open && $$active_tab === 'sse') renderSSETab();
    });
}

// Main render function
function renderSSETab() {
    if (!eventListEl) return;

    const allowedTypes = capture.buildAllowedTypes(activeTypeFilters);
    const filtered = capture.getFilteredEvents($$visible_since_id, allowedTypes, $$filter_text);

    // Update chip counts
    const visible = capture.getFilteredEvents($$visible_since_id, null, '');
    for (const chip of capture.CHIP_CATEGORIES) {
        const count = visible.filter(ev => chip.types.includes(ev.type)).length;
        const chipEl = chipRefs[chip.key];
        if (chipEl) chipEl.textContent = chip.label.charAt(0).toUpperCase() + chip.label.slice(1) + ' (' + count + ')';
    }

    // Update event count label
    if (eventCountLabel) {
        eventCountLabel.textContent = filtered.length + ' event' + (filtered.length !== 1 ? 's' : '');
    }

    const wasAtBottom = userAtBottom;
    const filteredIds = filtered.map(ev => ev.id);

    // Incremental append
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
            // Same events, no changes — return without full re-render
            return;
        }
    }

    // Full render fallback — reset expand state since innerHTML wipes detail divs
    $$expanded_id = -1;
    let html = '';
    for (const ev of filtered) html += capture.buildRowHtml(ev);
    eventListEl.innerHTML = html;
    lastRenderedIds = filteredIds;
    needsFullRender = false;

    if (wasAtBottom && tabContentEl) tabContentEl.scrollTop = tabContentEl.scrollHeight;
    $$show_jump_btn = !userAtBottom && filtered.length > 0;
}

// Reactive render trigger — re-render when signals change
// NOTE: $$expanded_id deliberately excluded — expand/collapse is imperative (click handler)
effect(() => {
    void $$event_count;
    void $$filter_text;
    void $$visible_since_id;
    if ($$is_open && $$active_tab === 'sse') scheduleRender();
});

// Force full re-render when filter text or visible_since_id changes
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

// Resize handle drag
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

// Tab-bar as resize target (drag from empty space, not tab buttons)
if (tabBar) {
    tabBar.addEventListener('mousedown', (e) => {
        if (e.target.closest('.tab-btn')) return;
        startResize(e);
    });
}

// Keyboard shortcut: Ctrl+Shift+. (or Cmd+Shift+.)
const onKeydown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.code === 'Period') {
        e.preventDefault();
        $$is_open = !$$is_open;
    }
};
document.addEventListener('keydown', onKeydown);
onCleanup(() => document.removeEventListener('keydown', onKeydown));
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
        is_open = Local("is_open", False, type_=bool)
        panel_height = Local("panel_height", 300, type_=int)
        active_tab = Local("active_tab", "sse", type_=str)
        unseen_count = Local("unseen_count", 0, type_=int)
        filter_text = Local("filter_text", "", type_=str)
        visible_since_id = Local("visible_since_id", 0, type_=int)
        expanded_id = Local("expanded_id", -1, type_=int)  # noqa: F841
        event_count = Local("event_count", 0, type_=int)  # noqa: F841
        chips = {key: Local(f"chip_{key}_on", key != "lifecycle", type_=bool) for _, key in CHIP_DEFS}
        show_jump_btn = Local("show_jump_btn", False, type_=bool)
        signal_count = Local("signal_count", 0, type_=int)  # noqa: F841
        signal_filter = Local("signal_filter", "", type_=str)
        signal_expanded_path = Local("signal_expanded_path", "", type_=str)  # noqa: F841

        return Div(
            Style(DEBUGGER_CSS),
            Script(DEBUGGER_SETUP),
            # --- Debugger tab (toggle button) ---
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
            # --- Panel ---
            Div(
                # Resize handle
                Div(data_ref="resize_handle", cls="resize-handle"),
                # Tab bar
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
                # SSE tab content
                Div(
                    # Toolbar
                    Div(
                        # Type filter chips
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
                        # Filter input
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
                        # Clear Events button
                        Button(
                            "Clear Events",
                            data_ref="clear_events_btn",
                            cls="clear-events-btn",
                            title="Clear visible events",
                        ),
                        # Copy All button
                        Button(
                            "Copy All",
                            data_ref="copy_all_btn",
                            title="Copy all visible events for LLM context",
                        ),
                        # Event count
                        Span(data_ref="event_count_label", cls="count"),
                        cls="toolbar",
                    ),
                    # Event list container (populated imperatively by setup script)
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
                # Signals tab content
                Div(
                    # Toolbar
                    Div(
                        # Filter input
                        Div(
                            Input(
                                type="text",
                                placeholder="Filter signals...",
                                data_bind=signal_filter,
                                style="width:200px;padding-right:20px",
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
                        # Signal count
                        Span(data_ref="signal_count_label", cls="count"),
                        # Clear Persisted button
                        Button(
                            "Clear Persisted",
                            data_ref="clear_persist_btn",
                            cls="clear-events-btn",
                            title="Clear all persisted signal data",
                        ),
                        cls="toolbar",
                    ),
                    # Signal list container (populated imperatively)
                    Div(data_ref="signal_list", cls="signal-list"),
                    # Empty state
                    Div(
                        "No signals detected",
                        data_ref="signal_empty",
                        style="color:#6c7086;padding:16px;text-align:center;",
                    ),
                    data_ref="signal_tab_content",
                    data_show=active_tab == "signals",
                    cls="tab-content",
                ),
                # Timeline tab placeholder
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
