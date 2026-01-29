"""Demo: motion-svg plugin for declarative SVG attribute animation.

The motion-svg plugin provides smooth, reactive animations for SVG attributes
that CSS can't animate (height, width, x, y, cx, cy, r, etc.).

Unlike CSS transforms which only animate visual transforms, motion-svg
animates the actual SVG attribute values, making it perfect for:
- Data visualization (bar charts, line charts, gauges)
- Interactive diagrams
- Progress indicators

Uses Datastar computed signals for derived values - the expression evaluation
happens in Datastar, not in the plugin.
"""

from starhtml import *
from starhtml.plugins import motion_svg, track

app, rt = star_app(
    title="Motion SVG Plugin Demo",
    htmlkw={"lang": "en"},
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body { background: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; -webkit-font-smoothing: antialiased; }
        """),
    ],
)

app.register(motion_svg)


# Path morphing shapes - defined outside to avoid rendering as text
CIRCLE_PATH = "M100,50 C127.6,50 150,72.4 150,100 C150,127.6 127.6,150 100,150 C72.4,150 50,127.6 50,100 C50,72.4 72.4,50 100,50 Z"
SQUARE_PATH = "M60,60 L140,60 L140,140 L60,140 Z"
TRIANGLE_PATH = "M100,45 L150,140 L50,140 Z"
STAR_PATH = "M100,30 L112,72 L156,72 L120,100 L132,142 L100,115 L68,142 L80,100 L44,72 L88,72 Z"


def path_morphing_section():
    """Section 9: Path Morphing with Flubber.

    This is extracted to a function because we need to set the initial
    path signal value directly (not via array indexing expression).
    """
    # Define signals
    current_shape = Signal("current_shape", CIRCLE_PATH)
    morph_duration = Signal("morph_duration", 600)

    return Div(
        H3("Path Morphing", cls="text-2xl font-bold text-black mb-6"),
        P(
            "Morph between arbitrary SVG shapes using Flubber for smooth interpolation. "
            "Click the buttons to morph between different shapes.",
            cls="text-gray-600 mb-6",
        ),
        # Include signals
        current_shape,
        morph_duration,
        # Duration slider
        Div(
            Label("Duration: ", cls="font-medium"),
            Span(data_text=morph_duration, cls="font-mono font-bold w-16 inline-block"),
            Span("ms", cls="font-mono"),
            Input(
                type="range",
                min="100",
                max="2000",
                step="100",
                data_bind=morph_duration,
                cls="w-64 ml-4 accent-indigo-500",
            ),
            cls="mb-6 flex items-center",
        ),
        # Shape buttons
        Div(
            Button(
                "Circle",
                data_on_click=current_shape.set(CIRCLE_PATH),
                cls="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors",
            ),
            Button(
                "Square",
                data_on_click=current_shape.set(SQUARE_PATH),
                cls="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition-colors",
            ),
            Button(
                "Triangle",
                data_on_click=current_shape.set(TRIANGLE_PATH),
                cls="px-4 py-2 bg-amber-500 text-white rounded hover:bg-amber-600 transition-colors",
            ),
            Button(
                "Star",
                data_on_click=current_shape.set(STAR_PATH),
                cls="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 transition-colors",
            ),
            cls="flex gap-4 mb-6",
        ),
        Svg(
            # The morphing path - duration is reactive via signal
            SvgPath(
                d=CIRCLE_PATH,
                fill="#6366f1",
                data_motion_svg=track(d=current_shape, duration=morph_duration, ease="ease-in-out"),
            ),
            viewBox="0 0 200 200",
            cls="w-48 h-48",
        ),
        P(
            "The Flubber library handles point normalization and alignment automatically, "
            "creating smooth transitions even between shapes with different point counts.",
            cls="text-sm text-gray-500 mt-4",
        ),
        cls="mb-12 p-8 bg-white border border-gray-200",
    )


@rt("/")
def home():
    return Div(
        Div(
            # Header
            Div(
                H1("24", cls="text-8xl font-black text-gray-100 leading-none"),
                H1("Motion SVG Plugin", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
                P(
                    "Smooth, reactive SVG attribute animations with Datastar signals",
                    cls="text-lg text-gray-600 mt-4",
                ),
                cls="mb-16",
            ),
            # Section 1: Simple Bar Chart
            Div(
                H3("Interactive Bar Chart", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "Move the slider to animate bar heights with spring physics. "
                    "The motion-svg plugin animates actual SVG attributes (height, y), not CSS transforms.",
                    cls="text-gray-600 mb-6",
                ),
                # Base signal - user controls this
                (value := Signal("value", 0.6)),
                # Computed signals for each bar's derived values
                # Bar A: height = value * 100, y = 120 - value * 100
                (bar_a_height := Signal("bar_a_height", value * 100)),
                (bar_a_y := Signal("bar_a_y", 120 - value * 100)),
                # Bar B: height = value * 80, y = 120 - value * 80
                (bar_b_height := Signal("bar_b_height", value * 80)),
                (bar_b_y := Signal("bar_b_y", 120 - value * 80)),
                # Bar C: height = value * 90, y = 120 - value * 90
                (bar_c_height := Signal("bar_c_height", value * 90)),
                (bar_c_y := Signal("bar_c_y", 120 - value * 90)),
                # Bar D: height = value * 60, y = 120 - value * 60
                (bar_d_height := Signal("bar_d_height", value * 60)),
                (bar_d_y := Signal("bar_d_y", 120 - value * 60)),
                Div(
                    Label("Value: ", cls="font-medium"),
                    Span(data_text=value, cls="font-mono font-bold w-16 inline-block"),
                    Input(
                        type="range",
                        min="0.1",
                        max="1",
                        step="0.05",
                        data_bind=value,
                        cls="w-64 ml-4 accent-blue-500",
                    ),
                    cls="mb-6 flex items-center",
                ),
                Svg(
                    # Background
                    Rect(width="280", height="140", fill="#f3f4f6", rx="8"),
                    # Animated bars - pass Signal objects directly to track()
                    Rect(
                        width="40",
                        height="50",
                        x="30",
                        y="70",
                        fill="#3b82f6",
                        rx="4",
                        data_motion_svg=track(height=bar_a_height, y=bar_a_y, spring="gentle"),
                    ),
                    Rect(
                        width="40",
                        height="40",
                        x="90",
                        y="80",
                        fill="#22c55e",
                        rx="4",
                        data_motion_svg=track(height=bar_b_height, y=bar_b_y, spring="gentle"),
                    ),
                    Rect(
                        width="40",
                        height="70",
                        x="150",
                        y="50",
                        fill="#f59e0b",
                        rx="4",
                        data_motion_svg=track(height=bar_c_height, y=bar_c_y, spring="bouncy"),
                    ),
                    Rect(
                        width="40",
                        height="30",
                        x="210",
                        y="90",
                        fill="#ec4899",
                        rx="4",
                        data_motion_svg=track(height=bar_d_height, y=bar_d_y, spring="gentle"),
                    ),
                    # Labels
                    Text("A", x="50", y="135", text_anchor="middle", cls="text-xs fill-gray-500"),
                    Text("B", x="110", y="135", text_anchor="middle", cls="text-xs fill-gray-500"),
                    Text("C", x="170", y="135", text_anchor="middle", cls="text-xs fill-gray-500"),
                    Text("D", x="230", y="135", text_anchor="middle", cls="text-xs fill-gray-500"),
                    viewBox="0 0 280 145",
                    cls="w-full max-w-md",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # Section 2: Circular Gauge
            Div(
                H3("Animated Gauge", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "The circle radius animates smoothly as you change the value. "
                    "Uses the 'bouncy' spring preset for playful overshoot.",
                    cls="text-gray-600 mb-6",
                ),
                (gauge := Signal("gauge", 50)),
                # Computed signal: radius = gauge * 0.8
                (gauge_radius := Signal("gauge_radius", gauge * 0.8)),
                Div(
                    Label("Gauge: ", cls="font-medium"),
                    Span(data_text=gauge, cls="font-mono font-bold w-16 inline-block"),
                    Input(
                        type="range",
                        min="10",
                        max="100",
                        step="5",
                        data_bind=gauge,
                        cls="w-64 ml-4 accent-purple-500",
                    ),
                    cls="mb-6 flex items-center",
                ),
                Svg(
                    # Outer ring
                    Circle(cx="100", cy="100", r="90", fill="none", stroke="#e5e7eb", stroke_width="4"),
                    # Animated inner circle
                    Circle(
                        cx="100",
                        cy="100",
                        r="40",
                        fill="#8b5cf6",
                        data_motion_svg=track(r=gauge_radius, spring="bouncy", duration=400),
                    ),
                    # Center value display
                    Text(
                        data_text=gauge,
                        x="100",
                        y="108",
                        text_anchor="middle",
                        cls="text-2xl font-bold fill-white",
                    ),
                    viewBox="0 0 200 200",
                    cls="w-48 h-48",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # Section 3: Position Animation
            Div(
                H3("Position Animation", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "Animate both x and y positions with computed signals. "
                    "The circle follows a diagonal path across the grid.",
                    cls="text-gray-600 mb-6",
                ),
                (pos := Signal("pos", 50)),
                # Computed signals: cx = 20 + pos * 1.6, cy = 180 - pos * 1.6
                (circle_cx := Signal("circle_cx", 20 + pos * 1.6)),
                (circle_cy := Signal("circle_cy", 180 - pos * 1.6)),
                Div(
                    Label("Position: ", cls="font-medium"),
                    Span(data_text=pos, cls="font-mono font-bold w-16 inline-block"),
                    Input(
                        type="range",
                        min="0",
                        max="100",
                        step="5",
                        data_bind=pos,
                        cls="w-64 ml-4 accent-rose-500",
                    ),
                    cls="mb-6 flex items-center",
                ),
                Svg(
                    # Background grid
                    *[Line(x1="0", y1=str(i * 40), x2="200", y2=str(i * 40), stroke="#e5e7eb") for i in range(6)],
                    *[Line(x1=str(i * 40), y1="0", x2=str(i * 40), y2="200", stroke="#e5e7eb") for i in range(6)],
                    # Animated circle following diagonal
                    Circle(
                        cx="20",
                        cy="180",
                        r="15",
                        fill="#f43f5e",
                        data_motion_svg=track(cx=circle_cx, cy=circle_cy, ease="ease-out", duration=200),
                    ),
                    viewBox="0 0 200 200",
                    cls="w-48 h-48 border rounded",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # Section 4: Stroke Animation
            Div(
                H3("Stroke Animation", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "Animate stroke-width with signal values. The line thickness changes based on the signal value.",
                    cls="text-gray-600 mb-6",
                ),
                (stroke := Signal("stroke", 3)),
                # Computed signal: thicker stroke = stroke * 1.5
                (stroke_thick := Signal("stroke_thick", stroke * 1.5)),
                Div(
                    Label("Stroke Width: ", cls="font-medium"),
                    Span(data_text=stroke, cls="font-mono font-bold w-16 inline-block"),
                    Input(
                        type="range",
                        min="1",
                        max="10",
                        step="1",
                        data_bind=stroke,
                        cls="w-64 ml-4 accent-teal-500",
                    ),
                    cls="mb-6 flex items-center",
                ),
                Svg(
                    # Animated stroke width on a path
                    Circle(
                        cx="100",
                        cy="100",
                        r="70",
                        fill="none",
                        stroke="#14b8a6",
                        stroke_width="3",
                        data_motion_svg=track(stroke_width=stroke, spring="gentle"),
                    ),
                    Line(
                        x1="30",
                        y1="100",
                        x2="170",
                        y2="100",
                        stroke="#0d9488",
                        stroke_width="3",
                        data_motion_svg=track(stroke_width=stroke_thick, spring="gentle"),
                    ),
                    viewBox="0 0 200 200",
                    cls="w-48 h-48",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # Section 5: Path Drawing Animation
            Div(
                H3("Path Drawing Animation", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "Animate stroke-dashoffset for progressive path drawing effects. "
                    "Great for line drawing animations and progress indicators.",
                    cls="text-gray-600 mb-6",
                ),
                (draw := Signal("draw", 0)),
                # Path length is 283 (circumference of r=45 circle: 2 * pi * 45)
                # dashoffset = 283 - (draw / 100 * 283) = 283 * (1 - draw/100)
                (dash_offset := Signal("dash_offset", 283 - draw * 2.83)),
                Div(
                    Label("Draw Progress: ", cls="font-medium"),
                    Span(data_text=draw, cls="font-mono font-bold w-16 inline-block"),
                    Span("%", cls="font-mono"),
                    Input(
                        type="range",
                        min="0",
                        max="100",
                        step="1",
                        data_bind=draw,
                        cls="w-64 ml-4 accent-indigo-500",
                    ),
                    cls="mb-6 flex items-center",
                ),
                Svg(
                    # Background circle
                    Circle(
                        cx="100",
                        cy="100",
                        r="45",
                        fill="none",
                        stroke="#e5e7eb",
                        stroke_width="8",
                    ),
                    # Animated drawing circle
                    Circle(
                        cx="100",
                        cy="100",
                        r="45",
                        fill="none",
                        stroke="#6366f1",
                        stroke_width="8",
                        stroke_linecap="round",
                        stroke_dasharray="283",
                        stroke_dashoffset="283",
                        transform="rotate(-90 100 100)",
                        data_motion_svg=track(stroke_dashoffset=dash_offset, spring="gentle"),
                    ),
                    # Percentage text
                    Text(
                        data_text=draw,
                        x="100",
                        y="105",
                        text_anchor="middle",
                        cls="text-2xl font-bold fill-indigo-600",
                    ),
                    Text("%", x="100", y="125", text_anchor="middle", cls="text-sm fill-gray-400"),
                    viewBox="0 0 200 200",
                    cls="w-48 h-48",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # Section 6: Transform Animations
            Div(
                H3("Transform Animations", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "Animate rotation, scale, and translation transforms. "
                    "These are applied via the SVG transform attribute.",
                    cls="text-gray-600 mb-6",
                ),
                (transform := Signal("transform", 0)),
                # Computed signals for transforms
                (rotation := Signal("rotation", transform * 3.6)),  # 0-360 degrees
                (scale_val := Signal("scale_val", 0.5 + transform * 0.01)),  # 0.5-1.5
                (translate_x := Signal("translate_x", transform * 0.5)),  # 0-50
                Div(
                    Label("Transform: ", cls="font-medium"),
                    Span(data_text=transform, cls="font-mono font-bold w-16 inline-block"),
                    Input(
                        type="range",
                        min="0",
                        max="100",
                        step="1",
                        data_bind=transform,
                        cls="w-64 ml-4 accent-amber-500",
                    ),
                    cls="mb-6 flex items-center",
                ),
                Div(
                    # Rotation
                    Div(
                        Span("Rotate", cls="text-sm text-gray-500 block mb-2"),
                        Svg(
                            Rect(
                                x="75",
                                y="75",
                                width="50",
                                height="50",
                                fill="#f59e0b",
                                rx="4",
                                transform="rotate(0 100 100)",
                                data_motion_svg=track(rotate=rotation, spring="bouncy"),
                            ),
                            viewBox="0 0 200 200",
                            cls="w-24 h-24",
                        ),
                        cls="text-center",
                    ),
                    # Scale
                    Div(
                        Span("Scale", cls="text-sm text-gray-500 block mb-2"),
                        Svg(
                            Rect(
                                x="75",
                                y="75",
                                width="50",
                                height="50",
                                fill="#10b981",
                                rx="4",
                                transform="scale(1)",
                                data_motion_svg=track(scale=scale_val, spring="gentle"),
                            ),
                            viewBox="0 0 200 200",
                            cls="w-24 h-24",
                        ),
                        cls="text-center",
                    ),
                    # Translate
                    Div(
                        Span("Translate", cls="text-sm text-gray-500 block mb-2"),
                        Svg(
                            Rect(
                                x="50",
                                y="75",
                                width="50",
                                height="50",
                                fill="#3b82f6",
                                rx="4",
                                transform="translate(0 0)",
                                data_motion_svg=track(translate_x=translate_x, spring="gentle"),
                            ),
                            viewBox="0 0 200 200",
                            cls="w-24 h-24",
                        ),
                        cls="text-center",
                    ),
                    cls="flex gap-8 justify-center",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # Section 7: Filter Effects
            Div(
                H3("Filter Effects Animation", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "Animate SVG filter parameters like blur (stdDeviation). "
                    "Creates smooth transitions for visual effects.",
                    cls="text-gray-600 mb-6",
                ),
                (blur := Signal("blur", 0)),
                # Computed signal for blur amount
                (blur_amount := Signal("blur_amount", blur * 0.1)),
                Div(
                    Label("Blur Amount: ", cls="font-medium"),
                    Span(data_text=blur, cls="font-mono font-bold w-16 inline-block"),
                    Input(
                        type="range",
                        min="0",
                        max="50",
                        step="1",
                        data_bind=blur,
                        cls="w-64 ml-4 accent-violet-500",
                    ),
                    cls="mb-6 flex items-center",
                ),
                Svg(
                    # Define filter
                    Defs(
                        Filter(
                            FeGaussianBlur(
                                id="blur-effect-inner",
                                stdDeviation="0",
                                data_motion_svg=track(std_deviation=blur_amount, spring="gentle"),
                            ),
                            id="blur-effect",
                        ),
                    ),
                    # Background
                    Rect(width="200", height="200", fill="#f3f4f6", rx="8"),
                    # Blurred shape
                    Circle(
                        cx="100",
                        cy="100",
                        r="50",
                        fill="#8b5cf6",
                        filter="url(#blur-effect)",
                    ),
                    viewBox="0 0 200 200",
                    cls="w-48 h-48",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # Section 8: Text Animation
            Div(
                H3("Text Animation", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "Animate text properties like font-size and letter-spacing. "
                    "Great for emphasis effects and dynamic typography.",
                    cls="text-gray-600 mb-6",
                ),
                (text_scale := Signal("text_scale", 50)),
                # Computed signals for text properties
                (font_size := Signal("font_size", 16 + text_scale * 0.32)),  # 16-48
                (letter_space := Signal("letter_space", text_scale * 0.1)),  # 0-5
                Div(
                    Label("Text Scale: ", cls="font-medium"),
                    Span(data_text=text_scale, cls="font-mono font-bold w-16 inline-block"),
                    Input(
                        type="range",
                        min="0",
                        max="100",
                        step="1",
                        data_bind=text_scale,
                        cls="w-64 ml-4 accent-pink-500",
                    ),
                    cls="mb-6 flex items-center",
                ),
                Svg(
                    Text(
                        "Motion",
                        x="100",
                        y="100",
                        text_anchor="middle",
                        dominant_baseline="middle",
                        fill="#ec4899",
                        font_size="24",
                        letter_spacing="0",
                        data_motion_svg=track(font_size=font_size, letter_spacing=letter_space, spring="bouncy"),
                    ),
                    viewBox="0 0 200 200",
                    cls="w-64 h-32",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # Section 9: Path Morphing
            path_morphing_section(),
            # Section 10: API Reference
            Div(
                H3("API Reference", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "The motion-svg plugin uses Datastar signals for attribute animation. "
                    "Use computed signals for derived values:",
                    cls="text-gray-600 mb-6",
                ),
                Div(
                    Div(
                        H4("Syntax", cls="text-lg font-bold text-black mb-4"),
                        Pre(
                            Code(
                                "from starhtml.plugins import track\n\n"
                                "# Define computed signals for derived values\n"
                                '(value := Signal("value", 0.5)),\n'
                                '(bar_height := Signal("bar_height", value * 100)),\n'
                                '(bar_y := Signal("bar_y", 120 - value * 100)),\n\n'
                                "# Pass Signal objects directly to track()\n"
                                "Rect(\n"
                                "    data_motion_svg=track(\n"
                                "        height=bar_height,\n"
                                "        y=bar_y,\n"
                                '        spring="gentle"\n'
                                "    )\n"
                                ")",
                                cls="text-sm",
                            ),
                            cls="p-4 bg-gray-800 text-green-400 rounded overflow-x-auto",
                        ),
                    ),
                    Div(
                        H4("Animatable Properties", cls="text-lg font-bold text-black mb-4"),
                        Ul(
                            Li(
                                Code("height, width, x, y", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Rectangle geometry",
                            ),
                            Li(
                                Code("cx, cy, r, rx, ry", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Circle/ellipse geometry",
                            ),
                            Li(
                                Code("x1, y1, x2, y2", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Line endpoints",
                            ),
                            Li(
                                Code("stroke-width, stroke-dashoffset", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Stroke properties",
                            ),
                            Li(
                                Code(
                                    "rotate, scale, translate-x, translate-y",
                                    cls="text-xs bg-gray-100 px-1 py-0.5 rounded",
                                ),
                                " - Transforms",
                            ),
                            Li(
                                Code(
                                    "opacity, fill-opacity, stroke-opacity",
                                    cls="text-xs bg-gray-100 px-1 py-0.5 rounded",
                                ),
                                " - Opacity",
                            ),
                            Li(
                                Code("font-size, letter-spacing", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Text properties",
                            ),
                            Li(
                                Code("stdDeviation", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Filter effects (blur)",
                            ),
                            Li(
                                Code("d", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Path morphing (via Flubber)",
                            ),
                            cls="text-sm space-y-2 list-disc list-inside text-gray-700",
                        ),
                        H4("Animation Options", cls="text-lg font-bold text-black mb-4 mt-6"),
                        Ul(
                            Li(
                                Code("duration:300", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Animation duration in ms",
                            ),
                            Li(
                                Code("delay:100", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Delay before animation",
                            ),
                            Li(
                                Code(
                                    "spring:gentle|bouncy|tight|slow|snappy",
                                    cls="text-xs bg-gray-100 px-1 py-0.5 rounded",
                                ),
                                " - Spring physics preset",
                            ),
                            Li(
                                Code(
                                    "ease:ease-in|ease-out|ease-in-out", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"
                                ),
                                " - Easing function",
                            ),
                            cls="text-sm space-y-2 list-disc list-inside text-gray-700",
                        ),
                    ),
                    cls="grid grid-cols-1 lg:grid-cols-2 gap-8",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white",
        ),
        cls="min-h-screen bg-white",
    )


if __name__ == "__main__":
    print("Motion SVG Plugin Demo running on http://localhost:5002")
    serve(port=5002)
