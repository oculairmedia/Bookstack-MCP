"""Tests for BookStack search edge cases (bookstack-mcp-kbj)."""
from __future__ import annotations

import json
from typing import Any, Dict

import pytest
from fastmcp import FastMCP
from pytest import MonkeyPatch

import fastmcp_server.bookstack.tools as tools
from fastmcp_server.bookstack.tools import register_bookstack_tools


@pytest.mark.asyncio
async def test_search_with_empty_results(monkeypatch: MonkeyPatch) -> None:
    """Test that search returns success with empty results array."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    
    empty_response = {
        "total": 0,
        "data": [],
    }
    
    def fake_request(method: str, path: str, **kwargs) -> Dict[str, Any]:
        assert method == "GET"
        assert path == "/api/search"
        return empty_response
    
    monkeypatch.setattr(tools, "_bookstack_request", fake_request)
    
    tool = await mcp.get_tool("bookstack_search")
    result = await tool.run({"query": "nonexistent"})
    
    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["total"] == 0
    assert data["results"] == []


@pytest.mark.asyncio
async def test_search_results_without_book_chapter_info(monkeypatch: MonkeyPatch) -> None:
    """Test that results without book/chapter info handle missing fields gracefully."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    
    response = {
        "total": 1,
        "data": [
            {
                "id": 1,
                "type": "page",
                "name": "Orphan Page",
                "url": "https://example.com/page/1",
                "preview_html": {"content": "Content"},
                # No book or chapter fields
            },
        ],
    }
    
    def fake_request(method: str, path: str, **kwargs) -> Dict[str, Any]:
        assert method == "GET"
        assert path == "/api/search"
        return response
    
    monkeypatch.setattr(tools, "_bookstack_request", fake_request)
    
    tool = await mcp.get_tool("bookstack_search")
    result = await tool.run({"query": "orphan"})
    
    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert len(data["results"]) == 1
    first = data["results"][0]
    assert first["title"] == "Orphan Page"
    # Book and chapter fields should not be present
    assert "book" not in first
    assert "chapter" not in first


@pytest.mark.asyncio
async def test_search_results_with_slug_but_no_name(monkeypatch: MonkeyPatch) -> None:
    """Test that results with slug but no name use the slug."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    
    response = {
        "total": 1,
        "data": [
            {
                "id": 2,
                "type": "chapter",
                "slug": "introduction-chapter",
                "url": "https://example.com/chapter/2",
                # No name field, only slug
            },
        ],
    }
    
    def fake_request(method: str, path: str, **kwargs) -> Dict[str, Any]:
        assert method == "GET"
        assert path == "/api/search"
        return response
    
    monkeypatch.setattr(tools, "_bookstack_request", fake_request)
    
    tool = await mcp.get_tool("bookstack_search")
    result = await tool.run({"query": "intro"})
    
    data = json.loads(result.content[0].text)
    assert data["success"] is True
    first = data["results"][0]
    # Should use slug as title when name is missing
    assert first["title"] == "introduction-chapter"


@pytest.mark.asyncio
async def test_search_preview_html_content_extraction(monkeypatch: MonkeyPatch) -> None:
    """Test that preview_html content is properly extracted."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    
    response = {
        "total": 1,
        "data": [
            {
                "id": 3,
                "type": "page",
                "name": "Installation Guide",
                "url": "https://example.com/page/3",
                "preview_html": {
                    "content": "<p>Follow these <strong>steps</strong> to install.</p>"
                },
            },
        ],
    }
    
    def fake_request(method: str, path: str, **kwargs) -> Dict[str, Any]:
        assert method == "GET"
        assert path == "/api/search"
        return response
    
    monkeypatch.setattr(tools, "_bookstack_request", fake_request)
    
    tool = await mcp.get_tool("bookstack_search")
    result = await tool.run({"query": "install"})
    
    data = json.loads(result.content[0].text)
    assert data["success"] is True
    first = data["results"][0]
    # Should extract text content from HTML
    assert "summary" in first
    assert "Follow these" in first["summary"]
    assert "steps" in first["summary"]


@pytest.mark.asyncio
async def test_search_count_and_page_params_forwarded(monkeypatch: MonkeyPatch) -> None:
    """Test that count and page parameters are correctly forwarded to API."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    
    response = {
        "total": 100,
        "data": [
            {"id": 10, "type": "page", "name": "Page 10", "url": "https://example.com/page/10"},
        ],
    }
    
    def fake_request(method: str, path: str, *, params=None, **kwargs) -> Dict[str, Any]:
        assert method == "GET"
        assert path == "/api/search"
        assert params is not None
        assert params["query"] == "test"
        assert params["count"] == 1
        assert params["page"] == 10
        return response
    
    monkeypatch.setattr(tools, "_bookstack_request", fake_request)
    
    tool = await mcp.get_tool("bookstack_search")
    result = await tool.run({
        "query": "test",
        "count": 1,
        "page": 10,
    })
    
    data = json.loads(result.content[0].text)
    assert data["success"] is True


@pytest.mark.asyncio
async def test_search_with_description_field(monkeypatch: MonkeyPatch) -> None:
    """Test that description field is included when present."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    
    response = {
        "total": 1,
        "data": [
            {
                "id": 4,
                "type": "chapter",
                "name": "Overview",
                "slug": "overview",
                "url": "https://example.com/chapter/4",
                "description": "This chapter provides an overview of the system.",
            },
        ],
    }
    
    def fake_request(method: str, path: str, **kwargs) -> Dict[str, Any]:
        assert method == "GET"
        assert path == "/api/search"
        return response
    
    monkeypatch.setattr(tools, "_bookstack_request", fake_request)
    
    tool = await mcp.get_tool("bookstack_search")
    result = await tool.run({"query": "overview"})
    
    data = json.loads(result.content[0].text)
    assert data["success"] is True
    first = data["results"][0]
    assert first["title"] == "Overview"
    # Description should be used as summary when preview_html is not present
    assert "summary" in first
    assert "overview of the system" in first["summary"]
