"""BookStack tool implementations for the FastMCP server."""

from .tools import register_bookstack_tools
from .tools_simplified import register_simplified_bookstack_tools
from .tools_selective import register_selective_bookstack_tools
from .tools_direct_pages import register_direct_page_tools
from .tools_pdf_attachments import register_pdf_attachment_tools


def register_production_tools(mcp) -> None:
    """Register the full production tool stack on a FastMCP instance.

    This is the single source of truth for which tools ship in production so
    that the HTTP server and the stdio/Inspector launcher stay in sync:

    - selective full-featured tools (search, list, images, observability),
      excluding the large-schema ``manage_content``/``batch_operations``
    - simplified CRUD/batch replacements (``bookstack_content_crud`` etc.)
    - direct page tools
    - PDF/attachment tools
    """
    register_selective_bookstack_tools(mcp)
    register_simplified_bookstack_tools(mcp)
    register_direct_page_tools(mcp)
    register_pdf_attachment_tools(mcp)


__all__ = [
    "register_bookstack_tools",
    "register_simplified_bookstack_tools",
    "register_selective_bookstack_tools",
    "register_direct_page_tools",
    "register_pdf_attachment_tools",
    "register_production_tools",
]
