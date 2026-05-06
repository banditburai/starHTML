"""Comprehensive demo showcasing the motion animation plugin capabilities."""

import time

from starhtml import *
from starhtml.plugins import (
    enter,
    exit_,
    hover,
    in_view,
    motion,
    motion_replace,
    press,
    resize_anim,
    scroll_link,
    visibility,
)

app, rt = star_app(
    sess_cls=None,
    title="Motion Plugin Demo",
    htmlkw={"lang": "en"},
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body { background: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; -webkit-font-smoothing: antialiased; }
        """),
    ],
)

app.register(motion)


def preset_cards(key: str = "0", stagger_delay: int = 0):
    """Enter animation preset cards - extracted for reuse."""
    # Each card gets a staggered delay based on its position
    return (
        Div(
            H4("Fade", cls="font-bold mb-2"),
            P("Fades in from transparent"),
            data_motion=enter(preset="fade", delay=stagger_delay * 0),
            id=f"preset-fade-{key}",
            cls="p-6 bg-blue-100 border border-blue-300 rounded",
        ),
        Div(
            H4("Slide Up", cls="font-bold mb-2"),
            P("Slides up while fading in"),
            data_motion=enter(preset="slide-up", delay=stagger_delay * 1),
            id=f"preset-slide-up-{key}",
            cls="p-6 bg-green-100 border border-green-300 rounded",
        ),
        Div(
            H4("Slide Down", cls="font-bold mb-2"),
            P("Slides down while fading in"),
            data_motion=enter(preset="slide-down", delay=stagger_delay * 2),
            id=f"preset-slide-down-{key}",
            cls="p-6 bg-purple-100 border border-purple-300 rounded",
        ),
        Div(
            H4("Scale", cls="font-bold mb-2"),
            P("Scales up from 0.9x"),
            data_motion=enter(preset="scale", delay=stagger_delay * 3),
            id=f"preset-scale-{key}",
            cls="p-6 bg-orange-100 border border-orange-300 rounded",
        ),
        Div(
            H4("Bounce", cls="font-bold mb-2"),
            P("Bounces in from above"),
            data_motion=enter(preset="bounce", spring="bouncy", delay=stagger_delay * 4),
            id=f"preset-bounce-{key}",
            cls="p-6 bg-pink-100 border border-pink-300 rounded",
        ),
    )


def custom_cards(key: str = "0"):
    """Custom enter animation cards - extracted for reuse."""
    return (
        Div(
            H4("From Left", cls="font-bold mb-2"),
            P("x:-50, opacity:0"),
            data_motion=enter(x=-50, opacity=0, duration=400),
            id=f"custom-left-{key}",
            cls="p-6 bg-cyan-100 border border-cyan-300 rounded",
        ),
        Div(
            H4("From Right", cls="font-bold mb-2"),
            P("x:50, opacity:0"),
            data_motion=enter(x=50, opacity=0, duration=400),
            id=f"custom-right-{key}",
            cls="p-6 bg-teal-100 border border-teal-300 rounded",
        ),
        Div(
            H4("Rotate In", cls="font-bold mb-2"),
            P("rotate:-15, scale:0.8"),
            data_motion=enter(rotate=-15, scale=0.8, opacity=0, duration=500),
            id=f"custom-rotate-{key}",
            cls="p-6 bg-amber-100 border border-amber-300 rounded",
        ),
        Div(
            H4("With Delay", cls="font-bold mb-2"),
            P("delay:500ms"),
            data_motion=enter(y=30, opacity=0, delay=500),
            id=f"custom-delay-{key}",
            cls="p-6 bg-rose-100 border border-rose-300 rounded",
        ),
    )


def spring_cards(key: str = "0", stagger_delay: int = 0):
    """Spring physics cards - extracted for reuse.

    Uses 600ms duration and 80px movement to make differences visible.
    Cubic-bezier can only approximate springs; true oscillation needs JS.
    """
    return (
        Div(
            H4("Gentle", cls="font-bold mb-2"),
            P("Soft and smooth"),
            data_motion=enter(y=80, opacity=0, spring="gentle", duration=600, delay=stagger_delay * 0),
            id=f"spring-gentle-{key}",
            cls="p-6 bg-indigo-100 border border-indigo-300 rounded",
        ),
        Div(
            H4("Bouncy", cls="font-bold mb-2"),
            P("Playful overshoot"),
            data_motion=enter(y=80, opacity=0, spring="bouncy", duration=600, delay=stagger_delay * 1),
            id=f"spring-bouncy-{key}",
            cls="p-6 bg-violet-100 border border-violet-300 rounded",
        ),
        Div(
            H4("Tight", cls="font-bold mb-2"),
            P("Snappy response"),
            data_motion=enter(y=80, opacity=0, spring="tight", duration=600, delay=stagger_delay * 2),
            id=f"spring-tight-{key}",
            cls="p-6 bg-fuchsia-100 border border-fuchsia-300 rounded",
        ),
        Div(
            H4("Slow", cls="font-bold mb-2"),
            P("Relaxed timing"),
            data_motion=enter(y=80, opacity=0, spring="slow", duration=600, delay=stagger_delay * 3),
            id=f"spring-slow-{key}",
            cls="p-6 bg-sky-100 border border-sky-300 rounded",
        ),
    )


def repeat_cards(key: str = "0"):
    """Repeat animation cards - extracted for reuse."""
    return (
        Div(
            H4("Pulse (3x)", cls="font-bold mb-2"),
            P("Repeats 3 times"),
            data_motion=enter(scale=0.95, opacity=0.7, duration=600, repeat=3),
            id=f"repeat-3x-{key}",
            cls="p-6 bg-pink-100 border border-pink-300 rounded",
        ),
        Div(
            H4("Infinite Pulse", cls="font-bold mb-2"),
            P("Repeats forever"),
            data_motion=enter(scale=0.95, opacity=0.8, duration=800, ease="ease-in-out", repeat="infinite"),
            id=f"repeat-infinite-{key}",
            cls="p-6 bg-red-100 border border-red-300 rounded",
        ),
    )


def sequenced_cards(completed_signal, key: str = "0"):
    """Sequenced animation cards - staggered with data-on:motion-complete.

    Uses delay parameter for staggered timing. The last card sets a signal
    when complete to demonstrate data-on:motion-complete event handling.

    Args:
        completed_signal: Signal to set when all animations complete
        key: Unique key for element IDs (for SSE replacement)
    """
    return (
        Div(
            H4("Step 1", cls="font-bold mb-2"),
            P("delay: 0ms"),
            data_motion=enter(preset="fade", duration=400),
            id=f"seq-step1-{key}",
            cls="p-6 bg-blue-100 border border-blue-300 rounded",
        ),
        Div(
            H4("Step 2", cls="font-bold mb-2"),
            P("delay: 200ms"),
            data_motion=enter(x=-30, opacity=0, duration=400, delay=200),
            id=f"seq-step2-{key}",
            cls="p-6 bg-green-100 border border-green-300 rounded",
        ),
        Div(
            H4("Step 3", cls="font-bold mb-2"),
            P("delay: 400ms"),
            data_motion=enter(scale=0.8, opacity=0, duration=400, delay=400, spring="bouncy"),
            id=f"seq-step3-{key}",
            cls="p-6 bg-purple-100 border border-purple-300 rounded",
        ),
        Div(
            H4("Step 4", cls="font-bold mb-2"),
            P("delay: 600ms + on_complete"),
            data_motion=enter(y=-20, opacity=0, duration=400, delay=600, spring="bouncy"),
            data_on_motion_complete=completed_signal.set(True),
            id=f"seq-step4-{key}",
            cls="p-6 bg-orange-100 border border-orange-300 rounded",
        ),
    )


def replay_button(endpoint: str):
    """Button that replays animations via SSE fragment replacement."""
    # Note: No leading slash - works when app is mounted at a subpath
    return Button(
        "Replay",
        data_on_click=get(endpoint),
        cls="px-4 py-2 bg-gray-800 text-white text-sm font-medium rounded hover:bg-gray-700 transition-colors",
    )


@rt("/")
def home():
    return Div(
        Div(
            # Header
            Div(
                H1("23", cls="text-8xl font-black text-gray-100 leading-none"),
                H1("Motion Plugin", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
                P(
                    "Declarative animations powered by Motion (motion.dev)",
                    cls="text-lg text-gray-600 mt-4",
                ),
                cls="mb-16",
            ),
            # Section 1: Enter Animations with Presets
            Div(
                (stagger := Signal("stagger", 100)),
                Div(
                    H3("Enter Animations with Presets", cls="text-2xl font-bold text-black"),
                    replay_button("replay/presets"),
                    cls="flex items-center justify-between mb-6",
                ),
                P(
                    "Predefined animation presets for common enter effects:",
                    cls="text-gray-600 mb-4",
                ),
                # Stagger delay slider
                Div(
                    Label(
                        "Stagger delay: ",
                        Span(data_text=stagger, cls="font-mono font-bold"),
                        "ms",
                        cls="text-sm text-gray-600",
                    ),
                    Input(
                        type="range",
                        min="0",
                        max="300",
                        step="25",
                        data_bind=stagger,
                        cls="w-48 ml-4",
                    ),
                    cls="flex items-center mb-6",
                ),
                Div(
                    *preset_cards(),
                    id="presets-grid",
                    cls="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # Section 2: Custom Enter Animations
            Div(
                Div(
                    H3("Custom Enter Animations", cls="text-2xl font-bold text-black"),
                    replay_button("replay/custom"),
                    cls="flex items-center justify-between mb-6",
                ),
                P(
                    "Define your own animation parameters with full control:",
                    cls="text-gray-600 mb-6",
                ),
                Div(
                    *custom_cards(),
                    id="custom-grid",
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # Section 3: Spring Physics
            Div(
                (spring_stagger := Signal("spring_stagger", 150)),
                Div(
                    H3("Spring Physics", cls="text-2xl font-bold text-black"),
                    replay_button("replay/spring"),
                    cls="flex items-center justify-between mb-6",
                ),
                P(
                    "Spring presets use cubic-bezier approximations. Bouncy has overshoot, slow is gradual:",
                    cls="text-gray-600 mb-4",
                ),
                # Stagger delay slider
                Div(
                    Label(
                        "Stagger delay: ",
                        Span(data_text=spring_stagger, cls="font-mono font-bold"),
                        "ms",
                        cls="text-sm text-gray-600",
                    ),
                    Input(
                        type="range",
                        min="0",
                        max="500",
                        step="50",
                        data_bind=spring_stagger,
                        cls="w-48 ml-4",
                    ),
                    cls="flex items-center mb-6",
                ),
                Div(
                    *spring_cards(),
                    id="spring-grid",
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # Section 4: Hover Gestures
            Div(
                H3("Hover Gestures", cls="text-2xl font-bold text-black mb-6"),
                P("Hover over these elements to see the animation:", cls="text-gray-600 mb-6"),
                Div(
                    Div(
                        H4("Scale Up", cls="font-bold mb-2"),
                        P("Grows on hover"),
                        data_motion=hover(scale=1.1),
                        cls="p-6 bg-emerald-100 border border-emerald-300 rounded cursor-pointer",
                    ),
                    Div(
                        H4("Lift Up", cls="font-bold mb-2"),
                        P("Rises on hover"),
                        data_motion=hover(y=-8),
                        cls="p-6 bg-lime-100 border border-lime-300 rounded cursor-pointer",
                    ),
                    Div(
                        H4("Rotate", cls="font-bold mb-2"),
                        P("Tilts on hover"),
                        data_motion=hover(rotate=5, scale=1.05),
                        cls="p-6 bg-yellow-100 border border-yellow-300 rounded cursor-pointer",
                    ),
                    cls="grid grid-cols-1 md:grid-cols-3 gap-4",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # Section 5: Press Gestures
            Div(
                H3("Press Gestures", cls="text-2xl font-bold text-black mb-6"),
                P("Click and hold these buttons to see press effects:", cls="text-gray-600 mb-6"),
                Div(
                    Button(
                        "Press Me",
                        data_motion=press(scale=0.95),
                        cls="px-6 py-3 bg-blue-500 text-white font-bold rounded cursor-pointer select-none",
                    ),
                    Button(
                        "Push Down",
                        data_motion=press(scale=0.97, y=2),
                        cls="px-6 py-3 bg-green-500 text-white font-bold rounded cursor-pointer select-none",
                    ),
                    Button(
                        "Squish",
                        data_motion=press(scale=0.9),
                        cls="px-6 py-3 bg-purple-500 text-white font-bold rounded cursor-pointer select-none",
                    ),
                    cls="flex flex-wrap gap-4",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # Section 6: In-View Animations (scroll triggered, re-triggerable)
            Div(
                H3("Scroll-Triggered In-View Animations", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "Scroll down to see these elements animate into view. Scroll away and back to see them again!",
                    cls="text-gray-600 mb-6",
                ),
                Div(cls="h-8"),
                Div(
                    Div(
                        H4("Fade In", cls="font-bold mb-2"),
                        P("Animates when scrolled into view"),
                        data_motion=in_view(preset="fade", duration=600, once=False),
                        cls="p-6 bg-red-100 border border-red-300 rounded",
                    ),
                    Div(cls="h-32"),
                    Div(
                        H4("Slide Up", cls="font-bold mb-2"),
                        P("Slides up from below"),
                        data_motion=in_view(y=50, opacity=0, duration=700, once=False),
                        cls="p-6 bg-blue-100 border border-blue-300 rounded",
                    ),
                    Div(cls="h-32"),
                    Div(
                        H4("Scale In", cls="font-bold mb-2"),
                        P("Scales up into view"),
                        data_motion=in_view(scale=0.8, opacity=0, duration=500, spring="bouncy", once=False),
                        cls="p-6 bg-green-100 border border-green-300 rounded",
                    ),
                    Div(cls="h-32"),
                    Div(
                        H4("From Left", cls="font-bold mb-2"),
                        P("Slides in from the left"),
                        data_motion=in_view(x=-100, opacity=0, duration=600, once=False),
                        cls="p-6 bg-purple-100 border border-purple-300 rounded",
                    ),
                    Div(cls="h-32"),
                    Div(
                        H4("From Right", cls="font-bold mb-2"),
                        P("Slides in from the right"),
                        data_motion=in_view(x=100, opacity=0, duration=600, once=False),
                        cls="p-6 bg-orange-100 border border-orange-300 rounded",
                    ),
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # Section 7: Scroll-Linked Parallax
            Div(
                H3("Scroll-Linked Animations", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "Elements that animate based on scroll position (watch as you scroll this section):",
                    cls="text-gray-600 mb-6",
                ),
                Div(
                    Div(
                        H4("Parallax Layer 1", cls="font-bold mb-2 text-white"),
                        P("Moves slower (y: 0 to -50)", cls="text-white/80"),
                        data_motion=scroll_link(y=(0, -50)),
                        cls="p-6 bg-gradient-to-r from-blue-500 to-purple-500 rounded",
                    ),
                    Div(
                        H4("Parallax Layer 2", cls="font-bold mb-2 text-white"),
                        P("Moves faster (y: 0 to 50)", cls="text-white/80"),
                        data_motion=scroll_link(y=(0, 50)),
                        cls="p-6 bg-gradient-to-r from-green-500 to-teal-500 rounded",
                    ),
                    Div(
                        H4("Scale on Scroll", cls="font-bold mb-2 text-white"),
                        P("Scales up as you scroll (0.8 to 1.0)", cls="text-white/80"),
                        data_motion=scroll_link(scale=(0.8, 1.0)),
                        cls="p-6 bg-gradient-to-r from-orange-500 to-red-500 rounded",
                    ),
                    Div(
                        H4("Fade on Scroll", cls="font-bold mb-2 text-white"),
                        P("Fades in as you scroll (0.3 to 1.0)", cls="text-white/80"),
                        data_motion=scroll_link(opacity=(0.3, 1.0)),
                        cls="p-6 bg-gradient-to-r from-pink-500 to-rose-500 rounded",
                    ),
                    Div(
                        H4("Rotate on Scroll", cls="font-bold mb-2 text-white"),
                        P("Rotates as you scroll (-10 to 10 deg)", cls="text-white/80"),
                        data_motion=scroll_link(rotate=(-10, 10)),
                        cls="p-6 bg-gradient-to-r from-violet-500 to-indigo-500 rounded",
                    ),
                    cls="space-y-8",
                ),
                Div(cls="h-64"),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # Section 8: Staggered Animations with data-on:motion-complete
            Div(
                (seq_complete := Signal("seq_complete", False)),
                Div(
                    H3("Staggered Animations", cls="text-2xl font-bold text-black"),
                    replay_button("replay/sequence"),
                    cls="flex items-center justify-between mb-6",
                ),
                P(
                    "Use the delay parameter for staggered timing. The last card demonstrates data-on:motion-complete event handling.",
                    cls="text-gray-600 mb-6",
                ),
                Div(
                    Span("Sequence complete: ", cls="text-gray-600"),
                    Span(data_text=seq_complete, cls="font-mono font-bold"),
                    cls="mb-4",
                ),
                Div(
                    *sequenced_cards(seq_complete),
                    id="sequence-grid",
                    cls="grid grid-cols-1 md:grid-cols-4 gap-4",
                ),
                cls="mb-12 p-8 bg-gradient-to-r from-blue-50 to-purple-50",
            ),
            # Section 9: Visibility Helper (NEW unified API)
            Div(
                (show_details := Signal("show_details", False)),
                H3("Visibility Helper", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "The visibility() helper provides a clean, single-attribute API for animated show/hide. "
                    "It watches a signal and handles both enter and exit animations automatically.",
                    cls="text-gray-600 mb-6",
                ),
                # Accordion-style expandable section
                Div(
                    # Header (always visible)
                    Div(
                        Button(
                            Span("Show Details", data_show=f"!{show_details}"),
                            Span("Hide Details", data_show=show_details),
                            data_on_click=show_details.toggle(),
                            cls="flex items-center gap-2 w-full text-left px-4 py-3 bg-emerald-500 text-white font-bold rounded-t hover:bg-emerald-600",
                        ),
                        Span(
                            " Expanded: ",
                            Span(data_text=show_details, cls="font-mono font-bold"),
                            cls="ml-4 text-gray-600 text-sm",
                        ),
                        cls="flex items-center",
                    ),
                    # Expandable content
                    Div(
                        Div(
                            H4("Additional Information", cls="font-bold mb-3"),
                            P(
                                "This content smoothly animates in and out using the visibility() helper. "
                                "The layout shift is intentional for accordion-style components.",
                                cls="text-gray-600 mb-3",
                            ),
                            Ul(
                                Li("Single attribute handles both enter and exit"),
                                Li("Watches a signal for reactive show/hide"),
                                Li("Configurable animations for each direction"),
                                cls="list-disc list-inside text-gray-600 space-y-1",
                            ),
                            cls="p-4",
                        ),
                        data_motion=visibility(
                            signal=show_details,
                            enter=enter(y=-20, opacity=0, duration=400),
                            exit_=exit_(y=-10, opacity=0, duration=250),
                        ),
                        cls="bg-emerald-100 border border-emerald-300 border-t-0 rounded-b",
                    ),
                    cls="max-w-lg",
                ),
                Pre(
                    Code(
                        "# Accordion with visibility():\n"
                        "(show := Signal('show', False)),\n"
                        "Button('Toggle', data_on_click=show.toggle()),\n"
                        "Div(\n"
                        "    'Expandable content here...',\n"
                        "    data_motion=visibility(\n"
                        "        signal=show,\n"
                        "        enter=enter(y=-20, opacity=0, duration=400),\n"
                        "        exit_=exit_(y=-10, opacity=0, duration=250),\n"
                        "    ),\n"
                        ")",
                        cls="text-sm",
                    ),
                    cls="mt-6 p-4 bg-gray-800 text-green-400 rounded overflow-x-auto",
                ),
                cls="mb-12 p-8 bg-emerald-50",
            ),
            # Section 10: Repeating Animations
            Div(
                Div(
                    H3("Repeating Animations", cls="text-2xl font-bold text-black"),
                    replay_button("replay/repeat"),
                    cls="flex items-center justify-between mb-6",
                ),
                P("Use repeat() for looping animations:", cls="text-gray-600 mb-6"),
                Div(
                    *repeat_cards(),
                    id="repeat-grid",
                    cls="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl",
                ),
                cls="mb-12 p-8 bg-pink-50",
            ),
            # Section 11: Imperative Actions
            Div(
                H3("Imperative Actions", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "Use motion.animate(), motion.set() for event-driven animations:",
                    cls="text-gray-600 mb-6",
                ),
                Div(
                    # Target box to animate
                    Div(
                        "Target",
                        id="action-target",
                        cls="w-24 h-24 bg-indigo-500 text-white flex items-center justify-center font-bold rounded",
                    ),
                    cls="mb-6",
                ),
                Div(
                    Button(
                        "Slide Right",
                        data_on_click=motion.animate("#action-target", x=100, duration=300),
                        cls="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600",
                    ),
                    Button(
                        "Slide Back",
                        data_on_click=motion.animate("#action-target", x=0, duration=300),
                        cls="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600",
                    ),
                    Button(
                        "Scale Up",
                        data_on_click=motion.animate("#action-target", scale=1.5, duration=200, spring="bouncy"),
                        cls="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600",
                    ),
                    Button(
                        "Reset",
                        data_on_click=motion.set("#action-target", x=0, scale=1, opacity=1),
                        cls="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600",
                    ),
                    Button(
                        "Fade Out",
                        data_on_click=motion.animate("#action-target", opacity=0.3, duration=400),
                        cls="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600",
                    ),
                    cls="flex flex-wrap gap-3",
                ),
                cls="mb-12 p-8 bg-indigo-50",
            ),
            # Section 12: Remove and Replace Actions (SSE-friendly)
            Div(
                H3("Remove & Replace Actions", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "Use motion.remove() and motion.replace() for SSE-driven DOM changes with exit animations. "
                    "The element plays its exit animation before being removed or replaced.",
                    cls="text-gray-600 mb-6",
                ),
                # Remove demo
                Div(
                    H4("Remove Example", cls="font-semibold mb-3"),
                    Div(
                        Div(
                            "Notification 1",
                            id="notif-1",
                            data_motion_exit=exit_(opacity=0, x=50, duration=300),
                            cls="p-3 bg-blue-100 border border-blue-300 rounded flex justify-between items-center",
                        ),
                        Div(
                            "Notification 2",
                            id="notif-2",
                            data_motion_exit=exit_(opacity=0, x=50, duration=300),
                            cls="p-3 bg-green-100 border border-green-300 rounded flex justify-between items-center",
                        ),
                        Div(
                            "Notification 3",
                            id="notif-3",
                            data_motion_exit=exit_(opacity=0, x=50, duration=300),
                            cls="p-3 bg-purple-100 border border-purple-300 rounded flex justify-between items-center",
                        ),
                        id="notif-container",
                        cls="space-y-2 mb-4",
                    ),
                    Div(
                        Button(
                            "Remove #1",
                            data_on_click=motion.remove("#notif-1"),
                            cls="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600",
                        ),
                        Button(
                            "Remove #2",
                            data_on_click=motion.remove("#notif-2"),
                            cls="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600",
                        ),
                        Button(
                            "Remove #3",
                            data_on_click=motion.remove("#notif-3"),
                            cls="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600",
                        ),
                        replay_button("replay/notifications"),
                        cls="flex flex-wrap gap-2",
                    ),
                    cls="mb-8",
                ),
                # Replace demo - using SSE with motion_replace
                Div(
                    H4("Replace Example (SSE)", cls="font-semibold mb-3"),
                    P(
                        "Use motion_replace() SSE helper for animated replacements. "
                        "Exit animation plays first, then new content fades in:",
                        cls="text-sm text-gray-500 mb-3",
                    ),
                    Div(
                        Div(
                            H4("Version 1", cls="font-bold"),
                            P("Original content"),
                            id="replace-target",
                            data_motion=enter(preset="fade", duration=300),
                            data_motion_exit=exit_(opacity=0, scale=0.9, duration=200),
                            cls="p-4 bg-amber-100 border border-amber-300 rounded",
                        ),
                        cls="max-w-xs mb-4",
                    ),
                    Div(
                        Button(
                            "Replace → V2",
                            data_on_click=get("./replace/v2"),
                            cls="px-3 py-1 bg-amber-500 text-white text-sm rounded hover:bg-amber-600",
                        ),
                        Button(
                            "Reset → V1",
                            data_on_click=get("./replace/v1"),
                            cls="px-3 py-1 bg-gray-500 text-white text-sm rounded hover:bg-gray-600 ml-2",
                        ),
                        cls="flex gap-2",
                    ),
                    cls="mb-4",
                ),
                Pre(
                    Code(
                        "# SSE endpoint with exit animation:\n"
                        "from starhtml.plugins import motion_replace\n\n"
                        "@rt('/update')\n"
                        "@sse\n"
                        "def update(req):\n"
                        "    yield motion_replace(\n"
                        '        "#target",\n'
                        "        Div('New content',\n"
                        "            data_motion_exit=exit_(opacity=0))\n"
                        "    )",
                        cls="text-sm",
                    ),
                    cls="mt-4 p-4 bg-gray-800 text-green-400 rounded overflow-x-auto",
                ),
                cls="mb-12 p-8 bg-amber-50",
            ),
            # Section 13: Animation Sequences
            Div(
                H3("Animation Sequences", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "Chain animations with motion.sequence() using dict() syntax for keyframes and options. "
                    "Click Reset first to hide elements, then Run Sequence to see the staggered animation:",
                    cls="text-gray-600 mb-6",
                ),
                Div(
                    Button(
                        "Reset",
                        data_on_click=motion.set("#seq-title", opacity=0)
                        + motion.set("#seq-subtitle", y=20, opacity=0)
                        + motion.set("#seq-button", scale=0.8, opacity=0),
                        cls="px-4 py-2 bg-gray-500 text-white font-bold rounded hover:bg-gray-600",
                    ),
                    Button(
                        "Run Sequence",
                        data_on_click=motion.sequence(
                            [
                                ("#seq-title", dict(opacity=1, duration=300)),
                                ("#seq-subtitle", dict(y=0, opacity=1, duration=300), dict(at="+0.15")),
                                ("#seq-button", dict(scale=1, opacity=1, duration=300), dict(at="+0.15")),
                            ]
                        ),
                        cls="px-4 py-2 bg-cyan-500 text-white font-bold rounded hover:bg-cyan-600 ml-3",
                    ),
                    cls="mb-6",
                ),
                Div(
                    Div(
                        "Title",
                        id="seq-title",
                        cls="text-3xl font-bold text-cyan-600",
                    ),
                    Div(
                        "Subtitle text appears after title",
                        id="seq-subtitle",
                        cls="text-lg text-gray-600 mt-2",
                    ),
                    Div(
                        Button("Action Button", cls="px-4 py-2 bg-cyan-500 text-white rounded"),
                        id="seq-button",
                        cls="mt-4",
                    ),
                    cls="p-6 bg-white border border-cyan-200 rounded",
                ),
                cls="mb-12 p-8 bg-cyan-50",
            ),
            # Section 13: Resize Animations
            Div(
                H3("Resize Animations", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "Animations triggered by element resize. Drag the corner to resize and see the pulse effect:",
                    cls="text-gray-600 mb-6",
                ),
                Div(
                    Div(
                        H4("Resize Me", cls="font-bold mb-2"),
                        P("Pulses when resized (scale bounces from 1.1x to 1x)"),
                        data_motion=resize_anim(scale=1.1, opacity=0.7, duration=400),
                        style="resize: both; overflow: auto; min-width: 150px; min-height: 100px; width: 250px; height: 120px;",
                        cls="p-4 bg-teal-100 border-2 border-teal-400 rounded cursor-se-resize",
                    ),
                    cls="max-w-md",
                ),
                cls="mb-12 p-8 bg-teal-50",
            ),
            # Section 15: Playback Controls
            Div(
                # State: 'stopped' | 'playing' | 'paused'
                (anim_state := Signal("anim_state", "stopped")),
                H3("Playback Controls", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "Simple play/pause toggle with stop:",
                    cls="text-gray-600 mb-6",
                ),
                Div(
                    Div(
                        "Animated Box",
                        id="playback-target",
                        cls="w-32 h-32 bg-amber-500 text-white flex items-center justify-center font-bold rounded",
                    ),
                    cls="mb-6",
                ),
                Div(
                    # Play button - starts new animation or resumes paused
                    Button(
                        "Play",
                        data_on_click=motion.animate(
                            "#playback-target",
                            x=100,
                            duration=1000,
                            ease="ease-in-out",
                            repeat="infinite",
                            repeatType="mirror",
                            name="demo-anim",
                        )
                        + "; "
                        + motion.play("demo-anim")
                        + f"; {anim_state.set('playing')}",
                        cls="px-6 py-2 bg-green-500 text-white rounded hover:bg-green-600",
                    ),
                    Button(
                        "Pause",
                        data_on_click=motion.pause("demo-anim") + f"; {anim_state.set('paused')}",
                        cls="px-6 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600",
                    ),
                    Button(
                        "Stop",
                        data_on_click=motion.cancel("demo-anim")
                        + "; "
                        + motion.set("#playback-target", x=0)
                        + f"; {anim_state.set('stopped')}",
                        cls="px-6 py-2 bg-gray-500 text-white rounded hover:bg-gray-600",
                    ),
                    cls="flex flex-wrap gap-3",
                ),
                Div(
                    Span("State: ", cls="text-gray-600"),
                    Span(data_text=anim_state, cls="font-mono font-bold"),
                    cls="mt-4 text-sm",
                ),
                P(
                    "Play starts or resumes. Pause freezes at current position. "
                    "Stop uses cancel() + set() to revert to original position.",
                    cls="text-sm text-gray-500 mt-2",
                ),
                cls="mb-12 p-8 bg-amber-50",
            ),
            # Section 16: Named Animations
            Div(
                H3("Named Animations", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "Give animations a name to control them programmatically from anywhere:",
                    cls="text-gray-600 mb-6",
                ),
                Div(
                    Div(
                        H4("Hero Element", cls="font-bold mb-2"),
                        P("Named 'hero' for remote control"),
                        id="hero-element",
                        cls="p-6 bg-violet-100 border border-violet-300 rounded",
                    ),
                    cls="max-w-md mb-6",
                ),
                Div(
                    Button(
                        "Play",
                        data_on_click=motion.animate(
                            "#hero-element",
                            scale=1.05,
                            duration=800,
                            ease="ease-in-out",
                            repeat="infinite",
                            repeatType="mirror",
                            name="hero",
                        )
                        + "; "
                        + motion.play("hero"),
                        cls="px-6 py-2 bg-green-500 text-white rounded hover:bg-green-600",
                    ),
                    Button(
                        "Pause",
                        data_on_click=motion.pause("hero"),
                        cls="px-6 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600",
                    ),
                    Button(
                        "Stop",
                        data_on_click=motion.cancel("hero") + "; " + motion.set("#hero-element", scale=1),
                        cls="px-6 py-2 bg-gray-500 text-white rounded hover:bg-gray-600",
                    ),
                    cls="flex flex-wrap gap-3",
                ),
                Pre(
                    Code(
                        "# Named animations can be controlled from anywhere\n"
                        'motion.animate("#hero", scale=1.05, repeat="infinite", name="hero")\n'
                        'motion.pause("hero")  # Pause by name\n'
                        'motion.play("hero")   # Resume by name\n'
                        'motion.cancel("hero") + motion.set("#hero", scale=1)  # Stop and reset',
                        cls="text-sm",
                    ),
                    cls="mt-4 p-4 bg-gray-800 text-green-400 rounded overflow-x-auto",
                ),
                cls="mb-12 p-8 bg-violet-50",
            ),
            # Section 17: Motion Events
            Div(
                (event_log := Signal("event_log", "No events yet")),
                H3("Motion Events", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "Listen to animation lifecycle events. Click 'Start Slide' then quickly 'Stop' to see the cancel event:",
                    cls="text-gray-600 mb-6",
                ),
                Div(
                    Span("Event log: ", cls="text-gray-600"),
                    Span(data_text=event_log, cls="font-mono font-bold text-blue-600"),
                    cls="mb-4 p-3 bg-white border border-gray-200 rounded",
                ),
                # Card slides edge-to-edge using CSS calc with container queries
                Div(
                    Div(
                        H4("Event Tracked Card", cls="font-bold mb-2"),
                        P("Slides across over 3 seconds"),
                        id="event-card",
                        data_on_motion_start=event_log.set("Animation started!"),
                        data_on_motion_complete=event_log.set("Animation complete!"),
                        data_on_motion_cancel=event_log.set("Animation cancelled!"),
                        cls="p-4 bg-sky-100 border border-sky-300 rounded w-48",
                    ),
                    id="event-card-container",
                    cls="mb-6",
                    style="container-type: inline-size;",
                ),
                Div(
                    Button(
                        "Start Slide",
                        data_on_click=motion.animate(
                            "#event-card",
                            x="calc(100cqw - 100%)",
                            duration=3000,
                            ease="ease-in-out",
                            name="event-demo",
                        ),
                        cls="px-4 py-2 bg-sky-500 text-white rounded hover:bg-sky-600",
                    ),
                    Button(
                        "Stop",
                        data_on_click=motion.cancel("event-demo") + "; " + motion.set("#event-card", x=0),
                        cls="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600",
                    ),
                    cls="flex flex-wrap gap-3",
                ),
                Pre(
                    Code(
                        'data_on_motion_start=event_log.set("Started!")\n'
                        'data_on_motion_complete=event_log.set("Complete!")\n'
                        'data_on_motion_cancel=event_log.set("Cancelled!")',
                        cls="text-sm",
                    ),
                    cls="mt-4 p-4 bg-gray-800 text-green-400 rounded overflow-x-auto",
                ),
                cls="mb-12 p-8 bg-sky-50",
            ),
            # Section 18: API Reference
            Div(
                H3("API Reference", cls="text-2xl font-bold text-black mb-6"),
                P("Motion config is declarative - describes WHAT the animation looks like:", cls="text-gray-600 mb-6"),
                Div(
                    Div(
                        H4("Animation Config Parameters", cls="text-lg font-bold text-black mb-4"),
                        Ul(
                            Li(
                                Code("duration=300", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Animation duration in ms",
                            ),
                            Li(
                                Code("delay=0", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Delay before animation starts",
                            ),
                            Li(
                                Code("repeat=n", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Repeat n times or 'infinite'",
                            ),
                            Li(
                                Code("stagger=100", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Stagger children by delay (ms)",
                            ),
                            Li(
                                Code("spring='bouncy'", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Spring preset: gentle, bouncy, tight, slow",
                            ),
                            cls="text-sm space-y-2 list-disc list-inside text-gray-700",
                        ),
                    ),
                    Div(
                        H4("Event Handling", cls="text-lg font-bold text-black mb-4"),
                        Ul(
                            Li(
                                Code("data_on_motion_start", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Handler for animation start event",
                            ),
                            Li(
                                Code("data_on_motion_complete", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Handler for animation complete event",
                            ),
                            Li(
                                Code("data_on_motion_cancel", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Handler for animation cancel event",
                            ),
                            Li(
                                Code("data_show=signal", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Combine with Datastar for visibility",
                            ),
                            cls="text-sm space-y-2 list-disc list-inside text-gray-700",
                        ),
                        H4("Exposed Signals", cls="text-lg font-bold text-black mb-4 mt-6"),
                        Ul(
                            Li(
                                Code("motion.is_animating", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Boolean: animation active",
                            ),
                            Li(
                                Code("motion.phase", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Current phase: idle/enter/hover/tap",
                            ),
                            Li(
                                Code("motion.progress", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Scroll progress 0-100",
                            ),
                            cls="text-sm space-y-2 list-disc list-inside text-gray-700",
                        ),
                    ),
                    cls="grid grid-cols-1 lg:grid-cols-2 gap-8",
                ),
                cls="mb-12 p-8 bg-purple-50",
            ),
            cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white",
        ),
        cls="min-h-screen bg-white",
    )


# SSE endpoints for replaying animations
# Use unique IDs on each card to force morph to create new elements (triggers plugin re-apply)
@rt("/replay/presets")
@sse
def replay_presets(req, stagger: int = 100):
    """Replace preset cards to replay their enter animations."""
    key = str(time.time_ns())
    yield elements(
        Div(*preset_cards(key, stagger), id="presets-grid", cls="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4"),
        "#presets-grid",
        "outer",
    )


@rt("/replay/custom")
@sse
def replay_custom(req):
    """Replace custom cards to replay their enter animations."""
    key = str(time.time_ns())
    yield elements(
        Div(*custom_cards(key), id="custom-grid", cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"),
        "#custom-grid",
        "outer",
    )


@rt("/replay/spring")
@sse
def replay_spring(req, spring_stagger: int = 150):
    """Replace spring cards to replay their enter animations."""
    key = str(time.time_ns())
    yield elements(
        Div(
            *spring_cards(key, spring_stagger),
            id="spring-grid",
            cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4",
        ),
        "#spring-grid",
        "outer",
    )


@rt("/replay/repeat")
@sse
def replay_repeat(req):
    """Replace repeat cards to replay their animations."""
    key = str(time.time_ns())
    yield elements(
        Div(*repeat_cards(key), id="repeat-grid", cls="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl"),
        "#repeat-grid",
        "outer",
    )


@rt("/replay/sequence")
@sse
def replay_sequence(req):
    """Replace sequenced cards to reset and replay their animations."""
    key = str(time.time_ns())
    seq_complete = Signal("seq_complete", False)
    yield elements(
        Div(
            seq_complete,
            *sequenced_cards(seq_complete, key),
            id="sequence-grid",
            cls="grid grid-cols-1 md:grid-cols-4 gap-4",
        ),
        "#sequence-grid",
        "outer",
    )


@rt("/replay/notifications")
@sse
def replay_notifications(req):
    """Replace notification container to restore removed notifications."""
    yield elements(
        Div(
            Div(
                "Notification 1",
                id="notif-1",
                data_motion_exit=exit_(opacity=0, x=50, duration=300),
                cls="p-3 bg-blue-100 border border-blue-300 rounded flex justify-between items-center",
            ),
            Div(
                "Notification 2",
                id="notif-2",
                data_motion_exit=exit_(opacity=0, x=50, duration=300),
                cls="p-3 bg-green-100 border border-green-300 rounded flex justify-between items-center",
            ),
            Div(
                "Notification 3",
                id="notif-3",
                data_motion_exit=exit_(opacity=0, x=50, duration=300),
                cls="p-3 bg-purple-100 border border-purple-300 rounded flex justify-between items-center",
            ),
            id="notif-container",
            cls="space-y-2 mb-4",
        ),
        "#notif-container",
        "outer",
    )


@rt("/replace/v2")
@sse
def replace_to_v2(req):
    """Replace card with Version 2 content using motion_replace for exit animation."""
    yield motion_replace(
        "#replace-target",
        Div(
            H4("Version 2", cls="font-bold"),
            P("Replaced content!"),
            id="replace-target",
            data_motion=enter(preset="fade", duration=300),
            data_motion_exit=exit_(opacity=0, scale=0.9, duration=200),
            cls="p-4 bg-teal-100 border border-teal-300 rounded",
        ),
    )


@rt("/replace/v1")
@sse
def replace_to_v1(req):
    """Reset card back to Version 1 content using motion_replace for exit animation."""
    yield motion_replace(
        "#replace-target",
        Div(
            H4("Version 1", cls="font-bold"),
            P("Original content"),
            id="replace-target",
            data_motion=enter(preset="fade", duration=300),
            data_motion_exit=exit_(opacity=0, scale=0.9, duration=200),
            cls="p-4 bg-amber-100 border border-amber-300 rounded",
        ),
    )


if __name__ == "__main__":
    print("Motion Plugin Demo running on http://localhost:5001")
    serve(port=5001)
