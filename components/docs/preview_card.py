"""Component preview card with Preview/Code tabs for documentation pages."""
from typing import Optional, Union, Dict, Any
from starhtml import Div, Button, Pre, Code, P, FT
from ..utils import cn, cva
from ..ui.iconify import Icon


def ComponentPreview(
    preview_content: FT,
    code_content: str,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    preview_class: str = "",
    copy_button: bool = True,
    default_tab: str = "preview",
    preview_id: Optional[str] = None,
    **attrs
) -> FT:
    """
    Component preview card with Preview/Code tabs.
    
    Args:
        preview_content: The live component preview
        code_content: The code string to display
        title: Optional title for the preview
        description: Optional description
        preview_class: Additional classes for preview area
        copy_button: Whether to show copy button
        default_tab: Default tab ("preview" or "code")
        preview_id: Unique ID for this preview (auto-generated if not provided)
        **attrs: Additional HTML attributes
        
    Returns:
        Component preview card element
    """
    if preview_id is None:
        import uuid
        preview_id = f"preview_{str(uuid.uuid4())[:8]}"
    
    tab_signal = f"{preview_id}_tab"
    code_signal = f"{preview_id}_code"
    
    # Tab button component
    def tab_button(tab_id: str, label: str, is_active: bool = False):
        return Button(
            label,
            type="button",
            variant="ghost",
            size="sm",
            cls=cn(
                "relative h-9 rounded-none border-b-2 border-transparent bg-transparent px-4 pb-3 pt-2 font-semibold text-muted-foreground shadow-none transition-none",
                "data-[state=active]:border-b-primary data-[state=active]:text-foreground data-[state=active]:shadow-none"
            ),
            data_on_click=f"${tab_signal} = '{tab_id}'",
            data_bind_attrs=f"{{state: ${tab_signal} === '{tab_id}' ? 'active' : 'inactive'}}"
        )
    
    return Div(
        # Header with title and description
        (Div(
            title and Div(title, cls="text-base font-semibold"),
            description and P(description, cls="text-sm text-muted-foreground mt-1"),
            cls="px-6 pt-6"
        ) if title or description else None),
        
        # Tab bar
        Div(
            Div(
                tab_button("preview", "Preview", default_tab == "preview"),
                tab_button("code", "Code", default_tab == "code"),
                cls="inline-flex h-9 items-center justify-center rounded-none bg-transparent p-0"
            ),
            cls="flex h-9 items-center justify-between border-b bg-transparent px-6"
        ),
        
        # Preview content
        Div(
            Div(
                preview_content,
                cls=cn("flex min-h-[200px] w-full items-center justify-center p-10", preview_class)
            ),
            cls="relative overflow-hidden rounded-none border-b",
            data_bind_show=f"${tab_signal} === 'preview'"
        ),
        
        # Code content  
        Div(
            # Copy button
            (Div(
                Button(
                    Icon("lucide:copy", cls="h-4 w-4"),
                    type="button",
                    variant="outline",
                    size="icon",
                    cls="absolute right-4 top-4 h-8 w-8 rounded-md",
                    data_on_click=f"""
                        navigator.clipboard.writeText(${code_signal});
                        $copied_{preview_id} = true;
                        setTimeout(() => $copied_{preview_id} = false, 2000);
                    """,
                    title="Copy code"
                ),
                # Copy feedback
                Div(
                    "Copied!",
                    cls="absolute right-12 top-4 rounded bg-foreground px-2 py-1 text-xs text-background",
                    data_bind_show=f"$copied_{preview_id}"
                ),
                cls="absolute right-0 top-0"
            ) if copy_button else None),
            
            # Code block
            Pre(
                Code(
                    code_content,
                    cls="relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm"
                ),
                cls="max-h-[650px] overflow-x-auto rounded-lg border bg-zinc-950 py-4 dark:bg-zinc-900",
                data_bind_text=f"${code_signal}"
            ),
            cls="relative",
            data_bind_show=f"${tab_signal} === 'code'"
        ),
        
        cls=cn("relative w-full rounded-lg border bg-background shadow", attrs.get("cls", "")),
        data_signals={
            tab_signal: default_tab,
            code_signal: code_content,
            f"copied_{preview_id}": False
        },
        **{k: v for k, v in attrs.items() if k != "cls"}
    )


def component_preview(
    preview_content: FT,
    code_content: str,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    preview_class: str = "",
    copy_button: bool = True,
    default_tab: str = "preview",
    preview_id: Optional[str] = None,
    **attrs
) -> FT:
    """Alias for ComponentPreview() using lowercase convention."""
    return ComponentPreview(
        preview_content,
        code_content,
        title=title,
        description=description,
        preview_class=preview_class,
        copy_button=copy_button,
        default_tab=default_tab,
        preview_id=preview_id,
        **attrs
    )