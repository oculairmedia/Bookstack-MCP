"""Tests for the direct page tools (fastmcp_server.bookstack.tools_direct_pages)."""
from __future__ import annotations

import asyncio

import pytest
from fastmcp import FastMCP

import fastmcp_server.bookstack.tools_direct_pages as direct
from fastmcp_server.bookstack.tools_direct_pages import register_direct_page_tools


def _tool_fns() -> dict:
    mcp = FastMCP("test")
    register_direct_page_tools(mcp)
    tools = asyncio.run(mcp.get_tools())
    return {name: t.fn for name, t in tools.items()}


@pytest.fixture()
def captured(monkeypatch):
    """Capture BookStack requests and cache invalidations."""
    calls = {"requests": [], "invalidations": []}

    def fake_request(method, path, *, params=None, json=None):
        calls["requests"].append({"method": method, "path": path, "json": json})
        return {"id": 42, "name": (json or {}).get("name")}

    def fake_invalidate(entity_type, entity_id=None):
        calls["invalidations"].append((entity_type, entity_id))

    monkeypatch.setattr(direct, "_bookstack_request", fake_request)
    monkeypatch.setattr(direct, "_invalidate_entity_cache", fake_invalidate)
    return calls


def test_create_page_direct_posts_and_invalidates(captured):
    fns = _tool_fns()
    result = fns["bookstack_create_page_direct"](
        name="My Page", book_id=3, markdown="## Hi", chapter_id=None
    )
    assert result["id"] == 42
    req = captured["requests"][0]
    assert req["method"] == "POST"
    assert req["path"] == "/api/pages"
    assert req["json"]["book_id"] == 3
    assert req["json"]["markdown"] == "## Hi"
    assert captured["invalidations"] == [("page", 42)]


def test_update_page_direct_puts_and_invalidates(captured):
    fns = _tool_fns()
    result = fns["bookstack_update_page_direct"](page_id=7, name="X", markdown="body")
    assert result["id"] == 42
    req = captured["requests"][0]
    assert req["method"] == "PUT"
    assert req["path"] == "/api/pages/7"
    assert captured["invalidations"] == [("page", 7)]


def test_create_page_direct_includes_chapter_id(captured):
    fns = _tool_fns()
    fns["bookstack_create_page_direct"](
        name="P", book_id=1, markdown="m", chapter_id=99
    )
    assert captured["requests"][0]["json"]["chapter_id"] == 99


def test_safe_markdown_path_rejects_outside_data():
    with pytest.raises(ValueError):
        direct._safe_markdown_path("/etc/passwd")
