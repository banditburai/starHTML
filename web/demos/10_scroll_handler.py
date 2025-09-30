"""Comprehensive demo showcasing the scroll handler capabilities."""

from starhtml import *  # This imports scroll namespace automatically

app, rt = star_app(
    title="Scroll Handler Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body { background: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; -webkit-font-smoothing: antialiased; }
        """),
        (scroll := scroll_handler()),  # Assign to variable for signal access
    ],
    iconify=True,
    compression=False,
)


@rt("/")
def home():
    return Div(
        # Main container
        Div(
            # The scroll handler will initialize its own signals automatically
            (fast_count := Signal("fast_count", 0)),
            (medium_count := Signal("medium_count", 0)),
            (slow_count := Signal("slow_count", 0)),
            (parallax1 := Signal("parallax1", 0)),
            (parallax2 := Signal("parallax2", 0)),
            (parallax3 := Signal("parallax3", 0)),
            (fade_visible := Signal("fade_visible", False)),
            (scale_visible := Signal("scale_visible", False)),
            (slide_visible := Signal("slide_visible", False)),
            (current_scroll_direction := Signal("current_scroll_direction", "down")),
            # The scroll handler provides variables via scroll namespace:
            # scroll_x, scroll_y, scroll_direction, scroll_velocity, etc. or underscore instead of dot for the js variables
            # Header with bold typography
            Div(
                H1("10", cls="text-8xl font-black text-gray-100 leading-none"),
                H1("Scroll Handler", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
                P("Data-on-scroll functionality with optimized scroll detection", cls="text-lg text-gray-600 mt-4"),
                cls="mb-16",
            ),
            # Basic Scroll Detection
            Div(
                H3("Basic Scroll Detection", cls="text-2xl font-bold text-black mb-6"),
                P("Scroll down to see real-time scroll position updates:", cls="text-gray-600 mb-6"),
                Div(
                    H4("Scroll Monitor", cls="text-lg font-bold text-black mb-4"),
                    Div(
                        # Position indicator
                        P(
                            "Position: ",
                            Span(data_text=scroll.y.round(), cls="font-mono font-bold text-blue-600"),
                            " px",
                            cls="text-lg",
                        ),
                        # Visual scroll activity indicator (more intuitive than numbers)
                        Div(
                            Div(
                                # Activity bar that scales with velocity
                                data_style_width=js("Math.min(100, $scroll_velocity / 10) + '%'"),
                                data_class=switch(
                                    [
                                        (scroll.direction == "up", "bg-green-500"),
                                        (scroll.direction == "down", "bg-red-500"),
                                    ],
                                    default="bg-gray-300",
                                ),
                                cls="h-2 transition-all duration-100 rounded",
                            ),
                            P(
                                "Activity: ",
                                Span(
                                    data_text=switch(
                                        [
                                            (scroll.velocity == 0, "Idle"),
                                            (scroll.direction == "up", "Scrolling Up"),
                                            (scroll.direction == "down", "Scrolling Down"),
                                        ],
                                        default="Idle",
                                    ),
                                    data_class=switch(
                                        [
                                            (scroll.direction == "up", "text-green-600 font-bold"),
                                            (scroll.direction == "down", "text-red-600 font-bold"),
                                        ],
                                        default="text-gray-500",
                                    ),
                                ),
                                cls="text-sm mt-1",
                            ),
                            cls="w-full",
                        ),
                        cls="space-y-3",
                    ),
                    cls="p-6 bg-white border border-gray-200 sticky top-24 z-5",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # Hide/Show on Scroll Direction
            Div(
                H3("Hide/Show Based on Scroll Direction", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "Fixed indicators that respond to scroll direction (like the comparison demo):",
                    cls="text-gray-600 mb-4",
                ),
                P(
                    "Scroll up and down to see the indicators change on the right side!",
                    cls="text-center text-gray-500 mb-6",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # Scroll Progress Indicator
            Div(
                H3("Scroll Progress Indicator", cls="text-2xl font-bold text-black mb-6"),
                P("A progress bar that fills as you scroll:", cls="text-gray-600 mb-6"),
                Div(
                    Div(
                        H4("Scroll Progress", cls="text-lg font-bold text-black mb-4"),
                        Div(
                            Div(
                                # Pythonic: String concatenation for percentage
                                data_style_width=scroll.page_progress + "%",
                                # JS equivalent: `${$pageProgress || 0}%`
                                id="progress-fill",
                                cls="h-3 bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-150 rounded-full",
                            ),
                            cls="w-full h-3 bg-gray-200 rounded-full overflow-hidden",
                        ),
                        P(
                            "Page Progress: ",
                            # Pythonic: String concatenation
                            Span(data_text=scroll.page_progress.round() + "%", cls="font-bold text-purple-600"),
                            cls="text-sm mt-2",
                        ),
                        cls="p-6 bg-white border border-gray-200 sticky top-24 z-5",
                    ),
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # Throttling Demo
            Div(
                H3("Throttling Configuration", cls="text-2xl font-bold text-black mb-6"),
                P("Different throttle settings for performance optimization:", cls="text-gray-600 mb-6"),
                Div(
                    Div(
                        H4("High Frequency (25ms)", cls="text-lg font-bold text-black mb-2"),
                        Div(
                            Span(data_text=fast_count, cls="text-3xl font-black text-black"),
                            Span(" updates", cls="text-sm text-gray-500 ml-1"),
                            cls="mb-2",
                        ),
                        P("Very responsive", cls="text-sm text-gray-600"),
                        data_scroll=(fast_count.add(1), dict(throttle=25)),
                        id="throttle-25",
                        cls="p-6 bg-white border border-gray-200 rounded",
                    ),
                    Div(
                        H4("Medium Frequency (100ms)", cls="text-lg font-bold text-black mb-2"),
                        Div(
                            Span(data_text=medium_count, cls="text-3xl font-black text-black"),
                            Span(" updates", cls="text-sm text-gray-500 ml-1"),
                            cls="mb-2",
                        ),
                        P("Balanced performance", cls="text-sm text-gray-600"),
                        data_scroll=(medium_count.add(1), dict(throttle=100)),
                        id="throttle-100",
                        cls="p-6 bg-white border border-gray-200 rounded",
                    ),
                    Div(
                        H4("Low Frequency (250ms)", cls="text-lg font-bold text-black mb-2"),
                        Div(
                            Span(data_text=slow_count, cls="text-3xl font-black text-black"),
                            Span(" updates", cls="text-sm text-gray-500 ml-1"),
                            cls="mb-2",
                        ),
                        P("Best for performance", cls="text-sm text-gray-600"),
                        data_scroll=(slow_count.add(1), dict(throttle=250)),
                        id="throttle-250",
                        cls="p-6 bg-white border border-gray-200 rounded",
                    ),
                    cls="grid grid-cols-1 md:grid-cols-3 gap-4",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # === 4. PARALLAX EFFECT ===
            Div(
                H3("Parallax Effect", cls="text-2xl font-bold text-black mb-6"),
                P("Elements that move at different speeds based on scroll:", cls="text-gray-600 mb-4"),
                # Smooth parallax with optimized performance
                Style("""
                    .parallax-smooth {
                        will-change: transform;
                        transform: translateZ(0); /* Enable GPU acceleration */
                        backface-visibility: hidden; /* Prevent flickering */
                        perspective: 1000px; /* Improve 3D acceleration */
                    }
                    .parallax-container {
                        overflow: hidden; /* Hide elements that move outside container */
                        position: relative;
                    }
                """),
                # Add container with overflow hidden to prevent overlap
                Div(
                    Div(
                        H3("Slow Parallax (0.8x speed)", cls="font-medium text-white relative z-10"),
                        P("Moves slower than scroll", cls="text-white/80"),
                        P(
                            "Y Offset: ",
                            # Pythonic: String concatenation with round to 1 decimal
                            Span(data_text=parallax1.round(1) + "px"),
                            # JS equivalent: `${Math.round($parallax1 * 10) / 10}px`
                            cls="text-sm text-white/70",
                        ),
                        # Slow parallax: moves slower than scroll (factor of 0.2)
                        # Variables from scroll handler need $ prefix in expressions
                        data_scroll=(
                            parallax1.set(
                                js(
                                    "$scroll_visible ? Math.max(-100, Math.min(100, ($scroll_y - $scroll_element_top + 300) * -0.2)) : $parallax1"
                                )
                            ),
                            dict(smooth=True),
                        ),
                        data_style_transform="translateY(" + parallax1 + "px)",  # Python concat → JS template literal
                        id="parallax-box-1",
                        cls="parallax-smooth p-6 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg mb-8 shadow-lg",
                        style="min-height: 120px;",
                    ),
                    Div(
                        H3("Normal Parallax (1.0x speed)", cls="font-medium text-white relative z-10"),
                        P("Moves with normal scroll", cls="text-white/80"),
                        P(
                            "Y Offset: ",
                            # Pythonic: String concatenation with round to 1 decimal
                            Span(data_text=parallax2.round(1) + "px"),
                            # JS equivalent: `${Math.round($parallax2 * 10) / 10}px`
                            cls="text-sm text-white/70",
                        ),
                        # No parallax effect - stays at base position
                        data_scroll=(parallax2.set(0), dict(smooth=True)),
                        data_style_transform="translateY(" + parallax2 + "px)",  # Python concat → JS template literal
                        id="parallax-box-2",
                        cls="parallax-smooth p-6 bg-gradient-to-r from-green-600 to-blue-600 rounded-lg mb-8 shadow-lg",
                        style="min-height: 120px;",
                    ),
                    Div(
                        H3("Fast Parallax (1.2x speed)", cls="font-medium text-white relative z-10"),
                        P("Moves faster than scroll", cls="text-white/80"),
                        P(
                            "Y Offset: ",
                            # Pythonic: String concatenation with round to 1 decimal
                            Span(data_text=parallax3.round(1) + "px"),
                            # JS equivalent: `${Math.round($parallax3 * 10) / 10}px`
                            cls="text-sm text-white/70",
                        ),
                        # Fast parallax: moves faster than scroll (factor of 0.2 in same direction)
                        data_scroll=(
                            parallax3.set(
                                js(
                                    "$scroll_visible ? Math.max(-100, Math.min(100, ($scroll_y - $scroll_element_top + 300) * 0.2)) : $parallax3"
                                )
                            ),
                            dict(smooth=True),
                        ),
                        data_style_transform="translateY(" + parallax3 + "px)",  # Python concat → JS template literal
                        id="parallax-box-3",
                        cls="parallax-smooth p-6 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg mb-8 shadow-lg",
                        style="min-height: 120px;",
                    ),
                    cls="parallax-container space-y-8 mb-12 relative min-h-[800px] pt-32 pb-32",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # === 5. SCROLL-TRIGGERED ANIMATIONS ===
            Div(
                H3("Scroll-triggered Animations", cls="text-2xl font-bold text-black mb-6"),
                P("Elements that animate when they come into view:", cls="text-gray-600 mb-4"),
                Div(
                    Div(
                        H3("Fade In Animation", cls="font-medium mb-2"),
                        P("This box fades in when you scroll to it."),
                        data_scroll=fade_visible.set(scroll.visible),
                        data_style_opacity=fade_visible.if_("1", "0"),
                        data_style_transform=fade_visible.if_("translateY(0)", "translateY(20px)"),
                        cls="p-6 bg-orange-100 border border-orange-300 rounded transition-all duration-500",
                    ),
                    # Reduced spacer
                    Div(cls="h-32"),
                    Div(
                        H3("Scale In Animation", cls="font-medium mb-2"),
                        P("This box scales in when visible."),
                        data_scroll=scale_visible.set(scroll.visible),
                        data_style_opacity=scale_visible.if_("1", "0"),
                        data_style_transform=scale_visible.if_("scale(1)", "scale(0.8)"),
                        cls="p-6 bg-teal-100 border border-teal-300 rounded transition-all duration-500",
                    ),
                    # Reduced spacer
                    Div(cls="h-32"),
                    Div(
                        H3("Slide In Animation", cls="font-medium mb-2"),
                        P("This box slides in from the side."),
                        data_scroll=slide_visible.set(scroll.visible),
                        data_style_opacity=slide_visible.if_("1", "0"),
                        data_style_transform=slide_visible.if_("translateX(0)", "translateX(-100px)"),
                        cls="p-6 bg-pink-100 border border-pink-300 rounded transition-all duration-500",
                    ),
                    cls="space-y-32 mb-8",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # === 6. PERFORMANCE INFORMATION ===
            Div(
                H3("How Scroll Handling Works", cls="text-2xl font-bold text-black mb-6"),
                Div(
                    Div(
                        H4("Performance Optimizations", cls="text-lg font-bold text-black mb-4"),
                        Ul(
                            Li("RequestAnimationFrame throttling for smooth 60fps updates", cls="text-gray-600"),
                            Li("Configurable throttling with 100ms default", cls="text-gray-600"),
                            Li("Passive event listeners prevent scroll jank", cls="text-gray-600"),
                            Li("WeakMap storage for automatic memory cleanup", cls="text-gray-600"),
                            Li("50ms velocity decay for responsive detection", cls="text-gray-600"),
                            Li("Optional smooth interpolation with lerp", cls="text-gray-600"),
                            cls="space-y-2 list-disc list-inside",
                        ),
                    ),
                    Div(
                        H4("Available Signals", cls="text-lg font-bold text-black mb-4"),
                        Ul(
                            Li(
                                Code("scroll.x", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Horizontal scroll position",
                            ),
                            Li(
                                Code("scroll.y", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Vertical scroll position",
                            ),
                            Li(
                                Code("scroll.direction", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - 'up', 'down', or 'none'",
                            ),
                            Li(
                                Code("scroll.velocity", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Scroll speed in px/s",
                            ),
                            Li(
                                Code("scroll.page_progress", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Page scroll % (0-100)",
                            ),
                            Li(
                                Code("scroll.visible", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Element in viewport",
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
        # Fixed scroll direction indicators - Single signal approach for mutual exclusivity
        Div(
            # UP indicator
            Div(
                H4("Scrolling UP", cls="font-bold text-sm text-green-700"),
                P("Scroll up detected", cls="text-xs text-green-600"),
                data_style_opacity=(current_scroll_direction == "up").if_("1", "0"),
                data_style_transform=(current_scroll_direction == "up").if_("translateY(0)", "translateY(-20px)"),
                cls="p-3 bg-green-100 border-2 border-green-300 rounded shadow-lg mb-3 transition-all duration-300",
            ),
            # DOWN indicator
            Div(
                H4("Scrolling DOWN", cls="font-bold text-sm text-red-700"),
                P("Scroll down detected", cls="text-xs text-red-600"),
                data_style_opacity=(current_scroll_direction == "down").if_("1", "0"),
                data_style_transform=(current_scroll_direction == "down").if_("translateY(0)", "translateY(20px)"),
                cls="p-3 bg-red-100 border-2 border-red-300 rounded shadow-lg transition-all duration-300",
            ),
            # Only update direction when actively scrolling (keep last direction when stopped)
            # Pythonic: Use .then() for conditional execution
            data_scroll=(scroll.direction != "none").then(current_scroll_direction.set(scroll.direction)),
            # JS equivalent: data_scroll=js("if ($direction !== 'none') { $current_scroll_direction = $direction; }"),
            cls="fixed top-20 right-6 w-48 z-50",
        ),
        cls="min-h-screen bg-white",
    )


if __name__ == "__main__":
    print("Scroll Handler Demo running on http://localhost:5001")
    serve(port=5001)
