"""Tests for BookStack MCP resource endpoints (bookstack-mcp-55w)."""
from __future__ import annotations

from typing import Any, Dict

import pytest
from fastmcp import FastMCP
from pytest import MonkeyPatch

import fastmcp_server.bookstack.tools as tools
from fastmcp_server.bookstack.tools import register_bookstack_tools


@pytest.mark.asyncio
async def test_bookstack_book_resource_returns_api_response(monkeypatch: MonkeyPatch) -> None:
    """Test that bookstack_book_resource returns API response for valid book_id."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    expected_response = {"id": 42, "name": "Test Book", "slug": "test-book"}

    calls: list[tuple[str, str]] = []

    def fake_request(method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        calls.append((method, path))
        return expected_response

    monkeypatch.setattr(tools, "_bookstack_request", fake_request)

    # Get the resource template and call the underlying function
    resource = await mcp.get_resource_template("resource://bookstack/books/{book_id}")
    result = resource.fn(book_id=42)

    assert result == expected_response
    assert calls == [("GET", "/api/books/42")]


@pytest.mark.asyncio
async def test_bookstack_page_resource_returns_api_response(monkeypatch: MonkeyPatch) -> None:
    """Test that bookstack_page_resource returns API response for valid page_id."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    expected_response = {"id": 123, "name": "Test Page", "book_id": 42}

    calls: list[tuple[str, str]] = []

    def fake_request(method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        calls.append((method, path))
        return expected_response

    monkeypatch.setattr(tools, "_bookstack_request", fake_request)

    # Get the resource template and call the underlying function
    resource = await mcp.get_resource_template("resource://bookstack/pages/{page_id}")
    result = resource.fn(page_id=123)

    assert result == expected_response
    assert calls == [("GET", "/api/pages/123")]


@pytest.mark.asyncio
async def test_book_resource_validates_entity_id(monkeypatch: MonkeyPatch) -> None:
    """Test that book resource validates the entity ID."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    
    # Validation happens before the request, so we shouldn't reach the fake_request
    def fake_request(method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        pytest.fail("Should not reach _bookstack_request with invalid ID")
    
    monkeypatch.setattr(tools, "_bookstack_request", fake_request)
    
    # Get the resource function
    resource = await mcp.get_resource_template("resource://bookstack/books/{book_id}")
    
    # Try to call with invalid book_id (0 or negative)
    with pytest.raises(Exception):
        resource.fn(book_id=0)


@pytest.mark.asyncio
async def test_page_resource_validates_entity_id(monkeypatch: MonkeyPatch) -> None:
    """Test that page resource validates the entity ID."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    
    # Validation happens before the request
    def fake_request(method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        pytest.fail("Should not reach _bookstack_request with invalid ID")
    
    monkeypatch.setattr(tools, "_bookstack_request", fake_request)
    
    # Get the resource function
    resource = await mcp.get_resource_template("resource://bookstack/pages/{page_id}")
    
    # Try to call with invalid page_id
    with pytest.raises(Exception):
        resource.fn(page_id=-1)
