"""StarHTML Debugger v2 - StarElements-based component."""

from starelements import Local, element

from .tags import Button, Div, Input, Span
from .xtend import Script, Style

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
    display: none;
    flex-direction: column;
    overflow: hidden;
  }
  .debugger-panel.open { display: flex; }
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

DEBUGGER_SETUP = "// Setup wired in Tasks 4-6"


@element(
    "starhtml-debugger",
    shadow=True,
    imports={"capture": "/_pkg/starhtml/plugins/debugger-capture.js"},
)
def StarHTMLDebugger():
    is_open = Local("is_open", False, type_=bool)
    panel_height = Local("panel_height", 300, type_=int)
    active_tab = Local("active_tab", "sse", type_=str)
    unseen_count = Local("unseen_count", 0, type_=int)
    filter_text = Local("filter_text", "", type_=str)
    visible_since_id = Local("visible_since_id", 0, type_=int)
    expanded_id = Local("expanded_id", -1, type_=int)
    event_count = Local("event_count", 0, type_=int)
    # type_filters not declared as Local — managed imperatively in setup script
    # (dict signals require JSON codec and add complexity for chip toggle UX)

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
            data_on_click=f"{is_open} = !{is_open}",
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
                    data_on_click=f"{active_tab} = 'sse'",
                    data_class_active=f"{active_tab} === 'sse'",
                    cls="tab-btn",
                ),
                Button(
                    "Signals",
                    data_on_click=f"{active_tab} = 'signals'",
                    data_class_active=f"{active_tab} === 'signals'",
                    cls="tab-btn",
                ),
                Button(
                    "Timeline",
                    data_on_click=f"{active_tab} = 'timeline'",
                    data_class_active=f"{active_tab} === 'timeline'",
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
                        Span("Signals", data_ref="chip_signals", cls="type-chip chip-signals"),
                        Span("Elements", data_ref="chip_elements", cls="type-chip chip-elements"),
                        Span("Script", data_ref="chip_script", cls="type-chip chip-script"),
                        Span("Lifecycle", data_ref="chip_lifecycle", cls="type-chip chip-lifecycle"),
                        cls="type-chips",
                    ),
                    Div(cls="toolbar-sep"),
                    # Filter input
                    Div(
                        Input(
                            type="text",
                            placeholder="Filter...",
                            data_model=filter_text,
                            style="width:160px;padding-right:20px",
                        ),
                        Button(
                            "\u00d7",
                            data_show=f"{filter_text} !== ''",
                            data_on_click=f"{filter_text} = ''",
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
                data_show=f"{active_tab} === 'sse'",
            ),
            # Signals tab placeholder
            Div(
                Div("Coming in Phase 3", style="color:#6c7086;padding:16px;"),
                data_show=f"{active_tab} === 'signals'",
            ),
            # Timeline tab placeholder
            Div(
                Div("Coming in Phase 3", style="color:#6c7086;padding:16px;"),
                data_show=f"{active_tab} === 'timeline'",
            ),
            data_ref="panel",
            data_show=is_open,
            cls="debugger-panel open",
            style=f"height:{panel_height}px",
        ),
    )
