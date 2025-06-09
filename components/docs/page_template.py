"""Documentation page template for component documentation."""
from typing import Optional, List, Dict, Any, Union
from starhtml import Div, H1, H2, P, A, FT
from ..utils import cn
from .layout import DocsLayout
from .preview_card import ComponentPreview
from .installation_section import InstallationSection
from .code_block import CodeBlock


def ComponentDocPage(
    component_name: str,
    description: str,
    *,
    # Page metadata
    breadcrumb_items: Optional[List[Dict[str, Any]]] = None,
    
    # Installation section
    cli_command: Optional[str] = None,
    manual_files: Optional[List[Dict[str, str]]] = None,
    dependencies: Optional[List[str]] = None,
    
    # Usage section
    usage_code: Optional[str] = None,
    usage_description: Optional[str] = None,
    
    # Examples section
    examples: Optional[List[Dict[str, Any]]] = None,
    
    # API Reference
    api_reference: Optional[Dict[str, Any]] = None,
    
    # Additional content
    additional_sections: Optional[List[FT]] = None,
    
    # Layout options
    show_toc: bool = True,
    cls: str = "",
    **layout_attrs
) -> FT:
    """
    Component documentation page template.
    
    Args:
        component_name: Name of the component
        description: Component description
        breadcrumb_items: Breadcrumb navigation items
        cli_command: CLI installation command
        manual_files: Manual installation files
        dependencies: Required dependencies
        usage_code: Basic usage code example
        usage_description: Usage description
        examples: List of component examples with previews
        api_reference: API reference information
        additional_sections: Additional content sections
        show_toc: Whether to show table of contents
        cls: Additional CSS classes
        **layout_attrs: Additional layout attributes
        
    Returns:
        Complete documentation page
    """
    
    # Default breadcrumb if not provided
    if breadcrumb_items is None:
        breadcrumb_items = [
            {"label": "Docs", "href": "/docs"},
            {"label": "Components", "href": "/docs/components"},
            {"label": component_name, "active": True}
        ]
    
    # Build page content
    content_sections = []
    
    # Page header
    content_sections.append(
        Div(
            H1(component_name, cls="scroll-m-20 text-4xl font-bold tracking-tight"),
            P(description, cls="text-xl text-muted-foreground mt-4"),
            cls="space-y-2"
        )
    )
    
    # Installation section
    content_sections.append(
        InstallationSection(
            component_name,
            cli_command=cli_command,
            manual_files=manual_files,
            dependencies=dependencies
        )
    )
    
    # Usage section
    if usage_code:
        content_sections.append(
            Div(
                H2("Usage", cls="scroll-m-20 text-2xl font-bold tracking-tight"),
                usage_description and P(usage_description, cls="text-muted-foreground mt-2"),
                CodeBlock(
                    usage_code,
                    language="tsx",
                    copy_button=True
                ),
                cls="space-y-4"
            )
        )
    
    # Examples section
    if examples:
        content_sections.append(
            Div(
                H2("Examples", cls="scroll-m-20 text-2xl font-bold tracking-tight mb-8"),
                Div(
                    *[
                        Div(
                            ComponentPreview(
                                example["preview"],
                                example["code"],
                                title=example.get("title"),
                                description=example.get("description"),
                                preview_class=example.get("preview_class", "")
                            ),
                            cls="mb-8" if i < len(examples) - 1 else ""
                        )
                        for i, example in enumerate(examples)
                    ],
                    cls="space-y-8"
                ),
                cls="space-y-8"
            )
        )
    
    # API Reference section
    if api_reference:
        content_sections.append(
            Div(
                H2("API Reference", cls="scroll-m-20 text-2xl font-bold tracking-tight"),
                _build_api_reference(api_reference),
                cls="space-y-6"
            )
        )
    
    # Additional sections
    if additional_sections:
        content_sections.extend(additional_sections)
    
    return DocsLayout(
        Div(
            *content_sections,
            cls=cn("max-w-none space-y-12", cls)
        ),
        title=f"{component_name} - Components",
        description=description,
        breadcrumb_items=breadcrumb_items,
        **layout_attrs
    )


def _build_api_reference(api_ref: Dict[str, Any]) -> FT:
    """Build API reference section."""
    sections = []
    
    # Props table
    if "props" in api_ref:
        sections.append(
            Div(
                H2("Props", cls="text-xl font-semibold mb-4"),
                _build_props_table(api_ref["props"]),
                cls="space-y-4"
            )
        )
    
    # Variants
    if "variants" in api_ref:
        sections.append(
            Div(
                H2("Variants", cls="text-xl font-semibold mb-4"),
                _build_variants_section(api_ref["variants"]),
                cls="space-y-4"
            )
        )
    
    return Div(*sections, cls="space-y-8")


def _build_props_table(props: List[Dict[str, str]]) -> FT:
    """Build props table."""
    from starhtml import Table, Thead, Tbody, Tr, Th, Td
    
    return Table(
        Thead(
            Tr(
                Th("Prop", cls="text-left"),
                Th("Type", cls="text-left"),
                Th("Default", cls="text-left"),
                Th("Description", cls="text-left"),
                cls="border-b"
            )
        ),
        Tbody(
            *[
                Tr(
                    Td(prop["name"], cls="font-mono text-sm"),
                    Td(prop["type"], cls="font-mono text-sm text-muted-foreground"),
                    Td(prop.get("default", "-"), cls="font-mono text-sm"),
                    Td(prop["description"], cls="text-sm"),
                    cls="border-b"
                )
                for prop in props
            ]
        ),
        cls="w-full border-collapse text-sm"
    )


def _build_variants_section(variants: Dict[str, Any]) -> FT:
    """Build variants section."""
    variant_sections = []
    
    for variant_name, variant_options in variants.items():
        variant_sections.append(
            Div(
                H2(variant_name.title(), cls="text-lg font-medium mb-2"),
                Div(
                    *[
                        Div(
                            Div(option["name"], cls="font-mono text-sm font-medium"),
                            option.get("description") and P(option["description"], cls="text-sm text-muted-foreground mt-1"),
                            cls="p-3 border rounded-md"
                        )
                        for option in variant_options
                    ],
                    cls="grid gap-3 sm:grid-cols-2 lg:grid-cols-3"
                ),
                cls="space-y-3"
            )
        )
    
    return Div(*variant_sections, cls="space-y-6")


def component_doc_page(
    component_name: str,
    description: str,
    *,
    breadcrumb_items: Optional[List[Dict[str, Any]]] = None,
    cli_command: Optional[str] = None,
    manual_files: Optional[List[Dict[str, str]]] = None,
    dependencies: Optional[List[str]] = None,
    usage_code: Optional[str] = None,
    usage_description: Optional[str] = None,
    examples: Optional[List[Dict[str, Any]]] = None,
    api_reference: Optional[Dict[str, Any]] = None,
    additional_sections: Optional[List[FT]] = None,
    show_toc: bool = True,
    cls: str = "",
    **layout_attrs
) -> FT:
    """Alias for ComponentDocPage() using lowercase convention."""
    return ComponentDocPage(
        component_name,
        description,
        breadcrumb_items=breadcrumb_items,
        cli_command=cli_command,
        manual_files=manual_files,
        dependencies=dependencies,
        usage_code=usage_code,
        usage_description=usage_description,
        examples=examples,
        api_reference=api_reference,
        additional_sections=additional_sections,
        show_toc=show_toc,
        cls=cls,
        **layout_attrs
    )