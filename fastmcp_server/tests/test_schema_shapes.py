"""Schema regression tests for BookStack tools."""
from __future__ import annotations

import pytest
from fastmcp import FastMCP

from fastmcp_server.bookstack.tools import register_bookstack_tools


@pytest.mark.asyncio
async def test_manage_content_updates_schema_references() -> None:
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    tool = await mcp.get_tool("bookstack_manage_content")
    parameters = tool.parameters
    updates_schema = parameters["properties"]["updates"]
    one_of_entries = updates_schema["oneOf"]

    head_descriptions = {entry.get("description") for entry in one_of_entries[:4]}
    assert head_descriptions == {
        "Fields accepted when creating or updating a book.",
        "Fields accepted when creating or updating a bookshelf.",
        "Fields accepted when creating or updating a chapter.",
        "Fields accepted when creating or updating a page.",
    }
    for entry in one_of_entries[:4]:
        assert entry.get("unevaluatedProperties") is False

    # Removed raw object payload schema to comply with MCP strict mode
    # Users can still pass custom fields via JSON string
    assert any(entry.get("type") == "string" for entry in one_of_entries)
    assert any(entry.get("type") == "null" for entry in one_of_entries)
    assert all(
        entry.get("unevaluatedProperties") is False
        for entry in one_of_entries[:4]
    )


@pytest.mark.asyncio
async def test_batch_operations_data_schema_references() -> None:
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    tool = await mcp.get_tool("bookstack_batch_operations")
    parameters = tool.parameters
    data_schema = parameters["properties"]["items"]["items"]["properties"]["data"]
    one_of_entries = data_schema["oneOf"]

    head_descriptions = {entry.get("description") for entry in one_of_entries[:4]}
    assert head_descriptions == {
        "Fields accepted when creating or updating a book.",
        "Fields accepted when creating or updating a bookshelf.",
        "Fields accepted when creating or updating a chapter.",
        "Fields accepted when creating or updating a page.",
    }
    for entry in one_of_entries[:4]:
        assert entry.get("unevaluatedProperties") is False
    # Removed raw object payload schema to comply with MCP strict mode
    # Users can still pass custom fields via JSON string
    assert any(entry.get("type") == "string" for entry in one_of_entries)
    assert any(entry.get("type") == "null" for entry in one_of_entries)
    assert all(
        entry.get("unevaluatedProperties") is False
        for entry in one_of_entries[:4]
    )
