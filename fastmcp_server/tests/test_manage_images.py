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
        assert data == {"name": "Logo", "type": "gallery", "uploaded_to": 0}
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


# URL Support Tests


@pytest.mark.asyncio
async def test_image_create_from_url(monkeypatch: MonkeyPatch) -> None:
    """Test creating an image from an HTTP URL."""
    payload = {"id": 10, "name": "test-image"}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    class FakeResponse:
        status_code = 200
        headers = {"content-type": "image/png", "content-length": "1234"}

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=8192):
            yield b"fake-png-data"

    def fake_get(url, **kwargs):
        assert url == "https://example.com/image.png"
        assert kwargs.get("timeout") == 30
        assert kwargs.get("stream") is True
        return FakeResponse()

    def fake_form(method: str, path: str, *, data=None, files=None):
        assert method == "POST"
        assert path == "/api/image-gallery"
        assert data == {
            "name": "test-image",
            "type": "gallery",
            "uploaded_to": 0,
        }
        assert "image" in files
        filename, content, mime_type = files["image"]
        assert filename == "image.png"
        assert content == b"fake-png-data"
        assert mime_type == "image/png"
        return payload

    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setattr(tools, "_bookstack_request_form", fake_form)

    tool = await mcp.get_tool("bookstack_manage_images")
    result = await tool.run({
        "operation": "create",
        "name": "test-image",
        "image": "https://example.com/image.png"
    })

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["data"] == payload


@pytest.mark.asyncio
async def test_image_create_from_url_with_mime_fallback(monkeypatch: MonkeyPatch) -> None:
    """Test MIME type fallback when Content-Type header is missing."""
    payload = {"id": 11, "name": "fallback-image"}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    class FakeResponse:
        status_code = 200
        headers = {}  # No Content-Type header

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=8192):
            yield b"fake-jpeg-data"

    def fake_get(url, **kwargs):
        return FakeResponse()

    def fake_form(method: str, path: str, *, data=None, files=None):
        assert "image" in files
        filename, content, mime_type = files["image"]
        # Should guess from .jpg extension
        assert mime_type == "image/jpeg"
        assert data == {
            "name": "fallback-image",
            "type": "gallery",
            "uploaded_to": 0,
        }
        return payload

    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setattr(tools, "_bookstack_request_form", fake_form)

    tool = await mcp.get_tool("bookstack_manage_images")
    result = await tool.run({
        "operation": "create",
        "name": "fallback-image",
        "image": "https://example.com/photo.jpg"
    })

    data = json.loads(result.content[0].text)
    assert data["success"] is True


@pytest.mark.asyncio
async def test_image_create_from_url_timeout(monkeypatch: MonkeyPatch) -> None:
    """Test handling of timeout when fetching from URL."""
    import requests

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    def fake_get(url, **kwargs):
        raise requests.exceptions.Timeout("Connection timeout")

    monkeypatch.setattr("requests.get", fake_get)

    tool = await mcp.get_tool("bookstack_manage_images")

    with pytest.raises(ToolError) as exc:
        await tool.run({
            "operation": "create",
            "name": "timeout-test",
            "image": "https://slow-server.example.com/image.png"
        })

    assert "timeout" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_image_create_from_url_too_large(monkeypatch: MonkeyPatch) -> None:
    """Test size limit enforcement via Content-Length header."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    class FakeResponse:
        status_code = 200
        headers = {"content-type": "image/png", "content-length": str(100 * 1024 * 1024)}  # 100MB

        def raise_for_status(self):
            pass

    def fake_get(url, **kwargs):
        return FakeResponse()

    monkeypatch.setattr("requests.get", fake_get)

    tool = await mcp.get_tool("bookstack_manage_images")

    with pytest.raises(ToolError) as exc:
        await tool.run({
            "operation": "create",
            "name": "large-image",
            "image": "https://example.com/huge.png"
        })

    assert "too large" in str(exc.value).lower()
    # Check for the byte limit (52428800 = 50MB)
    assert "52428800" in str(exc.value) or "50" in str(exc.value)


@pytest.mark.asyncio
async def test_image_create_from_url_invalid(monkeypatch: MonkeyPatch) -> None:
    """Test rejection of invalid URLs."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    tool = await mcp.get_tool("bookstack_manage_images")

    # Test ftp:// (not allowed)
    with pytest.raises(ToolError) as exc:
        await tool.run({
            "operation": "create",
            "name": "ftp-test",
            "image": "ftp://example.com/image.png"
        })

    assert "not supported" in str(exc.value).lower() or "ftp" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_image_create_from_url_http_error(monkeypatch: MonkeyPatch) -> None:
    """Test handling of HTTP errors (404, 403, etc.)."""
    import requests

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    class FakeResponse:
        status_code = 404

        def raise_for_status(self):
            raise requests.exceptions.HTTPError(response=self)

    def fake_get(url, **kwargs):
        return FakeResponse()

    monkeypatch.setattr("requests.get", fake_get)

    tool = await mcp.get_tool("bookstack_manage_images")

    with pytest.raises(ToolError) as exc:
        await tool.run({
            "operation": "create",
            "name": "not-found",
            "image": "https://example.com/missing.png"
        })

    assert "HTTP error 404" in str(exc.value)


@pytest.mark.asyncio
async def test_image_create_from_url_with_custom_target(monkeypatch: MonkeyPatch) -> None:
    """Ensure custom image_type and uploaded_to values are forwarded."""
    payload = {"id": 15, "name": "custom-target"}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    class FakeResponse:
        status_code = 200
        headers = {"content-type": "image/png"}

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=8192):
            yield b"custom-data"

    def fake_get(url, **kwargs):
        return FakeResponse()

    def fake_form(method: str, path: str, *, data=None, files=None):
        assert data == {
            "name": "custom-target",
            "type": "drawio",
            "uploaded_to": 42,
        }
        assert "image" in files
        return payload

    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setattr(tools, "_bookstack_request_form", fake_form)

    tool = await mcp.get_tool("bookstack_manage_images")
    result = await tool.run({
        "operation": "create",
        "name": "custom-target",
        "image": "https://example.com/custom.png",
        "image_type": "drawio",
        "uploaded_to": 42,
    })

    data = json.loads(result.content[0].text)
    assert data["success"] is True


@pytest.mark.asyncio
async def test_image_update_with_url(monkeypatch: MonkeyPatch) -> None:
    """Test updating an image using a URL."""
    payload = {"id": 20, "name": "updated-image"}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    class FakeResponse:
        status_code = 200
        headers = {"content-type": "image/webp"}

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=8192):
            yield b"fake-webp-data"

    def fake_get(url, **kwargs):
        assert url == "https://cdn.example.com/new-logo.webp"
        return FakeResponse()

    def fake_form(method: str, path: str, *, data=None, files=None):
        assert method == "PUT"
        assert path == "/api/image-gallery/20"
        assert data == {"name": "new-logo"}
        assert "image" in files
        filename, content, mime_type = files["image"]
        assert filename == "new-logo.webp"
        assert mime_type == "image/webp"
        return payload

    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setattr(tools, "_bookstack_request_form", fake_form)

    tool = await mcp.get_tool("bookstack_manage_images")
    result = await tool.run({
        "operation": "update",
        "id": 20,
        "new_name": "new-logo",
        "new_image": "https://cdn.example.com/new-logo.webp"
    })

    data = json.loads(result.content[0].text)
    assert data["success"] is True


@pytest.mark.asyncio
async def test_url_filename_extraction(monkeypatch: MonkeyPatch) -> None:
    """Test filename extraction from various URL patterns."""
    payload = {"id": 30, "name": "extracted"}

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    class FakeResponse:
        status_code = 200
        headers = {"content-type": "image/png"}

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=8192):
            yield b"data"

    captured_filenames = []

    def fake_get(url, **kwargs):
        return FakeResponse()

    def fake_form(method: str, path: str, *, data=None, files=None):
        if files and "image" in files:
            captured_filenames.append(files["image"][0])
        return payload

    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setattr(tools, "_bookstack_request_form", fake_form)

    tool = await mcp.get_tool("bookstack_manage_images")

    # Test with nested path
    await tool.run({
        "operation": "create",
        "name": "extracted",
        "image": "https://example.com/assets/images/logo.png"
    })

    assert captured_filenames[-1] == "logo.png"
