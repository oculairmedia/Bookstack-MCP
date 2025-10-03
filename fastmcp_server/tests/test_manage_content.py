"""Tests for the consolidated bookstack_manage_content tool."""
from __future__ import annotations

import base64
import json

import pytest
from pytest import MonkeyPatch
from fastmcp import FastMCP

import fastmcp_server.bookstack.tools as tools
from fastmcp_server.bookstack.tools import PreparedImage, ToolError, register_bookstack_tools


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


@pytest.mark.asyncio
async def test_update_book_cover_uses_multipart(monkeypatch: MonkeyPatch) -> None:
    payload = {"id": 85, "name": "Graphiti Architecture"}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    captured: Dict[str, Any] = {}

    def fake_form(method: str, path: str, *, data=None, files=None):
        captured["method"] = method
        captured["path"] = path
        captured["data"] = data
        captured["files"] = files
        return payload

    monkeypatch.setattr(tools, "_bookstack_request_form", fake_form)
    monkeypatch.setattr(tools, "_bookstack_request", pytest.fail)

    tool = await mcp.get_tool("bookstack_manage_content")
    cover_bytes = base64.b64encode(b"fake-image-bytes").decode("ascii")
    result = await tool.run(
        {
            "operation": "update",
            "entity_type": "book",
            "id": 85,
            "name": "Graphiti Architecture",
            "cover_image": cover_bytes,
        }
    )

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert captured.get("method") == "POST"
    assert captured.get("path") == "/api/books/85"
    assert captured.get("data", {}).get("_method") == "PUT"
    assert "image" in captured.get("files", {})
    filename, content, mime_type = captured["files"]["image"]
    assert filename.startswith("Graphiti")
    assert content == b"fake-image-bytes"
    assert mime_type == "application/octet-stream"


@pytest.mark.asyncio
async def test_updates_accepts_json_string(monkeypatch: MonkeyPatch) -> None:
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    captured: Dict[str, Any] = {}

    def fake_request(method: str, path: str, *, params=None, json=None):
        captured["method"] = method
        captured["path"] = path
        captured["json"] = json
        return {"id": 5}

    monkeypatch.setattr(tools, "_bookstack_request", fake_request)

    tool = await mcp.get_tool("bookstack_manage_content")
    await tool.run(
        {
            "operation": "update",
            "entity_type": "book",
            "id": 5,
            "updates": json.dumps({"description": "Parsed", "name": "Docs"}),
        }
    )

    assert captured["method"] == "PUT"
    assert captured["path"] == "/api/books/5"
    assert captured["json"] == {"description": "Parsed", "name": "Docs"}


@pytest.mark.asyncio
async def test_update_book_cover_from_gallery_image(monkeypatch: MonkeyPatch) -> None:
    payload = {"id": 85, "name": "Graphiti Architecture"}
    gallery_meta = {
        "id": 10,
        "name": "GraphRag-Figure1.jpg",
        "url": "https://cdn.example.com/GraphRag-Figure1.jpg",
    }

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    captured: Dict[str, Any] = {}
    dummy_image = PreparedImage(
        filename="GraphRag-Figure1.jpg",
        content=b"gallery-bytes",
        mime_type="image/jpeg",
    )

    def fake_request(method: str, path: str, *, params=None, json=None):
        assert method == "GET"
        assert path == "/api/image-gallery/10"
        return gallery_meta

    def fake_fetch(url: str, fallback_name: str) -> PreparedImage:
        assert url == gallery_meta["url"]
        assert "GraphRag" in fallback_name or fallback_name.startswith("book-")
        return dummy_image

    def fake_form(method: str, path: str, *, data=None, files=None):
        captured["method"] = method
        captured["path"] = path
        captured["data"] = data
        captured["files"] = files
        return payload

    monkeypatch.setattr(tools, "_bookstack_request_form", fake_form)
    monkeypatch.setattr(tools, "_bookstack_request", fake_request)
    monkeypatch.setattr(tools, "_fetch_image_from_url", fake_fetch)

    tool = await mcp.get_tool("bookstack_manage_content")
    result = await tool.run(
        {
            "operation": "update",
            "entity_type": "book",
            "id": 85,
            "image_id": 10,
        }
    )

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert captured.get("method") == "POST"
    assert captured.get("path") == "/api/books/85"
    assert captured.get("data", {}).get("_method") == "PUT"
    assert "image" in captured.get("files", {})
    assert captured["files"]["image"] == (
        dummy_image.filename,
        dummy_image.content,
        dummy_image.mime_type,
    )


@pytest.mark.asyncio
async def test_create_book_with_gallery_image(monkeypatch: MonkeyPatch) -> None:
    payload = {"id": 101, "name": "Architecture Handbook"}
    gallery_meta = {
        "id": 12,
        "name": "handbook-cover.png",
        "url": "https://cdn.example.com/handbook-cover.png",
    }

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    captured: Dict[str, Any] = {}
    dummy_image = PreparedImage(
        filename="handbook-cover.png",
        content=b"handbook-bytes",
        mime_type="image/png",
    )

    def fake_request(method: str, path: str, *, params=None, json=None):
        assert method == "GET"
        assert path == "/api/image-gallery/12"
        return gallery_meta

    def fake_fetch(url: str, fallback_name: str) -> PreparedImage:
        assert url == gallery_meta["url"]
        assert fallback_name in {"Architecture Handbook", "handbook-cover.png"}
        return dummy_image

    def fake_form(method: str, path: str, *, data=None, files=None):
        captured["method"] = method
        captured["path"] = path
        captured["data"] = data
        captured["files"] = files
        return payload

    monkeypatch.setattr(tools, "_bookstack_request_form", fake_form)
    monkeypatch.setattr(tools, "_bookstack_request", fake_request)
    monkeypatch.setattr(tools, "_fetch_image_from_url", fake_fetch)

    tool = await mcp.get_tool("bookstack_manage_content")
    result = await tool.run(
        {
            "operation": "create",
            "entity_type": "book",
            "name": "Architecture Handbook",
            "description": "Design notes",
            "image_id": 12,
        }
    )

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert captured.get("method") == "POST"
    assert captured.get("path") == "/api/books"
    assert captured.get("data") == {"name": "Architecture Handbook", "description": "Design notes"}
    assert captured.get("files", {}).get("image") == (
        dummy_image.filename,
        dummy_image.content,
        dummy_image.mime_type,
    )
