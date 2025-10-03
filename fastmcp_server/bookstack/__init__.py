"""BookStack tool implementations for the FastMCP server."""

from .tools import register_bookstack_tools
from .tools_simplified import register_simplified_bookstack_tools
from .tools_selective import register_selective_bookstack_tools

__all__ = [
    "register_bookstack_tools",
    "register_simplified_bookstack_tools",
    "register_selective_bookstack_tools",
]
