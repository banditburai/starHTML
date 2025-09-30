"""Datastar Helper Functions - Advanced Signal Patterns

Demonstrates the rich collection of helper functions and utilities available
in StarHTML's datastar module including logical operators, mathematical functions,
data helpers, and advanced expression patterns."""

from starhtml import *

app, rt = star_app(
    title="Datastar Helper Functions",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body { background: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; -webkit-font-smoothing: antialiased; }
        """),
    ],
    iconify=True,
    compression=False,
)


@rt("/")
def home():
    return Div(
        # === SIGNAL DEFINITIONS ===
        # Calculator inputs
        (calc_a := Signal("calc_a", 5)),
        (calc_b := Signal("calc_b", 3)),
        # Form validation signals
        (name := Signal("name", "")),
        (email := Signal("email", "")),
        (age := Signal("age", 18)),
        (terms := Signal("terms", False)),
        # Array and utility signals
        (numbers := Signal("numbers", [1, 2, 3, 4, 5])),
        (timestamp := Signal("timestamp", 0)),
        (random_num := Signal("random_num", 42)),
        # Header with large number and title
        Div(
            H1("21", cls="text-8xl font-black text-gray-100 leading-none"),
            H1("Datastar Helper Functions", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
            P("Advanced signal patterns and helper utilities", cls="text-lg text-gray-600 mt-4"),
            cls="mb-16",
        ),
        # === 1. LOGICAL OPERATORS ===
        Div(
            H3("Logical Operators", cls="text-2xl font-bold text-black mb-6"),
            P("Use all(), any() helpers and composable operators: & (AND), | (OR), ~ (NOT)", cls="text-gray-600 mb-6"),
            # Input fields
            Div(
                Input(
                    placeholder="Name",
                    data_bind=name,
                    cls="mr-3 px-3 py-2 border border-gray-300 focus:border-gray-500 focus:outline-none rounded",
                ),
                Input(
                    placeholder="Email",
                    data_bind=email,
                    cls="mr-3 px-3 py-2 border border-gray-300 focus:border-gray-500 focus:outline-none rounded",
                ),
                Input(
                    type="number",
                    placeholder="Age",
                    data_bind=age,
                    cls="mr-3 px-3 py-2 border border-gray-300 focus:border-gray-500 focus:outline-none rounded w-24",
                ),
                cls="mb-6 flex flex-wrap gap-2",
            ),
            Div(
                Label(
                    Input(type="checkbox", data_bind=terms, cls="mr-3 w-4 h-4 accent-black"),
                    "I agree to terms and conditions",
                    cls="flex items-center text-gray-700 mb-3 cursor-pointer",
                ),
            ),
            # Results display
            Div(
                Div(
                    Span("All fields filled: ", cls="text-gray-600"),
                    Span(data_text=all(name, email, age), cls="text-2xl font-black text-black"),
                    cls="p-6 bg-gray-50 border border-gray-200 mb-4",
                ),
                Div(
                    Span("Form valid (using &): ", cls="text-gray-600"),
                    Span(data_text=all(name, email, terms) & (age >= 13), cls="text-2xl font-black text-black"),
                    cls="p-6 bg-gray-50 border border-gray-200 mb-4",
                ),
                Div(
                    Span("Has name OR email: ", cls="text-gray-600"),
                    Span(data_text=name | email, cls="text-2xl font-black text-black"),
                    cls="p-6 bg-gray-50 border border-gray-200 mb-4",
                ),
                Div(
                    Span("Terms NOT agreed: ", cls="text-gray-600"),
                    Span(data_text=~terms, cls="text-2xl font-black text-black"),
                    cls="p-6 bg-gray-50 border border-gray-200 mb-4",
                ),
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        # === 2. MATHEMATICAL OPERATIONS ===
        Div(
            H3("Mathematical Operations", cls="text-2xl font-bold text-black mb-6"),
            P("Use Math helpers and rounding functions for calculations", cls="text-gray-600 mb-6"),
            # Calculator inputs
            Div(
                Label("A:", cls="text-gray-600 font-medium mr-2"),
                Input(
                    type="number",
                    data_bind=calc_a,
                    cls="mr-4 px-3 py-2 border border-gray-300 focus:border-gray-500 focus:outline-none rounded w-20",
                ),
                Label("B:", cls="text-gray-600 font-medium mr-2"),
                Input(
                    type="number",
                    data_bind=calc_b,
                    cls="px-3 py-2 border border-gray-300 focus:border-gray-500 focus:outline-none rounded w-20",
                ),
                cls="mb-6 flex items-center",
            ),
            # Math operations
            Div(
                Div(
                    Span("Sum: ", cls="text-gray-600 text-lg"),
                    Span(data_text=calc_a + calc_b, cls="text-6xl font-black text-black"),
                    cls="p-8 bg-gray-50 border border-gray-200 mb-6",
                ),
                Div(
                    Span("Maximum: ", cls="text-gray-600 text-lg"),
                    Span(data_text=js("Math.max($calc_a, $calc_b)"), cls="text-6xl font-black text-black"),
                    cls="p-8 bg-gray-50 border border-gray-200 mb-6",
                ),
                Div(
                    Span("Square root of A: ", cls="text-gray-600 text-lg"),
                    Span(data_text=js("Math.sqrt($calc_a).toFixed(2)"), cls="text-6xl font-black text-black"),
                    cls="p-8 bg-gray-50 border border-gray-200 mb-6",
                ),
                Div(
                    Span("Random number: ", cls="text-gray-600 text-lg mr-4"),
                    Span(data_text=random_num, cls="text-6xl font-black text-black mr-4"),
                    Button(
                        "Generate",
                        data_on_click=random_num.set(js("Math.floor(Math.random() * 100) + 1")),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                    ),
                    cls="p-8 bg-gray-50 border border-gray-200 flex items-center",
                ),
            ),
            cls="mb-12 p-8 bg-gray-50",
        ),
        # === 3. TEMPLATE FUNCTION f() ===
        Div(
            H3("Template Function f()", cls="text-2xl font-bold text-black mb-6"),
            P("Create dynamic template strings with signal interpolation", cls="text-gray-600 mb-6"),
            # Template examples with working signals
            Div(
                Div(
                    Span("Basic template: ", cls="text-gray-600 text-lg"),
                    Span(
                        data_text=f("Hello {name}, you are {age} years old", name=name | value("Anonymous"), age=age),
                        cls="text-xl font-bold text-black",
                    ),
                    cls="p-6 bg-gray-50 border border-gray-200 mb-6",
                ),
                Div(
                    Span("Email status: ", cls="text-gray-600 text-lg"),
                    Span(
                        data_text=f(
                            "Email {email} is {status}",
                            email=email | value("not provided"),
                            status=email.if_("confirmed", "pending"),
                        ),
                        cls="text-xl font-bold text-black",
                    ),
                    cls="p-6 bg-gray-50 border border-gray-200 mb-6",
                ),
                Div(
                    Span("Current time: ", cls="text-gray-600 text-lg mr-4"),
                    Span(
                        data_text=f(
                            "Updated at {time}", time=js("new Date($timestamp || Date.now()).toLocaleTimeString()")
                        ),
                        cls="text-xl font-bold text-black mr-4",
                    ),
                    Button(
                        "Update",
                        data_on_click=timestamp.set(js("Date.now()")),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                    ),
                    cls="p-6 bg-gray-50 border border-gray-200 flex items-center",
                ),
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        # === 4. VALUE FALLBACKS ===
        Div(
            H3("Value Fallbacks with value()", cls="text-2xl font-bold text-black mb-6"),
            P("Handle empty or undefined values gracefully using the value() helper", cls="text-gray-600 mb-6"),
            # Fallback examples
            Div(
                Div(
                    Span("Name with fallback: ", cls="text-gray-600 text-lg"),
                    Span(data_text=name | value("Anonymous User"), cls="text-2xl font-black text-black"),
                    cls="p-6 bg-gray-50 border border-gray-200 mb-6",
                ),
                Div(
                    Span("Email with fallback: ", cls="text-gray-600 text-lg"),
                    Span(data_text=email | value("no-email@example.com"), cls="text-2xl font-black text-black"),
                    cls="p-6 bg-gray-50 border border-gray-200 mb-6",
                ),
                Div(
                    Span("Conditional greeting: ", cls="text-gray-600 text-lg"),
                    Span(
                        data_text=(name.length > 0).if_(f("Hello, {name}!", name=name), "Please enter your name"),
                        cls="text-2xl font-black text-black",
                    ),
                    cls="p-6 bg-gray-50 border border-gray-200",
                ),
            ),
            cls="mb-12 p-8 bg-gray-50",
        ),
        # === 5. ARRAY OPERATIONS ===
        Div(
            H3("Array Operations", cls="text-2xl font-bold text-black mb-6"),
            P("Work with arrays using built-in methods and JavaScript helpers", cls="text-gray-600 mb-6"),
            # Array controls
            Div(
                Button(
                    "Add Random Number",
                    data_on_click=numbers.push(js("Math.floor(Math.random() * 10) + 1")),
                    cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors mr-2",
                ),
                Button(
                    "Clear Array",
                    data_on_click=numbers.set([]),
                    cls="px-4 py-2 border border-gray-300 text-black font-medium hover:border-gray-500 transition-colors",
                ),
                cls="mb-6",
            ),
            # Array display
            Div(
                Div(
                    Span("Array contents: ", cls="text-gray-600 text-lg"),
                    Span(data_text=numbers, cls="text-2xl font-black text-black"),
                    cls="p-6 bg-gray-50 border border-gray-200 mb-6",
                ),
                Div(
                    Span("Array length: ", cls="text-gray-600 text-lg"),
                    Span(data_text=numbers.length, cls="text-2xl font-black text-black"),
                    cls="p-6 bg-gray-50 border border-gray-200 mb-6",
                ),
                Div(
                    Span("Array sum: ", cls="text-gray-600 text-lg"),
                    Span(data_text=js("$numbers.reduce((a, b) => a + b, 0)"), cls="text-2xl font-black text-black"),
                    cls="p-6 bg-gray-50 border border-gray-200",
                ),
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        # === SUMMARY ===
        Div(
            H3("Key Takeaways", cls="text-2xl font-bold text-black mb-6"),
            Div(
                Div(
                    Icon(
                        "material-symbols:check-circle",
                        width="20",
                        height="20",
                        cls="mr-3 text-green-600 flex-shrink-0 mt-1",
                    ),
                    "Use all() and any() for readable multi-condition logic",
                    cls="flex items-start p-4 mb-3 bg-green-50 border border-green-200 rounded-lg text-green-900",
                ),
                Div(
                    Icon(
                        "material-symbols:calculate",
                        width="20",
                        height="20",
                        cls="mr-3 text-blue-600 flex-shrink-0 mt-1",
                    ),
                    "Leverage Math.* functions for calculations and rounding",
                    cls="flex items-start p-4 mb-3 bg-blue-50 border border-blue-200 rounded-lg text-blue-900",
                ),
                Div(
                    Icon(
                        "material-symbols:code", width="20", height="20", cls="mr-3 text-purple-600 flex-shrink-0 mt-1"
                    ),
                    "f() templates handle complex string interpolation",
                    cls="flex items-start p-4 mb-3 bg-purple-50 border border-purple-200 rounded-lg text-purple-900",
                ),
                Div(
                    Icon(
                        "material-symbols:backup",
                        width="20",
                        height="20",
                        cls="mr-3 text-orange-600 flex-shrink-0 mt-1",
                    ),
                    "Pipe operator (|) creates fallbacks using JavaScript's || logic",
                    cls="flex items-start p-4 mb-3 bg-orange-50 border border-orange-200 rounded-lg text-orange-900",
                ),
                Div(
                    Icon(
                        "material-symbols:view-list",
                        width="20",
                        height="20",
                        cls="mr-3 text-indigo-600 flex-shrink-0 mt-1",
                    ),
                    "Array methods (.push, .length) provide clean manipulation",
                    cls="flex items-start p-4 mb-3 bg-indigo-50 border border-indigo-200 rounded-lg text-indigo-900",
                ),
                Div(
                    Icon(
                        "material-symbols:integration-instructions",
                        width="20",
                        height="20",
                        cls="mr-3 text-teal-600 flex-shrink-0 mt-1",
                    ),
                    "JavaScript expressions integrate seamlessly with Python signals",
                    cls="flex items-start p-4 bg-teal-50 border border-teal-200 rounded-lg text-teal-900",
                ),
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen",
    )


if __name__ == "__main__":
    print("🧰 Datastar Helper Functions Demo")
    print("=" * 40)
    print("🚀 Running on http://localhost:5023")
    print("✨ Features:")
    print("   • Logical operators (all, any)")
    print("   • Math functions and calculations")
    print("   • Template strings with f()")
    print("   • Value fallbacks with value()")
    print("   • Array operations")
    print("   • Interactive examples")
    serve(port=5023)
