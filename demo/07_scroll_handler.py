"""Comprehensive demo showcasing the scroll handler capabilities."""

from starhtml import *

app, rt = star_app(
    title="Scroll Handler Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        scroll_handler(),
    ],
)


@rt("/")
def home():
    return Div(
        # Page Header
        Header(
            H1("📜 Scroll Handler Demo", cls="text-3xl font-bold mb-2"),
            P(
                "Demonstrating data-on-scroll functionality with optimized scroll detection",
                cls="text-muted-foreground",
            ),
            cls="text-center py-8 border-b bg-background sticky top-0 z-10",
        ),
        # Main Content
        Main(
            # Basic Scroll Detection
            Section(
                H2("Basic Scroll Detection", cls="text-2xl font-semibold mb-4"),
                P("Scroll down to see real-time scroll position updates:", cls="mb-4 text-muted-foreground"),
                Div(
                    H3("Scroll Monitor", cls="font-medium mb-4 text-blue-800"),
                    Div(
                        P(
                            "Scroll Position: ",
                            Span(ds_text("$scroll_pos"), cls="font-bold text-blue-600"),
                            " px",
                            cls="text-lg",
                        ),
                        P(
                            "Direction: ",
                            Span(
                                ds_text("$scroll_dir"),
                                ds_class(
                                    **{
                                        "$scroll_dir === 'up' ? 'text-green-600' : $scroll_dir === 'down' ? 'text-red-600' : 'text-gray-600'": True
                                    }
                                ),
                                cls="font-bold",
                            ),
                            cls="text-lg",
                        ),
                        P(
                            "Velocity: ",
                            Span(ds_text("$scroll_vel"), cls="font-bold text-purple-600"),
                            "px/scroll",
                            cls="text-lg",
                        ),
                        cls="space-y-2",
                    ),
                    # Safe assignment with fallbacks
                    ds_on_scroll("""
                        $scroll_pos = scrollY || 0;
                        $scroll_dir = direction || 'none';
                        $scroll_vel = velocity || 0;
                    """),
                    ds_signals(scroll_pos=0, scroll_dir="none", scroll_vel=0),
                    cls="p-6 bg-white border-2 border-blue-300 rounded-lg shadow-lg sticky top-24 z-5 mb-8",
                ),
                cls="mb-12",
            ),
            # Hide/Show on Scroll Direction
            Section(
                H2("Hide/Show Based on Scroll Direction", cls="text-2xl font-semibold mb-4"),
                P(
                    "Fixed indicators that respond to scroll direction (like the comparison demo):",
                    cls="mb-4 text-muted-foreground",
                ),
                P(
                    "💡 Scroll up and down to see the indicators change on the right side!",
                    cls="text-center text-gray-600 text-lg mb-8",
                ),
                cls="mb-8",
            ),
            # Scroll Progress Indicator
            Section(
                H2("Scroll Progress Indicator", cls="text-2xl font-semibold mb-4"),
                P("A progress bar that fills as you scroll:", cls="mb-4 text-muted-foreground"),
                Div(
                    Div(
                        H3("Scroll Progress", cls="font-medium mb-2"),
                        Div(
                            Div(
                                ds_style(width="$page_progress + '%'"),
                                id="progress-fill",
                                cls="h-3 bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-150 rounded-full",
                            ),
                            cls="w-full h-3 bg-gray-200 rounded-full overflow-hidden",
                        ),
                        P(
                            "Page Progress: ",
                            Span(ds_text("$page_progress"), cls="font-bold text-purple-600"),
                            "%",
                            cls="text-sm mt-2",
                        ),
                        # Use proper JavaScript expressions
                        ds_on_scroll("$page_progress = pageProgress || 0;"),
                        ds_signals(page_progress=0),
                        cls="p-6 bg-white border-2 border-purple-200 rounded-lg shadow-md sticky top-24 z-5",
                    ),
                    cls="mb-8",
                ),
                cls="mb-12",
            ),
            # Throttling Demo
            Section(
                H2("Throttling Configuration", cls="text-2xl font-semibold mb-4"),
                P("Different throttle settings for performance optimization:", cls="mb-4 text-muted-foreground"),
                Div(
                    Div(
                        H3("High Frequency (25ms)", cls="font-bold text-red-700 mb-2"),
                        P(
                            "Updates: ",
                            Span(ds_text("$fast_count"), cls="text-2xl font-bold text-red-600"),
                            cls="font-mono text-lg",
                        ),
                        P("Very responsive, updates frequently", cls="text-sm text-gray-600 mt-2"),
                        ds_on_scroll("$fast_count++;", throttle="25"),
                        ds_signals(fast_count=0),
                        cls="p-6 bg-red-50 border-2 border-red-300 rounded-lg shadow-md transform transition-transform hover:scale-105",
                    ),
                    Div(
                        H3("Medium Frequency (100ms)", cls="font-bold text-yellow-700 mb-2"),
                        P(
                            "Updates: ",
                            Span(ds_text("$medium_count"), cls="text-2xl font-bold text-yellow-600"),
                            cls="font-mono text-lg",
                        ),
                        P("Balanced performance", cls="text-sm text-gray-600 mt-2"),
                        ds_on_scroll("$medium_count++;", throttle="100"),
                        ds_signals(medium_count=0),
                        cls="p-6 bg-yellow-50 border-2 border-yellow-300 rounded-lg shadow-md transform transition-transform hover:scale-105",
                    ),
                    Div(
                        H3("Low Frequency (250ms)", cls="font-bold text-blue-700 mb-2"),
                        P(
                            "Updates: ",
                            Span(ds_text("$slow_count"), cls="text-2xl font-bold text-blue-600"),
                            cls="font-mono text-lg",
                        ),
                        P("Best for performance", cls="text-sm text-gray-600 mt-2"),
                        ds_on_scroll("$slow_count++;", throttle="250"),
                        ds_signals(slow_count=0),
                        cls="p-6 bg-blue-50 border-2 border-blue-300 rounded-lg shadow-md transform transition-transform hover:scale-105",
                    ),
                    cls="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 sticky top-96 z-4 bg-white p-4 rounded-lg shadow-lg",
                ),
                cls="mb-12",
            ),
            # Parallax Effect Demo
            Section(
                H2("Parallax Effect", cls="text-2xl font-semibold mb-4"),
                P("Elements that move at different speeds based on scroll:", cls="mb-4 text-muted-foreground"),
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
                        P("Y Offset: ", Span(ds_text("$parallax1_display")), "px", cls="text-sm text-white/70"),
                        # Smooth parallax using the scroll handler's smooth modifier
                        ds_on_scroll(
                            "$parallax1 = visible ? Math.max(-100, Math.min(100, (scrollY - elementTop + 300) * -0.2)) : $parallax1; $parallax1_display = Math.round($parallax1 * 10) / 10;",
                            "smooth",
                        ),
                        ds_style(transform="'translateY(' + $parallax1 + 'px)'"),
                        ds_signals(parallax1=0, parallax1_display=0),
                        id="parallax-box-1",
                        cls="parallax-smooth p-6 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg mb-8 shadow-lg",
                        style="min-height: 120px;",
                    ),
                    Div(
                        H3("Normal Parallax (1.0x speed)", cls="font-medium text-white relative z-10"),
                        P("Moves with normal scroll", cls="text-white/80"),
                        P("Y Offset: ", Span(ds_text("$parallax2_display")), "px", cls="text-sm text-white/70"),
                        # No parallax effect - stays at base position
                        ds_on_scroll("$parallax2 = 0; $parallax2_display = 0;", "smooth"),
                        ds_style(transform="'translateY(' + $parallax2 + 'px)'"),
                        ds_signals(parallax2=0, parallax2_display=0),
                        id="parallax-box-2",
                        cls="parallax-smooth p-6 bg-gradient-to-r from-green-600 to-blue-600 rounded-lg mb-8 shadow-lg",
                        style="min-height: 120px;",
                    ),
                    Div(
                        H3("Fast Parallax (1.2x speed)", cls="font-medium text-white relative z-10"),
                        P("Moves faster than scroll", cls="text-white/80"),
                        P("Y Offset: ", Span(ds_text("$parallax3_display")), "px", cls="text-sm text-white/70"),
                        # Smooth parallax using the scroll handler's smooth modifier
                        ds_on_scroll(
                            "$parallax3 = visible ? Math.max(-100, Math.min(100, (scrollY - elementTop + 300) * 0.2)) : $parallax3; $parallax3_display = Math.round($parallax3 * 10) / 10;",
                            "smooth",
                        ),
                        ds_style(transform="'translateY(' + $parallax3 + 'px)'"),
                        ds_signals(parallax3=0, parallax3_display=0),
                        id="parallax-box-3",
                        cls="parallax-smooth p-6 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg mb-8 shadow-lg",
                        style="min-height: 120px;",
                    ),
                    cls="parallax-container space-y-8 mb-12 relative min-h-[800px] pt-32 pb-32",
                ),
                cls="mb-12",
            ),
            # Scroll-triggered Animations
            Section(
                H2("Scroll-triggered Animations", cls="text-2xl font-semibold mb-4"),
                P("Elements that animate when they come into view:", cls="mb-4 text-muted-foreground"),
                Div(
                    Div(
                        H3("Fade In Animation", cls="font-medium mb-2"),
                        P("This box fades in when you scroll to it."),
                        ds_on_scroll("$fade_visible = visible;"),
                        ds_signals(fade_visible=False),
                        ds_style(
                            opacity="$fade_visible ? '1' : '0'",
                            transform="$fade_visible ? 'translateY(0)' : 'translateY(20px)'",
                        ),
                        cls="p-6 bg-orange-100 border border-orange-300 rounded transition-all duration-500",
                    ),
                    # Reduced spacer
                    Div(cls="h-32"),
                    Div(
                        H3("Scale In Animation", cls="font-medium mb-2"),
                        P("This box scales in when visible."),
                        ds_on_scroll("$scale_visible = visible;"),
                        ds_signals(scale_visible=False),
                        ds_style(
                            opacity="$scale_visible ? '1' : '0'", transform="$scale_visible ? 'scale(1)' : 'scale(0.8)'"
                        ),
                        cls="p-6 bg-teal-100 border border-teal-300 rounded transition-all duration-500",
                    ),
                    # Reduced spacer
                    Div(cls="h-32"),
                    Div(
                        H3("Slide In Animation", cls="font-medium mb-2"),
                        P("This box slides in from the side."),
                        ds_on_scroll("$slide_visible = visible;"),
                        ds_signals(slide_visible=False),
                        ds_style(
                            opacity="$slide_visible ? '1' : '0'",
                            transform="$slide_visible ? 'translateX(0)' : 'translateX(-100px)'",
                        ),
                        cls="p-6 bg-pink-100 border border-pink-300 rounded transition-all duration-500",
                    ),
                    cls="space-y-32 mb-8",
                ),
                cls="mb-12",
            ),
            # Performance Information
            Section(
                H2("Performance Information", cls="text-2xl font-semibold mb-4"),
                Div(
                    Div(
                        H3("🚀 Optimizations", cls="font-medium mb-2"),
                        Ul(
                            Li("RequestAnimationFrame debouncing for smooth scrolling"),
                            Li("Passive event listeners for better performance"),
                            Li("WeakMap for memory-efficient element tracking"),
                            Li("Automatic cleanup of disconnected elements"),
                            Li("Configurable throttling (default: 100ms)"),
                            Li("Direction detection with velocity calculation"),
                            cls="text-sm space-y-1 list-disc list-inside",
                        ),
                        cls="p-4 bg-green-50 border border-green-200 rounded",
                    ),
                    Div(
                        H3("📊 Usage Patterns", cls="font-medium mb-2"),
                        Ul(
                            Li('ds_on_scroll("$signal = value") - Default 100ms throttle'),
                            Li('ds_on_scroll("$signal++", throttle="50") - Custom throttle'),
                            Li("Available context: direction, scrollY, velocity, visible, progress, etc."),
                            Li("Direction: 'up', 'down', or 'none'"),
                            Li("Use ds_signals() for reactive state"),
                            Li("Use ds_style() for dynamic styling"),
                            Li("Avoid complex JavaScript - use context variables"),
                            Li("Works with dynamically added elements"),
                            Li("Automatic initial execution on page load"),
                            cls="text-sm space-y-1 list-disc list-inside",
                        ),
                        cls="p-4 bg-blue-50 border border-blue-200 rounded",
                    ),
                    cls="grid grid-cols-1 md:grid-cols-2 gap-6",
                ),
                cls="mb-12",
            ),
            cls="container mx-auto px-4 py-8 max-w-6xl",
        ),
        # Fixed scroll direction indicators - Single signal approach for mutual exclusivity
        Div(
            # UP indicator
            Div(
                H4("Scrolling UP", cls="font-bold text-sm text-green-700"),
                P("Scroll up detected", cls="text-xs text-green-600"),
                ds_style(
                    opacity="$current_scroll_direction === 'up' ? '1' : '0'",
                    transform="$current_scroll_direction === 'up' ? 'translateY(0)' : 'translateY(-20px)'",
                ),
                cls="p-3 bg-green-100 border-2 border-green-300 rounded shadow-lg mb-3 transition-all duration-300",
            ),
            # DOWN indicator
            Div(
                H4("Scrolling DOWN", cls="font-bold text-sm text-red-700"),
                P("Scroll down detected", cls="text-xs text-red-600"),
                ds_style(
                    opacity="$current_scroll_direction === 'down' ? '1' : '0'",
                    transform="$current_scroll_direction === 'down' ? 'translateY(0)' : 'translateY(20px)'",
                ),
                cls="p-3 bg-red-100 border-2 border-red-300 rounded shadow-lg transition-all duration-300",
            ),
            # Only update direction when actively scrolling (ignore 'none')
            ds_on_scroll("if (direction !== 'none') { $current_scroll_direction = direction; }"),
            ds_signals(current_scroll_direction="down"),  # Start with DOWN
            cls="fixed top-20 right-6 w-48 z-50",
        ),
        # Footer
        Footer(
            P(
                "Scroll Handler Demo - Powered by StarHTML Scroll Detection",
                cls="text-center text-sm text-muted-foreground py-8",
            ),
            cls="border-t",
        ),
        cls="min-h-screen bg-background text-foreground",
    )


if __name__ == "__main__":
    print("Scroll Handler Demo running on http://localhost:5001")
    serve(port=5001)
