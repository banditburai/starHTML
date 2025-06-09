"""Demo showcasing Button component with exact shadcn-ui layout and styling."""

from starhtml import *
from components.ui import Button, ThemeToggle

app, rt = star_app(
    title="Button",
    live=True,
    hdrs=(
        Script(src="https://cdn.jsdelivr.net/npm/iconify-icon@2.3.0/dist/iconify-icon.min.js", type="module"),
        Link(rel="stylesheet", href="/components/styles/theme.css"),
    ),
    htmlkw=dict(lang="en", dir="ltr"),
    bodykw=dict(cls="min-h-screen bg-background text-foreground")
)

@rt('/')
def home():
    """Button page with exact shadcn-ui layout and styling."""
    return Div(
        # Include Tailwind CSS v4 Alpha
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        
        # Theme toggle in top right corner
        ThemeToggle(cls="fixed top-4 right-4 z-50"),
        
        # Main wrapper with exact shadcn layout
        Div(
            # Container wrapper - exact shadcn structure
            Div(
                # Container with proper max-width and padding  
                Div(
                    # Docs layout - simulating sidebar + main content layout
                    Div(
                        # Main content area (no actual sidebar for this demo)
                        Div(
                            # Page header with exact typography
                            Div(
                                H1("Button", cls="scroll-m-20 text-4xl font-bold tracking-tight lg:text-5xl"),
                                P("Displays a button or a component that looks like a button.", cls="leading-7 [&:not(:first-child)]:mt-6"),
                                cls="space-y-2"
                            ),
                            
                            # Main preview
                            Div(
                                # Tabs container (visual structure only)
                                Div(
                                    # Tab list container (visual placeholder)
                                    Div(
                                        Div(
                                            Span("Preview", cls="border-b-2 border-primary px-4 pb-3 pt-2 font-semibold text-primary"),
                                            cls="flex items-center justify-between pb-3"
                                        ),
                                        cls="w-full justify-start rounded-none border-b bg-transparent p-0"
                                    ),
                                    # Tab content
                                    Div(
                                        # Preview card with toolbar
                                        Div(
                                            # Toolbar (minimal for clean look)
                                            Div(
                                                cls="flex h-4 items-center justify-between p-4"
                                            ),
                                            # Preview area
                                            Div(
                                                Button("Button"),
                                                cls="preview flex min-h-[350px] w-full justify-center p-10 items-center"
                                            ),
                                            cls="relative rounded-md border"
                                        )
                                    ),
                                    cls="relative mr-auto w-full"
                                ),
                                cls="my-6"
                            ),
                            
                            # Examples section
                            H2("Examples", cls="mt-16 scroll-m-20 border-b pb-4 text-xl font-semibold tracking-tight first:mt-0"),
                            
                            # Default variant
                            H3("Default", cls="mt-8 scroll-m-20 text-lg font-semibold tracking-tight"),
                            Div(
                                Div(
                                    Div(cls="w-full justify-start rounded-none border-b bg-transparent p-0"),
                                    Div(
                                        Div(
                                            Div(cls="flex h-4 items-center justify-between p-4"),
                                            Div(
                                                Button("Button"),
                                                cls="preview flex min-h-[350px] w-full justify-center p-10 items-center"
                                            ),
                                            cls="relative rounded-md border"
                                        )
                                    ),
                                    cls="relative mr-auto w-full"
                                ),
                                cls="my-6"
                            ),
                            
                            # Secondary variant
                            H3("Secondary", cls="mt-8 scroll-m-20 text-lg font-semibold tracking-tight"),
                            Div(
                                Div(
                                    Div(cls="w-full justify-start rounded-none border-b bg-transparent p-0"),
                                    Div(
                                        Div(
                                            Div(cls="flex h-4 items-center justify-between p-4"),
                                            Div(
                                                Button("Secondary", variant="secondary"),
                                                cls="preview flex min-h-[350px] w-full justify-center p-10 items-center"
                                            ),
                                            cls="relative rounded-md border"
                                        )
                                    ),
                                    cls="relative mr-auto w-full"
                                ),
                                cls="my-6"
                            ),
                            
                            # Destructive variant
                            H3("Destructive", cls="mt-8 scroll-m-20 text-lg font-semibold tracking-tight"),
                            Div(
                                Div(
                                    Div(cls="w-full justify-start rounded-none border-b bg-transparent p-0"),
                                    Div(
                                        Div(
                                            Div(cls="flex h-4 items-center justify-between p-4"),
                                            Div(
                                                Button("Destructive", variant="destructive"),
                                                cls="preview flex min-h-[350px] w-full justify-center p-10 items-center"
                                            ),
                                            cls="relative rounded-md border"
                                        )
                                    ),
                                    cls="relative mr-auto w-full"
                                ),
                                cls="my-6"
                            ),
                            
                            # Outline variant
                            H3("Outline", cls="mt-8 scroll-m-20 text-lg font-semibold tracking-tight"),
                            Div(
                                Div(
                                    Div(cls="w-full justify-start rounded-none border-b bg-transparent p-0"),
                                    Div(
                                        Div(
                                            Div(cls="flex h-4 items-center justify-between p-4"),
                                            Div(
                                                Button("Outline", variant="outline"),
                                                cls="preview flex min-h-[350px] w-full justify-center p-10 items-center"
                                            ),
                                            cls="relative rounded-md border"
                                        )
                                    ),
                                    cls="relative mr-auto w-full"
                                ),
                                cls="my-6"
                            ),
                            
                            # Ghost variant
                            H3("Ghost", cls="mt-8 scroll-m-20 text-lg font-semibold tracking-tight"),
                            Div(
                                Div(
                                    Div(cls="w-full justify-start rounded-none border-b bg-transparent p-0"),
                                    Div(
                                        Div(
                                            Div(cls="flex h-4 items-center justify-between p-4"),
                                            Div(
                                                Button("Ghost", variant="ghost"),
                                                cls="preview flex min-h-[350px] w-full justify-center p-10 items-center"
                                            ),
                                            cls="relative rounded-md border"
                                        )
                                    ),
                                    cls="relative mr-auto w-full"
                                ),
                                cls="my-6"
                            ),
                            
                            # Link variant
                            H3("Link", cls="mt-8 scroll-m-20 text-lg font-semibold tracking-tight"),
                            Div(
                                Div(
                                    Div(cls="w-full justify-start rounded-none border-b bg-transparent p-0"),
                                    Div(
                                        Div(
                                            Div(cls="flex h-4 items-center justify-between p-4"),
                                            Div(
                                                Button("Link", variant="link"),
                                                cls="preview flex min-h-[350px] w-full justify-center p-10 items-center"
                                            ),
                                            cls="relative rounded-md border"
                                        )
                                    ),
                                    cls="relative mr-auto w-full"
                                ),
                                cls="my-6"
                            ),
                            
                            # Icon button
                            H3("Icon", cls="mt-8 scroll-m-20 text-lg font-semibold tracking-tight"),
                            Div(
                                Div(
                                    Div(cls="w-full justify-start rounded-none border-b bg-transparent p-0"),
                                    Div(
                                        Div(
                                            Div(cls="flex h-4 items-center justify-between p-4"),
                                            Div(
                                                Button(
                                                    Svg(
                                                        Path(d="m6 9 6 6 6-6", stroke_linecap="round", stroke_linejoin="round"),
                                                        cls="h-4 w-4", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2"
                                                    ),
                                                    size="icon",
                                                    variant="outline"
                                                ),
                                                cls="preview flex min-h-[350px] w-full justify-center p-10 items-center"
                                            ),
                                            cls="relative rounded-md border"
                                        )
                                    ),
                                    cls="relative mr-auto w-full"
                                ),
                                cls="my-6"
                            ),
                            
                            # Button with icon
                            H3("With Icon", cls="mt-8 scroll-m-20 text-lg font-semibold tracking-tight"),
                            Div(
                                Div(
                                    Div(cls="w-full justify-start rounded-none border-b bg-transparent p-0"),
                                    Div(
                                        Div(
                                            Div(cls="flex h-4 items-center justify-between p-4"),
                                            Div(
                                                Button(
                                                    Svg(
                                                        Path(d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9", stroke_linecap="round", stroke_linejoin="round"),
                                                        cls="mr-2 h-4 w-4", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2"
                                                    ),
                                                    "Login with Email"
                                                ),
                                                cls="preview flex min-h-[350px] w-full justify-center p-10 items-center"
                                            ),
                                            cls="relative rounded-md border"
                                        )
                                    ),
                                    cls="relative mr-auto w-full"
                                ),
                                cls="my-6"
                            ),
                            
                            # Loading state
                            H3("Loading", cls="mt-8 scroll-m-20 text-lg font-semibold tracking-tight"),
                            Div(
                                Div(
                                    Div(cls="w-full justify-start rounded-none border-b bg-transparent p-0"),
                                    Div(
                                        Div(
                                            Div(cls="flex h-4 items-center justify-between p-4"),
                                            Div(
                                                Button(
                                                    Svg(
                                                        Path(d="M21 12a9 9 0 11-6.219-8.56", stroke_linecap="round", stroke_linejoin="round"),
                                                        cls="mr-2 h-4 w-4 animate-spin", viewBox="0 0 24 24", fill="none", stroke="currentColor", stroke_width="2"
                                                    ),
                                                    "Please wait",
                                                    disabled=True
                                                ),
                                                cls="preview flex min-h-[350px] w-full justify-center p-10 items-center"
                                            ),
                                            cls="relative rounded-md border"
                                        )
                                    ),
                                    cls="relative mr-auto w-full"
                                ),
                                cls="my-6"
                            ),
                            
                            # Interactive example
                            H3("As Child", cls="mt-8 scroll-m-20 text-lg font-semibold tracking-tight"),
                            P(
                                "You can use StarHTML buttons with Datastar for reactivity.",
                                cls="leading-7 [&:not(:first-child)]:mt-6"
                            ),
                            Div(
                                Div(
                                    Div(cls="w-full justify-start rounded-none border-b bg-transparent p-0"),
                                    Div(
                                        Div(
                                            Div(cls="flex h-4 items-center justify-between p-4"),
                                            Div(
                                                Div(
                                                    Button(
                                                        "Click count: ",
                                                        Span(ds_text="$count"),
                                                        ds_on_click="$count++"
                                                    ),
                                                    ds_signals={"count": 0}
                                                ),
                                                cls="preview flex min-h-[350px] w-full justify-center p-10 items-center"
                                            ),
                                            cls="relative rounded-md border"
                                        )
                                    ),
                                    cls="relative mr-auto w-full"
                                ),
                                cls="my-6"
                            ),
                            
                            cls="mx-auto w-full min-w-0"
                        ),
                        cls="md:grid md:grid-cols-[minmax(0,1fr)] md:gap-6 lg:gap-10"
                    ),
                    cls="container px-4 xl:px-6 mx-auto max-w-screen-2xl"
                ),
                cls="max-w-[1400px] min-[1800px]:max-w-screen-2xl min-[1400px]:border-x border-border/70 dark:border-border mx-auto w-full border-dashed"
            ),
            cls="flex flex-1 flex-col"
        )
    )

if __name__ == "__main__":
    print("Button Component Demo running on http://localhost:5003")
    serve(port=5003)