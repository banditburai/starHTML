"""Code block component with copy functionality and syntax highlighting."""
from typing import Optional, Literal
from starhtml import Div, Pre, Code, Button, FT
from ..utils import cn
from ..ui.iconify import Icon


def CodeBlock(
    code: str,
    *,
    language: Optional[str] = None,
    title: Optional[str] = None,
    copy_button: bool = True,
    line_numbers: bool = False,
    max_height: Optional[str] = None,
    cls: str = "",
    **attrs
) -> FT:
    """
    Code block with syntax highlighting and copy functionality.
    
    Args:
        code: The code content to display
        language: Programming language for syntax highlighting
        title: Optional title for the code block
        copy_button: Whether to show copy button
        line_numbers: Whether to show line numbers
        max_height: Maximum height (e.g., "400px")
        cls: Additional CSS classes
        **attrs: Additional HTML attributes
        
    Returns:
        Code block element
    """
    import uuid
    block_id = f"code_block_{str(uuid.uuid4())[:8]}"
    copied_signal = f"copied_{block_id}"
    
    # Process code for line numbers if needed
    processed_code = code
    if line_numbers:
        lines = code.split('\n')
        max_digits = len(str(len(lines)))
        processed_lines = []
        for i, line in enumerate(lines, 1):
            line_num = str(i).rjust(max_digits)
            processed_lines.append(f"{line_num} | {line}")
        processed_code = '\n'.join(processed_lines)
    
    return Div(
        # Title bar
        (Div(
            title,
            cls="border-b bg-zinc-100 px-4 py-2 text-sm font-medium dark:bg-zinc-800"
        ) if title else None),
        
        # Code container
        Div(
            # Copy button
            (Div(
                Button(
                    Icon("lucide:copy", cls="h-4 w-4"),
                    type="button", 
                    variant="outline",
                    size="icon",
                    cls="h-8 w-8 rounded-md bg-background",
                    data_on_click=f"""
                        navigator.clipboard.writeText(`{code}`);
                        ${copied_signal} = true;
                        setTimeout(() => ${copied_signal} = false, 2000);
                    """,
                    title="Copy code"
                ),
                # Copy feedback
                Div(
                    "Copied!",
                    cls="absolute right-12 top-2 rounded bg-foreground px-2 py-1 text-xs text-background",
                    data_bind_show=f"${copied_signal}"
                ),
                cls="absolute right-2 top-2 z-10"
            ) if copy_button else None),
            
            # Code content
            Pre(
                Code(
                    processed_code,
                    cls=cn(
                        "text-sm",
                        f"language-{language}" if language else None
                    )
                ),
                cls=cn(
                    "overflow-x-auto bg-zinc-950 p-4 text-white dark:bg-zinc-900",
                    f"max-h-[{max_height}]" if max_height else None,
                    "pr-12" if copy_button else None  # Space for copy button
                )
            ),
            cls="relative"
        ),
        
        cls=cn("rounded-lg border bg-background shadow-sm", cls),
        data_signals={copied_signal: False},
        **attrs
    )


def InstallationBlock(
    command: str,
    *,
    package_manager: Literal["npm", "yarn", "pnpm", "bun"] = "npm",
    copy_button: bool = True,
    cls: str = "",
    **attrs
) -> FT:
    """
    Installation command block.
    
    Args:
        command: The installation command
        package_manager: Package manager type
        copy_button: Whether to show copy button
        cls: Additional CSS classes
        **attrs: Additional HTML attributes
        
    Returns:
        Installation code block
    """
    return CodeBlock(
        command,
        language="bash",
        title=f"Install via {package_manager}",
        copy_button=copy_button,
        cls=cls,
        **attrs
    )


def code_block(
    code: str,
    *,
    language: Optional[str] = None,
    title: Optional[str] = None,
    copy_button: bool = True,
    line_numbers: bool = False,
    max_height: Optional[str] = None,
    cls: str = "",
    **attrs
) -> FT:
    """Alias for CodeBlock() using lowercase convention."""
    return CodeBlock(
        code,
        language=language,
        title=title,
        copy_button=copy_button,
        line_numbers=line_numbers,
        max_height=max_height,
        cls=cls,
        **attrs
    )


def installation_block(
    command: str,
    *,
    package_manager: Literal["npm", "yarn", "pnpm", "bun"] = "npm",
    copy_button: bool = True,
    cls: str = "",
    **attrs
) -> FT:
    """Alias for InstallationBlock() using lowercase convention."""
    return InstallationBlock(
        command,
        package_manager=package_manager,
        copy_button=copy_button,
        cls=cls,
        **attrs
    )