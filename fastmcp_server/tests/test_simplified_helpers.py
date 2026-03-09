"""Regression tests for simplified BookStack helpers."""
from __future__ import annotations

import json

import pytest
from fastmcp import FastMCP
from pytest import MonkeyPatch

import fastmcp_server.bookstack.tools_simplified as simplified_tools
from fastmcp_server.bookstack.tools_simplified import register_simplified_bookstack_tools


@pytest.mark.asyncio
async def test_simplified_crud_create_page_uses_book_scope(monkeypatch: MonkeyPatch) -> None:
    mcp = FastMCP("test")
    register_simplified_bookstack_tools(mcp)

    captured: dict[str, object] = {}

    def fake_request(method: str, path: str, *, params=None, json=None):
        captured["method"] = method
        captured["path"] = path
        captured["params"] = params
        captured["json"] = json
        return {"id": 501, "name": json.get("name") if isinstance(json, dict) else None}

    monkeypatch.setattr(simplified_tools, "_bookstack_request", fake_request)

    tool = await mcp.get_tool("bookstack_content_crud")
    result = await tool.run(
        {
            "action": "create_page",
            "data": json.dumps(
                {
                    "name": "Simplified Page",
                    "markdown": "# Simplified",
                    "book_id": 85,
                    "chapter_id": 0,
                }
            ),
        }
    )

    response = json.loads(result.content[0].text)
    assert response["success"] is True
    assert response["action"] == "create_page"

    payload = captured.get("json")
    assert captured.get("method") == "POST"
    assert captured.get("path") == "/api/pages"
    assert isinstance(payload, dict)
    assert payload.get("book_id") == 85
    assert "chapter_id" not in payload
    assert payload.get("markdown") == "# Simplified"


@pytest.mark.asyncio
async def test_simplified_batch_create_page_strips_placeholder(monkeypatch: MonkeyPatch) -> None:
    mcp = FastMCP("test")
    register_simplified_bookstack_tools(mcp)

    # Ensure network is not invoked in dry-run mode
    monkeypatch.setattr(simplified_tools, "_bookstack_request", pytest.fail)

    tool = await mcp.get_tool("bookstack_batch_operations")
    result = await tool.run(
        {
            "operation": "bulk_create",
            "entity_type": "page",
            "dry_run": True,
            "items": [
                {
                    "data": {
                        "name": "Dry Run Page",
                        "book_id": 33,
                        "chapter_id": 0,
                        "markdown": "Dry run",
                    }
                }
            ],
        }
    )

    response = json.loads(result.content[0].text)
    assert response["success_count"] == 1
    payload = response["results"][0]["payload"]
    assert payload == {"name": "Dry Run Page", "book_id": 33, "markdown": "Dry run"}
