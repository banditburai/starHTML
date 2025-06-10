"""Demo showcasing the docs layout components."""

from components.docs import DocsLayout
from components.ui import Button

from starhtml import *

app, rt = star_app(title="Docs Layout Demo", live=True)


@rt("/")
def docs_demo():
    """Create a demo page using the docs layout."""
    return DocsLayout(
        # Page content
        Div(
            H2("Button Component", cls="scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight first:mt-0"),
            P("Displays a button or a component that looks like a button.", cls="leading-7 [&:not(:first-child)]:mt-6"),
            # Installation section
            H3("Installation", cls="scroll-m-20 text-2xl font-semibold tracking-tight mt-8 mb-4"),
            Div(
                Pre(
                    Code("npx shadcn-ui@latest add button", cls="language-bash"),
                    cls="overflow-x-auto rounded-lg border bg-muted p-4",
                ),
                cls="mb-6",
            ),
            # Usage section
            H3("Usage", cls="scroll-m-20 text-2xl font-semibold tracking-tight mt-8 mb-4"),
            Div(
                Pre(
                    Code(
                        """import { Button } from "@/components/ui/button"

export function ButtonDemo() {
  return <Button>Click me</Button>
}""",
                        cls="language-tsx",
                    ),
                    cls="overflow-x-auto rounded-lg border bg-muted p-4",
                ),
                cls="mb-6",
            ),
            # Examples section
            H3("Examples", cls="scroll-m-20 text-2xl font-semibold tracking-tight mt-8 mb-4"),
            Div(
                H4("Default", cls="scroll-m-20 text-xl font-semibold tracking-tight mb-4"),
                Div(Button("Default"), cls="flex items-center justify-center p-6 border rounded-lg bg-background"),
                H4("Variants", cls="scroll-m-20 text-xl font-semibold tracking-tight mt-6 mb-4"),
                Div(
                    Button("Default", variant="default", cls="mr-2"),
                    Button("Secondary", variant="secondary", cls="mr-2"),
                    Button("Destructive", variant="destructive", cls="mr-2"),
                    Button("Outline", variant="outline", cls="mr-2"),
                    Button("Ghost", variant="ghost", cls="mr-2"),
                    Button("Link", variant="link"),
                    cls="flex flex-wrap items-center gap-2 p-6 border rounded-lg bg-background",
                ),
                cls="space-y-6",
            ),
            cls="max-w-4xl",
        ),
        # Page configuration
        title="Button",
        description="Displays a button or a component that looks like a button.",
        breadcrumb_items=[
            {"label": "Docs", "href": "/docs"},
            {"label": "Components", "href": "/docs/components"},
            {"label": "Button", "active": True},
        ],
    )


if __name__ == "__main__":
    print("Docs Layout Demo running on http://localhost:5004")
    serve(port=5004)
