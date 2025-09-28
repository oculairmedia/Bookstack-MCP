"""Tests for the BookStack image management FastMCP tool."""
from __future__ import annotations

import base64
import json
from typing import Any, Dict

import pytest
from fastmcp import FastMCP
from pytest import MonkeyPatch

import fastmcp_server.bookstack.tools as tools
from fastmcp_server.bookstack.tools import ToolError, register_bookstack_tools


@pytest.fixture(autouse=True)
def clear_image_cache() -> None:
    tools._invalidate_list_cache()
    yield
    tools._invalidate_list_cache()


@pytest.mark.asyncio
async def test_image_create_uses_form_payload(monkeypatch: MonkeyPatch) -> None:
    payload = {"id": 5, "name": "Logo"}
    captured_files: Dict[str, Any] = {}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    def fake_form(method: str, path: str, *, data=None, files=None):
        assert method == "POST"
        assert path == "/api/image-gallery"
        assert data == {"name": "Logo"}
        assert files is not None and "image" in files
        image_tuple = files["image"]
        assert image_tuple[0] == "Logo"
        assert isinstance(image_tuple[1], (bytes, bytearray))
        captured_files.update(files)
        return payload

    monkeypatch.setattr(tools, "_bookstack_request_form", fake_form)
    monkeypatch.setattr(tools, "_bookstack_request", pytest.fail)

    tool = await mcp.get_tool("bookstack_manage_images")
    image_data = base64.b64encode(b"sample-bytes").decode("ascii")
    result = await tool.run(
        {
            "operation": "create",
            "name": "Logo",
            "image": image_data,
        }
    )

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["data"] == payload
    assert "image" in captured_files


@pytest.mark.asyncio
async def test_image_update_requires_target(monkeypatch: MonkeyPatch) -> None:
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    tool = await mcp.get_tool("bookstack_manage_images")

    with MonkeyPatch.context() as patch:
        patch.setattr(tools, "_bookstack_request_form", pytest.fail)

        with pytest.raises(ToolError) as exc:
            await tool.run({"operation": "update"})

    assert "'id' is required" in str(exc.value)


@pytest.mark.asyncio
async def test_image_update_sends_new_payload(monkeypatch: MonkeyPatch) -> None:
    payload = {"id": 7, "name": "Logo v2"}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    def fake_form(method: str, path: str, *, data=None, files=None):
        assert method == "PUT"
        assert path == "/api/image-gallery/7"
        assert data == {"name": "Logo v2"}
        assert "image" in files
        filename, content, mime_type = files["image"]
        assert filename == "Logo v2"
        assert content
        assert mime_type == "application/octet-stream"
        return payload

    monkeypatch.setattr(tools, "_bookstack_request_form", fake_form)
    monkeypatch.setattr(tools, "_bookstack_request", pytest.fail)

    tool = await mcp.get_tool("bookstack_manage_images")
    result = await tool.run(
        {
            "operation": "update",
            "id": 7,
            "new_name": "Logo v2",
            "new_image": base64.b64encode(b"updated-bytes").decode("ascii"),
        }
    )

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["data"] == payload


@pytest.mark.asyncio
async def test_image_delete_calls_api(monkeypatch: MonkeyPatch) -> None:
    payload = {"status": 204}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    def fake_request(method: str, path: str, *, params=None, json=None):
        assert method == "DELETE"
        assert path == "/api/image-gallery/3"
        assert params is None and json is None
        return payload

    monkeypatch.setattr(tools, "_bookstack_request", fake_request)

    tool = await mcp.get_tool("bookstack_manage_images")
    result = await tool.run({"operation": "delete", "id": 3})

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["data"] == payload


@pytest.mark.asyncio
async def test_image_list_uses_cache(monkeypatch: MonkeyPatch) -> None:
    first_payload = {
        "data": [{"id": 1}, {"id": 2}],
        "total": 2,
        "count": 2,
        "offset": 0,
    }

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    call_counter = {"count": 0}

    def fake_request(method: str, path: str, *, params=None, json=None):
        call_counter["count"] += 1
        assert method == "GET"
        assert path == "/api/image-gallery"
        assert params == {"offset": 0, "count": 2}
        return first_payload

    monkeypatch.setattr(tools, "_bookstack_request", fake_request)

    tool = await mcp.get_tool("bookstack_manage_images")
    first_result = await tool.run({"operation": "list", "offset": 0, "count": 2})
    first_data = json.loads(first_result.content[0].text)
    assert first_data["data"] == first_payload["data"]
    assert first_data["metadata"]["count"] == 2
    assert first_data["metadata"].get("cached") is None

    monkeypatch.setattr(tools, "_bookstack_request", pytest.fail)
    second_result = await tool.run({"operation": "list", "offset": 0, "count": 2})
    second_data = json.loads(second_result.content[0].text)
    assert second_data["data"] == first_payload["data"]
    assert second_data["metadata"]["cached"] is True
    assert call_counter["count"] == 1
