"""Tests for BookStack tool registration (bookstack-mcp-vz9)."""
from __future__ import annotations

import pytest
from fastmcp import FastMCP

from fastmcp_server.bookstack.tools import register_bookstack_tools
from fastmcp_server.bookstack.tools_simplified import register_simplified_bookstack_tools


@pytest.mark.asyncio
async def test_register_bookstack_tools_registers_expected_tools() -> None:
    """Test that register_bookstack_tools registers all expected tools."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    
    # Get all registered tools
    tools = [t.name for t in (await mcp.get_tools()).values()]
    
    expected_tools = [
        "bookstack_manage_content",
        "bookstack_list_content",
        "bookstack_search",
        "bookstack_semantic_search",
        "bookstack_manage_images",
        "bookstack_search_images",
        "bookstack_batch_operations",
        "bookstack_get_metrics",
        "bookstack_health_check",
        "bookstack_dashboard",
    ]
    
    for expected_tool in expected_tools:
        assert expected_tool in tools, f"Expected tool {expected_tool} not registered"


@pytest.mark.asyncio
async def test_register_simplified_bookstack_tools_registers_expected_tools() -> None:
    """Test that register_simplified_bookstack_tools registers expected tools."""
    mcp = FastMCP("test")
    register_simplified_bookstack_tools(mcp)
    
    # Get all registered tools
    tools = [t.name for t in (await mcp.get_tools()).values()]
    
    expected_tools = [
        "bookstack_content_crud",
        "bookstack_batch_operations",
    ]
    
    for expected_tool in expected_tools:
        assert expected_tool in tools, f"Expected tool {expected_tool} not registered"


@pytest.mark.asyncio
async def test_no_tool_name_collisions_in_full_registration() -> None:
    """Test that there are no duplicate tool names in the registration."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    
    tools = [t.name for t in (await mcp.get_tools()).values()]
    
    # Check for duplicates
    seen = set()
    duplicates = set()
    for tool in tools:
        if tool in seen:
            duplicates.add(tool)
        seen.add(tool)
    
    assert len(duplicates) == 0, f"Found duplicate tool registrations: {duplicates}"


@pytest.mark.asyncio
async def test_tool_count_matches_expected() -> None:
    """Test that the expected number of tools are registered."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    
    tools = [t.name for t in (await mcp.get_tools()).values()]
    
    # We expect exactly 10 tools
    assert len(tools) == 10, f"Expected 10 tools, got {len(tools)}: {tools}"
