"""Tests for the consolidated bookstack_manage_content tool."""
from __future__ import annotations

import json

import pytest
from pytest import MonkeyPatch
from fastmcp import FastMCP

import fastmcp_server.bookstack.tools as tools
from fastmcp_server.bookstack.tools import ToolError, register_bookstack_tools


@pytest.mark.asyncio
async def test_create_book_sends_expected_payload() -> None:
    response_payload = {"id": 42, "name": "Docs", "description": "Team handbook"}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    with MonkeyPatch.context() as monkeypatch:
        def fake_request(method: str, path: str, *, params=None, json=None):
            assert method == "POST"
            assert path == "/api/books"
            assert params is None
            assert json == {"name": "Docs", "description": "Team handbook"}
            return response_payload

        monkeypatch.setattr(tools, "_bookstack_request", fake_request)

        tool = await mcp.get_tool("bookstack_manage_content")
        result = await tool.run(
            {
                "operation": "create",
                "entity_type": "book",
                "name": " Docs ",
                "description": "Team handbook",
            }
        )

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["id"] == 42
    assert data["data"] == response_payload


@pytest.mark.asyncio
async def test_update_requires_identifier() -> None:
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    tool = await mcp.get_tool("bookstack_manage_content")

    with MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(tools, "_bookstack_request", pytest.fail)  # should not be invoked

        with pytest.raises(ToolError) as exc:
            await tool.run({"operation": "update", "entity_type": "book"})

    assert "'id' is required when updating an entity" in str(exc.value)


@pytest.mark.asyncio
async def test_create_page_requires_scope_hint() -> None:
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    tool = await mcp.get_tool("bookstack_manage_content")

    with MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(tools, "_bookstack_request", pytest.fail)  # should not be invoked

        with pytest.raises(ToolError) as exc:
            await tool.run(
                {
                    "operation": "create",
                    "entity_type": "page",
                    "name": "Release notes",
                }
            )

    message = str(exc.value)
    assert "Provide either 'book_id' or 'chapter_id'" in message
    assert "Hint:" in message


@pytest.mark.asyncio
async def test_downstream_toolerror_is_propagated() -> None:
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    mock_error = ToolError("Failed\nHint: verify API token")

    with MonkeyPatch.context() as monkeypatch:
        def raise_error(*args, **kwargs):  # type: ignore[no-untyped-def]
            raise mock_error

        monkeypatch.setattr(tools, "_bookstack_request", raise_error)

        tool = await mcp.get_tool("bookstack_manage_content")

        with pytest.raises(ToolError) as exc:
            await tool.run(
                {
                    "operation": "delete",
                    "entity_type": "book",
                    "id": 99,
                }
            )

    assert exc.value is mock_error
    assert "Hint: verify API token" in str(exc.value)
