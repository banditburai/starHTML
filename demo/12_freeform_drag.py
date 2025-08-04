"""Demo: Freeform Drag with Zone Awareness

This demo shows freeform dragging where items can be positioned anywhere,
while drop zones track what's over them without constraining movement.
"""

from starhtml import *

app, rt = star_app(
    title="Freeform Drag Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        # Freeform drag handler with zone awareness
        drag_handler(
            signal="drag",
            mode="freeform",  # Freeform mode with zone tracking
            throttle_ms=16,  # 60fps smooth dragging
            constrain_to_parent=True,
        ),
    ],
)


@rt("/")
def freeform_drag():
    """Freeform drag demo with zone awareness."""
    return Div(
        # Header
        Div(
            H1("🎯 Freeform Drag with Zone Awareness", cls="text-3xl font-bold mb-2"),
            P("Drag items anywhere within the workspace. Zones track what's over them.", cls="text-gray-600 mb-4"),
            cls="p-6 bg-white border-b",
        ),
        # Main workspace
        Div(
            # Draggable items (positioned absolutely)
            Div(
                "📦 Package A",
                ds_draggable(),
                ds_on_drag("console.log('Dragging package A')"),
                id="package-a",
                cls="draggable-item bg-blue-500",
                style="left: 50px; top: 50px;",
            ),
            Div(
                "📮 Package B",
                ds_draggable(),
                ds_on_drag("console.log('Dragging package B')"),
                id="package-b",
                cls="draggable-item bg-green-500",
                style="left: 50px; top: 150px;",
            ),
            Div(
                "🎁 Package C",
                ds_draggable(),
                ds_on_drag("console.log('Dragging package C')"),
                id="package-c",
                cls="draggable-item bg-purple-500",
                style="left: 50px; top: 250px;",
            ),
            # Drop zones (visual areas that track what's over them)
            Div(
                Div(
                    H3("📥 Inbox Zone", cls="font-semibold mb-2 text-center"),
                    Div(
                        P("Items here: ", ds_text("($zone_inbox_items || []).join(', ') || 'none'"), cls="zone-status"),
                        ds_drop_zone("inbox"),
                        ds_class(active="$dropZone === 'inbox'"),
                        cls="drop-zone inbox-zone",
                    ),
                    cls="zone-wrapper",
                ),
                Div(
                    H3("🗃️ Archive Zone", cls="font-semibold mb-2 text-center"),
                    Div(
                        P(
                            "Items here: ",
                            ds_text("($zone_archive_items || []).join(', ') || 'none'"),
                            cls="zone-status",
                        ),
                        ds_drop_zone("archive"),
                        ds_class(active="$dropZone === 'archive'"),
                        cls="drop-zone archive-zone",
                    ),
                    cls="zone-wrapper",
                ),
                cls="zones-container",
            ),
            cls="workspace",
            id="drag-workspace",
        ),
        # Status bar
        Div(
            Div(
                Span("Currently dragging: ", cls="text-gray-600"),
                Span(
                    ds_text("$isDragging ? $elementId : 'none'"),
                    ds_class(active="$isDragging"),
                    cls="font-mono text-sm font-medium",
                ),
            ),
            P(
                "Items can be dragged anywhere. Zones show awareness of what's over them.",
                cls="text-sm text-gray-500 italic",
            ),
            cls="p-4 bg-gray-100 border-t",
        ),
        # CSS Styles
        Style("""
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                margin: 0;
                padding: 0;
                overflow-x: hidden;
            }
            
            .workspace {
                position: relative;
                height: 500px;
                background: #f8f9fa;
            }
            
            .draggable-item {
                position: absolute;
                padding: 0.75rem 1.25rem;
                color: white;
                border-radius: 8px;
                cursor: grab;
                user-select: none;
                transition: transform 0.2s, box-shadow 0.2s;
                font-weight: 500;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                z-index: 100;
            }
            
            .draggable-item:hover {
                transform: scale(1.05);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            
            .draggable-item:active {
                cursor: grabbing;
            }
            
            .draggable-item.is-dragging {
                transform: scale(1.1);
                box-shadow: 0 8px 24px rgba(0,0,0,0.25);
                z-index: 1000;
                transition: none;
            }
            
            .zones-container {
                position: absolute;
                right: 20px;
                top: 50%;
                transform: translateY(-50%);
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            
            .zone-wrapper {
                background: white;
                padding: 1rem;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            .drop-zone {
                width: 250px;
                height: 150px;
                border: 3px dashed #d1d5db;
                border-radius: 12px;
                background: rgba(250, 250, 250, 0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s;
                position: relative;
            }
            
            .inbox-zone {
                border-color: #60a5fa;
            }
            
            .archive-zone {
                border-color: #a78bfa;
            }
            
            .drop-zone.active {
                transform: scale(1.05);
                box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            }
            
            .drop-zone.active.inbox-zone {
                background: rgba(239, 246, 255, 0.9);
                border-color: #3b82f6;
            }
            
            .drop-zone.active.archive-zone {
                background: rgba(245, 243, 255, 0.9);
                border-color: #7c3aed;
            }
            
            .zone-status {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
                color: #6b7280;
                font-size: 0.875rem;
                width: 90%;
            }
            
            .status-indicator.active {
                color: #10b981;
                font-weight: 600;
            }
            
            /* Prevent text selection during drag */
            body.is-drag-active * {
                user-select: none !important;
            }
        """),
        cls="freeform-drag-demo",
    )


if __name__ == "__main__":
    print("=" * 60)
    print("🎯 FREEFORM DRAG WITH ZONE AWARENESS")
    print("=" * 60)
    print("📍 Running on: http://localhost:5001")
    print("🎨 Features:")
    print("   • Drag items anywhere on the page")
    print("   • Zones track what's over them")
    print("   • No movement constraints")
    print("   • Visual feedback for zone overlap")
    print("   • Real-time tracking")
    print("=" * 60)
    serve(port=5001)
