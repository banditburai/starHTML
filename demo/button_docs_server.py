"""Server to demo the Button documentation page."""

from starhtml import *
from components.docs import ComponentDocPage
from components.ui import Button
from components.ui.iconify import IconifyIcon

app, rt = star_app(title="Button - StarHTML UI", live=True)


@rt("/")
def button_docs_page():
    """Button documentation page route."""

    # Button examples matching shadcn-ui
    examples = [
        {"title": "Default", "preview": Button("Button"), "code": "<Button>Button</Button>"},
        {
            "title": "Secondary",
            "preview": Button("Secondary", variant="secondary"),
            "code": '<Button variant="secondary">Secondary</Button>',
        },
        {
            "title": "Destructive",
            "preview": Button("Destructive", variant="destructive"),
            "code": '<Button variant="destructive">Destructive</Button>',
        },
        {
            "title": "Outline",
            "preview": Button("Outline", variant="outline"),
            "code": '<Button variant="outline">Outline</Button>',
        },
        {
            "title": "Ghost",
            "preview": Button("Ghost", variant="ghost"),
            "code": '<Button variant="ghost">Ghost</Button>',
        },
        {"title": "Link", "preview": Button("Link", variant="link"), "code": '<Button variant="link">Link</Button>'},
        {
            "title": "Icon",
            "preview": Button(IconifyIcon("lucide:chevron-right", cls="h-4 w-4"), variant="outline", size="icon"),
            "code": """<Button variant="outline" size="icon">
  <ChevronRight className="h-4 w-4" />
</Button>""",
        },
        {
            "title": "With Icon",
            "preview": Button(IconifyIcon("lucide:mail", cls="mr-2 h-4 w-4"), "Login with Email"),
            "code": """<Button>
  <Mail className="mr-2 h-4 w-4" />
  Login with Email
</Button>""",
        },
        {
            "title": "Loading",
            "preview": Button(
                IconifyIcon("lucide:loader-2", cls="mr-2 h-4 w-4 animate-spin"), "Please wait", disabled=True
            ),
            "code": """<Button disabled>
  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
  Please wait
</Button>""",
        },
        {
            "title": "As Child",
            "description": "Use the asChild prop to make another component look like a button.",
            "preview": Button("Login", variant="outline"),
            "code": """<Button asChild>
  <Link href="/login">Login</Link>
</Button>""",
        },
    ]

    # Manual installation files
    manual_files = [
        {
            "filename": "components/ui/button.tsx",
            "content": """import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        destructive:
          "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
        outline:
          "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
        secondary:
          "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }""",
            "language": "tsx",
        }
    ]

    # Dependencies for manual installation
    dependencies = ["@radix-ui/react-slot", "class-variance-authority", "clsx", "tailwind-merge"]

    # Usage code example
    usage_code = """import { Button } from "@/components/ui/button"

export function ButtonDemo() {
  return <Button>Button</Button>
}"""

    # API Reference
    api_reference = {
        "props": [
            {
                "name": "variant",
                "type": "'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link'",
                "default": "'default'",
                "description": "The visual style variant of the button.",
            },
            {
                "name": "size",
                "type": "'default' | 'sm' | 'lg' | 'icon'",
                "default": "'default'",
                "description": "The size variant of the button.",
            },
            {
                "name": "asChild",
                "type": "boolean",
                "default": "false",
                "description": "Change the default rendered element for the one passed as a child, merging their props and behavior.",
            },
        ],
        "variants": {
            "variant": [
                {"name": "default", "description": "The default button style with primary background."},
                {"name": "destructive", "description": "A destructive action button with red styling."},
                {"name": "outline", "description": "A button with transparent background and border."},
                {"name": "secondary", "description": "A secondary button with muted styling."},
                {"name": "ghost", "description": "A button with no background that appears on hover."},
                {"name": "link", "description": "A button that looks like a text link."},
            ],
            "size": [
                {"name": "default", "description": "Default button size (36px height)."},
                {"name": "sm", "description": "Small button size (32px height)."},
                {"name": "lg", "description": "Large button size (40px height)."},
                {"name": "icon", "description": "Square button optimized for icons (36px × 36px)."},
            ],
        },
    }

    return ComponentDocPage(
        "Button",
        "Displays a button or a component that looks like a button.",
        cli_command="npx shadcn-ui@latest add button",
        manual_files=manual_files,
        dependencies=dependencies,
        usage_code=usage_code,
        usage_description="Import and use the Button component in your React components.",
        examples=examples,
        api_reference=api_reference,
        breadcrumb_items=[
            {"label": "Docs", "href": "/docs"},
            {"label": "Components", "href": "/docs/components"},
            {"label": "Button", "active": True},
        ],
    )


@rt("/static/globals.css")
def css_route():
    """Serve CSS with theme variables."""
    css_content = """
    :root {
        --background: 0 0% 100%;
        --foreground: 222.2 84% 4.9%;
        --card: 0 0% 100%;
        --card-foreground: 222.2 84% 4.9%;
        --popover: 0 0% 100%;
        --popover-foreground: 222.2 84% 4.9%;
        --primary: 222.2 47.4% 11.2%;
        --primary-foreground: 210 40% 98%;
        --secondary: 210 40% 96%;
        --secondary-foreground: 222.2 84% 4.9%;
        --muted: 210 40% 96%;
        --muted-foreground: 215.4 16.3% 46.9%;
        --accent: 210 40% 96%;
        --accent-foreground: 222.2 84% 4.9%;
        --destructive: 0 84.2% 60.2%;
        --destructive-foreground: 210 40% 98%;
        --border: 214.3 31.8% 91.4%;
        --input: 214.3 31.8% 91.4%;
        --ring: 222.2 84% 4.9%;
        --radius: 0.5rem;
    }
    
    .dark {
        --background: 222.2 84% 4.9%;
        --foreground: 210 40% 98%;
        --card: 222.2 84% 4.9%;
        --card-foreground: 210 40% 98%;
        --popover: 222.2 84% 4.9%;
        --popover-foreground: 210 40% 98%;
        --primary: 210 40% 98%;
        --primary-foreground: 222.2 47.4% 11.2%;
        --secondary: 217.2 32.6% 17.5%;
        --secondary-foreground: 210 40% 98%;
        --muted: 217.2 32.6% 17.5%;
        --muted-foreground: 215 20.2% 65.1%;
        --accent: 217.2 32.6% 17.5%;
        --accent-foreground: 210 40% 98%;
        --destructive: 0 62.8% 30.6%;
        --destructive-foreground: 210 40% 98%;
        --border: 217.2 32.6% 17.5%;
        --input: 217.2 32.6% 17.5%;
        --ring: 212.7 26.8% 83.9%;
    }
    
    * {
        border-color: hsl(var(--border));
    }
    
    body {
        background-color: hsl(var(--background));
        color: hsl(var(--foreground));
    }
    """

    return Response(css_content, media_type="text/css")


if __name__ == "__main__":
    print("Starting Button Documentation Server...")
    print("Visit: http://localhost:8005")
    serve(port=8005)
