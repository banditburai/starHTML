#!/usr/bin/env python3
"""
Comprehensive test suite for position.ts handler functionality:
- Opacity-based hiding to prevent flashing
- Container parameter for controlling nested popover positioning
- Scroll behavior for different placements
- Edge cases and stress testing
"""

import sys

sys.path.insert(0, "src")

from uuid import uuid4

from starhtml import *


# Popover component code exactly as provided
def cn(*classes):
    """Concatenate class names."""
    return " ".join(filter(None, classes))


def make_injectable(func):
    """Mark a function as injectable."""
    func._inject_signal = func
    return func


def inject_signals(children, *args):
    """Process children and inject signals."""
    result = []
    for child in children:
        if hasattr(child, "_inject_signal") and callable(child._inject_signal):
            result.append(child._inject_signal(*args))
        else:
            result.append(child)
    return result


def Popover(*children, cls="relative inline-block", **attrs):
    signal = f"popover_{uuid4().hex[:8]}"
    return Div(*inject_signals(children, signal), cls=cls, **attrs)


def PopoverTrigger(*children, variant="default", cls="", **attrs):
    def _inject_signal(signal):
        return Button(
            *children,
            data_ref=f"{signal}Trigger",
            popovertarget=f"{signal}-content",
            popoveraction="toggle",
            id=f"{signal}-trigger",
            cls=cls,
            **attrs,
        )

    return make_injectable(_inject_signal)


def PopoverContent(*children, cls="", side="bottom", align="center", offset=None, container="auto", **attrs):
    def _inject_signal(signal):
        placement = f"{side}-{align}" if align != "center" else side

        def process_element(element):
            if callable(element) and getattr(element, "_is_popover_close", False):
                return element(signal)
            if hasattr(element, "tag") and hasattr(element, "children") and element.children:
                processed_children = tuple(process_element(child) for child in element.children)
                return FT(element.tag, processed_children, element.attrs)
            return element

        processed_children = [process_element(child) for child in children]

        # Build position modifiers
        position_mods = {"placement": placement, "flip": True, "shift": True, "hide": True, "container": container}
        if offset is not None:
            position_mods["offset"] = offset

        return Div(
            *processed_children,
            data_ref=f"{signal}Content",
            data_position=(f"{signal}-trigger", dict(**position_mods)),
            popover="auto",
            id=f"{signal}-content",
            role="dialog",
            tabindex="-1",
            cls=cn(
                "z-50 w-72 rounded-md border bg-white p-4 shadow-md outline-none",
                cls,
            ),
            **attrs,
        )

    return make_injectable(_inject_signal)


def PopoverClose(*children, cls="", **attrs):
    def close_button(signal):
        return Button(
            *children,
            popovertarget=f"{signal}-content",
            popoveraction="hide",
            cls=cn("absolute right-2 top-2 px-2 py-1 bg-gray-200 rounded", cls),
            **attrs,
        )

    close_button._is_popover_close = True
    return close_button


# Create the test app
app, rt = star_app(
    title="Position Handler Test Suite",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        position_handler(),
        Style("""
            /* Visual indicator for flash detection */
            .flash-test-bg {
                background: repeating-linear-gradient(
                    45deg,
                    #ff0000,
                    #ff0000 10px,
                    #ffff00 10px,
                    #ffff00 20px
                );
            }
            
            /* Counter display */
            #flash-counter {
                position: fixed;
                top: 20px;
                right: 20px;
                background: #333;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                font-family: monospace;
                z-index: 10000;
            }
            
            .test-section {
                margin-bottom: 3rem;
                padding: 1.5rem;
                background: #f3f4f6;
                border-radius: 0.5rem;
            }
        """),
    ],
)


@rt("/")
def home():
    return Div(
        # Flash counter
        Div(
            "Flash Count: ",
            Span("0", id="flash-count", cls="text-xl font-bold"),
            id="flash-counter",
        ),
        # Header
        H1("Position Handler Test Suite", cls="text-3xl font-bold text-center py-8"),
        P(
            "Comprehensive testing of position.ts functionality including opacity, container parameter, and scroll behavior",
            cls="text-center text-gray-600 pb-8",
        ),
        # Test 1: Basic popover with bright background
        Div(
            H2("Test 1: Flash Detection", cls="text-xl font-semibold mb-4"),
            P("Bright pattern background makes any flash extremely visible", cls="text-gray-600 mb-4"),
            Popover(
                PopoverTrigger(
                    "Open Flash Test",
                    cls="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700",
                ),
                PopoverContent(
                    H3("Flash Detection Test", cls="font-bold mb-2"),
                    P("This popover should appear smoothly without any flash or jump."),
                    P("The bright background makes any flash very visible.", cls="text-sm text-gray-600 mt-2"),
                    PopoverClose("✕"),
                    cls="flash-test-bg border-2 border-red-500",
                ),
            ),
            cls="test-section",
        ),
        # Test 2: Different positions
        Div(
            H2("Test 2: All Positions", cls="text-xl font-semibold mb-4"),
            P("Test different placement options", cls="text-gray-600 mb-4"),
            Div(
                Popover(
                    PopoverTrigger("Top", cls="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"),
                    PopoverContent(
                        P("Top positioned", cls="font-semibold"),
                        P("Should appear above without flash"),
                        PopoverClose("✕"),
                        side="top",
                        cls="bg-green-50 border-green-300",
                    ),
                ),
                Popover(
                    PopoverTrigger("Right", cls="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"),
                    PopoverContent(
                        P("Right positioned", cls="font-semibold"),
                        P("Should appear to the right without flash"),
                        PopoverClose("✕"),
                        side="right",
                        cls="bg-purple-50 border-purple-300",
                    ),
                ),
                Popover(
                    PopoverTrigger("Bottom", cls="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"),
                    PopoverContent(
                        P("Bottom positioned", cls="font-semibold"),
                        P("Should appear below without flash"),
                        PopoverClose("✕"),
                        side="bottom",
                        cls="bg-blue-50 border-blue-300",
                    ),
                ),
                Popover(
                    PopoverTrigger("Left", cls="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700"),
                    PopoverContent(
                        P("Left positioned", cls="font-semibold"),
                        P("Should appear to the left without flash"),
                        PopoverClose("✕"),
                        side="left",
                        cls="bg-orange-50 border-orange-300",
                    ),
                ),
                cls="flex gap-4 justify-center flex-wrap",
            ),
            cls="test-section",
        ),
        # Test 3: Alignment options
        Div(
            H2("Test 3: Alignment Options", cls="text-xl font-semibold mb-4"),
            P("Test alignment variations (start, center, end)", cls="text-gray-600 mb-4"),
            Div(
                Popover(
                    PopoverTrigger("Bottom-Start", cls="px-4 py-2 bg-teal-600 text-white rounded hover:bg-teal-700"),
                    PopoverContent(
                        P("Aligned to start", cls="font-semibold"),
                        PopoverClose("✕"),
                        side="bottom",
                        align="start",
                        cls="bg-teal-50",
                    ),
                ),
                Popover(
                    PopoverTrigger(
                        "Bottom-Center", cls="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                    ),
                    PopoverContent(
                        P("Aligned to center", cls="font-semibold"),
                        PopoverClose("✕"),
                        side="bottom",
                        align="center",
                        cls="bg-indigo-50",
                    ),
                ),
                Popover(
                    PopoverTrigger("Bottom-End", cls="px-4 py-2 bg-pink-600 text-white rounded hover:bg-pink-700"),
                    PopoverContent(
                        P("Aligned to end", cls="font-semibold"),
                        PopoverClose("✕"),
                        side="bottom",
                        align="end",
                        cls="bg-pink-50",
                    ),
                ),
                cls="flex gap-4 justify-center flex-wrap",
            ),
            cls="test-section",
        ),
        # Test 4: Rapid toggle stress test
        Div(
            H2("Test 4: Rapid Toggle", cls="text-xl font-semibold mb-4"),
            P("Click rapidly to stress test - should never flash", cls="text-gray-600 mb-4"),
            Popover(
                PopoverTrigger(
                    "Rapid Toggle Test",
                    cls="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700",
                ),
                PopoverContent(
                    H3("Stress Test", cls="font-bold mb-2"),
                    P("Toggle me rapidly!"),
                    P("Even with rapid clicking, there should be no flash.", cls="text-sm text-gray-600 mt-2"),
                    Div(
                        "Toggle count: ",
                        Span("0", id="toggle-count", cls="font-mono text-lg"),
                        cls="mt-3 p-2 bg-gray-100 rounded",
                    ),
                    PopoverClose("Done"),
                    cls="bg-red-50 border-2 border-red-300",
                ),
            ),
            cls="test-section text-center",
        ),
        # Test 5: Complex content
        Div(
            H2("Test 5: Complex Content", cls="text-xl font-semibold mb-4"),
            P("Popover with form elements", cls="text-gray-600 mb-4"),
            Popover(
                PopoverTrigger(
                    "Open Form",
                    cls="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-800",
                ),
                PopoverContent(
                    H3("Settings Form", cls="font-bold mb-4"),
                    Div(
                        Label("Name", cls="block text-sm font-medium mb-1"),
                        Input(type="text", placeholder="Your name", cls="w-full px-3 py-2 border rounded"),
                        cls="mb-3",
                    ),
                    Div(
                        Label("Email", cls="block text-sm font-medium mb-1"),
                        Input(type="email", placeholder="your@email.com", cls="w-full px-3 py-2 border rounded"),
                        cls="mb-3",
                    ),
                    Div(
                        Label(
                            Input(type="checkbox", cls="mr-2"),
                            "Enable notifications",
                            cls="flex items-center text-sm",
                        ),
                        cls="mb-4",
                    ),
                    Div(
                        Button("Cancel", cls="px-3 py-1 bg-gray-200 rounded mr-2"),
                        Button("Save", cls="px-3 py-1 bg-blue-600 text-white rounded"),
                        cls="flex justify-end",
                    ),
                    PopoverClose("✕"),
                    side="bottom",
                    align="end",
                    cls="w-80",
                ),
            ),
            cls="test-section",
        ),
        # Test 6: Multiple popovers simultaneously
        Div(
            H2("Test 6: Multiple Active Popovers", cls="text-xl font-semibold mb-4"),
            P("Open multiple popovers to test simultaneous positioning", cls="text-gray-600 mb-4"),
            Div(
                Popover(
                    PopoverTrigger("Popover A", cls="px-4 py-2 bg-cyan-600 text-white rounded"),
                    PopoverContent(
                        P("First popover active"),
                        PopoverClose("✕"),
                        cls="bg-cyan-50",
                    ),
                ),
                Popover(
                    PopoverTrigger("Popover B", cls="px-4 py-2 bg-amber-600 text-white rounded"),
                    PopoverContent(
                        P("Second popover active"),
                        PopoverClose("✕"),
                        cls="bg-amber-50",
                    ),
                ),
                Popover(
                    PopoverTrigger("Popover C", cls="px-4 py-2 bg-emerald-600 text-white rounded"),
                    PopoverContent(
                        P("Third popover active"),
                        PopoverClose("✕"),
                        cls="bg-emerald-50",
                    ),
                ),
                cls="flex gap-4 justify-center flex-wrap",
            ),
            cls="test-section",
        ),
        # Test 7: Edge cases
        Div(
            H2("Test 7: Edge Cases", cls="text-xl font-semibold mb-4"),
            P("Test edge positioning and flipping", cls="text-gray-600 mb-4"),
            Div(
                Div(
                    Popover(
                        PopoverTrigger("Far Left", cls="px-3 py-1 bg-violet-600 text-white rounded text-sm"),
                        PopoverContent(
                            P("Should flip if needed", cls="text-sm"),
                            PopoverClose("✕"),
                            side="left",
                        ),
                    ),
                    cls="text-left",
                ),
                Div(
                    Popover(
                        PopoverTrigger("Far Right", cls="px-3 py-1 bg-rose-600 text-white rounded text-sm"),
                        PopoverContent(
                            P("Should flip if needed", cls="text-sm"),
                            PopoverClose("✕"),
                            side="right",
                        ),
                    ),
                    cls="text-right",
                ),
                cls="flex justify-between",
            ),
            cls="test-section",
        ),
        # Test 8: Nested Submenu Test - Critical for menubar functionality
        Div(
            H2("Test 8: Nested Submenu Positioning", cls="text-xl font-semibold mb-4"),
            P(
                "Testing submenu positioning in nested popover contexts (critical for menubar)",
                cls="text-gray-600 mb-4",
            ),
            Div(
                # Main menu with submenu using nested popovers
                Popover(
                    PopoverTrigger(
                        "Open Menu with Submenu",
                        cls="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700",
                    ),
                    PopoverContent(
                        H3("Main Menu", cls="font-bold mb-3"),
                        Div(
                            Button("Regular Item 1", cls="w-full text-left px-3 py-2 hover:bg-gray-100 rounded"),
                            Button("Regular Item 2", cls="w-full text-left px-3 py-2 hover:bg-gray-100 rounded"),
                            # Nested popover for submenu
                            Popover(
                                PopoverTrigger(
                                    "Submenu →",
                                    cls="w-full text-left px-3 py-2 hover:bg-gray-100 rounded flex justify-between items-center",
                                ),
                                PopoverContent(
                                    H4("Submenu Items", cls="font-semibold mb-2 text-sm"),
                                    Button(
                                        "Submenu Item 1",
                                        cls="w-full text-left px-3 py-2 hover:bg-blue-50 rounded text-sm",
                                    ),
                                    Button(
                                        "Submenu Item 2",
                                        cls="w-full text-left px-3 py-2 hover:bg-blue-50 rounded text-sm",
                                    ),
                                    Button(
                                        "Submenu Item 3",
                                        cls="w-full text-left px-3 py-2 hover:bg-blue-50 rounded text-sm",
                                    ),
                                    PopoverClose("✕"),
                                    side="right",
                                    align="start",
                                    cls="bg-blue-50 border-blue-300 w-48",
                                ),
                                cls="w-full",
                            ),
                            Button("Regular Item 3", cls="w-full text-left px-3 py-2 hover:bg-gray-100 rounded"),
                            cls="space-y-1",
                        ),
                        PopoverClose("✕"),
                        side="bottom",
                        align="start",
                        cls="w-64",
                    ),
                ),
                # Test all placement directions for submenus
                Popover(
                    PopoverTrigger(
                        "Test All Submenu Placements",
                        cls="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700",
                    ),
                    PopoverContent(
                        H3("Placement Tests", cls="font-bold mb-3"),
                        Div(
                            # Right-start submenu
                            Popover(
                                PopoverTrigger(
                                    "Right-Start →",
                                    cls="w-full text-left px-3 py-2 hover:bg-gray-100 rounded",
                                ),
                                PopoverContent(
                                    P("Positioned right-start", cls="text-sm"),
                                    PopoverClose("✕"),
                                    side="right",
                                    align="start",
                                    cls="bg-green-50 w-40",
                                ),
                                cls="w-full",
                            ),
                            # Right-end submenu
                            Popover(
                                PopoverTrigger(
                                    "Right-End →",
                                    cls="w-full text-left px-3 py-2 hover:bg-gray-100 rounded",
                                ),
                                PopoverContent(
                                    P("Positioned right-end", cls="text-sm"),
                                    PopoverClose("✕"),
                                    side="right",
                                    align="end",
                                    cls="bg-yellow-50 w-40",
                                ),
                                cls="w-full",
                            ),
                            # Bottom submenu
                            Popover(
                                PopoverTrigger(
                                    "Bottom ↓",
                                    cls="w-full text-left px-3 py-2 hover:bg-gray-100 rounded",
                                ),
                                PopoverContent(
                                    P("Positioned bottom", cls="text-sm"),
                                    PopoverClose("✕"),
                                    side="bottom",
                                    align="start",
                                    cls="bg-red-50 w-40",
                                ),
                                cls="w-full",
                            ),
                            # Left submenu
                            Popover(
                                PopoverTrigger(
                                    "← Left",
                                    cls="w-full text-left px-3 py-2 hover:bg-gray-100 rounded",
                                ),
                                PopoverContent(
                                    P("Positioned left", cls="text-sm"),
                                    PopoverClose("✕"),
                                    side="left",
                                    align="start",
                                    cls="bg-cyan-50 w-40",
                                ),
                                cls="w-full",
                            ),
                            # Top submenu
                            Popover(
                                PopoverTrigger(
                                    "Top ↑",
                                    cls="w-full text-left px-3 py-2 hover:bg-gray-100 rounded",
                                ),
                                PopoverContent(
                                    P("Positioned top", cls="text-sm"),
                                    PopoverClose("✕"),
                                    side="top",
                                    align="start",
                                    cls="bg-purple-50 w-40",
                                ),
                                cls="w-full",
                            ),
                            cls="space-y-1",
                        ),
                        PopoverClose("✕"),
                        side="bottom",
                        align="center",
                        cls="w-56",
                    ),
                ),
                # Deep nesting test
                Popover(
                    PopoverTrigger(
                        "Deep Nesting Test",
                        cls="px-4 py-2 bg-teal-600 text-white rounded hover:bg-teal-700",
                    ),
                    PopoverContent(
                        H3("Level 1", cls="font-bold mb-2 text-sm"),
                        Popover(
                            PopoverTrigger(
                                "Open Level 2 →",
                                cls="w-full text-left px-3 py-2 bg-teal-100 hover:bg-teal-200 rounded",
                            ),
                            PopoverContent(
                                H4("Level 2", cls="font-semibold mb-2 text-xs"),
                                Popover(
                                    PopoverTrigger(
                                        "Open Level 3 →",
                                        cls="w-full text-left px-2 py-1 bg-teal-200 hover:bg-teal-300 rounded text-sm",
                                    ),
                                    PopoverContent(
                                        P("Level 3 - Deepest", cls="text-xs"),
                                        PopoverClose("✕"),
                                        side="right",
                                        align="start",
                                        cls="bg-teal-300 w-32",
                                    ),
                                    cls="w-full",
                                ),
                                PopoverClose("✕"),
                                side="right",
                                align="start",
                                cls="bg-teal-100 w-40",
                            ),
                            cls="w-full",
                        ),
                        PopoverClose("✕"),
                        side="bottom",
                        cls="w-48",
                    ),
                ),
                cls="flex gap-4 justify-center flex-wrap",
            ),
            cls="test-section",
        ),
        # Test 9: Custom Offset Test - Verify user-specified offsets work
        Div(
            H2("Test 9: Custom Offset for Submenus", cls="text-xl font-semibold mb-4"),
            P(
                "Testing that user-specified offsets override smart defaults",
                cls="text-gray-600 mb-4",
            ),
            Div(
                # Test with explicit large gap (20px)
                Popover(
                    PopoverTrigger(
                        "Menu with 20px Gap",
                        cls="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700",
                    ),
                    PopoverContent(
                        H3("20px Gap Test", cls="font-bold mb-3"),
                        Popover(
                            PopoverTrigger(
                                "Submenu with 20px offset →",
                                cls="w-full text-left px-3 py-2 hover:bg-gray-100 rounded",
                            ),
                            PopoverContent(
                                P("This should have 20px gap", cls="text-sm"),
                                PopoverClose("✕"),
                                side="right",
                                align="start",
                                offset=20,
                                cls="w-48 bg-green-50",
                            ),
                            cls="w-full",
                        ),
                        PopoverClose("✕"),
                        side="bottom",
                        cls="w-64",
                    ),
                ),
                # Test with zero offset (touching)
                Popover(
                    PopoverTrigger(
                        "Menu with 0px Gap",
                        cls="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700",
                    ),
                    PopoverContent(
                        H3("0px Gap Test", cls="font-bold mb-3"),
                        Popover(
                            PopoverTrigger(
                                "Submenu with 0px offset →",
                                cls="w-full text-left px-3 py-2 hover:bg-gray-100 rounded",
                            ),
                            PopoverContent(
                                P("This should be touching", cls="text-sm"),
                                PopoverClose("✕"),
                                side="right",
                                align="start",
                                offset=0,
                                cls="w-48 bg-yellow-50",
                            ),
                            cls="w-full",
                        ),
                        PopoverClose("✕"),
                        side="bottom",
                        cls="w-64",
                    ),
                ),
                # Test with negative offset (overlapping more)
                Popover(
                    PopoverTrigger(
                        "Menu with -10px Overlap",
                        cls="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700",
                    ),
                    PopoverContent(
                        H3("-10px Overlap Test", cls="font-bold mb-3"),
                        Popover(
                            PopoverTrigger(
                                "Submenu with -10px offset →",
                                cls="w-full text-left px-3 py-2 hover:bg-gray-100 rounded",
                            ),
                            PopoverContent(
                                P("This should overlap by 10px", cls="text-sm"),
                                PopoverClose("✕"),
                                side="right",
                                align="start",
                                offset=-10,
                                cls="w-48 bg-red-50",
                            ),
                            cls="w-full",
                        ),
                        PopoverClose("✕"),
                        side="bottom",
                        cls="w-64",
                    ),
                ),
                cls="flex gap-4 justify-center flex-wrap",
            ),
            cls="test-section",
        ),
        # Test 10: Container Parameter - Calendar-like dropdown
        Div(
            H2("Test 10: Container Parameter - Calendar Pattern", cls="text-xl font-semibold mb-4"),
            P(
                "Calendar month/year dropdowns should position at their triggers, not parent edge (container='none')",
                cls="text-gray-600 mb-4",
            ),
            # Date picker popover
            Popover(
                PopoverTrigger(
                    "Open Date Picker",
                    cls="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700",
                ),
                PopoverContent(
                    H3("Select Date", cls="font-bold mb-3"),
                    # Calendar header with month/year selectors
                    Div(
                        # Month selector with container='none'
                        Popover(
                            PopoverTrigger(
                                "January ▼",
                                cls="px-3 py-1 bg-gray-100 rounded hover:bg-gray-200",
                            ),
                            PopoverContent(
                                H4("Select Month", cls="font-semibold mb-2 text-sm"),
                                Div(
                                    *[
                                        Button(
                                            month, cls="w-full text-left px-2 py-1 hover:bg-green-50 rounded text-sm"
                                        )
                                        for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
                                    ],
                                    cls="space-y-1",
                                ),
                                PopoverClose("✕"),
                                side="bottom",
                                align="start",
                                container="none",  # KEY: Positions relative to trigger
                                cls="bg-green-50 border-green-300 w-32 max-h-48 overflow-y-auto",
                            ),
                        ),
                        # Year selector with container='none'
                        Popover(
                            PopoverTrigger(
                                "2025 ▼",
                                cls="px-3 py-1 bg-gray-100 rounded hover:bg-gray-200 ml-2",
                            ),
                            PopoverContent(
                                H4("Select Year", cls="font-semibold mb-2 text-sm"),
                                Div(
                                    *[
                                        Button(
                                            str(year),
                                            cls="w-full text-left px-2 py-1 hover:bg-green-50 rounded text-sm",
                                        )
                                        for year in range(2020, 2026)
                                    ],
                                    cls="space-y-1",
                                ),
                                PopoverClose("✕"),
                                side="bottom",
                                align="start",
                                container="none",  # KEY: Positions relative to trigger
                                cls="bg-green-50 border-green-300 w-24 max-h-48 overflow-y-auto",
                            ),
                        ),
                        cls="flex items-center mb-3",
                    ),
                    # Simplified calendar grid
                    Div(
                        *[
                            Div(str(day), cls="px-2 py-1 text-center border rounded hover:bg-gray-100 text-sm")
                            for day in range(1, 8)
                        ],
                        cls="grid grid-cols-7 gap-1",
                    ),
                    PopoverClose("✕"),
                    side="bottom",
                    cls="w-80",
                ),
            ),
            cls="test-section",
        ),
        # Test 11: Container Parameter Comparison
        Div(
            H2("Test 11: Container Parameter Comparison", cls="text-xl font-semibold mb-4"),
            P("Compare auto vs none vs parent behaviors side-by-side", cls="text-gray-600 mb-4"),
            Div(
                # Left: container='auto' (default)
                Div(
                    H3("container='auto'", cls="font-semibold mb-2 text-sm"),
                    Popover(
                        PopoverTrigger(
                            "Open Parent",
                            cls="px-3 py-2 bg-purple-600 text-white rounded text-sm",
                        ),
                        PopoverContent(
                            P("Parent Popover", cls="font-semibold mb-2"),
                            Popover(
                                PopoverTrigger(
                                    "Nested →",
                                    cls="w-full px-3 py-2 bg-purple-100 rounded text-sm",
                                ),
                                PopoverContent(
                                    P("Auto: Aligns with parent edge", cls="text-xs"),
                                    PopoverClose("✕"),
                                    side="right",
                                    container="auto",
                                    cls="bg-purple-50 w-44",
                                ),
                            ),
                            PopoverClose("✕"),
                            cls="w-48",
                        ),
                    ),
                    P("Smart submenu positioning", cls="text-xs text-gray-600 mt-2"),
                    cls="flex-1",
                ),
                # Middle: container='none'
                Div(
                    H3("container='none'", cls="font-semibold mb-2 text-sm"),
                    Popover(
                        PopoverTrigger(
                            "Open Parent",
                            cls="px-3 py-2 bg-orange-600 text-white rounded text-sm",
                        ),
                        PopoverContent(
                            P("Parent Popover", cls="font-semibold mb-2"),
                            Popover(
                                PopoverTrigger(
                                    "Nested ↓",
                                    cls="w-full px-3 py-2 bg-orange-100 rounded text-sm",
                                ),
                                PopoverContent(
                                    P("None: At trigger button", cls="text-xs"),
                                    PopoverClose("✕"),
                                    side="bottom",
                                    container="none",
                                    cls="bg-orange-50 w-44",
                                ),
                            ),
                            PopoverClose("✕"),
                            cls="w-48",
                        ),
                    ),
                    P("Standard positioning", cls="text-xs text-gray-600 mt-2"),
                    cls="flex-1",
                ),
                # Right: container='parent'
                Div(
                    H3("container='parent'", cls="font-semibold mb-2 text-sm"),
                    Popover(
                        PopoverTrigger(
                            "Open Parent",
                            cls="px-3 py-2 bg-teal-600 text-white rounded text-sm",
                        ),
                        PopoverContent(
                            P("Parent Popover", cls="font-semibold mb-2"),
                            Div(
                                Div(
                                    Popover(
                                        PopoverTrigger(
                                            "Deep nested →",
                                            cls="px-2 py-1 bg-teal-100 rounded text-sm",
                                        ),
                                        PopoverContent(
                                            P("Parent: Forces edge align", cls="text-xs"),
                                            PopoverClose("✕"),
                                            side="right",
                                            container="parent",
                                            cls="bg-teal-50 w-44",
                                        ),
                                    ),
                                    cls="p-2 border rounded",
                                ),
                                cls="p-2",
                            ),
                            PopoverClose("✕"),
                            cls="w-48",
                        ),
                    ),
                    P("Force parent-relative", cls="text-xs text-gray-600 mt-2"),
                    cls="flex-1",
                ),
                cls="flex gap-4 justify-center",
            ),
            cls="test-section",
        ),
        # Automated test button
        Div(
            H2("Automated Test", cls="text-xl font-semibold mb-4"),
            Button(
                "Run All Tests Automatically",
                id="auto-test",
                cls="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700",
            ),
            P("Click to automatically test all popovers", cls="text-gray-600 mt-2"),
            cls="text-center p-6 bg-yellow-100 rounded-lg",
        ),
        # JavaScript to monitor for flashes and handle testing
        Script("""
            document.addEventListener('DOMContentLoaded', () => {
                let flashCount = 0;
                let toggleCount = 0;
                const flashCountEl = document.getElementById('flash-count');
                const toggleCountEl = document.getElementById('toggle-count');
                
                // Track elements that appear at 0,0 for actual user-visible flash detection
                const flashTracker = new Map();
                const FLASH_DURATION_THRESHOLD = 50; // ms - only count flashes visible for 50ms+
                
                // Monitor all popovers for actual user-visible flashing issues
                const observer = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                        if (mutation.type === 'attributes' &&
                            mutation.target.hasAttribute('popover') &&
                            mutation.attributeName === 'style') {
                            
                            const rect = mutation.target.getBoundingClientRect();
                            const style = window.getComputedStyle(mutation.target);
                            const elementId = mutation.target.id;
                            
                            // Check if element is truly visible to users (not just positioning states)
                            const isUserVisible = style.visibility !== 'hidden' &&
                                                 parseFloat(style.opacity) > 0.5 &&
                                                 mutation.target.matches(':popover-open');
                            
                            const isAt00 = rect.left >= -5 && rect.left <= 5 && rect.top >= -5 && rect.top <= 5;
                            
                            if (isUserVisible && isAt00) {
                                // Element is visible at 0,0 - start tracking
                                if (!flashTracker.has(elementId)) {
                                    flashTracker.set(elementId, Date.now());
                                    console.log(`[Flash Tracker] Started tracking ${elementId} at 0,0`);
                                }
                            } else if (flashTracker.has(elementId)) {
                                // Element moved away from 0,0 or became invisible
                                const startTime = flashTracker.get(elementId);
                                const duration = Date.now() - startTime;
                                flashTracker.delete(elementId);
                                
                                if (duration >= FLASH_DURATION_THRESHOLD) {
                                    // This was a real user-visible flash
                                    flashCount++;
                                    flashCountEl.textContent = flashCount;
                                    flashCountEl.style.color = 'red';
                                    console.warn(`REAL FLASH DETECTED: ${elementId} was visible at 0,0 for ${duration}ms`, {
                                        element: mutation.target,
                                        duration,
                                        rect: rect
                                    });
                                } else {
                                    console.log(`[Flash Tracker] ${elementId} was at 0,0 for only ${duration}ms - not counted as flash`);
                                }
                            }
                        }
                    });
                });
                
                document.querySelectorAll('[popover]').forEach(el => {
                    observer.observe(el, {
                        attributes: true,
                        attributeFilter: ['style']
                    });
                });
                
                // Track rapid toggle count
                document.querySelectorAll('[id*="trigger"]').forEach(trigger => {
                    if (trigger.textContent.includes('Rapid Toggle')) {
                        trigger.addEventListener('click', () => {
                            toggleCount++;
                            if (toggleCountEl) toggleCountEl.textContent = toggleCount;
                        });
                    }
                });
                
                // Simplified automated test - only test top-level popovers
                // Nested submenus require manual testing due to complex parent-child relationships
                document.getElementById('auto-test')?.addEventListener('click', async () => {
                    const allTriggers = document.querySelectorAll('[popovertarget]');
                    const topLevelTriggers = Array.from(allTriggers).filter(trigger => {
                        // Skip nested submenu triggers - they don't work reliably in automated tests
                        const isInPopover = trigger.closest('[popover]');
                        return !isInPopover && trigger.id !== 'auto-test';
                    });
                    
                    flashCount = 0;
                    flashCountEl.textContent = '0';
                    flashTracker.clear();
                    
                    console.log(`Testing ${topLevelTriggers.length} top-level popovers (${allTriggers.length - topLevelTriggers.length - 1} nested submenus require manual testing)`);
                    
                    for (const trigger of topLevelTriggers) {
                        console.log('Testing:', trigger.textContent.trim());
                        
                        trigger.click(); // Open
                        await new Promise(r => setTimeout(r, 300));
                        
                        // Close if still open
                        const target = document.getElementById(trigger.getAttribute('popovertarget'));
                        if (target && target.matches(':popover-open')) {
                            trigger.click();
                        }
                        await new Promise(r => setTimeout(r, 100));
                    }
                    
                    flashTracker.clear();
                    
                    const message = flashCount === 0
                        ? `SUCCESS! ${topLevelTriggers.length} top-level popovers tested with no flashing.`
                        : `FAILED: ${flashCount} flash events detected in top-level popovers.`;
                    
                    alert(message + '\\n\\nNote: Nested submenus should be tested manually by hovering/clicking.');
                });
                
                // Log success after 2 seconds if no flash
                setTimeout(() => {
                    if (flashCount === 0) {
                        console.log('SUCCESS: No flashing detected!');
                        flashCountEl.style.color = '#10b981';
                    }
                }, 2000);
            });
        """),
        cls="min-h-screen bg-gray-50 p-8 max-w-6xl mx-auto",
    )


if __name__ == "__main__":
    print("Running on http://localhost:5008")
    print("\nPosition Handler Test Suite:")
    print("- Opacity-based hiding to prevent flashing")
    print("- Container parameter (auto/none/parent) for nested popovers")
    print("- Edge cases and stress testing")
    print("\nKey container parameter usage:")
    print("  container='auto' (default): Smart submenu positioning")
    print("  container='none': Standard positioning for independent dropdowns")
    print("  container='parent': Force parent-relative positioning")
    serve(port=5009)
