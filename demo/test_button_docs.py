#!/usr/bin/env python3
"""Test script to verify the Button documentation page works correctly."""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_imports():
    """Test that all required components can be imported."""
    print("🧪 Testing imports...")

    try:
        from components.docs import ComponentDocPage

        print("✅ ComponentDocPage import successful")
    except Exception as e:
        print(f"❌ ComponentDocPage import failed: {e}")
        return False

    try:
        from components.ui.button import Button

        print("✅ Button component import successful")
    except Exception as e:
        print(f"❌ Button component import failed: {e}")
        return False

    try:
        from components.ui.iconify import Icon

        print("✅ Icon component import successful")
    except Exception as e:
        print(f"❌ Icon component import failed: {e}")
        return False

    return True


def test_button_examples():
    """Test that button examples can be created."""
    print("\n🧪 Testing button examples...")

    try:
        from components.ui.button import Button
        from components.ui.iconify import Icon

        # Test basic button
        basic_button = Button("Test Button")
        print("✅ Basic button created")

        # Test button with variant
        outline_button = Button("Outline", variant="outline")
        print("✅ Outline button created")

        # Test button with icon
        icon_button = Button(Icon("lucide:home", cls="h-4 w-4"), "Home", variant="secondary")
        print("✅ Button with icon created")

        return True
    except Exception as e:
        print(f"❌ Button example creation failed: {e}")
        return False


def test_page_generation():
    """Test that the documentation page can be generated."""
    print("\n🧪 Testing page generation...")

    try:
        from demo.docs_button_page import button_docs_page

        page = button_docs_page()
        print("✅ Button documentation page generated successfully")
        print(f"📄 Page type: {type(page)}")

        # Convert to string to test HTML generation
        html_str = str(page)
        if len(html_str) > 1000:  # Should be a substantial page
            print(f"✅ Generated HTML has {len(html_str)} characters")
        else:
            print(f"⚠️  Generated HTML seems short: {len(html_str)} characters")

        # Check for key elements
        if "Button" in html_str:
            print("✅ Page contains Button title")
        if "Displays a button" in html_str:
            print("✅ Page contains description")
        if "Installation" in html_str:
            print("✅ Page contains installation section")

        return True
    except Exception as e:
        print(f"❌ Page generation failed: {e}")
        return False


def test_app_creation():
    """Test that the Starlette app can be created."""
    print("\n🧪 Testing app creation...")

    try:
        from demo.docs_button_page import create_app

        app = create_app()
        print("✅ Starlette app created successfully")
        print(f"📱 App type: {type(app)}")

        # Check routes
        routes = app.routes
        print(f"✅ App has {len(routes)} routes configured")

        return True
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Testing Button Documentation Implementation")
    print("=" * 50)

    tests = [test_imports, test_button_examples, test_page_generation, test_app_creation]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The Button documentation is ready to use.")
        print("\n🚀 To start the server, run:")
        print("   uv run demo/docs_button_page.py")
        print("\n🌐 Then visit: http://localhost:8000")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
