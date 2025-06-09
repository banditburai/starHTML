"""Complete example showing all docs layout components in action."""

from starhtml import *
from components.docs import DocsLayout, DocsHeader, DocsSidebar, DocsBreadcrumb, DocsFooter
from components.ui import Button, ThemeToggle
from components.ui.iconify import IconifyIcon

app, rt = star_app(
    title="Complete Docs Example",
    live=True
)

# Custom navigation items for this example
CUSTOM_NAV_ITEMS = [
    {"href": "/docs", "label": "Docs"},
    {"href": "/docs/components", "label": "Components", "active": True},
    {"href": "/blocks", "label": "Blocks"},
    {"href": "/examples", "label": "Examples"},
]

# Custom sidebar sections for component documentation
COMPONENT_SIDEBAR_SECTIONS = [
    {
        "title": "Getting Started",
        "collapsible": True,
        "default_open": True,
        "items": [
            {"href": "/docs", "label": "Introduction"},
            {"href": "/docs/installation", "label": "Installation"},
            {"href": "/docs/components-json", "label": "components.json"},
            {"href": "/docs/theming", "label": "Theming"},
            {"href": "/docs/cli", "label": "CLI"},
        ]
    },
    {
        "title": "Layout Components",
        "collapsible": True,
        "default_open": True,
        "items": [
            {"href": "/docs/components/header", "label": "Header"},
            {"href": "/docs/components/sidebar", "label": "Sidebar"},
            {"href": "/docs/components/breadcrumb", "label": "Breadcrumb"},
            {"href": "/docs/components/footer", "label": "Footer"},
            {"href": "/docs/components/layout", "label": "Layout"},
        ]
    },
    {
        "title": "UI Components",
        "collapsible": True,
        "default_open": True,
        "items": [
            {"href": "/docs/components/button", "label": "Button", "active": True},
            {"href": "/docs/components/card", "label": "Card"},
            {"href": "/docs/components/input", "label": "Input"},
            {"href": "/docs/components/select", "label": "Select"},
            {"href": "/docs/components/dialog", "label": "Dialog"},
            {"href": "/docs/components/popover", "label": "Popover"},
            {"href": "/docs/components/tooltip", "label": "Tooltip"},
        ]
    },
    {
        "title": "Advanced",
        "collapsible": True,
        "default_open": False,
        "items": [
            {"href": "/docs/components/data-table", "label": "Data Table"},
            {"href": "/docs/components/command", "label": "Command"},
            {"href": "/docs/components/calendar", "label": "Calendar"},
            {"href": "/docs/components/date-picker", "label": "Date Picker"},
        ]
    }
]

@rt('/')
def complete_docs_example():
    """Create a complete documentation example."""
    return DocsLayout(
        # Main content
        Div(
            # Component installation
            H2("Installation", cls="scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight first:mt-0"),
            P("Install the component from your command line.", cls="leading-7 [&:not(:first-child)]:mt-6 mb-4"),
            
            Div(
                Pre(
                    Code("npx shadcn-ui@latest add button", cls="language-bash"),
                    cls="overflow-x-auto p-4 text-sm"
                ),
                cls="rounded-lg border bg-background"
            ),
            
            # Usage section
            H2("Usage", cls="scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight mt-10"),
            P("Import and use the component in your project.", cls="leading-7 [&:not(:first-child)]:mt-6 mb-4"),
            
            Div(
                Pre(
                    Code('''import { Button } from "@/components/ui/button"

export function ButtonDemo() {
  return <Button>Click me</Button>
}''', cls="language-typescript"),
                    cls="overflow-x-auto p-4 text-sm"
                ),
                cls="rounded-lg border bg-background"
            ),
            
            # Examples section
            H2("Examples", cls="scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight mt-10"),
            
            # Default example
            Div(
                H3("Default", cls="scroll-m-20 text-2xl font-semibold tracking-tight mb-2"),
                P("The default button style.", cls="text-muted-foreground mb-4"),
                Div(
                    Button("Default Button"),
                    cls="flex items-center justify-center min-h-[200px] w-full rounded-lg border border-dashed bg-muted/30 p-6"
                ),
                cls="mb-8"
            ),
            
            # Variants example
            Div(
                H3("Variants", cls="scroll-m-20 text-2xl font-semibold tracking-tight mb-2"),
                P("Different visual styles for different purposes.", cls="text-muted-foreground mb-4"),
                Div(
                    Div(
                        Button("Primary", variant="default", cls="mr-2"),
                        Button("Secondary", variant="secondary", cls="mr-2"),
                        Button("Destructive", variant="destructive", cls="mr-2"),
                        Button("Outline", variant="outline", cls="mr-2"),
                        Button("Ghost", variant="ghost", cls="mr-2"),
                        Button("Link", variant="link"),
                        cls="flex flex-wrap gap-2"
                    ),
                    cls="flex items-center justify-center min-h-[200px] w-full rounded-lg border border-dashed bg-muted/30 p-6"
                ),
                cls="mb-8"
            ),
            
            # Sizes example
            Div(
                H3("Sizes", cls="scroll-m-20 text-2xl font-semibold tracking-tight mb-2"),
                P("Different sizes for different contexts.", cls="text-muted-foreground mb-4"),
                Div(
                    Div(
                        Button("Small", size="sm", cls="mr-2"),
                        Button("Default", size="default", cls="mr-2"),
                        Button("Large", size="lg", cls="mr-2"),
                        Button(IconifyIcon("ph:plus-bold"), size="icon"),
                        cls="flex items-center gap-2"
                    ),
                    cls="flex items-center justify-center min-h-[200px] w-full rounded-lg border border-dashed bg-muted/30 p-6"
                ),
                cls="mb-8"
            ),
            
            # With Icons example
            Div(
                H3("With Icons", cls="scroll-m-20 text-2xl font-semibold tracking-tight mb-2"),
                P("Buttons can include icons for better visual communication.", cls="text-muted-foreground mb-4"),
                Div(
                    Div(
                        Button(
                            IconifyIcon("ph:download-bold", cls="mr-2 h-4 w-4"),
                            "Download",
                            cls="mr-2"
                        ),
                        Button(
                            "Next",
                            IconifyIcon("ph:arrow-right-bold", cls="ml-2 h-4 w-4"),
                            variant="outline"
                        ),
                        cls="flex items-center gap-2"
                    ),
                    cls="flex items-center justify-center min-h-[200px] w-full rounded-lg border border-dashed bg-muted/30 p-6"
                ),
                cls="mb-8"
            ),
            
            # Loading State example
            Div(
                H3("Loading State", cls="scroll-m-20 text-2xl font-semibold tracking-tight mb-2"),
                P("Show loading states with Datastar reactivity.", cls="text-muted-foreground mb-4"),
                Div(
                    Button(
                        Span("Loading...", ds_show="$isLoading"),
                        Span("Click to Load", ds_show="!$isLoading"),
                        disabled=True,  # You would use ds_disabled="$isLoading" in real usage
                        ds_on_click="$isLoading = true; setTimeout(() => $isLoading = false, 2000)",
                        ds_signals={"isLoading": False}
                    ),
                    cls="flex items-center justify-center min-h-[200px] w-full rounded-lg border border-dashed bg-muted/30 p-6"
                ),
                cls="mb-8"
            ),
            
            # API Reference
            H2("API Reference", cls="scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight mt-10"),
            
            H3("Button", cls="scroll-m-20 text-2xl font-semibold tracking-tight mt-8 mb-4"),
            P("The Button component accepts the following props:", cls="leading-7 mb-4"),
            
            Div(
                Table(
                    Thead(
                        Tr(
                            Th("Prop", cls="border px-4 py-2"),
                            Th("Type", cls="border px-4 py-2"),
                            Th("Default", cls="border px-4 py-2"),
                            Th("Description", cls="border px-4 py-2")
                        )
                    ),
                    Tbody(
                        Tr(
                            Td("variant", cls="border px-4 py-2 font-mono text-sm"),
                            Td("'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link'", cls="border px-4 py-2 font-mono text-sm"),
                            Td("'default'", cls="border px-4 py-2 font-mono text-sm"),
                            Td("The visual style variant", cls="border px-4 py-2")
                        ),
                        Tr(
                            Td("size", cls="border px-4 py-2 font-mono text-sm"),
                            Td("'default' | 'sm' | 'lg' | 'icon'", cls="border px-4 py-2 font-mono text-sm"),
                            Td("'default'", cls="border px-4 py-2 font-mono text-sm"),
                            Td("The size variant", cls="border px-4 py-2")
                        ),
                        Tr(
                            Td("disabled", cls="border px-4 py-2 font-mono text-sm"),
                            Td("boolean", cls="border px-4 py-2 font-mono text-sm"),
                            Td("false", cls="border px-4 py-2 font-mono text-sm"),
                            Td("Whether the button is disabled", cls="border px-4 py-2")
                        ),
                        Tr(
                            Td("type", cls="border px-4 py-2 font-mono text-sm"),
                            Td("'button' | 'submit' | 'reset'", cls="border px-4 py-2 font-mono text-sm"),
                            Td("'button'", cls="border px-4 py-2 font-mono text-sm"),
                            Td("The HTML button type", cls="border px-4 py-2")
                        )
                    ),
                    cls="w-full border-collapse"
                ),
                cls="overflow-x-auto rounded-lg border"
            ),
            
            cls="max-w-4xl"
        ),
        
        # Page configuration
        title="Button",
        description="Displays a button or a component that looks like a button.",
        breadcrumb_items=[
            {"label": "Docs", "href": "/docs"},
            {"label": "Components", "href": "/docs/components"},
            {"label": "Button", "active": True}
        ],
        
        # Custom navigation
        nav_items=CUSTOM_NAV_ITEMS,
        
        # Custom sidebar
        sidebar_sections=COMPONENT_SIDEBAR_SECTIONS,
        
        # Custom footer
        footer_attribution="Built with StarHTML",
        footer_hosting="Powered by Datastar",
        footer_links=[
            {"href": "/privacy", "label": "Privacy Policy"},
            {"href": "/terms", "label": "Terms of Service"}
        ]
    )

if __name__ == "__main__":
    print("Complete Docs Example running on http://localhost:5005")
    serve(port=5005)