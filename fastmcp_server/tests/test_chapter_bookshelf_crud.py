"""Tests for chapter and bookshelf CRUD operations in bookstack_manage_content tool."""
from __future__ import annotations

import json
from typing import Any, Dict

import pytest
from pytest import MonkeyPatch
from fastmcp import FastMCP

import fastmcp_server.bookstack.tools as tools
from fastmcp_server.bookstack.tools import ToolError, register_bookstack_tools


# ===== Chapter Tests =====


@pytest.mark.asyncio
async def test_create_chapter_sends_expected_payload() -> None:
    """Test that creating a chapter sends the correct POST request with required fields."""
    response_payload = {"id": 10, "name": "Introduction", "book_id": 5, "description": "Getting started"}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    with MonkeyPatch.context() as monkeypatch:
        def fake_request(method: str, path: str, *, params=None, json=None):
            assert method == "POST"
            assert path == "/api/chapters"
            assert params is None
            assert json == {
                "name": "Introduction",
                "book_id": 5,
                "description": "Getting started",
            }
            return response_payload

        monkeypatch.setattr(tools, "_bookstack_request", fake_request)

        tool = await mcp.get_tool("bookstack_manage_content")
        result = await tool.run(
            {
                "operation": "create",
                "entity_type": "chapter",
                "name": "Introduction",
                "book_id": 5,
                "description": "Getting started",
            }
        )

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["id"] == 10
    assert data["data"] == response_payload


@pytest.mark.asyncio
async def test_create_chapter_with_priority() -> None:
    """Test that creating a chapter with priority includes it in the payload."""
    response_payload = {"id": 11, "name": "Advanced Topics", "book_id": 5, "priority": 10}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    captured: Dict[str, Any] = {}

    with MonkeyPatch.context() as monkeypatch:
        def fake_request(method: str, path: str, *, params=None, json=None):
            captured["method"] = method
            captured["path"] = path
            captured["json"] = json
            return response_payload

        monkeypatch.setattr(tools, "_bookstack_request", fake_request)

        tool = await mcp.get_tool("bookstack_manage_content")
        result = await tool.run(
            {
                "operation": "create",
                "entity_type": "chapter",
                "name": "Advanced Topics",
                "book_id": 5,
                "priority": 10,
            }
        )

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert captured["method"] == "POST"
    assert captured["path"] == "/api/chapters"
    assert captured["json"]["priority"] == 10


@pytest.mark.asyncio
async def test_create_chapter_rejects_missing_book_id() -> None:
    """Test that creating a chapter without book_id raises a ToolError with a helpful hint."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    tool = await mcp.get_tool("bookstack_manage_content")

    with MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(tools, "_bookstack_request", pytest.fail)  # should not be invoked

        with pytest.raises(ToolError) as exc:
            await tool.run(
                {
                    "operation": "create",
                    "entity_type": "chapter",
                    "name": "Introduction",
                }
            )

    message = str(exc.value)
    assert "'book_id' is required" in message.lower() or "'book_id'" in message


@pytest.mark.asyncio
async def test_create_chapter_validates_name_is_present() -> None:
    """Test that creating a chapter without a name raises a ToolError."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    tool = await mcp.get_tool("bookstack_manage_content")

    with MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(tools, "_bookstack_request", pytest.fail)  # should not be invoked

        with pytest.raises(ToolError) as exc:
            await tool.run(
                {
                    "operation": "create",
                    "entity_type": "chapter",
                    "book_id": 5,
                }
            )

    message = str(exc.value)
    assert "'name' is required" in message


@pytest.mark.asyncio
async def test_read_chapter_sends_get_request() -> None:
    """Test that reading a chapter sends GET to /api/chapters/{id}."""
    response_payload = {"id": 10, "name": "Introduction", "book_id": 5}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    with MonkeyPatch.context() as monkeypatch:
        def fake_request(method: str, path: str, *, params=None, json=None):
            assert method == "GET"
            assert path == "/api/chapters/10"
            assert params is None
            assert json is None
            return response_payload

        monkeypatch.setattr(tools, "_bookstack_request", fake_request)

        tool = await mcp.get_tool("bookstack_manage_content")
        result = await tool.run(
            {
                "operation": "read",
                "entity_type": "chapter",
                "id": 10,
            }
        )

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["data"] == response_payload


@pytest.mark.asyncio
async def test_update_chapter_sends_put_request() -> None:
    """Test that updating a chapter sends PUT to /api/chapters/{id} with updated fields."""
    response_payload = {"id": 10, "name": "Updated Chapter", "description": "New description"}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    captured: Dict[str, Any] = {}

    with MonkeyPatch.context() as monkeypatch:
        def fake_request(method: str, path: str, *, params=None, json=None):
            captured["method"] = method
            captured["path"] = path
            captured["json"] = json
            return response_payload

        monkeypatch.setattr(tools, "_bookstack_request", fake_request)

        tool = await mcp.get_tool("bookstack_manage_content")
        result = await tool.run(
            {
                "operation": "update",
                "entity_type": "chapter",
                "id": 10,
                "name": "Updated Chapter",
                "description": "New description",
            }
        )

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert captured["method"] == "PUT"
    assert captured["path"] == "/api/chapters/10"
    assert captured["json"]["name"] == "Updated Chapter"
    assert captured["json"]["description"] == "New description"


@pytest.mark.asyncio
async def test_update_chapter_without_id_raises_error() -> None:
    """Test that updating a chapter without id raises ToolError."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    tool = await mcp.get_tool("bookstack_manage_content")

    with MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(tools, "_bookstack_request", pytest.fail)  # should not be invoked

        with pytest.raises(ToolError) as exc:
            await tool.run(
                {
                    "operation": "update",
                    "entity_type": "chapter",
                    "name": "Updated Chapter",
                }
            )

    assert "'id' is required when updating an entity" in str(exc.value)


@pytest.mark.asyncio
async def test_delete_chapter_sends_delete_request() -> None:
    """Test that deleting a chapter sends DELETE to /api/chapters/{id}."""
    response_payload = {"success": True, "status": 204}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    with MonkeyPatch.context() as monkeypatch:
        def fake_request(method: str, path: str, *, params=None, json=None):
            assert method == "DELETE"
            assert path == "/api/chapters/10"
            assert params is None
            assert json is None
            return response_payload

        monkeypatch.setattr(tools, "_bookstack_request", fake_request)

        tool = await mcp.get_tool("bookstack_manage_content")
        result = await tool.run(
            {
                "operation": "delete",
                "entity_type": "chapter",
                "id": 10,
            }
        )

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["data"] == response_payload


# ===== Bookshelf Tests =====


@pytest.mark.asyncio
async def test_create_bookshelf_sends_expected_payload() -> None:
    """Test that creating a bookshelf sends the correct POST request."""
    response_payload = {"id": 20, "name": "Technical Docs", "description": "All technical documentation"}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    with MonkeyPatch.context() as monkeypatch:
        def fake_request(method: str, path: str, *, params=None, json=None):
            assert method == "POST"
            assert path == "/api/bookshelves"
            assert params is None
            assert json == {
                "name": "Technical Docs",
                "description": "All technical documentation",
            }
            return response_payload

        monkeypatch.setattr(tools, "_bookstack_request", fake_request)

        tool = await mcp.get_tool("bookstack_manage_content")
        result = await tool.run(
            {
                "operation": "create",
                "entity_type": "bookshelf",
                "name": "Technical Docs",
                "description": "All technical documentation",
            }
        )

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["id"] == 20
    assert data["data"] == response_payload


@pytest.mark.asyncio
async def test_create_bookshelf_with_books_list() -> None:
    """Test that creating a bookshelf normalizes books list into array of book IDs."""
    response_payload = {"id": 21, "name": "Engineering", "books": [1, 2, 3]}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    captured: Dict[str, Any] = {}

    with MonkeyPatch.context() as monkeypatch:
        def fake_request(method: str, path: str, *, params=None, json=None):
            captured["method"] = method
            captured["path"] = path
            captured["json"] = json
            return response_payload

        monkeypatch.setattr(tools, "_bookstack_request", fake_request)

        tool = await mcp.get_tool("bookstack_manage_content")
        result = await tool.run(
            {
                "operation": "create",
                "entity_type": "bookshelf",
                "name": "Engineering",
                "books": [1, 2, 3],
            }
        )

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert captured["method"] == "POST"
    assert captured["path"] == "/api/bookshelves"
    assert captured["json"]["books"] == [1, 2, 3]


@pytest.mark.asyncio
async def test_create_bookshelf_validates_name_is_present() -> None:
    """Test that creating a bookshelf without a name raises a ToolError."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    tool = await mcp.get_tool("bookstack_manage_content")

    with MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(tools, "_bookstack_request", pytest.fail)  # should not be invoked

        with pytest.raises(ToolError) as exc:
            await tool.run(
                {
                    "operation": "create",
                    "entity_type": "bookshelf",
                    "description": "A shelf without a name",
                }
            )

    message = str(exc.value)
    assert "'name' is required" in message


@pytest.mark.asyncio
async def test_read_bookshelf_sends_get_request() -> None:
    """Test that reading a bookshelf sends GET to /api/bookshelves/{id}."""
    response_payload = {"id": 20, "name": "Technical Docs", "books": []}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    with MonkeyPatch.context() as monkeypatch:
        def fake_request(method: str, path: str, *, params=None, json=None):
            assert method == "GET"
            assert path == "/api/bookshelves/20"
            assert params is None
            assert json is None
            return response_payload

        monkeypatch.setattr(tools, "_bookstack_request", fake_request)

        tool = await mcp.get_tool("bookstack_manage_content")
        result = await tool.run(
            {
                "operation": "read",
                "entity_type": "bookshelf",
                "id": 20,
            }
        )

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["data"] == response_payload


@pytest.mark.asyncio
async def test_update_bookshelf_sends_put_request() -> None:
    """Test that updating a bookshelf sends PUT to /api/bookshelves/{id}."""
    response_payload = {"id": 20, "name": "Updated Shelf", "description": "New description"}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    captured: Dict[str, Any] = {}

    with MonkeyPatch.context() as monkeypatch:
        def fake_request(method: str, path: str, *, params=None, json=None):
            captured["method"] = method
            captured["path"] = path
            captured["json"] = json
            return response_payload

        monkeypatch.setattr(tools, "_bookstack_request", fake_request)

        tool = await mcp.get_tool("bookstack_manage_content")
        result = await tool.run(
            {
                "operation": "update",
                "entity_type": "bookshelf",
                "id": 20,
                "name": "Updated Shelf",
                "description": "New description",
            }
        )

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert captured["method"] == "PUT"
    assert captured["path"] == "/api/bookshelves/20"
    assert captured["json"]["name"] == "Updated Shelf"
    assert captured["json"]["description"] == "New description"


@pytest.mark.asyncio
async def test_update_bookshelf_without_id_raises_error() -> None:
    """Test that updating a bookshelf without id raises ToolError."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    tool = await mcp.get_tool("bookstack_manage_content")

    with MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(tools, "_bookstack_request", pytest.fail)  # should not be invoked

        with pytest.raises(ToolError) as exc:
            await tool.run(
                {
                    "operation": "update",
                    "entity_type": "bookshelf",
                    "name": "Updated Shelf",
                }
            )

    assert "'id' is required when updating an entity" in str(exc.value)


@pytest.mark.asyncio
async def test_delete_bookshelf_sends_delete_request() -> None:
    """Test that deleting a bookshelf sends DELETE to /api/bookshelves/{id}."""
    response_payload = {"success": True, "status": 204}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    with MonkeyPatch.context() as monkeypatch:
        def fake_request(method: str, path: str, *, params=None, json=None):
            assert method == "DELETE"
            assert path == "/api/bookshelves/20"
            assert params is None
            assert json is None
            return response_payload

        monkeypatch.setattr(tools, "_bookstack_request", fake_request)

        tool = await mcp.get_tool("bookstack_manage_content")
        result = await tool.run(
            {
                "operation": "delete",
                "entity_type": "bookshelf",
                "id": 20,
            }
        )

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["data"] == response_payload
