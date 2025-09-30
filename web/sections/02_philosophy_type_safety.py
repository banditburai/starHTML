import random
from typing import Any

from starhtml import *
from starhtml.datastar import collect, js, switch, value


def create_header() -> Div:
    return Div(
        H1("Type Safety", cls="text-2xl font-bold text-black mb-2"),
        P(
            "StarHTML's Signals automatically infer types from initial values, enabling IDE support and type-specific operations.",
            cls="text-gray-600 mb-4",
        ),
        Div(
            Span(
                Icon("material-symbols:lightbulb", width="16", height="16", cls="mr-1 text-blue-600"),
                "IDE Support",
                cls="inline-flex items-center text-sm text-gray-700 mr-6",
            ),
            Span(
                Icon("material-symbols:shield", width="16", height="16", cls="mr-1 text-green-600"),
                "Runtime Safety",
                cls="inline-flex items-center text-sm text-gray-700 mr-6",
            ),
            Span(
                Icon("material-symbols:menu-book", width="16", height="16", cls="mr-1 text-purple-600"),
                "Self-Documenting",
                cls="inline-flex items-center text-sm text-gray-700",
            ),
            cls="mb-6 pb-4 border-b border-gray-200",
        ),
    )


def string_demo_code_panel() -> Div:
    return Div(
        Div(
            H4("Signal Declaration & Binding", cls="text-sm font-medium text-gray-700 mb-2"),
            Pre(
                Code(
                    """# Define string signal
message_text = Signal("message_text", "Hello!")

# Bind to textarea
Textarea(data_bind=message_text)""",
                    cls="text-xs text-blue-600",
                ),
                cls="bg-blue-50 p-3 rounded overflow-x-auto mb-4",
            ),
        ),
        Div(
            H4("String Methods Available", cls="text-sm font-medium text-gray-700 mb-2"),
            Div(
                Div(
                    Code(".upper()", cls="text-blue-600 text-xs font-mono bg-blue-50 px-2 py-1 rounded"),
                    " → UPPERCASE TEXT",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".lower()", cls="text-blue-600 text-xs font-mono bg-blue-50 px-2 py-1 rounded"),
                    " → lowercase text",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".length", cls="text-blue-600 text-xs font-mono bg-blue-50 px-2 py-1 rounded"),
                    " → character count",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".contains(s)", cls="text-blue-600 text-xs font-mono bg-blue-50 px-2 py-1 rounded"),
                    " → includes text?",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".split(' ')", cls="text-blue-600 text-xs font-mono bg-blue-50 px-2 py-1 rounded"),
                    " → split to array",
                    cls="mb-1 text-xs",
                ),
            ),
        ),
        cls="p-4 bg-white border border-gray-200",
    )


def string_demo_interactive(message_text: Any, char_limit: Any) -> Div:
    return Div(
        Label("Compose your message:", cls="text-sm font-medium text-gray-700 mb-2 block"),
        Textarea(
            data_bind=message_text,
            rows="3",
            placeholder="Type your message...",
            cls="w-full p-3 border border-gray-200 font-mono text-sm mb-4",
        ),
        Div(
            Div(
                Span(data_text=message_text.length, cls="font-bold text-lg"),
                Span(" / ", cls="text-gray-400"),
                Span(data_text=char_limit, cls="text-gray-600"),
                Span(" characters", cls="text-sm text-gray-600 ml-2"),
                cls="mb-2",
            ),
            Div(
                "Word count: ",
                Strong(data_text=message_text.split(" ").length, cls="font-mono"),
                " • Contains 'Star': ",
                Strong(data_text=message_text.contains("Star").if_("✅ Yes", "❌ No")),
                cls="text-sm text-gray-600 mb-4",
            ),
        ),
        Div(
            P("Transform text:", cls="text-sm text-gray-600 mb-2"),
            Button(
                "UPPERCASE",
                data_on_click=message_text.set(message_text.upper()),
                cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
            ),
            Button(
                "lowercase",
                data_on_click=message_text.set(message_text.lower()),
                cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
            ),
            Button(
                "Clear",
                data_on_click=message_text.set(""),
                cls="px-4 py-2 border border-gray-300 text-black font-medium hover:border-gray-500 transition-colors",
            ),
            cls="flex flex-wrap gap-2",
        ),
        cls="p-4 bg-white border border-gray-200",
    )


def create_string_demo(selected_type: Any) -> Div:
    return Div(
        (message_text := Signal("message_text", "Hello StarHTML! Type safety makes development better.")),
        (char_limit := Signal("char_limit", 100)),
        H3("String Type - Message Composer", cls="text-lg font-medium mb-4"),
        Div(
            string_demo_code_panel(),
            string_demo_interactive(message_text, char_limit),
            cls="grid grid-cols-1 md:grid-cols-2 gap-4",
        ),
        style="display: none",
        data_show=selected_type == "string",
    )


def integer_demo_code_panel() -> Div:
    return Div(
        Div(
            H4("Signal Declaration & Operations", cls="text-sm font-medium text-gray-700 mb-2"),
            Pre(
                Code(
                    """# Integer signal
player_score = Signal("player_score", 1250)

# Use integer methods
Button("+100", data_on_click=player_score.add(100))
Button("×2", data_on_click=player_score.mul(2))""",
                    cls="text-xs text-purple-600",
                ),
                cls="bg-purple-50 p-3 rounded overflow-x-auto mb-4",
            ),
        ),
        Div(
            H4("Integer Methods Available", cls="text-sm font-medium text-gray-700 mb-2"),
            Div(
                Div(
                    Code(".add(n)", cls="text-purple-600 text-xs font-mono bg-purple-50 px-2 py-1 rounded"),
                    " → add value to current",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".sub(n)", cls="text-purple-600 text-xs font-mono bg-purple-50 px-2 py-1 rounded"),
                    " → subtract from current",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".mul(n)", cls="text-purple-600 text-xs font-mono bg-purple-50 px-2 py-1 rounded"),
                    " → multiply current value",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".div(n)", cls="text-purple-600 text-xs font-mono bg-purple-50 px-2 py-1 rounded"),
                    " → divide current value",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".mod(n)", cls="text-purple-600 text-xs font-mono bg-purple-50 px-2 py-1 rounded"),
                    " → modulo operation",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".abs()", cls="text-purple-600 text-xs font-mono bg-purple-50 px-2 py-1 rounded"),
                    " → absolute value",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".min(n)", cls="text-purple-600 text-xs font-mono bg-purple-50 px-2 py-1 rounded"),
                    " → cap at minimum",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".max(n)", cls="text-purple-600 text-xs font-mono bg-purple-50 px-2 py-1 rounded"),
                    " → cap at maximum",
                    cls="mb-1 text-xs",
                ),
            ),
        ),
        cls="p-4 bg-white border border-gray-200",
    )


def integer_demo_interactive(player_score: Any, high_score: Any, bonus_multiplier: Any) -> Div:
    return Div(
        Div(
            Icon("material-symbols:sports-esports", width="24", height="24", cls="mb-3"),
            Div("Game Score Tracker", cls="font-bold mb-3"),
            Div(
                "Score: ", Span(data_text=player_score, cls="text-3xl font-bold font-mono text-purple-600"), cls="mb-3"
            ),
            Div("High Score: ", Span(data_text=high_score, cls="font-mono text-gray-600"), cls="text-sm mb-2"),
            Div(
                Strong(
                    data_text=switch(
                        [
                            (player_score == 0, "🎮 Game Not Started"),
                            (player_score < 500, "🟢 Getting Started"),
                            (player_score < 2000, "🟡 Making Progress"),
                            (player_score >= high_score, "🎉 NEW HIGH SCORE!"),
                        ],
                        default="🔥 On Fire!",
                    ),
                    cls="font-medium",
                ),
                cls="p-3 bg-purple-50 border border-purple-200 text-purple-800 rounded mb-4",
            ),
        ),
        Div(
            Button(
                "+100 pts",
                data_on_click=player_score.add(100),
                cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors mb-2 mr-2",
            ),
            Button(
                "Bonus ×2",
                data_on_click=player_score.mul(bonus_multiplier),
                cls="px-4 py-2 bg-purple-600 text-white font-medium hover:bg-purple-700 transition-colors mb-2 mr-2",
            ),
            Button(
                "Power-up +500",
                data_on_click=player_score.add(500),
                cls="px-4 py-2 bg-green-600 text-white font-medium hover:bg-green-700 transition-colors mb-2 mr-2",
            ),
            Button(
                "Reset Game",
                data_on_click=player_score.set(0),
                cls="px-4 py-2 border border-gray-300 text-black font-medium hover:border-gray-500 transition-colors mb-2",
            ),
            cls="flex flex-wrap gap-2",
        ),
        cls="p-4 bg-white border border-gray-200",
    )


def create_integer_demo(selected_type: Any) -> Div:
    return Div(
        (player_score := Signal("player_score", 1250)),
        (high_score := Signal("high_score", 9999)),
        (bonus_multiplier := Signal("bonus_multiplier", 2)),
        H3("Integer Type - Game Scoring System", cls="text-lg font-medium mb-4"),
        Div(
            integer_demo_code_panel(),
            integer_demo_interactive(player_score, high_score, bonus_multiplier),
            cls="grid grid-cols-1 md:grid-cols-2 gap-4",
        ),
        style="display: none",
        data_show=selected_type == "integer",
    )


def float_demo_code_panel() -> Div:
    return Div(
        Div(
            H4("Signal Declaration & Calculations", cls="text-sm font-medium text-gray-700 mb-2"),
            Pre(
                Code(
                    """# Float signal
temperature_c = Signal("temperature_c", 23.5)

# Use float calculations
fahrenheit = (temperature_c * 9/5) + 32
data_text=fahrenheit.round(1)""",
                    cls="text-xs text-pink-600",
                ),
                cls="bg-pink-50 p-3 rounded overflow-x-auto mb-4",
            ),
        ),
        Div(
            H4("Float Methods Available", cls="text-sm font-medium text-gray-700 mb-2"),
            Div(
                Div(
                    Code(".round()", cls="text-pink-600 text-xs font-mono bg-pink-50 px-2 py-1 rounded"),
                    " → round to integer",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".round(n)", cls="text-pink-600 text-xs font-mono bg-pink-50 px-2 py-1 rounded"),
                    " → round to n decimals",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".abs()", cls="text-pink-600 text-xs font-mono bg-pink-50 px-2 py-1 rounded"),
                    " → absolute value",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".max(n)", cls="text-pink-600 text-xs font-mono bg-pink-50 px-2 py-1 rounded"),
                    " → cap at maximum",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".min(n)", cls="text-pink-600 text-xs font-mono bg-pink-50 px-2 py-1 rounded"),
                    " → cap at minimum",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".clamp(min,max)", cls="text-pink-600 text-xs font-mono bg-pink-50 px-2 py-1 rounded"),
                    " → constrain to range",
                    cls="mb-1 text-xs",
                ),
            ),
        ),
        cls="p-4 bg-white border border-gray-200",
    )


def float_demo_interactive(temperature_c: Any, display_precision: Any) -> Div:
    return Div(
        Label("Temperature in Celsius:", cls="text-sm font-medium text-gray-700 mb-2 block"),
        Div(
            Input(
                type="range",
                min="-40",
                max="50",
                step="0.1",
                data_bind=temperature_c,
                cls="w-full mb-4 measurement-slider",
            ),
            Div(
                Span(
                    data_text=temperature_c.round(display_precision), cls="text-3xl font-bold font-mono text-pink-600"
                ),
                Span("°C", cls="text-gray-600 ml-1"),
                cls="mb-3",
            ),
            cls="p-4 bg-gray-50 border border-gray-200 rounded mb-4",
        ),
        Div(
            Div(
                Span("Fahrenheit: ", cls="text-sm text-gray-600"),
                Strong(data_text=((temperature_c * 9 / 5) + 32).round(display_precision), cls="font-mono text-lg"),
                Span("°F", cls="text-gray-600 ml-1"),
                cls="mb-2 p-2 bg-blue-50 border border-blue-200 rounded",
            ),
            Div(
                Span("Kelvin: ", cls="text-sm text-gray-600"),
                Strong(data_text=(temperature_c + 273.15).round(display_precision), cls="font-mono text-lg"),
                Span("K", cls="text-gray-600 ml-1"),
                cls="mb-2 p-2 bg-green-50 border border-green-200 rounded",
            ),
            Div(
                Span("Status: ", cls="text-sm text-gray-600"),
                Strong(
                    data_text=switch(
                        [
                            (temperature_c <= 0, "❄️ Freezing"),
                            (temperature_c < 10, "🥶 Cold"),
                            (temperature_c < 20, "😐 Cool"),
                            (temperature_c < 30, "😊 Comfortable"),
                            (temperature_c < 40, "🔥 Hot"),
                        ],
                        default="🌋 Extreme Heat",
                    ),
                    cls="font-mono text-lg",
                ),
                cls="mb-4 p-2 bg-yellow-50 border border-yellow-200 rounded",
            ),
        ),
        Div(
            P("Display precision:", cls="text-sm font-medium text-gray-700 mb-2"),
            Button(
                "Integer",
                data_on_click=display_precision.set(0),
                data_class_active=display_precision == 0,
                cls="precision-btn px-3 py-2 border border-gray-200 text-sm hover:bg-gray-50 rounded mr-2",
            ),
            Button(
                "1 decimal",
                data_on_click=display_precision.set(1),
                data_class_active=display_precision == 1,
                cls="precision-btn px-3 py-2 border border-gray-200 text-sm hover:bg-gray-50 rounded mr-2",
            ),
            Button(
                "2 decimals",
                data_on_click=display_precision.set(2),
                data_class_active=display_precision == 2,
                cls="precision-btn px-3 py-2 border border-gray-200 text-sm hover:bg-gray-50 rounded",
            ),
        ),
        cls="p-4 bg-white border border-gray-200",
    )


def create_float_demo(selected_type: Any) -> Div:
    return Div(
        (temperature_c := Signal("temperature_c", 23.5)),
        (display_precision := Signal("display_precision", 1)),
        H3("Float Type - Temperature Converter", cls="text-lg font-medium mb-4"),
        Div(
            float_demo_code_panel(),
            float_demo_interactive(temperature_c, display_precision),
            cls="grid grid-cols-1 md:grid-cols-2 gap-4",
        ),
        style="display: none",
        data_show=selected_type == "float",
    )


def boolean_demo_code_panel() -> Div:
    return Div(
        Div(
            H4("Signal Declaration & Toggle", cls="text-sm font-medium text-gray-700 mb-2"),
            Pre(
                Code(
                    """# Boolean signals
cookies = Signal("cookies", True)

# Toggle and conditional display
Button(data_text=cookies.if_("ON", "OFF"),
       data_on_click=cookies.toggle())""",
                    cls="text-xs text-green-600",
                ),
                cls="bg-green-50 p-3 rounded overflow-x-auto mb-4",
            ),
        ),
        Div(
            H4("Boolean Methods Available", cls="text-sm font-medium text-gray-700 mb-2"),
            Div(
                Div(
                    Code(".toggle()", cls="text-green-600 text-xs font-mono bg-green-50 px-2 py-1 rounded"),
                    " → flip true/false",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".if_(a, b)", cls="text-green-600 text-xs font-mono bg-green-50 px-2 py-1 rounded"),
                    " → conditional (ternary)",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code("all(a,b,c)", cls="text-green-600 text-xs font-mono bg-green-50 px-2 py-1 rounded"),
                    " → logical AND (all true)",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code("any(a,b,c)", cls="text-green-600 text-xs font-mono bg-green-50 px-2 py-1 rounded"),
                    " → logical OR (any true)",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code("~signal", cls="text-green-600 text-xs font-mono bg-green-50 px-2 py-1 rounded"),
                    " → logical NOT (negate)",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code("a & b", cls="text-green-600 text-xs font-mono bg-green-50 px-2 py-1 rounded"),
                    " → logical AND operator",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code("a | b", cls="text-green-600 text-xs font-mono bg-green-50 px-2 py-1 rounded"),
                    " → logical OR operator",
                    cls="mb-1 text-xs",
                ),
            ),
        ),
        cls="p-4 bg-white border border-gray-200",
    )


def boolean_demo_interactive(cookies_enabled: Any, analytics_enabled: Any, marketing_enabled: Any) -> Div:
    return Div(
        P("Privacy Controls:", cls="font-medium text-gray-700 mb-3"),
        Div(
            Div(
                Icon("material-symbols:cookie", width="20", height="20", cls="mr-2"),
                Span("Essential Cookies", cls="flex-1"),
                Button(
                    data_text=cookies_enabled.if_("Enabled", "Disabled"),
                    data_on_click=cookies_enabled.toggle(),
                    data_class_enabled=cookies_enabled,
                    cls="px-4 py-2 rounded text-sm font-medium min-w-[90px] border transition-colors enabled:bg-black enabled:text-white enabled:border-black bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200",
                ),
                cls="flex items-center mb-3 p-3 border border-gray-200",
            ),
            Div(
                Icon("material-symbols:bar-chart", width="20", height="20", cls="mr-2"),
                Span("Analytics", cls="flex-1"),
                Button(
                    data_text=analytics_enabled.if_("Enabled", "Disabled"),
                    data_on_click=analytics_enabled.toggle(),
                    data_class_enabled=analytics_enabled,
                    data_attr_disabled=~cookies_enabled,
                    cls="px-4 py-2 rounded text-sm font-medium min-w-[90px] border transition-colors enabled:bg-black enabled:text-white enabled:border-black bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed",
                ),
                cls="flex items-center mb-3 p-3 border border-gray-200",
            ),
            Div(
                Icon("material-symbols:campaign", width="20", height="20", cls="mr-2"),
                Span("Marketing", cls="flex-1"),
                Button(
                    data_text=marketing_enabled.if_("Enabled", "Disabled"),
                    data_on_click=marketing_enabled.toggle(),
                    data_class_enabled=marketing_enabled,
                    data_attr_disabled=~analytics_enabled,
                    cls="px-4 py-2 rounded text-sm font-medium min-w-[90px] border transition-colors enabled:bg-black enabled:text-white enabled:border-black bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed",
                ),
                cls="flex items-center mb-3 p-3 border border-gray-200",
            ),
        ),
        Div(
            P("Boolean Logic in Action:", cls="text-sm font-medium text-gray-700 mb-2"),
            Div(
                Div(
                    Strong(
                        data_text=switch(
                            [
                                (~cookies_enabled, "Maximum Privacy (NOT cookies)"),
                                (
                                    all(cookies_enabled, ~analytics_enabled, ~marketing_enabled),
                                    "GDPR Compliant (cookies AND NOT analytics AND NOT marketing)",
                                ),
                                (
                                    all(cookies_enabled, analytics_enabled, ~marketing_enabled),
                                    "Analytics Active (cookies AND analytics AND NOT marketing)",
                                ),
                                (
                                    all(cookies_enabled, analytics_enabled, marketing_enabled),
                                    "Full Tracking (cookies AND analytics AND marketing)",
                                ),
                            ],
                            default="Configuring...",
                        ),
                        cls="font-medium text-sm",
                    ),
                    cls="mb-2",
                ),
                Div(
                    Span("Features active: ", cls="text-xs text-gray-500"),
                    Span(
                        data_text=collect(
                            [
                                (cookies_enabled, "cookies"),
                                (analytics_enabled, "analytics"),
                                (marketing_enabled, "marketing"),
                            ]
                        ),
                        cls="font-mono text-xs",
                    ),
                    cls="text-xs text-gray-600",
                ),
                cls="p-3 bg-gray-50 border border-gray-200 rounded",
            ),
        ),
        cls="p-4 bg-white border border-gray-200",
    )


def create_boolean_demo(selected_type: Any) -> Div:
    return Div(
        (cookies_enabled := Signal("cookies_enabled", True)),
        (analytics_enabled := Signal("analytics_enabled", False)),
        (marketing_enabled := Signal("marketing_enabled", False)),
        H3("Boolean Type - Privacy Settings", cls="text-lg font-medium mb-4"),
        Div(
            boolean_demo_code_panel(),
            boolean_demo_interactive(cookies_enabled, analytics_enabled, marketing_enabled),
            cls="grid grid-cols-1 md:grid-cols-2 gap-4",
        ),
        style="display: none",
        data_show=selected_type == "boolean",
    )


def list_demo_code_panel() -> Div:
    return Div(
        Div(
            H4("Signal Declaration & Array Ops", cls="text-sm font-medium text-gray-700 mb-2"),
            Pre(
                Code(
                    """# List signal
playlist = Signal("playlist", [...])

# Array operations
playlist.push(new_song)
data_text=playlist.length""",
                    cls="text-xs text-orange-600",
                ),
                cls="bg-orange-50 p-3 rounded overflow-x-auto mb-4",
            ),
        ),
        Div(
            H4("List Methods Available", cls="text-sm font-medium text-gray-700 mb-2"),
            Div(
                Div(
                    Code(".length", cls="text-orange-600 text-xs font-mono bg-orange-50 px-2 py-1 rounded"),
                    " → get item count",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".push(item)", cls="text-orange-600 text-xs font-mono bg-orange-50 px-2 py-1 rounded"),
                    " → add to end",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".pop()", cls="text-orange-600 text-xs font-mono bg-orange-50 px-2 py-1 rounded"),
                    " → remove last",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code("[index]", cls="text-orange-600 text-xs font-mono bg-orange-50 px-2 py-1 rounded"),
                    " → get item at index",
                    cls="mb-1 text-xs",
                ),
                Div(
                    Code(".join(sep)", cls="text-orange-600 text-xs font-mono bg-orange-50 px-2 py-1 rounded"),
                    " → combine to string",
                    cls="mb-1 text-xs",
                ),
            ),
        ),
        cls="p-4 bg-white border border-gray-200",
    )


def list_demo_interactive(playlist: Any, new_song: Any, current_index: Any, song_count: Any) -> Div:
    return Div(
        Div(
            Icon("material-symbols:music-note", width="24", height="24", cls="mb-2"),
            Div("Now Playing", cls="font-bold text-sm text-gray-600 mb-1"),
            Div(data_text=playlist[current_index] | value("No songs in playlist"), cls="font-medium mb-3"),
            Div(
                Button(
                    Icon("material-symbols:skip-previous", width="20", height="20"),
                    data_on_click=[current_index.set((current_index <= 0).if_(song_count - 1, current_index - 1))],
                    data_attr_disabled=song_count == 0,
                    cls="p-2 bg-black text-white hover:bg-gray-800 rounded disabled:opacity-50 mr-2",
                ),
                Button(
                    Icon("material-symbols:skip-next", width="20", height="20"),
                    data_on_click=[current_index.set((current_index >= song_count - 1).if_(0, current_index + 1))],
                    data_attr_disabled=song_count == 0,
                    cls="p-2 bg-black text-white hover:bg-gray-800 rounded disabled:opacity-50 mr-2",
                ),
                Span(
                    "Track ",
                    Span(data_text=song_count.if_(current_index + 1, 0), cls="font-mono font-bold"),
                    " of ",
                    Span(data_text=song_count, cls="font-mono font-bold"),
                    cls="text-sm text-gray-600",
                ),
                cls="flex items-center",
            ),
            cls="p-4 bg-gray-50 border border-gray-200 rounded mb-4",
        ),
        Div(
            P("Playlist Queue:", cls="text-sm font-medium text-gray-700 mb-2"),
            Div(
                Div(
                    Icon("material-symbols:queue-music", width="48", height="48", cls="text-gray-300 mb-2"),
                    P("No songs in playlist", cls="text-gray-500"),
                    P("Add songs using the form below", cls="text-gray-400 text-sm mt-1"),
                    id="empty-playlist-message",
                    style="display: none",
                    data_show=song_count == 0,
                    cls="text-center py-8",
                ),
                Div(
                    id="playlist-items",
                    style="display: none",
                    data_show=song_count > 0,
                    cls="max-h-[200px] overflow-y-auto",
                    data_effect=js(
                        "el.children[$current_index]?.scrollIntoView({ behavior: 'smooth', block: 'center' })"
                    ),
                ),
                cls="mb-4",
            ),
        ),
        Div(
            P("Add Song:", cls="text-sm font-medium text-gray-700 mb-2"),
            Div(
                Input(
                    type="text",
                    data_bind=new_song,
                    placeholder="Enter song title (Artist - Song)",
                    data_on_keydown=js(
                        "if (evt.key === 'Enter' && $new_song.trim()) { evt.preventDefault(); @post('/api/philosophy/add-song'); }"
                    ),
                    cls="flex-1 px-3 py-2 border border-gray-200 text-sm mr-2",
                ),
                Button(
                    Icon("material-symbols:add-circle", width="20", height="20"),
                    data_on_click=post("/api/philosophy/add-song"),
                    cls="p-2 bg-black text-white hover:bg-gray-800 rounded",
                    data_attr_disabled=new_song.length == 0,
                ),
                cls="flex items-center mb-4",
            ),
            Div(
                Button(
                    Icon("material-symbols:shuffle", width="20", height="20", cls="mr-2"),
                    "Shuffle",
                    data_on_click=post("/api/philosophy/shuffle-playlist"),
                    data_attr_disabled=song_count == 0,
                    cls="flex items-center px-4 py-2 bg-purple-600 text-white font-medium hover:bg-purple-700 transition-colors rounded mr-2 disabled:opacity-50 disabled:cursor-not-allowed",
                ),
                Button(
                    Icon("material-symbols:clear-all", width="20", height="20", cls="mr-2"),
                    "Clear All",
                    data_on_click=post("/api/philosophy/clear-playlist"),
                    data_attr_disabled=song_count == 0,
                    cls="flex items-center px-4 py-2 bg-red-600 text-white font-medium hover:bg-red-700 transition-colors rounded disabled:opacity-50 disabled:cursor-not-allowed",
                ),
                cls="flex flex-wrap gap-2",
            ),
        ),
        cls="p-4 bg-white border border-gray-200",
    )


def create_list_demo(selected_type: Any) -> Div:
    return Div(
        (playlist := Signal("playlist", [])),
        (new_song := Signal("new_song", "")),
        (current_index := Signal("current_index", 0)),
        (song_count := Signal("song_count", 0)),
        H3("List Type - Music Playlist", cls="text-lg font-medium mb-4"),
        Div(
            list_demo_code_panel(),
            list_demo_interactive(playlist, new_song, current_index, song_count),
            cls="grid grid-cols-1 md:grid-cols-2 gap-4",
        ),
        style="display: none",
        data_show=selected_type == "list",
        data_on_intersect=get("/api/philosophy/load-sample-playlist").with_(once=True),
    )


def type_safety_section() -> Div:
    return Div(
        (selected_type := Signal("selected_type", "string")),
        Style("""
            body { background: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; -webkit-font-smoothing: antialiased; }
            .type-tab { transition: all 200ms ease; }
            .type-tab.active { background: #000; color: #fff; }
            .precision-btn { transition: all 200ms ease; }
            .precision-btn.active { background: #000; color: #fff; border-color: #000; }
            .measurement-slider::-webkit-slider-thumb { -webkit-appearance: none; appearance: none; width: 20px; height: 20px; background: #000; cursor: pointer; border-radius: 50%; }
            .measurement-slider::-moz-range-thumb { width: 20px; height: 20px; background: #000; cursor: pointer; border-radius: 50%; border: none; }
            .measurement-slider { -webkit-appearance: none; appearance: none; height: 6px; border-radius: 3px; background: #e5e7eb; outline: none; }
            .measurement-slider::-webkit-slider-track { height: 6px; border-radius: 3px; background: #e5e7eb; }
            .playlist-active { background: #dcfce7 !important; border-color: #16a34a !important; color: #166534; }
            .playlist-active .text-gray-400 { color: #16a34a !important; }
            .playlist-active .text-sm { color: #166534; font-weight: 500; }
        """),
        create_header(),
        Div(
            Div(
                Button(
                    "String",
                    data_on_click=selected_type.set("string"),
                    data_class_active=selected_type == "string",
                    cls="type-tab px-4 py-2 border border-gray-200 font-medium",
                ),
                Button(
                    "Integer",
                    data_on_click=selected_type.set("integer"),
                    data_class_active=selected_type == "integer",
                    cls="type-tab px-4 py-2 border border-gray-200 font-medium",
                ),
                Button(
                    "Float",
                    data_on_click=selected_type.set("float"),
                    data_class_active=selected_type == "float",
                    cls="type-tab px-4 py-2 border border-gray-200 font-medium",
                ),
                Button(
                    "Boolean",
                    data_on_click=selected_type.set("boolean"),
                    data_class_active=selected_type == "boolean",
                    cls="type-tab px-4 py-2 border border-gray-200 font-medium",
                ),
                Button(
                    "List",
                    data_on_click=selected_type.set("list"),
                    data_class_active=selected_type == "list",
                    cls="type-tab px-4 py-2 border border-gray-200 font-medium",
                ),
                cls="flex flex-wrap gap-2 mb-4",
            ),
            create_string_demo(selected_type),
            create_integer_demo(selected_type),
            create_float_demo(selected_type),
            create_boolean_demo(selected_type),
            create_list_demo(selected_type),
            cls="p-2 sm:p-4 bg-gray-50",
        ),
    )


from starhtml.server import APIRouter

section_router = APIRouter(prefix="/api/philosophy")

playlist_store = [
    "Bohemian Rhapsody - Queen",
    "Stairway to Heaven - Led Zeppelin",
    "Hotel California - Eagles",
    "Sweet Child O' Mine - Guns N' Roses",
    "November Rain - Guns N' Roses",
    "Comfortably Numb - Pink Floyd",
    "Wish You Were Here - Pink Floyd",
    "Purple Haze - Jimi Hendrix",
    "While My Guitar Gently Weeps - The Beatles",
    "Imagine - John Lennon",
    "Black - Pearl Jam",
    "Smells Like Teen Spirit - Nirvana",
]


def create_playlist_item(song_title: str, index: int, current_index: Signal) -> Div:
    return Div(
        Icon("material-symbols:music-note", width="16", height="16", cls="mr-2 text-gray-400"),
        Span(song_title, cls="text-sm flex-1 truncate mr-2"),
        Button(
            Icon("material-symbols:play-circle", width="16", height="16"),
            data_on_click=current_index.set(index),
            cls="p-1 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded mr-1",
        ),
        Button(
            Icon("material-symbols:close", width="16", height="16"),
            data_on_click=post("/api/philosophy/remove-song").with_(selector_song_index=value(index)),
            cls="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded",
        ),
        cls="flex items-center py-2 px-3 mb-1 border border-transparent hover:border-gray-200 hover:bg-gray-50 rounded",
        data_class_playlist_active=current_index == index,
        style="transition: all 0.2s ease;",
    )


@section_router.get("/load-sample-playlist")
@sse
def load_sample_playlist(req, current_index: Signal):
    clean_playlist = [song for song in playlist_store if song and song.strip()]

    yield signals(playlist=clean_playlist, current_index=0, song_count=len(clean_playlist))

    for i, song_title in enumerate(clean_playlist):
        yield elements(create_playlist_item(song_title, i, current_index), "#playlist-items", "append")


@section_router.post("/add-song")
@sse
def add_song_to_queue(req, new_song: str = "", playlist: list[str] = None, current_index: Signal = None):
    song_title = new_song.strip()
    if not song_title:
        return

    if not isinstance(playlist, list):
        playlist = []

    clean_playlist = [song for song in playlist if song and song.strip()]
    updated_playlist = clean_playlist + [song_title]
    new_index = len(updated_playlist) - 1

    yield signals(playlist=updated_playlist, new_song="", song_count=len(updated_playlist))

    yield elements(create_playlist_item(song_title, new_index, current_index), "#playlist-items", "append")


@section_router.post("/clear-playlist")
@sse
def clear_playlist(req):
    yield signals(playlist=[], current_index=0, song_count=0)

    yield elements("", "#playlist-items", "inner")


@section_router.post("/shuffle-playlist")
@sse
def shuffle_playlist(req, playlist: list[str] = None, current_index: int = 0):
    if not isinstance(playlist, list):
        playlist = []

    clean_playlist = [str(song).strip() for song in playlist if song and isinstance(song, str) and song.strip()]

    if len(clean_playlist) == 0:
        yield signals(playlist=[], current_index=0, song_count=0)
        return

    current_song = None
    if 0 <= current_index < len(clean_playlist):
        current_song = clean_playlist[current_index]

    if len(clean_playlist) == 1:
        yield signals(playlist=clean_playlist, current_index=0, song_count=1)
        yield elements("", "#playlist-items", "inner")
        current_index_sig = Signal("current_index", 0, _ref_only=True)
        yield elements(create_playlist_item(clean_playlist[0], 0, current_index_sig), "#playlist-items", "append")
        return

    others = [song for song in clean_playlist if song != current_song]
    random.shuffle(others)
    shuffled_playlist = [current_song] + others if current_song else others

    yield signals(playlist=shuffled_playlist, current_index=0, song_count=len(shuffled_playlist))

    yield elements("", "#playlist-items", "inner")

    current_index_sig = Signal("current_index", 0, _ref_only=True)
    for i, song in enumerate(shuffled_playlist):
        yield elements(create_playlist_item(song, i, current_index_sig), "#playlist-items", "append")


@section_router.post("/remove-song")
@sse
def remove_song(req, selector_song_index: int = -1, playlist: list[str] = None, current_index: int = 0):
    if selector_song_index < 0 or not isinstance(playlist, list):
        return

    clean_playlist = [song for song in playlist if song and song.strip()]

    if selector_song_index >= len(clean_playlist):
        return

    updated_playlist = [s for i, s in enumerate(clean_playlist) if i != selector_song_index]

    new_current_index = current_index
    if current_index >= len(updated_playlist):
        new_current_index = max(0, len(updated_playlist) - 1)
    elif current_index > selector_song_index:
        new_current_index = current_index - 1

    yield signals(playlist=updated_playlist, current_index=new_current_index, song_count=len(updated_playlist))

    yield elements("", "#playlist-items", "inner")

    current_index_sig = Signal("current_index", 0, _ref_only=True)
    for i, song in enumerate(updated_playlist):
        yield elements(create_playlist_item(song, i, current_index_sig), "#playlist-items", "append")


app, rt = star_app(
    title="Type Safety - StarHTML Philosophy (Dev Mode)",
    hdrs=[Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4")],
    iconify=True,
)

section_router.to_app(app)


@rt("/")
def dev_home():
    return Div(
        Div("⚠️ Development Mode - Type Safety Section", cls="bg-yellow-100 p-4 mb-4 text-center font-mono text-sm"),
        type_safety_section(),
    )


if __name__ == "__main__":
    print("🚀 Type Safety Philosophy - Development Mode")
    print("Visit: http://localhost:5099/")

    serve(port=5099)
