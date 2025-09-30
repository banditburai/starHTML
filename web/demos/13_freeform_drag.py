"""Demo: Freeform Drag with Zone Awareness

This demo shows freeform dragging where items can be positioned anywhere,
while drop zones track what's over them without constraining movement.
"""

from starhtml import *

app, rt = star_app(
    title="Freeform Drag Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body { background: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; -webkit-font-smoothing: antialiased; }
        """),
        # Freeform drag handler with zone awareness
        (
            drag := drag_handler(
                signal="drag",
                mode="freeform",  # Freeform mode with zone tracking
                throttle_ms=16,  # 60fps smooth dragging
                constrain_to_parent=True,
            )
        ),
    ],
    iconify=True,
    compression=False,
)


@rt("/")
def freeform_drag():
    """Freeform drag demo with zone awareness."""
    return Div(
        # Main container
        Div(
            # Header
            Div(
                H1("13", cls="text-8xl font-black text-gray-100 leading-none"),
                H1("Freeform Drag", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
                P("Drag items anywhere within the workspace with zone awareness", cls="text-lg text-gray-600 mt-4"),
                cls="mb-16",
            ),
            # === DRAG WORKSPACE ===
            Div(
                H3("Interactive Workspace", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "Drag the packages anywhere. Drop zones will detect when items are over them.",
                    cls="text-gray-600 mb-6",
                ),
                # Main workspace
                Div(
                    # Draggable items (positioned absolutely)
                    Div(
                        Icon(
                            "material-symbols:package-2",
                            width="20",
                            height="20",
                            cls="inline mr-1 lg:w-6 lg:h-6 lg:mr-2",
                        ),
                        Span("Package A", cls="text-sm lg:text-base"),
                        data_draggable=True,
                        id="package-a",
                        cls="draggable-item bg-black text-white",
                        style="left: 20px; top: 30px;",
                    ),
                    Div(
                        Icon("material-symbols:mail", width="20", height="20", cls="inline mr-1 lg:w-6 lg:h-6 lg:mr-2"),
                        Span("Package B", cls="text-sm lg:text-base"),
                        data_draggable=True,
                        id="package-b",
                        cls="draggable-item bg-black text-white",
                        style="left: 20px; top: 100px;",
                    ),
                    Div(
                        Icon(
                            "material-symbols:redeem", width="20", height="20", cls="inline mr-1 lg:w-6 lg:h-6 lg:mr-2"
                        ),
                        Span("Package C", cls="text-sm lg:text-base"),
                        data_draggable=True,
                        id="package-c",
                        cls="draggable-item bg-black text-white",
                        style="left: 20px; top: 170px;",
                    ),
                    # Drop zones - responsive grid at bottom on mobile, side on desktop
                    Div(
                        Div(
                            H4("Inbox", cls="text-sm font-bold text-black mb-2 text-center lg:text-base"),
                            Div(
                                Icon(
                                    "material-symbols:inbox",
                                    width="32",
                                    height="32",
                                    cls="text-gray-300 mb-1 lg:w-12 lg:h-12",
                                ),
                                P(
                                    Span(
                                        data_text="($drag_zone_inbox_items || []).join(', ') || 'Drop here'",
                                        cls="text-xs lg:text-sm",
                                    ),
                                    cls="text-gray-600 text-center px-2",
                                ),
                                data_drop_zone="inbox",
                                data_class_active=drag.drop_zone == "inbox",
                                cls="drop-zone inbox-zone flex flex-col items-center justify-center",
                            ),
                            cls="zone-wrapper bg-white p-2 rounded-lg shadow-sm lg:p-4",
                        ),
                        Div(
                            H4("Archive", cls="text-sm font-bold text-black mb-2 text-center lg:text-base"),
                            Div(
                                Icon(
                                    "material-symbols:archive",
                                    width="32",
                                    height="32",
                                    cls="text-gray-300 mb-1 lg:w-12 lg:h-12",
                                ),
                                P(
                                    Span(
                                        data_text="($drag_zone_archive_items || []).join(', ') || 'Drop here'",
                                        cls="text-xs lg:text-sm",
                                    ),
                                    cls="text-gray-600 text-center px-2",
                                ),
                                data_drop_zone="archive",
                                data_class_active=drag.drop_zone == "archive",
                                cls="drop-zone archive-zone flex flex-col items-center justify-center",
                            ),
                            cls="zone-wrapper bg-white p-2 rounded-lg shadow-sm lg:p-4",
                        ),
                        cls="zones-container",
                    ),
                    cls="workspace relative bg-gray-50 border border-gray-200 rounded-lg",
                    id="drag-workspace",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # === STATUS DISPLAY ===
            Div(
                H3("Drag Status", cls="text-2xl font-bold text-black mb-6"),
                Div(
                    Div(
                        P("Currently dragging:", cls="text-sm text-gray-600 mb-1"),
                        P(
                            data_text=f"{drag.is_dragging} ? {drag.element_id} : 'Nothing'",
                            data_class_active=drag.is_dragging,
                            cls="text-lg font-bold text-black active:text-blue-600",
                        ),
                    ),
                    Div(
                        P("Over zone:", cls="text-sm text-gray-600 mb-1"),
                        P(
                            data_text=f"{drag.drop_zone} || 'None'",
                            cls="text-lg font-bold text-black",
                        ),
                    ),
                    cls="grid grid-cols-2 gap-8",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # CSS Styles
            Style("""
                .workspace {
                    position: relative;
                    height: 400px;
                    min-height: 400px;
                }
                
                @media (min-width: 768px) {
                    .workspace {
                        height: 500px;
                        min-height: 500px;
                    }
                }
            
                .draggable-item {
                    position: absolute;
                    padding: 0.5rem 0.75rem;
                    border-radius: 0.375rem;
                    cursor: grab;
                    user-select: none;
                    transition: transform 0.2s, box-shadow 0.2s;
                    font-weight: 500;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    z-index: 100;
                    display: inline-flex;
                    align-items: center;
                }
                
                @media (min-width: 1024px) {
                    .draggable-item {
                        padding: 0.75rem 1.25rem;
                    }
                }
            
                .draggable-item:hover {
                    transform: scale(1.02);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }
                
                .draggable-item:active {
                    cursor: grabbing;
                }
                
                .draggable-item.is-dragging {
                    transform: scale(1.05);
                    box-shadow: 0 8px 24px rgba(0,0,0,0.2);
                    z-index: 1000;
                    transition: none;
                    opacity: 0.9;
                }
            
                /* Mobile: zones at bottom */
                .zones-container {
                    position: absolute;
                    bottom: 10px;
                    left: 10px;
                    right: 10px;
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 10px;
                }
                
                /* Desktop: zones on right side */
                @media (min-width: 1024px) {
                    .zones-container {
                        bottom: auto;
                        left: auto;
                        right: 20px;
                        top: 50%;
                        transform: translateY(-50%);
                        display: flex;
                        flex-direction: column;
                        gap: 20px;
                        width: auto;
                    }
                }
            
                /* Mobile: smaller zones */
                .drop-zone {
                    width: 100%;
                    height: 100px;
                    border: 2px dashed #e5e7eb;
                    border-radius: 0.5rem;
                    background: rgba(249, 250, 251, 0.8);
                    transition: all 0.2s;
                    position: relative;
                }
                
                /* Tablet and up */
                @media (min-width: 768px) {
                    .drop-zone {
                        height: 120px;
                    }
                }
                
                /* Desktop: fixed width zones on side */
                @media (min-width: 1024px) {
                    .drop-zone {
                        width: 220px;
                        height: 150px;
                    }
                }
            
                .drop-zone.active {
                    transform: scale(1.02);
                    border-color: #000;
                    background: rgba(249, 250, 251, 1);
                    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
                }
            
                /* Prevent text selection during drag */
                body.is-drag-active * {
                    user-select: none !important;
                }
            """),
        ),
        cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen",
    )


if __name__ == "__main__":
    print("Freeform Drag Demo running on http://localhost:5013")
    serve(port=5013)
