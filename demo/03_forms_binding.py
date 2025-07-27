"""Clean Forms and Binding Demo - Simple reactive forms with Datastar"""

from starhtml import *

app, rt = star_app(
    title="Forms and Binding Demo",
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
    error_signal = f"{signal_name}Error"

    label = Label(label_text, {"for": input_id})

    required_indicator = Span(
        " *" if required else " (optional)", cls="required" if required else "text-gray-500 text-sm"
    )

    input_attrs = {
        "type": input_type,
        "placeholder": placeholder,
        "id": input_id,
        "ds_bind": signal_name,
        "ds_on_input": validation_expr,
        "cls": "form-input w-full p-3 border rounded-lg mt-1",
        "ds_class": f"${error_signal} ? 'error' : ''",
    }

    if input_type == "number":
        input_attrs["min"] = "18"
        input_attrs["max"] = "120"

    input_elem = Input(**input_attrs)

    error_text = Span(ds_text=f"${error_signal}", cls="error-text", ds_show=f"${error_signal}")

    return Div(label, required_indicator, input_elem, error_text, cls="mb-4")


def create_name_field():
    return create_form_field(
        "Full Name",
        "text",
        "Enter your full name",
        "name",
        "$nameError = $name.length < 2 ? 'Name must be at least 2 characters' : ''",
    )


def create_email_field():
    return create_form_field(
        "Email Address",
        "email",
        "Enter your email",
        "email",
        "$emailError = !$email ? 'Email is required' : !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test($email) ? 'Please enter a valid email' : ''",
    )


def create_age_field():
    return create_form_field(
        "Age",
        "number",
        "Enter your age",
        "age",
        "$ageError = !$age ? 'Age is required' : $age < 18 || $age > 120 ? 'Age must be between 18 and 120' : ''",
    )


def create_phone_field():
    return create_form_field(
        "Phone Number",
        "tel",
        "(555) 123-4567",
        "phone",
        "$phoneError = $phone && !/^[\\+]?[\\d\\s\\-\\(\\)]{10,}$/.test($phone) ? 'Please enter a valid phone number' : ''",
        required=False,
    )


def create_form_status():
    return Div(
        Span("📝 "),
        Span(
            ds_text="$submitted ? 'Form has been submitted' : $is_valid ? 'Form is ready to submit' : 'Please complete all required fields'"
        ),
        cls="form-status",
        ds_class="$submitted ? 'valid' : $is_valid ? 'valid' : 'invalid'",
    )


def create_live_preview():
    return Div(
        H3("Live Preview", cls="text-lg font-semibold mb-4"),
        Div(
            P("Name: ", Span(ds_text="$name || 'Not provided'"), cls="py-2"),
            P("Email: ", Span(ds_text="$email || 'Not provided'"), cls="py-2"),
            P("Age: ", Span(ds_text="$age || 'Not provided'"), cls="py-2"),
            P("Phone: ", Span(ds_text="$phone || 'Not provided'"), cls="py-2"),
        ),
        cls="bg-white p-6 rounded-lg shadow mb-6",
    )


def create_debug_panel():
    return Div(
        H3("Debug Info", cls="text-lg font-semibold mb-4"),
        Pre(ds_json_signals=True, cls="bg-gray-100 p-3 rounded text-sm overflow-auto"),
        cls="bg-white p-6 rounded-lg shadow",
    )


def get_initial_signals():
    return {
        "name": "",
        "email": "",
        "age": "",
        "phone": "",
        "nameError": "",
        "emailError": "",
        "ageError": "",
        "phoneError": "",
        "submitting": False,
        "submitted": False,
        "is_valid": False,
    }


@rt("/")
def home():
    return Div(
        H1("Forms and Binding Demo", cls="text-3xl font-bold mb-6 text-center"),
        P("Reactive form validation with Datastar", cls="text-gray-600 mb-8 text-center"),
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
                        type="button",
                        ds_on_click="@post('/submit')",
                        ds_disabled="!$is_valid || $submitting",
                        cls="bg-blue-600 text-white px-6 py-3 rounded-lg mr-3 disabled:opacity-50",
                    ),
                    Button(
                        "Clear Form",
                        type="button",
                        ds_on_click="$name = ''; $email = ''; $age = ''; $phone = ''; $nameError = ''; $emailError = ''; $ageError = ''; $phoneError = ''; $submitted = false",
                        cls="bg-gray-500 text-white px-6 py-3 rounded-lg",
                    ),
                    cls="border-t pt-6",
                ),
                ds_on_submit="event.preventDefault()",
            ),
            cls="bg-white p-6 rounded-lg shadow mb-6",
        ),
        # Success Message
        Div(
            "✅ Success! Your information has been submitted.",
            cls="bg-green-50 border border-green-200 text-green-800 p-4 rounded-lg mb-6",
            ds_show="$submitted",
        ),
        create_live_preview(),
        create_debug_panel(),
        cls="max-w-2xl mx-auto p-6",
        ds_signals=get_initial_signals(),
        ds_computed_is_valid="!$nameError && !$emailError && !$ageError && !$phoneError && $name && $email && $age",
    )


@rt("/submit")
@sse
def submit_form(req):
    import time

    print("SSE /submit: Starting")
    yield signals(submitting=True)
    print("SSE /submit: Sent submitting=True")

    time.sleep(0.5)  # Simulate processing

    print("SSE /submit: About to send submitted=True")
    yield signals(submitting=False, submitted=True)
    print("SSE /submit: Sent submitted=True - DONE")


if __name__ == "__main__":
    print("Forms and Binding Demo")
    print("=" * 30)
    print("🚀 Running on http://localhost:5001")
    print("✨ Features:")
    print("   - Real-time form validation")
    print("   - Two-way data binding")
    print("   - Live preview")
    print("   - Clean reactive patterns")
    serve(port=5001)
