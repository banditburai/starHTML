"""Improved Forms and Binding Demo - Native form handling with Datastar validation"""

from starhtml import *

app, rt = star_app(
    title="Forms and Binding Demo (Improved)",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            .form-input { transition: border-color 0.2s; }
            .form-input.error { border-color: #ef4444; }
            .error-text { color: #ef4444; font-size: 0.75rem; margin-top: 0.25rem; }
            .form-status { padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; text-align: center; font-weight: 500; }
            .form-status.valid { background: #ecfdf5; color: #047857; border: 1px solid #10b981; }
            .form-status.invalid { background: #fef2f2; color: #dc2626; border: 1px solid #ef4444; }
            .required { color: #ef4444; }
        """),
    ],
)


def create_form_field(label_text, input_type, placeholder, signal_name, validation_expr, required=True):
    """Create a standardized form field with validation"""
    input_id = f"{signal_name}_input"
    error_signal = f"{signal_name}error"

    label = Label(label_text, {"for": input_id})

    required_indicator = Span(
        " *" if required else " (optional)", cls="required" if required else "text-gray-500 text-sm"
    )

    input_attrs = {
        "type": input_type,
        "placeholder": placeholder,
        "id": input_id,
        "name": signal_name,  # Add name for native form handling
        "cls": "form-input w-full p-3 border rounded-lg mt-1",
    }

    if required:
        input_attrs["required"] = True

    if input_type == "number":
        input_attrs["min"] = "18"
        input_attrs["max"] = "120"

    input_elem = Input(
        ds_bind(signal_name),
        ds_on_input(validation_expr),
        ds_class(error=if_(f"${error_signal}", True, False)),
        **input_attrs,
    )

    error_text = Span(ds_text(f"${error_signal}"), ds_show(f"${error_signal}"), cls="error-text")

    return Div(label, required_indicator, input_elem, error_text, cls="mb-4")


def create_name_field():
    return create_form_field(
        "Full Name",
        "text",
        "Enter your full name",
        "name",
        "name_error = $name.length < 2 ? 'Name must be at least 2 characters' : ''",
    )


def create_email_field():
    return create_form_field(
        "Email Address",
        "email",
        "Enter your email",
        "email",
        "email_error = !$email ? 'Email is required' : !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test($email) ? 'Please enter a valid email' : ''",
    )


def create_age_field():
    return create_form_field(
        "Age",
        "number",
        "Enter your age",
        "age",
        "age_error = !$age ? 'Age is required' : $age < 18 || $age > 120 ? 'Age must be between 18 and 120' : ''",
    )


def create_phone_field():
    return create_form_field(
        "Phone Number",
        "tel",
        "(555) 123-4567",
        "phone",
        "phone_error = $phone && !/^[\\+]?[\\d\\s\\-\\(\\)]{10,}$/.test($phone) ? 'Please enter a valid phone number' : ''",
        required=False,
    )


def create_form_status():
    return Div(
        Span("📝 "),
        Span(
            ds_text(
                "$submitted ? 'Form has been submitted' : $is_valid ? 'Form is ready to submit' : 'Please complete all required fields'"
            )
        ),
        ds_class(valid="$is_valid"),
        cls="form-status",
    )


def create_live_preview():
    return Div(
        H3("Live Preview", cls="text-lg font-semibold mb-4"),
        Div(
            P("Name: ", Span(ds_text("$name || 'Not provided'")), cls="py-2"),
            P("Email: ", Span(ds_text("$email || 'Not provided'")), cls="py-2"),
            P("Age: ", Span(ds_text("$age || 'Not provided'")), cls="py-2"),
            P("Phone: ", Span(ds_text("$phone || 'Not provided'")), cls="py-2"),
        ),
        cls="bg-white p-6 rounded-lg shadow mb-6",
    )


def create_debug_panel():
    return Div(
        H3("Debug Info", cls="text-lg font-semibold mb-4"),
        Pre(ds_json_signals(), cls="bg-gray-100 p-3 rounded text-sm overflow-auto"),
        cls="bg-white p-6 rounded-lg shadow",
    )


def get_initial_signals():
    return {
        "name": "",
        "email": "",
        "age": "",
        "phone": "",
        "name_error": "",
        "email_error": "",
        "age_error": "",
        "phone_error": "",
        "submitting": False,
        "submitted": False,
    }


@rt("/")
def home():
    return Div(
        H1("Forms and Binding Demo (Improved)", cls="text-3xl font-bold mb-6 text-center"),
        P("Native form handling with Datastar validation", cls="text-gray-600 mb-8 text-center"),
        # Main Form
        Div(
            H2("Contact Information", cls="text-xl font-semibold mb-4"),
            Form(
                create_name_field(),
                create_email_field(),
                create_age_field(),
                create_phone_field(),
                create_form_status(),
                # Submit buttons
                Div(
                    Button(
                        "Submit Form",
                        ds_disabled("!$is_valid || $submitting"),
                        type="submit",
                        cls="bg-blue-600 text-white px-6 py-3 rounded-lg mr-3 disabled:opacity-50",
                    ),
                    Button(
                        "Clear Form",
                        ds_on_click(clear_form_signals(get_initial_signals())),
                        type="button",
                        cls="bg-gray-500 text-white px-6 py-3 rounded-lg",
                    ),
                    cls="border-t pt-6",
                ),
                # Proper form submission handling
                ds_on_submit(
                    """
                    if($is_valid && !$submitting) {
                        @post('/submit')
                    }
                """,
                    "prevent",
                ),
                action="/submit",
                method="post",
            ),
            cls="bg-white p-6 rounded-lg shadow mb-6",
        ),
        # Success Message
        Div(
            "✅ Success! Your information has been submitted.",
            ds_show("$submitted"),
            cls="bg-green-50 border border-green-200 text-green-800 p-4 rounded-lg mb-6",
        ),
        create_live_preview(),
        create_debug_panel(),
        # Initialize signals
        ds_signals(get_initial_signals()),
        # Computed signal for form validity - check both required fields AND no errors
        ds_computed(
            "is_valid", "$name && $email && $age && !$name_error && !$email_error && !$age_error && !$phone_error"
        ),
        cls="max-w-2xl mx-auto p-6",
    )


@rt("/submit")
@sse
def submit_form(req):
    import time

    print("SSE /submit: Form submission received")
    yield signals(submitting=True)

    time.sleep(0.5)  # Simulate processing

    yield signals(submitting=False, submitted=True)
    print("SSE /submit: Form submission complete")


if __name__ == "__main__":
    print("Improved Forms and Binding Demo")
    print("=" * 30)
    print("🚀 Running on http://localhost:5001")
    print("✨ Features:")
    print("   - Native HTML5 form validation")
    print("   - Datastar reactive validation")
    print("   - Validation runs on mount")
    print("   - Proper form submission handling")
    serve(port=5001)
