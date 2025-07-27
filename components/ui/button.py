"""Button component matching shadcn/ui styling and behavior."""
from typing import Literal

from starhtml import FT
from starhtml import Button as BaseButton

from ..utils import cn, cva

ButtonVariant = Literal["default", "destructive", "outline", "secondary", "ghost", "link"]
ButtonSize = Literal["default", "sm", "lg", "icon"]


button_variants = cva(
    base="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
    config={
        "variants": {
            "variant": {
                "default": "bg-primary text-primary-foreground shadow hover:bg-primary/90",
                "destructive": "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
                "outline": "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
                "secondary": "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
                "ghost": "hover:bg-accent hover:text-accent-foreground",
                "link": "text-primary underline-offset-4 hover:underline"
            },
            "size": {
                "default": "h-9 px-4 py-2",
                "sm": "h-8 rounded-md px-3 text-xs",
                "lg": "h-10 rounded-md px-8",
                "icon": "h-9 w-9"
            }
        },
        "defaultVariants": {
            "variant": "default",
            "size": "default"
        }
    }
)


def Button(
    *children,
    variant: ButtonVariant = "default",
    size: ButtonSize = "default",
    class_name: str = "",
    disabled: bool = False,
    type: Literal["button", "submit", "reset"] = "button",
    cls: str = "",
    **attrs
) -> FT:
    """
    Button component matching shadcn/ui styling and behavior.
    
    Args:
        *children: Button content
        variant: Visual style variant
        size: Size variant
        class_name: Additional CSS classes
        disabled: Whether button is disabled
        type: HTML button type
        **attrs: Additional HTML attributes including Datastar directives
        
    Returns:
        Button element
        
    Examples:
        # Basic button
        Button("Click me")
        
        # With variant and size
        Button("Delete", variant="destructive", size="sm")
        
        # With Datastar click handler
        Button("Toggle", data_on_click="$open = !$open")
        
        # Loading state with spinner
        Button(
            Spinner() if loading else "Submit",
            disabled=loading,
            data_signals={"loading": False}
        )
    """
    classes = cn(
        button_variants(variant=variant, size=size),
        class_name,
        cls
    )
    
    return BaseButton(
        *children,
        cls=classes,
        disabled=disabled,
        type=type,
        **attrs
    )


def button(
    *children,
    variant: ButtonVariant = "default",
    size: ButtonSize = "default",
    class_name: str = "",
    disabled: bool = False,
    type: Literal["button", "submit", "reset"] = "button",
    cls: str = "",
    **attrs
) -> FT:
    """Alias for Button() using lowercase convention."""
    return Button(
        *children,
        variant=variant,
        size=size,
        class_name=class_name,
        disabled=disabled,
        type=type,
        cls=cls,
        **attrs
    )
