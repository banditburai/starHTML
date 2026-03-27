"""Forms and Binding Demo - Signal.validate() + form_submit() API"""

from starhtml import *

app, rt = star_app(
    devtools=True,
    title="Forms and Binding Demo",
    htmlkw={"lang": "en"},
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body { background: #fff; color: #000; margin: 0; padding: 0;
                   -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }
            ::selection { background: #000; color: #fff; }
            .form-field-focus { transition: all 200ms ease; }
            .form-field-focus:focus-within label { color: #0ea5e9; }
        """),
    ],
)

# Phone regex: digits, spaces, dashes, parens, optional leading +
_PHONE_RE = r"^[\+]?[\d\s\-\(\)]+$"


def _age_rule(sig):
    return switch([(~sig, "Age is required"), ((sig < 18) | (sig > 120), "Age must be between 18 and 120")])


@rt("/")
def home():
    name = Signal("name", "")
    name_v = name.validate(min_length, 2, "Name")

    em = Signal("email", "")
    em_v = em.validate(email)

    age = Signal("age", "")
    age_v = age.validate(_age_rule)

    phone = Signal("phone", "")
    phone_v = phone.validate(pattern, _PHONE_RE, "Please enter a valid phone number", optional=True)

    submitted = Signal("contact_submitted", False)

    inp_cls = (
        "w-full px-3 py-2 border border-gray-300 rounded-md"
        " focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        " error:border-red-500 error:focus:ring-red-500"
    )
    err_cls = "text-red-500 text-xs mt-1 block"

    return Div(
        name,
        em,
        age,
        phone,
        submitted,
        # Header
        Div(
            H1("03", cls="text-8xl font-black text-gray-100 leading-none"),
            H1("Forms and Binding", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
            P("Signal.validate() + form_submit() API", cls="text-lg text-gray-600 mt-4"),
            cls="mb-16",
        ),
        # Form
        Div(
            H2("Contact Information", cls="text-2xl font-bold text-black mb-8"),
            Form(
                (fs := form_submit("submit", name, em, age, phone, name="contact", submitted=submitted)),
                # Name
                Div(
                    Label(
                        "Full Name",
                        Span(" *", cls="text-red-500"),
                        fr="name_input",
                        cls="block text-sm font-medium text-gray-700 mb-1",
                    ),
                    Input(
                        name_v,
                        type="text",
                        placeholder="Enter your full name",
                        id="name_input",
                        name="name",
                        cls=inp_cls,
                        required=True,
                    ),
                    Span(data_text=name.err, data_show=name.err, cls=err_cls),
                    cls="mb-6",
                ),
                # Email
                Div(
                    Label(
                        "Email Address",
                        Span(" *", cls="text-red-500"),
                        fr="email_input",
                        cls="block text-sm font-medium text-gray-700 mb-1",
                    ),
                    Input(
                        em_v,
                        type="email",
                        placeholder="Enter your email",
                        id="email_input",
                        name="email",
                        cls=inp_cls,
                        required=True,
                    ),
                    Span(data_text=em.err, data_show=em.err, cls=err_cls),
                    cls="mb-6",
                ),
                # Age
                Div(
                    Label(
                        "Age",
                        Span(" *", cls="text-red-500"),
                        fr="age_input",
                        cls="block text-sm font-medium text-gray-700 mb-1",
                    ),
                    Input(
                        age_v,
                        type="number",
                        placeholder="Enter your age",
                        id="age_input",
                        name="age",
                        cls=inp_cls,
                        required=True,
                        min="1",
                        max="120",
                    ),
                    Span(data_text=age.err, data_show=age.err, cls=err_cls),
                    cls="mb-6",
                ),
                # Phone (optional)
                Div(
                    Label(
                        "Phone Number",
                        Span(" (optional)", cls="text-gray-400 text-xs"),
                        fr="phone_input",
                        cls="block text-sm font-medium text-gray-700 mb-1",
                    ),
                    Input(
                        phone_v, type="tel", placeholder="(555) 123-4567", id="phone_input", name="phone", cls=inp_cls
                    ),
                    Span(data_text=phone.err, data_show=phone.err, cls=err_cls),
                    cls="mb-6",
                ),
                # Status
                Div(
                    Span(
                        data_text=switch(
                            [
                                (fs.submitted, "✓ Form has been submitted"),
                                (
                                    ~any_(name.err, em.err, age.err, phone.err) & name & em & age,
                                    "✓ Form is ready to submit",
                                ),
                            ],
                            default="Please complete all required fields",
                        )
                    ),
                    cls="px-4 py-3 rounded-md text-sm mb-6 bg-gray-50 text-gray-600",
                ),
                # Buttons
                Div(
                    Button(
                        data_text=fs.submitting.if_("Submitting...", "Submit Form"),
                        data_attr_disabled=fs.submitting,
                        type="submit",
                        cls="px-6 py-2 bg-black text-white rounded-md hover:bg-gray-800 transition-colors"
                        " disabled:opacity-40 disabled:cursor-not-allowed mr-3",
                    ),
                    Button(
                        "Clear Form",
                        type="button",
                        data_on_click=form_reset(name, em, age, phone, fs.submitted),
                        cls="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors",
                    ),
                    cls="pt-6 border-t border-gray-200",
                ),
            ),
            cls="bg-white p-8 rounded-lg border border-gray-200",
        ),
        # Success message
        Div(
            "✅ Success! Your information has been submitted.",
            data_show=submitted,
            cls="px-4 py-3 bg-green-50 border border-green-200 text-green-700 rounded-md my-6",
        ),
        # Live Preview
        Div(
            H3("Live Preview", cls="text-lg font-medium mb-4 text-gray-700"),
            Div(
                *(
                    P(
                        Span(f"{label}:", cls="text-gray-500 text-sm"),
                        " ",
                        Span(data_text=sig | expr("Not provided"), cls="text-gray-900 text-sm font-medium"),
                        cls=f"py-2{' border-b border-gray-100' if i < 3 else ''}",
                    )
                    for i, (label, sig) in enumerate([("Name", name), ("Email", em), ("Age", age), ("Phone", phone)])
                )
            ),
            cls="bg-gray-50 p-6 rounded-lg mt-6",
        ),
        cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen",
    )


@rt("/submit", methods=["POST"])
@sse
async def submit_form(req, name: str = "", email: str = "", age: str = "", phone: str = ""):
    import asyncio
    import re

    yield signals(contact_submitting=True)
    await asyncio.sleep(0.5)

    errors = {}
    if not name or len(name) < 2:
        errors["name_err"] = "Name must be at least 2 characters"
    if not email:
        errors["email_err"] = "Email is required"
    elif not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        errors["email_err"] = "Please enter a valid email"
    if not age:
        errors["age_err"] = "Age is required"
    else:
        try:
            age_num = int(age)
            if age_num < 18 or age_num > 120:
                errors["age_err"] = "Age must be between 18 and 120"
        except ValueError:
            errors["age_err"] = "Age must be a number"
    if phone and not re.match(r"^[\+]?[\d\s\-\(\)]+$", phone):
        errors["phone_err"] = "Please enter a valid phone number"

    if errors:
        yield signals(contact_submitting=False, **errors)
    else:
        yield signals(
            contact_submitting=False,
            contact_submitted=True,
            name="",
            email="",
            age="",
            phone="",
            name_err="",
            email_err="",
            age_err="",
            phone_err="",
        )
        await asyncio.sleep(3)
        yield signals(contact_submitted=False)


if __name__ == "__main__":
    print("Forms and Binding Demo")
    print("=" * 30)
    print("Running on http://localhost:5001")
    serve(port=5001)
