"""Tests for BookStack batch content operations."""
from __future__ import annotations

import json

import pytest
from fastmcp import FastMCP
from pytest import MonkeyPatch

import fastmcp_server.bookstack.tools as tools
from fastmcp_server.bookstack.tools import ToolError, register_bookstack_tools


@pytest.mark.asyncio
async def test_batch_dry_run_generates_prepared_requests(monkeypatch: MonkeyPatch) -> None:
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    tool = await mcp.get_tool("bookstack_batch_operations")

    monkeypatch.setattr(tools, "_bookstack_request", pytest.fail)

    result = await tool.run(
        {
            "operation": "bulk_create",
            "entity_type": "book",
            "dry_run": True,
            "items": [
                {
                    "data": {
                        "name": "Docs",
                        "description": "Team handbook",
                    }
                }
            ],
        }
    )

    data = json.loads(result.content[0].text)
    assert data["dry_run"] is True
    assert data["success_count"] == 1
    request_info = data["results"][0]
    assert request_info["method"] == "POST"
    assert request_info["path"] == "/api/books"
    assert request_info["payload"] == {"name": "Docs", "description": "Team handbook"}


@pytest.mark.asyncio
async def test_batch_processes_success_and_errors(monkeypatch: MonkeyPatch) -> None:
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    calls = []

    def fake_request(method: str, path: str, *, params=None, json=None):
        calls.append((method, path, json))
        assert method == "PUT"
        assert path == "/api/books/1"
        return {"updated": True}

    monkeypatch.setattr(tools, "_bookstack_request", fake_request)

    tool = await mcp.get_tool("bookstack_batch_operations")
    result = await tool.run(
        {
            "operation": "bulk_update",
            "entity_type": "book",
            "items": [
                {"id": 1, "data": {"description": "Updated"}},
                {"data": {"description": "Missing id"}},
            ],
            "continue_on_error": True,
        }
    )

    data = json.loads(result.content[0].text)
    assert data["success_count"] == 1
    assert data["failure_count"] == 1
    assert len(data["errors"]) == 1
    assert "Each update item requires an 'id'" in data["errors"][0]["error"]
    assert calls == [("PUT", "/api/books/1", {"description": "Updated"})]


@pytest.mark.asyncio
async def test_batch_halts_when_continue_on_error_false(monkeypatch: MonkeyPatch) -> None:
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    tool = await mcp.get_tool("bookstack_batch_operations")

    monkeypatch.setattr(tools, "_bookstack_request", pytest.fail)

    result = await tool.run(
        {
            "operation": "bulk_delete",
            "entity_type": "page",
            "continue_on_error": False,
            "items": [
                {"data": {}},
                {"id": 10, "data": {}},
            ],
        }
    )

    data = json.loads(result.content[0].text)
    assert data["success_count"] == 0
    assert data["failure_count"] == 1
    assert len(data["errors"]) == 1
    assert "Each delete item requires an 'id'" in data["errors"][0]["error"]


@pytest.mark.asyncio
async def test_batch_accepts_string_payload(monkeypatch: MonkeyPatch) -> None:
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    calls = []

    def fake_request(method: str, path: str, *, params=None, json=None):
        calls.append((method, path, json))
        return {"ok": True}

    monkeypatch.setattr(tools, "_bookstack_request", fake_request)

    tool = await mcp.get_tool("bookstack_batch_operations")
    await tool.run(
        {
            "operation": "bulk_update",
            "entity_type": "book",
            "items": [
                {"id": 3, "data": json.dumps({"name": "String Name"})},
            ],
        }
    )

    assert calls == [("PUT", "/api/books/3", {"name": "String Name"})]
