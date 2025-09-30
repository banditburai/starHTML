"""
Universal Split Demo - Apply split behavior to ANY div structure
Using the FT Splitter approach with Datastar patterns
"""

from starhtml import *
from starhtml.handlers import split_handler

app, rt = star_app(
    title="Universal Split Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        # Separate handlers for independent splits
        (main := split_handler(signal="main", responsive=False)),
        (nested := split_handler(signal="nested", responsive=False)),
        Style("""
            @layer base {
                :root {
                    --split-handle-size: 12px;
                    --split-handle-color: linear-gradient(135deg, rgba(0, 123, 255, 0.15), rgba(0, 123, 255, 0.25));
                    --split-handle-hover-color: linear-gradient(135deg, rgba(0, 123, 255, 0.25), rgba(0, 123, 255, 0.35));
                    --split-handle-active-color: linear-gradient(135deg, rgba(0, 123, 255, 0.4), rgba(0, 123, 255, 0.5));
                }
                
                html, body {
                    margin: 0;
                    padding: 0;
                    height: 100vh;
                    font-family: system-ui, -apple-system, sans-serif;
                    background: white;
                    max-width: none !important;
                    width: 100vw !important;
                }
                
                body > * {
                    max-width: none !important;
                }
            }
            
            .split-wrapper {
                position: absolute;
                top: 44px;
                left: 0;
                right: 0;
                bottom: 0;
                max-width: none !important;
                width: 100% !important;
            }
            
            .split-container {
                height: 100%;
                width: 100%;
                display: flex;
                overflow: hidden;
            }
            
            .nested-container {
                display: flex;
                flex-direction: column;
                flex: 1;
            }
            
            .panel {
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 2rem;
                color: white;
                font-weight: 500;
                text-align: center;
                position: relative;
                overflow: auto;
            }
            
            .panel-1 {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            
            .panel-2 {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            }
            
            .panel-3 {
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            }
            
            .panel-info {
                background: rgba(0,0,0,0.2);
                backdrop-filter: blur(10px);
                padding: 2rem;
                border-radius: 1rem;
                border: 1px solid rgba(255,255,255,0.1);
                max-width: 320px;
            }
            
            .size-display {
                font-size: 3rem;
                font-weight: 200;
                margin: 1rem 0;
                display: block;
            }
            
            .controls {
                margin-top: 1.5rem;
                display: flex;
                gap: 0.5rem;
                justify-content: center;
                flex-wrap: wrap;
            }
            
            .btn {
                padding: 0.5rem 1rem;
                background: rgba(255,255,255,0.2);
                border: 1px solid rgba(255,255,255,0.3);
                color: white;
                border-radius: 0.5rem;
                cursor: pointer;
                transition: all 0.2s;
                font-size: 0.875rem;
                font-weight: 500;
            }
            
            .btn:hover {
                background: rgba(255,255,255,0.3);
                transform: translateY(-1px);
            }
            
            @layer components {
                [data-split-handle] {
                    transition: background-color 0.2s ease;
                    border-radius: 3px;
                    box-shadow: inset 0 1px 0 rgba(255,255,255,0.1);
                }
                
                [data-split-handle="horizontal"] {
                    border-left: 1px solid rgba(255,255,255,0.1);
                    border-right: 1px solid rgba(255,255,255,0.1);
                }
                
                [data-split-handle="vertical"] {
                    border-top: 1px solid rgba(255,255,255,0.1);
                    border-bottom: 1px solid rgba(255,255,255,0.1);
                }
            }
            
        """),
    ],
    iconify=True,
    compression=False,
)


def create_panel_content(title, *content, size_signal=None, default_size="30%"):
    """Create standardized panel content with title, description, and optional size display."""
    elements = [H2(title, style="margin: 0 0 1rem 0;"), *content]

    if size_signal:
        elements.append(
            Div(
                "Size: ",
                Span(data_text=size_signal.if_(size_signal[0].round() + "%", default_size), cls="size-display"),
            )
        )

    return Div(*elements, cls="panel-info")


def create_control_buttons():
    """Create the control buttons for resetting and equalizing splits."""
    return Div(
        Button("Reset", data_on_click=[main.sizes.set([30, 70]), nested.sizes.set([60, 40])], cls="btn"),
        Button("Equal", data_on_click=[main.sizes.set([50, 50]), nested.sizes.set([50, 50])], cls="btn"),
        cls="controls",
    )


def create_left_panel():
    """Create the left panel with universal split info."""
    content = create_panel_content(
        "Left Panel",
        P("Universal split behavior"),
        P("Just add data-split to any div!"),
        size_signal=main.sizes,
        default_size="30%",
    )
    return Div(content, cls="panel panel-1")


def create_top_panel():
    """Create the top panel of the nested split."""
    content = create_panel_content(
        "Main Content",
        P("Nested splits work perfectly"),
        P("Drag any gap to resize"),
        size_signal=nested.sizes,
        default_size="60%",
    )
    return Div(content, cls="panel panel-2")


def create_bottom_panel():
    """Create the bottom panel with controls."""
    content = create_panel_content(
        "Bottom Panel",
        P("Completely flexible"),
        P("CSS custom properties with CSS layers"),
        P("Modern gradient handles with enhanced styling"),
        create_control_buttons(),
    )
    return Div(content, cls="panel panel-3")


def create_nested_split():
    """Create the nested vertical split container."""
    return Div(
        create_top_panel(), Div(data_split="nested:vertical:60,40"), create_bottom_panel(), cls="nested-container"
    )


def create_main_split():
    """Create the main horizontal split container."""
    return Div(
        create_left_panel(), Div(data_split="main:horizontal:30,70"), create_nested_split(), cls="split-container"
    )


@rt("/")
def home():
    """Main route handler - composed of modular split components."""
    return Div(Div(create_main_split(), cls="split-wrapper"))


if __name__ == "__main__":
    serve(port=5024)
