"""StarHTML DevTools — auto-injected when devtools=True."""
# ruff: noqa: F841  (Local vars are consumed by StarElements $$ proxy in Script)

import warnings
from pathlib import Path

from .html import ft_html
from .xtend import Script

_DEVTOOLS_DIR = Path(__file__).parent / "static" / "js" / "devtools"

_CHIP_DEFS = (
    ("Signals", "signals"),
    ("Elements", "elements"),
    ("Script", "script"),
    ("Lifecycle", "lifecycle"),
)

_TL_CHIP_DEFS = (
    ("User", "user"),
    ("SSE", "sse"),
    ("Signal", "signal"),
    ("Warnings", "warning"),
)

_EXPORT_OPTS = (
    ("Last 5s", "tl_exp_5s"),
    ("Last 15s", "tl_exp_15s"),
    ("Last 30s", "tl_exp_30s"),
    ("Last 60s", "tl_exp_60s"),
    ("All Visible", "tl_exp_all"),
)


def _setup_capture_only(app):
    """Capture-mode wiring: load capture.js (so window.__starhtml_capture__
    is populated and SSE events accumulate), but skip the <starhtml-devtools>
    UI panel. Used by diagnostic rigs that want programmatic access to the
    Datastar event log without the panel's ~50 reactive bindings distorting
    cascade measurements."""
    app.hdrs.append(
        Script(
            "import {init} from '/_pkg/starhtml/devtools/capture.js'; init();",
            type="module",
        )
    )


def setup_devtools(app, mode: bool | str = True):
    """Register the StarElements devtools, or warn if starelements is missing.

    mode:
        True: full UI panel + capture.js data layer (legacy default)
        'capture': capture.js only — no UI panel. For diagnostic rigs.
    """
    if mode == "capture":
        _setup_capture_only(app)
        return

    try:
        from starelements import Local, element  # noqa: PLC0415
    except ImportError:
        warnings.warn(
            "starelements not installed — devtools disabled. Install with: uv pip install 'starhtml[debug]'",
            stacklevel=2,
        )
        return

    from .tags import Button, Div, Input, Span  # noqa: PLC0415
    from .xtend import Style  # noqa: PLC0415

    devtools_css = (_DEVTOOLS_DIR / "devtools.css").read_text()
    devtools_setup = "_setup.setup(el, onCleanup, refs);"
    empty_style = "color:#6c7086;padding:16px;text-align:center;"

    def _filter_input(signal, placeholder="Filter..."):
        return Div(
            Input(
                type="text",
                placeholder=placeholder,
                data_bind=signal,
                style="width:160px;padding-right:20px",
            ),
            Button(
                "\u00d7",
                data_show=signal != "",
                data_on_click=signal.set(""),
                cls="clear-filter-btn",
                title="Clear filter",
            ),
            cls="filter-wrap",
        )

    def _type_chips(defs, chip_signals):
        return Div(
            *[
                Span(
                    label,
                    data_ref=f"chip_{key}",
                    data_on_click=chip_signals[key].toggle(),
                    data_class_active=chip_signals[key],
                    cls=f"type-chip chip-{key}",
                )
                for label, key in defs
            ],
            cls="type-chips",
        )

    def _tab_toggle(is_open, unseen_count):
        return Div(
            "StarHTML DevTools",
            Span(
                data_show=unseen_count > 0,
                data_text=unseen_count,
                cls="badge",
            ),
            data_on_click=is_open.toggle(),
            cls="devtools-tab",
        )

    def _tab_bar(active_tab):
        def _tab_btn(label, tab_id, count_ref=None):
            if count_ref:
                children = (Span(label), Span(data_ref=count_ref, style="margin-left:4px;color:#9399b2;"))
            else:
                children = (label,)
            return Button(
                *children,
                data_on_click=active_tab.set(tab_id),
                data_class_active=active_tab == tab_id,
                cls="tab-btn",
            )

        return Div(
            _tab_btn("SSE Events", "sse"),
            _tab_btn("Signals", "signals", "signal_tab_count"),
            _tab_btn("Timeline", "timeline", "timeline_tab_count"),
            data_ref="tab_bar",
            cls="tab-bar",
        )

    def _sse_tab(active_tab, chips, filter_text, show_jump_btn):
        return Div(
            Div(
                _type_chips(_CHIP_DEFS, chips),
                Div(cls="toolbar-sep"),
                _filter_input(filter_text),
                Button(
                    "Clear Events", data_ref="clear_events_btn", cls="clear-events-btn", title="Clear visible events"
                ),
                Button("Copy All", data_ref="copy_all_btn", title="Copy all visible events for LLM context"),
                Span(data_ref="error_count_badge", cls="error-count-badge", style="display:none"),
                Span(data_ref="event_count_label", cls="count"),
                cls="toolbar",
            ),
            Div(data_ref="event_list", cls="event-list"),
            Button("Jump to latest", data_show=show_jump_btn, data_ref="jump_btn", cls="jump-btn"),
            data_ref="tab_content",
            data_show=active_tab == "sse",
            cls="tab-content",
        )

    def _signals_tab(active_tab, signal_filter):
        return Div(
            Div(
                _filter_input(signal_filter, "Filter signals..."),
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
            Div("No signals detected", data_ref="signal_empty", style=empty_style),
            data_show=active_tab == "signals",
            cls="tab-content",
        )

    def _timeline_tab(active_tab, tl_chips, timeline_filter, show_tl_jump):
        return Div(
            Div(
                _type_chips(_TL_CHIP_DEFS, tl_chips),
                Div(cls="toolbar-sep"),
                _filter_input(timeline_filter, "Filter traces..."),
                Span(data_ref="timeline_count_label", cls="count"),
                Div(
                    Button(
                        "Export \u25be",
                        data_ref="tl_export_btn",
                        cls="clear-events-btn",
                        title="Export traces as Markdown",
                    ),
                    Div(
                        *[Button(label, data_ref=ref, cls="tl-export-opt") for label, ref in _EXPORT_OPTS],
                        data_ref="tl_export_menu",
                        cls="tl-export-menu",
                    ),
                    cls="tl-export-wrap",
                ),
                cls="toolbar",
            ),
            Div(
                Span(data_ref="tl_range_label"),
                Button("Copy Range", data_ref="tl_range_copy", cls="tl-range-copy"),
                Button("Clear", data_ref="tl_range_clear", cls="tl-range-clear"),
                data_ref="tl_range_bar",
                cls="tl-range-bar",
            ),
            Div(data_ref="timeline_list", cls="timeline-list"),
            Button("Jump to latest", data_show=show_tl_jump, data_ref="tl_jump_btn", cls="jump-btn"),
            Div("No traces captured", data_ref="timeline_empty", style=empty_style),
            data_ref="timeline_content",
            data_show=active_tab == "timeline",
            cls="tab-content",
        )

    @element(
        "starhtml-devtools",
        shadow=True,
        imports={"_setup": "/_pkg/starhtml/devtools/setup.js"},
    )
    def StarHTMLDevtools():
        is_open = Local("is_open", False)
        panel_height = Local("panel_height", 300)
        active_tab = Local("active_tab", "sse")
        unseen_count = Local("unseen_count", 0)
        filter_text = Local("filter_text", "")
        visible_since_id = Local("visible_since_id", 0)
        expanded_id = Local("expanded_id", -1)
        event_count = Local("event_count", 0)
        chips = {key: Local(f"chip_{key}_on", key != "lifecycle") for _, key in _CHIP_DEFS}
        show_jump_btn = Local("show_jump_btn", False)
        signal_count = Local("signal_count", 0)
        signal_filter = Local("signal_filter", "")
        signal_expanded_path = Local("signal_expanded_path", "")
        timeline_count = Local("timeline_count", 0)
        timeline_filter = Local("timeline_filter", "")
        timeline_expanded_id = Local("timeline_expanded_id", -1)
        tl_chips = {key: Local(f"tl_chip_{key}", True) for _, key in _TL_CHIP_DEFS}
        show_tl_jump = Local("show_tl_jump", False)

        return Div(
            Style(devtools_css),
            Script(devtools_setup),
            _tab_toggle(is_open, unseen_count),
            Div(
                Div(data_ref="resize_handle", cls="resize-handle"),
                _tab_bar(active_tab),
                _sse_tab(active_tab, chips, filter_text, show_jump_btn),
                _signals_tab(active_tab, signal_filter),
                _timeline_tab(active_tab, tl_chips, timeline_filter, show_tl_jump),
                data_ref="panel",
                data_show=is_open,
                data_style_height=panel_height + "px",
                cls="devtools-panel",
            ),
        )

    app.register(StarHTMLDevtools)

    # Must start capture before component mounts to catch early SSE events
    app.hdrs.append(
        Script(
            "import {init} from '/_pkg/starhtml/devtools/capture.js'; init();",
            type="module",
        )
    )
    app.ftrs.append(ft_html("starhtml-devtools"))
