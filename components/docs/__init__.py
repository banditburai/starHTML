"""Documentation layout components for shadcn-ui style docs."""

from .header import DocsHeader, docs_header
from .sidebar import DocsSidebar, docs_sidebar
from .layout import DocsLayout, docs_layout
from .breadcrumb import DocsBreadcrumb, docs_breadcrumb
from .footer import DocsFooter, docs_footer
from .preview_card import ComponentPreview, component_preview
from .code_block import CodeBlock, InstallationBlock, code_block, installation_block
from .installation_section import InstallationSection, installation_section
from .page_template import ComponentDocPage, component_doc_page

__all__ = [
    "DocsHeader", "docs_header",
    "DocsSidebar", "docs_sidebar", 
    "DocsLayout", "docs_layout",
    "DocsBreadcrumb", "docs_breadcrumb",
    "DocsFooter", "docs_footer",
    "ComponentPreview", "component_preview",
    "CodeBlock", "InstallationBlock", "code_block", "installation_block",
    "InstallationSection", "installation_section",
    "ComponentDocPage", "component_doc_page"
]