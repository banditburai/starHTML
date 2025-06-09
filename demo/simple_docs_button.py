"""Simple Button documentation page following StarHTML patterns."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from starhtml import *
from components.ui import Button, ThemeToggle

app, rt = star_app(title="Button - shadcn/ui")


@rt("/")
def home():
    return Div(
        # Theme toggle
        ThemeToggle(cls="fixed top-4 right-4 z-50"),
        # Main content
        Div(
            # Header
            Div(
                H1("Button", cls="scroll-m-20 text-4xl font-bold tracking-tight lg:text-5xl"),
                P(
                    "Displays a button or a component that looks like a button.",
                    cls="leading-7 [&:not(:first-child)]:mt-6",
                ),
                cls="space-y-2",
            ),
            # Preview
            Div(
                H2("Preview", cls="font-heading mt-12 scroll-m-20 border-b pb-2 text-2xl font-semibold tracking-tight"),
                Div(
                    Div(Button("Button"), cls="flex min-h-[350px] items-center justify-center p-6"),
                    cls="relative rounded-lg border bg-card text-card-foreground shadow-sm",
                ),
                cls="mt-6",
            ),
            # Installation
            Div(
                H2(
                    "Installation",
                    cls="font-heading mt-12 scroll-m-20 border-b pb-2 text-2xl font-semibold tracking-tight",
                ),
                Div(
                    Pre(
                        Code("npx shadcn-ui@latest add button", cls="text-sm"),
                        cls="mb-4 mt-6 overflow-x-auto rounded-lg border bg-muted px-6 py-4",
                    ),
                    cls="mt-6",
                ),
                cls="mt-8",
            ),
            # Examples
            Div(
                H2(
                    "Examples", cls="font-heading mt-12 scroll-m-20 border-b pb-2 text-2xl font-semibold tracking-tight"
                ),
                # Default
                Div(
                    H3("Default", cls="font-heading mt-8 scroll-m-20 text-xl font-semibold tracking-tight"),
                    Div(
                        Div(Button("Button"), cls="flex min-h-[200px] items-center justify-center p-6"),
                        cls="relative rounded-lg border bg-card text-card-foreground shadow-sm",
                    ),
                    cls="mt-6",
                ),
                # Secondary
                Div(
                    H3("Secondary", cls="font-heading mt-8 scroll-m-20 text-xl font-semibold tracking-tight"),
                    Div(
                        Div(
                            Button("Secondary", variant="secondary"),
                            cls="flex min-h-[200px] items-center justify-center p-6",
                        ),
                        cls="relative rounded-lg border bg-card text-card-foreground shadow-sm",
                    ),
                    cls="mt-6",
                ),
                # Destructive
                Div(
                    H3("Destructive", cls="font-heading mt-8 scroll-m-20 text-xl font-semibold tracking-tight"),
                    Div(
                        Div(
                            Button("Destructive", variant="destructive"),
                            cls="flex min-h-[200px] items-center justify-center p-6",
                        ),
                        cls="relative rounded-lg border bg-card text-card-foreground shadow-sm",
                    ),
                    cls="mt-6",
                ),
                # Outline
                Div(
                    H3("Outline", cls="font-heading mt-8 scroll-m-20 text-xl font-semibold tracking-tight"),
                    Div(
                        Div(
                            Button("Outline", variant="outline"),
                            cls="flex min-h-[200px] items-center justify-center p-6",
                        ),
                        cls="relative rounded-lg border bg-card text-card-foreground shadow-sm",
                    ),
                    cls="mt-6",
                ),
                # Ghost
                Div(
                    H3("Ghost", cls="font-heading mt-8 scroll-m-20 text-xl font-semibold tracking-tight"),
                    Div(
                        Div(Button("Ghost", variant="ghost"), cls="flex min-h-[200px] items-center justify-center p-6"),
                        cls="relative rounded-lg border bg-card text-card-foreground shadow-sm",
                    ),
                    cls="mt-6",
                ),
                # Link
                Div(
                    H3("Link", cls="font-heading mt-8 scroll-m-20 text-xl font-semibold tracking-tight"),
                    Div(
                        Div(Button("Link", variant="link"), cls="flex min-h-[200px] items-center justify-center p-6"),
                        cls="relative rounded-lg border bg-card text-card-foreground shadow-sm",
                    ),
                    cls="mt-6",
                ),
                cls="mt-8",
            ),
            cls="container mx-auto px-4 py-6 lg:py-10 max-w-5xl",
        ),
        # Include theme CSS
        Link(rel="stylesheet", href="/components/styles/theme.css"),
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Script(src="https://cdn.jsdelivr.net/npm/iconify-icon@2.3.0/dist/iconify-icon.min.js", type="module"),
    )


if __name__ == "__main__":
    print("Simple Button Docs running on http://localhost:5007")
    serve(port=5007)
