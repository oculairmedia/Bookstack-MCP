"""Selective tool registration for BookStack MCP - registers only specific tools."""

from fastmcp import FastMCP
from .tools import register_bookstack_tools


def register_selective_bookstack_tools(mcp: FastMCP) -> None:
    """
    Register only the search, list, and image tools from the full-featured set.

    Note: The simplified tools are now registered as the primary bookstack_manage_content
    and bookstack_batch_operations tools, so we only register the additional tools here.
    """
    register_bookstack_tools(mcp, exclude={"bookstack_manage_content", "bookstack_batch_operations"})

