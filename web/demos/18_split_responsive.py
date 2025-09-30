"""
Split Demo - Responsive Mode Testing
Test vertical stacking on mobile and scrolling behavior
"""

from starhtml import *
from starhtml.handlers import split_handler

app, rt = star_app(
    title="Split Demo - Responsive Test",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        # Enable responsive mode for mobile testing
        (splitter := split_handler(signal="responsive", responsive=True, responsive_breakpoint=768)),
        Style("""
            :root {
                --split-handle-size: 8px;
                --split-handle-color: rgba(0, 0, 0, 0.15);
                --split-handle-hover-color: rgba(0, 123, 255, 0.3);
                --split-handle-active-color: rgba(0, 123, 255, 0.5);
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
            
            .split-wrapper {
                position: absolute;
                top: 44px;
                left: 0;
                right: 0;
                bottom: 0;
                max-width: none !important;
                width: 100% !important;
            }
            
            .split-wrapper .split-container {
                height: 100%;
                width: 100%;
                display: flex;
                overflow: hidden;
            }
            
            .split-wrapper .panel {
                padding: 1.5rem;
                overflow: auto;
                position: relative;
            }
            
            .split-wrapper .panel.left {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            
            .split-wrapper .panel.right {
                background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
                color: #333;
            }
            
            .split-wrapper .viewport-info {
                padding: 0.75rem 1rem;
                background: rgba(0, 123, 255, 0.1);
                border: 1px solid rgba(0, 123, 255, 0.3);
                border-radius: 0.5rem;
                margin-bottom: 1rem;
                font-size: 0.875rem;
            }

            .split-wrapper h2 {
                font-size: 1.5rem;
                font-weight: 600;
                margin: 0 0 1rem 0;
            }
            
            .split-wrapper h3 {
                margin-top: 2rem;
                font-size: 1.25rem;
                font-weight: 600;
            }
            
            .split-wrapper p {
                margin: 1rem 0;
                line-height: 1.6;
            }
            
            .split-wrapper .info-list {
                background: rgba(255,255,255,0.1);
                padding: 1rem;
                border-radius: 0.5rem;
                margin: 1rem 0;
            }
            
            .split-wrapper .panel.right .info-list {
                background: rgba(0,0,0,0.05);
            }
            
            .split-wrapper ul {
                margin-left: 1.5rem;
                line-height: 1.8;
            }
        """),
    ],
    iconify=True,
    compression=False,
)


def create_size_controls():
    """Create responsive size control buttons."""
    btn_cls = "px-4 py-2 bg-white/20 border border-white/30 text-white rounded-lg hover:bg-white/30 hover:-translate-y-px transition-all text-sm font-medium"
    return Div(
        Button("30/70", data_on_click=splitter.sizes.set([30, 70]), cls=btn_cls),
        Button("50/50", data_on_click=splitter.sizes.set([50, 50]), cls=btn_cls),
        Button("70/30", data_on_click=splitter.sizes.set([70, 30]), cls=btn_cls),
        cls="flex gap-2 flex-wrap my-4",
    )


def create_viewport_info(text_prefix="Mode"):
    """Create viewport information display."""
    return Div(
        f"{text_prefix}: ",
        Span(data_text=splitter.direction, style="font-weight: bold; text-transform: capitalize;"),
        cls="viewport-info",
    )


def create_size_display(panel_index=0):
    """Create size display for panels."""
    return Div(
        "Current size: ",
        Span(
            data_text=splitter.sizes.if_(splitter.sizes[panel_index].round() + "%", "50%"),
            cls="text-4xl font-light opacity-90",
        ),
        cls="mb-4",
    )


def create_left_panel():
    """Create the left panel with testing content."""
    return Div(
        create_viewport_info(),
        H2("Left Panel - Responsive Test"),
        create_size_display(0),
        create_size_controls(),
        H3("Testing Responsive Behavior"),
        Div(
            P("Resize your browser window to test:"),
            Ul(
                Li("Desktop (>768px): Horizontal split with draggable handle"),
                Li("Mobile (≤768px): Vertical stack with scrolling"),
                Li("Transition is automatic based on viewport width"),
                Li("Each panel scrolls independently in both modes"),
            ),
            cls="info-list",
        ),
        H3("Long Content for Scroll Testing"),
        *[
            P(
                f"Paragraph {i}: Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                "Vestibulum id ligula porta felis euismod semper. Nullam quis risus eget "
                "urna mollis ornare vel eu leo. Cras justo odio, dapibus ac facilitis in, "
                "egestas eget quam. Morbi leo risus, porta ac consectetur ac."
            )
            for i in range(1, 16)
        ],
        H3("Mobile Scroll Behavior"),
        P(
            "On mobile devices, panels stack vertically and each maintains its own "
            "scroll position. The content should be easily readable and navigation should "
            "remain accessible at the top of the screen."
        ),
        P("Scroll continues below..."),
        *[P(f"Additional content block {i}") for i in range(1, 11)],
        cls="panel left",
    )


def create_right_panel():
    """Create the right panel with different content."""
    return Div(
        Div(
            "Direction: ",
            Span(data_text=splitter.direction, style="font-weight: bold;"),
            " | Panel 2 Size: ",
            Span(data_text=splitter.sizes.if_(splitter.sizes[1].round() + "%", "50%"), style="font-weight: bold;"),
            cls="viewport-info",
        ),
        H2("Right Panel - Different Content"),
        create_size_display(1),
        H3("Mobile-First Design"),
        P(
            "This demo implements mobile-first responsive design. The split panels "
            "automatically adapt to the viewport size, providing an optimal experience "
            "on both desktop and mobile devices."
        ),
        Div(
            P("Key Features:"),
            Ul(
                Li("Automatic layout switching at 768px breakpoint"),
                Li("Touch-friendly handles on mobile"),
                Li("Preserved scroll positions"),
                Li("Full viewport utilization"),
                Li("Smooth transitions between modes"),
            ),
            cls="info-list",
        ),
        H3("Content Adaptation"),
        P(
            "Content reflows naturally as the layout changes. On mobile, panels "
            "stack vertically to maximize readability. On desktop, side-by-side layout "
            "allows for comparison and multitasking."
        ),
        *[
            P(f"Right panel content {i}. This panel has less content to demonstrate different scroll lengths.")
            for i in range(1, 8)
        ],
        H3("Testing Instructions"),
        P("1. Resize browser window to cross the 768px threshold"),
        P("2. Check that layout switches between horizontal and vertical"),
        P("3. Verify scroll positions are maintained"),
        P("4. Test dragging handles in both modes"),
        P("5. Confirm touch/mouse interactions work correctly"),
        cls="panel right",
    )


@rt("/")
def home():
    """Responsive split demo with modular components."""
    return Div(
        Div(
            Div(
                create_left_panel(),
                Div(data_split="responsive:horizontal:50,50"),
                create_right_panel(),
                cls="split-container",
            ),
            cls="split-wrapper",
        )
    )


if __name__ == "__main__":
    serve(port=5025)
