"""Selective tool registration for BookStack MCP - registers only specific tools."""

from fastmcp import FastMCP
from .tools import register_bookstack_tools


def register_selective_bookstack_tools(mcp: FastMCP) -> None:
    """
    Register only the search, list, and image tools from the full-featured set.

    Note: The simplified tools are now registered as the primary bookstack_manage_content
    and bookstack_batch_operations tools, so we only register the additional tools here.
    """
    # Register all tools from the full-featured set
    register_bookstack_tools(mcp)

    # Remove the complex manage_content and batch_operations tools
    # since the simplified versions are already registered with these names
    tools_to_remove = ['bookstack_manage_content', 'bookstack_batch_operations']
    for tool_name in tools_to_remove:
        try:
            mcp.remove_tool(tool_name)
            print(f"   ✅ Removed full-featured {tool_name} (using simplified version instead)")
        except Exception as e:
            # This is expected if the tool doesn't exist
            pass

