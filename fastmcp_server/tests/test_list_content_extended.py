"""Tests for extended list content scenarios (bookstack-mcp-e3v)."""
from __future__ import annotations

import json
from typing import Any, Dict

import pytest
from fastmcp import FastMCP
from pytest import MonkeyPatch

import fastmcp_server.bookstack.tools as tools
from fastmcp_server.bookstack.tools import register_bookstack_tools


@pytest.mark.asyncio
async def test_unscoped_book_listing_with_sort_parameter(monkeypatch: MonkeyPatch) -> None:
    """Test unscoped book listing with sort parameter."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    
    api_response = {
        "data": [
            {"id": 3, "name": "Book C", "created_at": "2024-01-03T00:00:00Z"},
            {"id": 2, "name": "Book B", "created_at": "2024-01-02T00:00:00Z"},
            {"id": 1, "name": "Book A", "created_at": "2024-01-01T00:00:00Z"},
        ],
        "total": 3,
        "count": 3,
        "offset": 0,
    }
    
    def fake_request(method: str, path: str, *, params=None, **kwargs) -> Dict[str, Any]:
        assert method == "GET"
        assert path == "/api/books"
        assert params is not None
        assert params.get("sort") == "-created_at"
        return api_response
    
    monkeypatch.setattr(tools, "_bookstack_request", fake_request)
    
    tool = await mcp.get_tool("bookstack_list_content")
    result = await tool.run({
        "entity_type": "books",
        "sort": "-created_at",
    })
    
    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["metadata"]["total"] == 3
    assert data["data"]["data"][0]["id"] == 3
    assert data["data"]["data"][1]["id"] == 2
    assert data["data"]["data"][2]["id"] == 1


@pytest.mark.asyncio
async def test_unscoped_page_listing_with_offset_and_count(monkeypatch: MonkeyPatch) -> None:
    """Test unscoped page listing with offset and count parameters."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    
    api_response = {
        "data": [
            {"id": 25, "name": "Page 25"},
            {"id": 26, "name": "Page 26"},
        ],
        "total": 100,
        "count": 2,
        "offset": 24,
    }
    
    def fake_request(method: str, path: str, *, params=None, **kwargs) -> Dict[str, Any]:
        assert method == "GET"
        assert path == "/api/pages"
        assert params is not None
        assert params["offset"] == 24
        assert params["count"] == 2
        return api_response
    
    monkeypatch.setattr(tools, "_bookstack_request", fake_request)
    
    tool = await mcp.get_tool("bookstack_list_content")
    result = await tool.run({
        "entity_type": "pages",
        "offset": 24,
        "count": 2,
    })
    
    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["metadata"]["total"] == 100
    assert data["metadata"]["returned"] == 2
    assert len(data["data"]["data"]) == 2


@pytest.mark.asyncio
async def test_empty_results_for_unscoped_listing(monkeypatch: MonkeyPatch) -> None:
    """Test that empty results are handled correctly for unscoped listings."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    
    api_response = {
        "data": [],
        "total": 0,
        "count": 0,
        "offset": 0,
    }
    
    def fake_request(method: str, path: str, *, params=None, **kwargs) -> Dict[str, Any]:
        assert method == "GET"
        assert path == "/api/chapters"
        return api_response
    
    monkeypatch.setattr(tools, "_bookstack_request", fake_request)
    
    tool = await mcp.get_tool("bookstack_list_content")
    result = await tool.run({
        "entity_type": "chapters",
    })
    
    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["metadata"]["total"] == 0
    assert data["metadata"]["returned"] == 0
    assert data["data"]["data"] == []


@pytest.mark.asyncio
async def test_sort_with_leading_minus_descending(monkeypatch: MonkeyPatch) -> None:
    """Test that sort parameter with leading minus (descending) is forwarded correctly."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    
    api_response = {
        "data": [
            {"id": 10, "name": "Newest Book", "updated_at": "2024-12-31T00:00:00Z"},
            {"id": 5, "name": "Older Book", "updated_at": "2024-06-01T00:00:00Z"},
        ],
        "total": 2,
        "count": 2,
        "offset": 0,
    }
    
    def fake_request(method: str, path: str, *, params=None, **kwargs) -> Dict[str, Any]:
        assert method == "GET"
        assert path == "/api/books"
        assert params is not None
        # Verify the leading minus is preserved
        assert params.get("sort") == "-updated_at"
        return api_response
    
    monkeypatch.setattr(tools, "_bookstack_request", fake_request)
    
    tool = await mcp.get_tool("bookstack_list_content")
    result = await tool.run({
        "entity_type": "books",
        "sort": "-updated_at",
    })
    
    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["data"]["data"][0]["id"] == 10
    assert data["data"]["data"][1]["id"] == 5


@pytest.mark.asyncio
async def test_bookshelves_listing(monkeypatch: MonkeyPatch) -> None:
    """Test that bookshelves can be listed without scope."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    
    api_response = {
        "data": [
            {"id": 1, "name": "Shelf 1"},
            {"id": 2, "name": "Shelf 2"},
        ],
        "total": 2,
        "count": 2,
        "offset": 0,
    }
    
    def fake_request(method: str, path: str, *, params=None, **kwargs) -> Dict[str, Any]:
        assert method == "GET"
        assert path == "/api/bookshelves"
        return api_response
    
    monkeypatch.setattr(tools, "_bookstack_request", fake_request)
    
    tool = await mcp.get_tool("bookstack_list_content")
    result = await tool.run({
        "entity_type": "bookshelves",
    })
    
    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["metadata"]["total"] == 2
    # Scoped field is only present for scoped listings
    assert data["metadata"].get("scoped", False) is False


@pytest.mark.asyncio
async def test_chapters_listing_with_pagination(monkeypatch: MonkeyPatch) -> None:
    """Test chapters listing with offset and count pagination."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    
    api_response = {
        "data": [
            {"id": 11, "name": "Chapter 11"},
            {"id": 12, "name": "Chapter 12"},
            {"id": 13, "name": "Chapter 13"},
        ],
        "total": 50,
        "count": 3,
        "offset": 10,
    }
    
    def fake_request(method: str, path: str, *, params=None, **kwargs) -> Dict[str, Any]:
        assert method == "GET"
        assert path == "/api/chapters"
        assert params is not None
        assert params["offset"] == 10
        assert params["count"] == 3
        return api_response
    
    monkeypatch.setattr(tools, "_bookstack_request", fake_request)
    
    tool = await mcp.get_tool("bookstack_list_content")
    result = await tool.run({
        "entity_type": "chapters",
        "offset": 10,
        "count": 3,
    })
    
    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["metadata"]["total"] == 50
    assert data["metadata"]["returned"] == 3
    assert len(data["data"]["data"]) == 3
