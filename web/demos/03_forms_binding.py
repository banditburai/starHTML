"""Forms and Binding Demo - Using new Signal API with validation"""

from starhtml import *

app, rt = star_app(
    title="Forms and Binding Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body {
                background: #fff;
                color: #000;
                margin: 0;
                padding: 0;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }
            ::selection {
                background: #000;
                color: #fff;
            }
            .form-field-focus { transition: all 200ms ease; }
            .form-field-focus:focus-within label { color: #0ea5e9; }
        """),
    ],
    iconify=True,
    compression=False,
    static_path="demo",  # Serve static files from demo directory when run standalone
)


@rt("/")
def home():
    return Div(
        # Define all signals using walrus operator at the start
        (name := Signal("name", "")),
        (email := Signal("email", "")),
        (age := Signal("age", "")),
        (phone := Signal("phone", "")),
        # Error signals for validation
        (name_error := Signal("name_error", "")),
        (email_error := Signal("email_error", "")),
        (age_error := Signal("age_error", "")),
        (phone_error := Signal("phone_error", "")),
        # Computed signals
        (is_valid := Signal("is_valid", all(name, email, age) & ~any(name_error, email_error, age_error, phone_error))),
        # Form state signals
        (submitting := Signal("submitting", False)),
        (submitted := Signal("submitted", False)),
        # Header section with large number
        Div(
            H1("03", cls="text-8xl font-black text-gray-100 leading-none"),
            H1("Forms and Binding", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
            P("Using the new Signal API with validation", cls="text-lg text-gray-600 mt-4"),
            cls="mb-16",
        ),
        # Main Form
        Div(
            H2("Contact Information", cls="text-2xl font-bold text-black mb-8"),
            Form(
                # Name field with validation
                Div(
                    Label(
                        "Full Name",
                        Span(" *", cls="text-red-500"),
                        For="name_input",
                        cls="block text-sm font-medium text-gray-700 mb-1",
                    ),
                    Input(
                        type="text",
                        placeholder="Enter your full name",
                        id="name_input",
                        name="name",
                        data_bind=name,
                        # Simple length validation - Pythonic
                        data_on_input=name_error.set((name.length < 2).if_("Name must be at least 2 characters")),
                        data_class_error=name_error,  # Adds 'error' class when name_error is truthy
                        cls="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent error:border-red-500 error:focus:ring-red-500",
                        required=True,
                    ),
                    Span(
                        data_text=name_error,  # JS: data_text="$name_error"
                        data_show=name_error,  # JS: data_show="$name_error"
                        cls="text-red-500 text-xs mt-1 block",
                    ),
                    cls="mb-6",
                ),
                # Email field with validation
                Div(
                    Label(
                        "Email Address",
                        Span(" *", cls="text-red-500"),
                        For="email_input",
                        cls="block text-sm font-medium text-gray-700 mb-1",
                    ),
                    Input(
                        type="email",
                        placeholder="Enter your email",
                        id="email_input",
                        name="email",
                        data_bind=email,
                        # Email needs regex, so we use js() for the validation part only
                        data_on_input=email_error.set(
                            js(
                                "!$email ? 'Email is required' : !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test($email) ? 'Please enter a valid email' : ''"
                            )
                        ),
                        data_class_error=email_error,  # Adds 'error' class when email_error is truthy
                        cls="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent error:border-red-500 error:focus:ring-red-500",
                        required=True,
                    ),
                    Span(data_text=email_error, data_show=email_error, cls="text-red-500 text-xs mt-1 block"),
                    cls="mb-6",
                ),
                # Age field with validation
                Div(
                    Label(
                        "Age",
                        Span(" *", cls="text-red-500"),
                        For="age_input",
                        cls="block text-sm font-medium text-gray-700 mb-1",
                    ),
                    Input(
                        type="number",
                        placeholder="Enter your age",
                        id="age_input",
                        name="age",
                        data_bind=age,
                        # Range validation - Pythonic with switch
                        data_on_input=age_error.set(
                            switch(
                                [
                                    (~age, "Age is required"),
                                    ((age < 18) | (age > 120), "Age must be between 18 and 120"),
                                ],
                                default="",
                            )  # Explicitly set to empty string when valid
                        ),
                        data_class_error=age_error,  # Adds 'error' class when age_error is truthy
                        cls="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent error:border-red-500 error:focus:ring-red-500",
                        required=True,
                        min="1",
                        max="120",
                    ),
                    Span(data_text=age_error, data_show=age_error, cls="text-red-500 text-xs mt-1 block"),
                    cls="mb-6",
                ),
                # Phone field (optional)
                Div(
                    Label(
                        "Phone Number",
                        Span(" (optional)", cls="text-gray-400 text-xs"),
                        For="phone_input",
                        cls="block text-sm font-medium text-gray-700 mb-1",
                    ),
                    Input(
                        type="tel",
                        placeholder="(555) 123-4567",
                        id="phone_input",
                        name="phone",
                        data_bind=phone,
                        # Optional field - only validate if provided (regex for phone format)
                        data_on_input=phone_error.set(
                            js(
                                "$phone && !/^[\\+]?[\\d\\s\\-\\(\\)]+$/.test($phone) ? 'Please enter a valid phone number' : ''"
                            )
                        ),
                        data_class_error=phone_error,  # Adds 'error' class when phone_error is truthy
                        cls="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent error:border-red-500 error:focus:ring-red-500",
                    ),
                    Span(data_text=phone_error, data_show=phone_error, cls="text-red-500 text-xs mt-1 block"),
                    cls="mb-6",
                ),
                # Form status
                Div(
                    Span(
                        # Using switch for clearer priority order
                        data_text=switch(
                            [(submitted, "✓ Form has been submitted"), (is_valid, "✓ Form is ready to submit")],
                            default="Please complete all required fields",
                        )  # JS: data_text="$submitted ? 'Form has been submitted' : $is_valid ? 'Form is ready to submit' : 'Please complete all required fields'"
                    ),
                    data_class_valid=is_valid,  # JS: data_class_valid="$is_valid"
                    cls="px-4 py-3 rounded-md text-sm mb-6 bg-gray-50 text-gray-600 valid:bg-green-50 valid:text-green-700 valid:border valid:border-green-200",
                ),
                # Submit buttons
                Div(
                    Button(
                        "Submit Form",
                        data_attr_disabled=~is_valid | submitting,  # JS: data-attr-disabled="!$is_valid || $submitting"
                        type="submit",
                        cls="px-6 py-2 bg-black text-white rounded-md hover:bg-gray-800 transition-colors disabled:opacity-40 disabled:cursor-not-allowed mr-3",
                    ),
                    Button(
                        "Clear Form",
                        data_on_click=clear_form_signals(
                            name, email, age, phone, name_error, email_error, age_error, phone_error, submitted=False
                        ),
                        type="button",
                        cls="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors",
                    ),
                    cls="pt-6 border-t border-gray-200",
                ),
                # Form submission with prevent modifier using .with_()
                data_on_submit=(is_valid & ~submitting).then(post("submit")).with_(prevent=True),
                action="submit",  # Use relative path
                method="post",
            ),
            cls="bg-white p-8 rounded-lg border border-gray-200",
        ),
        # Success Message
        Div(
            "✅ Success! Your information has been submitted.",
            data_show=submitted,  # JS: data_show="$submitted"
            cls="px-4 py-3 bg-green-50 border border-green-200 text-green-700 rounded-md my-6",
        ),
        # Live Preview
        Div(
            H3("Live Preview", cls="text-lg font-medium mb-4 text-gray-700"),
            Div(
                P(
                    Span("Name:", cls="text-gray-500 text-sm"),
                    " ",
                    Span(data_text=name | value("Not provided"), cls="text-gray-900 text-sm font-medium"),
                    cls="py-2 border-b border-gray-100",
                ),  # JS: data_text="$name || 'Not provided'"
                P(
                    Span("Email:", cls="text-gray-500 text-sm"),
                    " ",
                    Span(data_text=email | value("Not provided"), cls="text-gray-900 text-sm font-medium"),
                    cls="py-2 border-b border-gray-100",
                ),  # JS: data_text="$email || 'Not provided'"
                P(
                    Span("Age:", cls="text-gray-500 text-sm"),
                    " ",
                    Span(data_text=age | value("Not provided"), cls="text-gray-900 text-sm font-medium"),
                    cls="py-2 border-b border-gray-100",
                ),  # JS: data_text="$age || 'Not provided'"
                P(
                    Span("Phone:", cls="text-gray-500 text-sm"),
                    " ",
                    Span(data_text=phone | value("Not provided"), cls="text-gray-900 text-sm font-medium"),
                    cls="py-2",
                ),  # JS: data_text="$phone || 'Not provided'"
            ),
            cls="bg-gray-50 p-6 rounded-lg mt-6",
        ),
        cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen",
    )


@rt("/submit")
@sse
def submit_form(req, name: str = "", email: str = "", age: str = "", phone: str = ""):
    """Handle form submission with SSE and server-side validation"""
    import re
    import time

    print(f"SSE /submit: Form submission received - Name: {name}, Email: {email}")
    yield signals(submitting=True)

    time.sleep(0.5)  # Simulate processing

    # Server-side validation
    errors = {}

    if not name or len(name) < 2:
        errors["name_error"] = "Name must be at least 2 characters"

    if not email:
        errors["email_error"] = "Email is required"
    elif not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        errors["email_error"] = "Please enter a valid email"

    if not age:
        errors["age_error"] = "Age is required"
    else:
        try:
            age_num = int(age)
            if age_num < 18 or age_num > 120:
                errors["age_error"] = "Age must be between 18 and 120"
        except ValueError:
            errors["age_error"] = "Age must be a number"

    if phone and not re.match(r"^[\+]?[\d\s\-\(\)]+$", phone):
        errors["phone_error"] = "Please enter a valid phone number"

    if errors:
        # Send validation errors back
        yield signals(submitting=False, **errors)
        print(f"SSE /submit: Validation failed - {errors}")
    else:
        # Success - clear form and mark as submitted
        # Note: For SSE, we still need to send the actual values, not Signal.set() expressions
        yield signals(
            submitting=False,
            submitted=True,
            name="",
            email="",
            age="",
            phone="",
            name_error="",
            email_error="",
            age_error="",
            phone_error="",
        )
        print("SSE /submit: Form submission complete")


if __name__ == "__main__":
    print("Forms and Binding Demo")
    print("=" * 30)
    print("🚀 Running on http://localhost:5001")
    print("✨ Features:")
    print("   - New Signal API with type safety")
    print("   - Reactive validation")
    print("   - Live preview")
    print("   - Form state management")
    serve(port=5001)
