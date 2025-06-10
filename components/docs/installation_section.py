"""Installation section component with CLI/Manual tabs."""
from typing import Optional, List, Dict, Any
from starhtml import Div, H2, H3, P, Button, FT
from ..utils import cn
from .code_block import CodeBlock


def InstallationSection(
    component_name: str,
    *,
    cli_command: Optional[str] = None,
    manual_files: Optional[List[Dict[str, str]]] = None,
    dependencies: Optional[List[str]] = None,
    description: Optional[str] = None,
    default_tab: str = "cli",
    cls: str = "",
    **attrs
) -> FT:
    """
    Installation section with CLI and Manual tabs.
    
    Args:
        component_name: Name of the component being installed
        cli_command: CLI installation command
        manual_files: List of manual installation files [{"filename": "...", "content": "..."}]
        dependencies: List of additional dependencies
        description: Optional description
        default_tab: Default tab ("cli" or "manual")
        cls: Additional CSS classes
        **attrs: Additional HTML attributes
        
    Returns:
        Installation section element
    """
    import uuid
    section_id = f"install_{str(uuid.uuid4())[:8]}"
    tab_signal = f"{section_id}_tab"
    
    # Default CLI command if not provided
    if cli_command is None:
        cli_command = f"npx shadcn-ui@latest add {component_name.lower()}"
    
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
        H2("Installation", cls="text-2xl font-bold tracking-tight"),
        
        description and P(description, cls="text-muted-foreground mt-2"),
        
        # Tab navigation
        Div(
            Div(
                tab_button("cli", "CLI", default_tab == "cli"),
                tab_button("manual", "Manual", default_tab == "manual"),
                cls="inline-flex h-9 items-center justify-center rounded-none bg-transparent p-0"
            ),
            cls="flex h-9 items-center justify-center border-b bg-transparent mt-6"
        ),
        
        # CLI Installation Tab
        Div(
            Div(
                CodeBlock(
                    cli_command,
                    language="bash",
                    copy_button=True
                ),
                cls="mt-6"
            ),
            data_bind_show=f"${tab_signal} === 'cli'"
        ),
        
        # Manual Installation Tab
        Div(
            Div(
                # Dependencies section
                (Div(
                    H3("Install dependencies", cls="text-lg font-semibold mb-4"),
                    CodeBlock(
                        f"npm install {' '.join(dependencies)}",
                        language="bash",
                        copy_button=True
                    ),
                    cls="mb-8"
                ) if dependencies else None),
                
                # Manual files section
                (Div(
                    H3("Copy and paste the following code into your project", cls="text-lg font-semibold mb-4"),
                    *[
                        Div(
                            CodeBlock(
                                file_info["content"],
                                language=file_info.get("language", "tsx"),
                                title=file_info["filename"],
                                copy_button=True
                            ),
                            cls="mb-6" if i < len(manual_files) - 1 else ""
                        )
                        for i, file_info in enumerate(manual_files)
                    ],
                    cls="space-y-6"
                ) if manual_files else Div(
                    P("Manual installation files not available for this component.", 
                      cls="text-muted-foreground italic")
                )),
                
                cls="mt-6"
            ),
            data_bind_show=f"${tab_signal} === 'manual'"
        ),
        
        cls=cn("space-y-6", cls),
        data_signals={tab_signal: default_tab},
        **attrs
    )


def installation_section(
    component_name: str,
    *,
    cli_command: Optional[str] = None,
    manual_files: Optional[List[Dict[str, str]]] = None,
    dependencies: Optional[List[str]] = None,
    description: Optional[str] = None,
    default_tab: str = "cli",
    cls: str = "",
    **attrs
) -> FT:
    """Alias for InstallationSection() using lowercase convention."""
    return InstallationSection(
        component_name,
        cli_command=cli_command,
        manual_files=manual_files,
        dependencies=dependencies,
        description=description,
        default_tab=default_tab,
        cls=cls,
        **attrs
    )