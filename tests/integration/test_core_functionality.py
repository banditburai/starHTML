"""Integration tests for core StarHTML functionality."""

import io

from starlette.datastructures import UploadFile
from starlette.testclient import TestClient

from starhtml import *
from starhtml.datastar import (
    ds_bind,
    ds_class,
    ds_on_blur,
    ds_on_click,
    ds_on_input,
    ds_on_submit,
    ds_show,
    ds_signals,
    ds_text,
)
from starhtml.realtime import elements, format_element_event, format_signal_event, signals
from starhtml.server import JSONResponse


class TestDatastarIntegrationScenarios:
    """Test realistic usage scenarios combining multiple Datastar features."""

    def test_reactive_form_scenario(self):
        """Test a complete reactive form with multiple Datastar features."""
        form = Form(
            Div(
                Input(
                    ds_bind("user.name"),
                    ds_on_input("validateName()", debounce="300ms"),
                    type="text",
                    placeholder="Full Name",
                ),
                Div("Name is required", ds_show("$errors.name"), style="color: red"),
            ),
            Div(
                Input(ds_bind("user.email"), ds_on_blur("validateEmail()"), type="email", placeholder="Email"),
                Div(ds_text("$errors.email"), ds_show("$errors.email"), style="color: red"),
            ),
            Button("Submit", ds_on_click("submitForm()"), ds_show("$isFormValid"), type="submit"),
            ds_on_submit("handleSubmit(event)"),
        )

        html = str(form)

        # Test that form has the expected structure and functionality
        # Check for form element
        assert html.startswith("<form")
        assert html.endswith("</form>")

        # Verify inputs are present and properly configured
        assert 'type="text"' in html
        assert 'type="email"' in html
        assert 'placeholder="Full Name"' in html
        assert 'placeholder="Email"' in html

        # Verify Datastar attributes are correctly transformed
        # These test the actual attribute conversion, not specific string formatting
        assert "data-bind=" in html
        assert "data-on-input" in html
        assert "data-show=" in html
        assert "data-text=" in html
        assert "data-on-click=" in html
        assert "data-on-submit=" in html

        # Test that error handling elements are present
        assert "color: red" in html  # Error styling

        # Verify button configuration
        assert 'type="submit"' in html

    def test_real_time_data_update_scenario(self):
        """Test real-time data updates using signals and elements."""
        # Create initial signals
        status_signal = signals(status="loading", progress=0, message="Initializing...")

        # Create progress update
        progress_signal = signals(progress=50, message="Processing data...")

        # Create content update
        content_element = elements(
            Div(
                H2("Processing Complete"),
                P("Data has been successfully processed."),
                Button("Continue", ds_on_click("nextStep()")),
            ),
            "#main-content",
            "inner",
        )

        # Verify signal formatting produces valid SSE format
        status_sse = format_signal_event(status_signal[1]["payload"])
        # Test SSE structure, not specific content
        assert status_sse.startswith("event: datastar-patch-signals")
        assert "data: signals" in status_sse
        assert status_sse.endswith("\n\n")

        progress_sse = format_signal_event(progress_signal[1]["payload"])
        assert progress_sse.startswith("event: datastar-patch-signals")
        assert "data: signals" in progress_sse
        assert progress_sse.endswith("\n\n")

        # Test that the JSON payload is valid
        import json

        data_line = [line for line in status_sse.split("\n") if line.startswith("data: signals ")][0]
        json_data = json.loads(data_line[len("data: signals ") :])
        assert isinstance(json_data, dict)
        assert "status" in json_data
        assert "message" in json_data

        # Verify element formatting produces valid SSE format
        content_sse = format_element_event(
            content_element[1][0],  # content
            content_element[1][1],  # selector
            content_element[1][2],  # mode
        )
        # Test SSE structure, not specific content formatting
        assert content_sse.startswith("event: datastar-patch-elements")
        assert "data: selector" in content_sse
        assert "data: mode" in content_sse
        assert "data: elements" in content_sse
        assert content_sse.endswith("\n\n")

        # Test that the HTML content is present in some form
        assert "Processing Complete" in content_sse  # Content should be preserved
        assert "nextStep" in content_sse  # Functionality should be preserved


class TestHTML5ElementsIntegration:
    """Test various HTML5 elements work correctly."""

    def test_basic_html_structure(self):
        """Test basic HTML document structure."""
        page = Html(
            Head(Title("Test Page"), Meta(charset="utf-8")),
            Body(H1("Welcome"), P("This is a test page"), Div("Content area", id="main")),
        )
        html = str(page)

        # Test document structure and functionality, not exact tag formatting
        assert html.startswith("<html")
        assert html.endswith("</html>")

        # Verify all major sections are present
        assert "<head" in html and "</head>" in html
        assert "<body" in html and "</body>" in html
        assert "<title" in html and "</title>" in html

        # Test that content is preserved
        assert "Test Page" in html
        assert "Welcome" in html
        assert "This is a test page" in html
        assert "Content area" in html

        # Verify important attributes are present
        assert "utf-8" in html
        assert 'id="main"' in html
        assert "<h1>Welcome</h1>" in html
        assert "<p>This is a test page</p>" in html
        assert 'id="main"' in html

    def test_semantic_html_elements(self):
        """Test semantic HTML5 elements."""
        page = Main(
            Header(Nav(A("Home", href="/"), A("About", href="/about"))),
            Section(Article(H2("Article Title"), P("Article content"))),
            Footer(P("© 2024 Test Site")),
        )
        html = str(page)
        assert "<main>" in html
        assert "<header>" in html
        assert "<nav>" in html
        assert "<section>" in html
        assert "<article>" in html
        assert "<footer>" in html
        assert 'href="/"' in html
        assert 'href="/about"' in html


class TestAttributeHandling:
    """Test attribute handling and edge cases."""

    def test_boolean_attributes(self):
        """Test boolean attribute handling."""
        input_elem = Input(type="checkbox", checked=True, disabled=False, required=True)
        html = str(input_elem)
        assert "checked" in html
        assert "required" in html
        # disabled=False should not appear
        assert "disabled" not in html

    def test_class_and_id_attributes(self):
        """Test class and id attribute handling."""
        element = Div("Content", id="main-content", cls="container primary")
        # Test element attributes directly
        assert element.get("id") == "main-content"
        assert element.get("class") == "container primary"
        assert element.children == ("Content",)
        assert element.tag == "div"

    def test_data_attributes(self):
        """Test custom data attributes."""
        element = Div("Content", data_value="123", data_name="test", data_active="true")
        html = str(element)
        assert 'data-value="123"' in html
        assert 'data-name="test"' in html
        assert 'data-active="true"' in html

    def test_style_attribute(self):
        """Test style attribute handling."""
        element = Div("Styled content", style="color: red; background: blue;")
        html = str(element)
        assert 'style="color: red; background: blue;"' in html

    def test_mixed_attributes(self):
        """Test mixing regular and Datastar attributes."""
        element = Div(
            "Mixed attributes",
            ds_show("$isVisible"),
            ds_on_click("handleClick()"),
            id="test",
            cls="test-class",
            style="color: blue;",
            data_custom="value",
        )
        # Test attributes directly
        assert element.get("id") == "test"
        assert element.get("class") == "test-class"
        assert element.get("style") == "color: blue;"
        assert element.get("data-show") == "$isVisible"
        assert element.get("data-on-click") == "handleClick()"
        assert element.get("data-custom") == "value"
        assert element.children == ("Mixed attributes",)


class TestNestedStructures:
    """Test complex nested HTML structures."""

    def test_deeply_nested_elements(self):
        """Test deeply nested element structures."""
        structure = Div(
            Header(
                H1("Site Title"),
                Nav(Ul(Li(A("Home", href="/")), Li(A("About", href="/about")), Li(A("Contact", href="/contact")))),
            ),
            Main(
                Section(
                    Article(
                        H2("Article Title"),
                        P("First paragraph"),
                        P("Second paragraph"),
                        Div(Button("Action", ds_on_click("doAction()")), Span("Status", ds_text("$status"))),
                    )
                )
            ),
            cls="page-wrapper",
        )

        html = str(structure)
        assert 'class="page-wrapper"' in html
        assert "<header>" in html
        assert "<h1>Site Title</h1>" in html
        assert "<nav>" in html
        assert "<ul>" in html
        assert 'href="/"' in html
        assert 'href="/about"' in html
        assert 'href="/contact"' in html
        assert "<main>" in html
        assert "<section>" in html
        assert "<article>" in html
        assert "<h2>Article Title</h2>" in html
        assert "<p>First paragraph</p>" in html
        assert "<p>Second paragraph</p>" in html
        assert 'data-on-click="doAction()"' in html
        assert 'data-text="$status"' in html

    def test_component_like_structure(self):
        """Test creating component-like structures."""

        def UserCard(name, email, avatar_url):
            return Div(
                Img(src=avatar_url, alt=f"{name}'s avatar", cls="avatar"),
                Div(
                    H3(name, cls="user-name"),
                    P(email, cls="user-email"),
                    Button(
                        "Follow", ds_on_click(f"followUser('{email}')"), ds_class(active=f"$isFollowing('{email}')")
                    ),
                    cls="user-info",
                ),
                ds_signals({"user": {"name": name, "email": email}}),
                cls="user-card",
            )

        card = UserCard("John Doe", "john@example.com", "/avatars/john.jpg")
        html = str(card)

        assert 'class="user-card"' in html
        assert 'class="avatar"' in html
        assert 'src="/avatars/john.jpg"' in html
        assert 'alt="John Doe\'s avatar"' in html
        assert 'class="user-name"' in html
        assert 'class="user-email"' in html
        assert "John Doe" in html
        assert "john@example.com" in html
        assert "data-on-click=\"followUser('john@example.com')\"" in html
        assert "data-class-active=\"$isFollowing('john@example.com')\"" in html
        assert "data-signals-user=" in html
        assert '"name": "John Doe"' in html
        assert '"email": "john@example.com"' in html


class TestIntegrationEdgeCases:
    """Test integration-specific edge cases that aren't covered in unit tests."""

    def test_complex_nested_form_validation(self):
        """Test complex nested forms with validation patterns."""
        form = Form(
            Div(Input(type="text", name="nested_input", required=True, pattern="[A-Za-z]+"), cls="input-group"),
            Select(
                Option("Please choose", value=""),
                Option("Valid option", value="valid"),
                name="nested_select",
                required=True,
            ),
            Button("Submit", type="submit"),
            method="post",
            novalidate=False,
        )
        html = str(form)
        assert "required" in html
        assert 'pattern="[A-Za-z]+"' in html
        assert 'method="post"' in html
        assert 'class="input-group"' in html


class TestComplexFormScenarios:
    """Test complex form validation and processing scenarios."""

    def test_dynamic_form_validation(self):
        """Test dynamic form validation with conditional fields."""
        app, rt = star_app()

        @rt("/validate-dynamic", methods=["POST"])
        async def validate_dynamic_form(request):
            form_data = await request.form()

            errors = []
            values = {}

            # Extract values
            user_type = form_data.get("user_type")
            name = form_data.get("name")
            email = form_data.get("email")
            company = form_data.get("company")
            personal_id = form_data.get("personal_id")

            values.update(
                {"user_type": user_type, "name": name, "email": email, "company": company, "personal_id": personal_id}
            )

            # Basic validation
            if not name or len(name.strip()) < 2:
                errors.append("Name must be at least 2 characters")

            if not email or "@" not in email:
                errors.append("Valid email required")

            # Conditional validation based on user type
            if user_type == "business":
                if not company or len(company.strip()) < 3:
                    errors.append("Company name required for business users")
            elif user_type == "individual":
                if not personal_id or len(personal_id.strip()) < 5:
                    errors.append("Personal ID required for individual users")
            else:
                errors.append("Invalid user type")

            # Cross-field validation
            if email and name:
                if email.lower().startswith(name.lower()[:3]):
                    # This is just an example business rule
                    pass  # Valid
                elif len(errors) == 0:  # Only add this error if no other errors
                    errors.append("Email should be related to the provided name")

            if errors:
                return JSONResponse({"success": False, "errors": errors, "values": values}, status_code=422)

            return {"success": True, "message": "Form validation passed", "values": values}

        client = TestClient(app)

        # Test various validation scenarios
        test_cases = [
            # Valid business user
            {
                "data": {
                    "user_type": "business",
                    "name": "John Doe",
                    "email": "john@company.com",
                    "company": "Acme Corp",
                },
                "should_pass": True,
            },
            # Valid individual user
            {
                "data": {
                    "user_type": "individual",
                    "name": "Jane Smith",
                    "email": "jane@email.com",
                    "personal_id": "ID12345",
                },
                "should_pass": True,
            },
            # Business user missing company
            {
                "data": {"user_type": "business", "name": "John Doe", "email": "john@company.com"},
                "should_pass": False,
                "expected_error": "Company name required",
            },
            # Individual user missing personal ID
            {
                "data": {"user_type": "individual", "name": "Jane Smith", "email": "jane@email.com"},
                "should_pass": False,
                "expected_error": "Personal ID required",
            },
            # Invalid email
            {
                "data": {
                    "user_type": "individual",
                    "name": "Jane Smith",
                    "email": "invalid-email",
                    "personal_id": "ID12345",
                },
                "should_pass": False,
                "expected_error": "Valid email required",
            },
        ]

        for test_case in test_cases:
            response = client.post("/validate-dynamic", data=test_case["data"])

            if test_case["should_pass"]:
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
            else:
                assert response.status_code == 422
                data = response.json()
                assert data["success"] is False
                if "expected_error" in test_case:
                    assert any(test_case["expected_error"] in error for error in data["errors"])

    def test_form_with_file_and_data_mixed(self):
        """Test form processing with mixed file uploads and regular data."""
        app, rt = star_app()

        @rt("/mixed-form", methods=["POST"])
        async def process_mixed_form(request):
            form_data = await request.form()

            result = {"text_fields": {}, "files": [], "total_files": 0, "total_text_fields": 0}

            for key, value in form_data.items():
                if isinstance(value, UploadFile):
                    file_content = await value.read()
                    result["files"].append(
                        {
                            "field_name": key,
                            "filename": value.filename,
                            "content_type": value.content_type,
                            "size": len(file_content),
                        }
                    )
                    result["total_files"] += 1
                else:
                    result["text_fields"][key] = str(value)
                    result["total_text_fields"] += 1

            return result

        client = TestClient(app)

        # Create mixed form data
        form_data = {"name": "Test User", "description": "This is a test description", "category": "documents"}

        files = [
            ("document1", ("doc1.txt", io.BytesIO(b"Document 1 content"), "text/plain")),
            ("document2", ("doc2.txt", io.BytesIO(b"Document 2 content"), "text/plain")),
            ("image", ("image.jpg", io.BytesIO(b"fake image data"), "image/jpeg")),
        ]

        response = client.post("/mixed-form", data=form_data, files=files)
        assert response.status_code == 200

        data = response.json()
        assert data["total_text_fields"] == 3
        assert data["total_files"] == 3
        assert data["text_fields"]["name"] == "Test User"
        assert data["text_fields"]["description"] == "This is a test description"
        assert data["text_fields"]["category"] == "documents"

        # Check file information
        file_names = [f["filename"] for f in data["files"]]
        assert "doc1.txt" in file_names
        assert "doc2.txt" in file_names
        assert "image.jpg" in file_names

    def test_form_array_field_processing(self):
        """Test processing forms with array fields (multiple values)."""
        app, rt = star_app()

        @rt("/array-form", methods=["POST"])
        async def process_array_form(request):
            form_data = await request.form()

            # Process array fields
            result = {"single_fields": {}, "array_fields": {}, "processed_arrays": {}}

            # Get all form keys
            all_keys = set()
            for key in form_data.keys():
                all_keys.add(key)

            for key in all_keys:
                values = form_data.getlist(key)

                if len(values) == 1:
                    result["single_fields"][key] = values[0]
                else:
                    result["array_fields"][key] = values

                    # Process array fields with special logic
                    if key == "tags":
                        # Remove empty tags and convert to lowercase
                        processed_tags = [tag.lower().strip() for tag in values if tag.strip()]
                        result["processed_arrays"]["tags"] = processed_tags
                    elif key == "numbers":
                        # Convert to integers, filter invalid
                        processed_numbers = []
                        for num_str in values:
                            try:
                                processed_numbers.append(int(num_str))
                            except ValueError:
                                pass  # Skip invalid numbers
                        result["processed_arrays"]["numbers"] = processed_numbers

            return result

        client = TestClient(app)

        # Create form data with arrays using URL-encoded form data
        import urllib.parse

        form_encoded = urllib.parse.urlencode(
            [
                ("title", "Test Article"),
                ("content", "This is the article content"),
                ("tags", "python"),
                ("tags", "web"),
                ("tags", "  FastHTML  "),
                ("tags", ""),
                ("numbers", "1"),
                ("numbers", "2"),
                ("numbers", "invalid"),
                ("numbers", "3"),
                ("single_field", "single_value"),
            ]
        )

        response = client.post(
            "/array-form", content=form_encoded, headers={"content-type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200

        data = response.json()

        # Check single fields
        assert data["single_fields"]["title"] == "Test Article"
        assert data["single_fields"]["content"] == "This is the article content"
        assert data["single_fields"]["single_field"] == "single_value"

        # Check array fields
        assert "tags" in data["array_fields"]
        assert "numbers" in data["array_fields"]
        assert len(data["array_fields"]["tags"]) == 4  # Including empty one
        assert len(data["array_fields"]["numbers"]) == 4  # Including invalid one

        # Check processed arrays
        assert data["processed_arrays"]["tags"] == ["python", "web", "fasthtml"]  # Cleaned and lowercased
        assert data["processed_arrays"]["numbers"] == [1, 2, 3]  # Invalid filtered out
