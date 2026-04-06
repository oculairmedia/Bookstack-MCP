"""Tests for the BookStack semantic search tool."""
from __future__ import annotations

import json
from typing import Any, Dict

import pytest
from fastmcp import FastMCP
from pytest import MonkeyPatch

import fastmcp_server.bookstack.tools as tools
from fastmcp_server.bookstack.tools import ToolError, register_bookstack_tools


@pytest.mark.asyncio
async def test_semantic_search_happy_path(monkeypatch: MonkeyPatch) -> None:
    """Test semantic search returns results with success=True."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    fake_response = {
        "results": [
            {"title": "Test Doc", "content": "Sample content", "score": 0.95}
        ],
        "query": "test query",
    }

    class FakeResponse:
        def __init__(self, data: Dict[str, Any]) -> None:
            self._data = data
            self.status_code = 200

        def json(self):
            return self._data

        def raise_for_status(self):
            pass

    def fake_post(url: str, json: Dict[str, Any], timeout: int, headers: Dict[str, str]):
        assert "query" in json
        assert json["query"] == "test query"
        return FakeResponse(fake_response)

    monkeypatch.setattr("fastmcp_server.bookstack.tools.requests.post", fake_post)
    monkeypatch.setenv("HAYHOOKS_SEARCH_URL", "http://test-hayhooks:1416/search")

    tool = await mcp.get_tool("bookstack_semantic_search")
    result = await tool.run({"query": "test query"})

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert "results" in data


@pytest.mark.asyncio
async def test_semantic_search_default_params(monkeypatch: MonkeyPatch) -> None:
    """Test that default parameters are correctly forwarded to Hayhooks."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    captured_payload: Dict[str, Any] = {}

    class FakeResponse:
        def __init__(self) -> None:
            self.status_code = 200

        def json(self):
            return {"success": True, "results": []}

        def raise_for_status(self):
            pass

    def fake_post(url: str, json: Dict[str, Any], timeout: int, headers: Dict[str, str]):
        captured_payload.update(json)
        return FakeResponse()

    monkeypatch.setattr("fastmcp_server.bookstack.tools.requests.post", fake_post)
    monkeypatch.setenv("HAYHOOKS_SEARCH_URL", "http://test-hayhooks:1416/search")

    tool = await mcp.get_tool("bookstack_semantic_search")
    await tool.run({"query": "test"})

    assert captured_payload["query"] == "test"
    assert captured_payload["top_k"] == 5
    assert captured_payload["response_mode"] == "synthesis"
    assert captured_payload["score_threshold"] == 0.3


@pytest.mark.asyncio
async def test_semantic_search_custom_params(monkeypatch: MonkeyPatch) -> None:
    """Test that custom parameters are forwarded to Hayhooks."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    captured_payload: Dict[str, Any] = {}

    class FakeResponse:
        def __init__(self) -> None:
            self.status_code = 200

        def json(self):
            return {"success": True, "results": []}

        def raise_for_status(self):
            pass

    def fake_post(url: str, json: Dict[str, Any], timeout: int, headers: Dict[str, str]):
        captured_payload.update(json)
        return FakeResponse()

    monkeypatch.setattr("fastmcp_server.bookstack.tools.requests.post", fake_post)
    monkeypatch.setenv("HAYHOOKS_SEARCH_URL", "http://test-hayhooks:1416/search")

    tool = await mcp.get_tool("bookstack_semantic_search")
    await tool.run({
        "query": "custom query",
        "top_k": 10,
        "response_mode": "raw",
        "score_threshold": 0.7,
    })

    assert captured_payload["query"] == "custom query"
    assert captured_payload["top_k"] == 10
    assert captured_payload["response_mode"] == "raw"
    assert captured_payload["score_threshold"] == 0.7


@pytest.mark.asyncio
async def test_semantic_search_invalid_response_mode_fallback(monkeypatch: MonkeyPatch) -> None:
    """Test that invalid response_mode falls back to 'synthesis'."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    captured_payload: Dict[str, Any] = {}

    class FakeResponse:
        def __init__(self) -> None:
            self.status_code = 200

        def json(self):
            return {"success": True, "results": []}

        def raise_for_status(self):
            pass

    def fake_post(url: str, json: Dict[str, Any], timeout: int, headers: Dict[str, str]):
        captured_payload.update(json)
        return FakeResponse()

    monkeypatch.setattr("fastmcp_server.bookstack.tools.requests.post", fake_post)
    monkeypatch.setenv("HAYHOOKS_SEARCH_URL", "http://test-hayhooks:1416/search")

    tool = await mcp.get_tool("bookstack_semantic_search")
    await tool.run({
        "query": "test",
        "response_mode": "invalid_mode",
    })

    assert captured_payload["response_mode"] == "synthesis"


@pytest.mark.asyncio
async def test_semantic_search_invalid_score_threshold_fallback(monkeypatch: MonkeyPatch) -> None:
    """Test that invalid score_threshold (>1.0) falls back to 0.3."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    captured_payload: Dict[str, Any] = {}

    class FakeResponse:
        def __init__(self) -> None:
            self.status_code = 200

        def json(self):
            return {"success": True, "results": []}

        def raise_for_status(self):
            pass

    def fake_post(url: str, json: Dict[str, Any], timeout: int, headers: Dict[str, str]):
        captured_payload.update(json)
        return FakeResponse()

    monkeypatch.setattr("fastmcp_server.bookstack.tools.requests.post", fake_post)
    monkeypatch.setenv("HAYHOOKS_SEARCH_URL", "http://test-hayhooks:1416/search")

    tool = await mcp.get_tool("bookstack_semantic_search")
    
    # Test score > 1.0
    await tool.run({
        "query": "test",
        "score_threshold": 1.5,
    })
    assert captured_payload["score_threshold"] == 0.3

    # Test score < 0.0
    captured_payload.clear()
    await tool.run({
        "query": "test",
        "score_threshold": -0.5,
    })
    assert captured_payload["score_threshold"] == 0.3


@pytest.mark.asyncio
async def test_semantic_search_book_filter_mapped(monkeypatch: MonkeyPatch) -> None:
    """Test that book_filter is mapped to filename_filter in the Hayhooks payload."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    captured_payload: Dict[str, Any] = {}

    class FakeResponse:
        def __init__(self) -> None:
            self.status_code = 200

        def json(self):
            return {"success": True, "results": []}

        def raise_for_status(self):
            pass

    def fake_post(url: str, json: Dict[str, Any], timeout: int, headers: Dict[str, str]):
        captured_payload.update(json)
        return FakeResponse()

    monkeypatch.setattr("fastmcp_server.bookstack.tools.requests.post", fake_post)
    monkeypatch.setenv("HAYHOOKS_SEARCH_URL", "http://test-hayhooks:1416/search")

    tool = await mcp.get_tool("bookstack_semantic_search")
    await tool.run({
        "query": "test",
        "book_filter": "MyBook",
    })

    assert captured_payload["filename_filter"] == "MyBook"


@pytest.mark.asyncio
async def test_semantic_search_timeout_raises_error(monkeypatch: MonkeyPatch) -> None:
    """Test that Hayhooks timeout raises ToolError."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    import requests

    def fake_post(url: str, json: Dict[str, Any], timeout: int, headers: Dict[str, str]):
        raise requests.exceptions.Timeout("Request timed out")

    monkeypatch.setattr("fastmcp_server.bookstack.tools.requests.post", fake_post)
    monkeypatch.setenv("HAYHOOKS_SEARCH_URL", "http://test-hayhooks:1416/search")

    tool = await mcp.get_tool("bookstack_semantic_search")
    
    with pytest.raises(ToolError) as exc:
        await tool.run({"query": "test"})
    
    assert "timed out" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_semantic_search_connection_error_raises_error(monkeypatch: MonkeyPatch) -> None:
    """Test that Hayhooks connection error raises ToolError."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    import requests

    def fake_post(url: str, json: Dict[str, Any], timeout: int, headers: Dict[str, str]):
        raise requests.exceptions.ConnectionError("Failed to connect")

    monkeypatch.setattr("fastmcp_server.bookstack.tools.requests.post", fake_post)
    monkeypatch.setenv("HAYHOOKS_SEARCH_URL", "http://test-hayhooks:1416/search")

    tool = await mcp.get_tool("bookstack_semantic_search")
    
    with pytest.raises(ToolError) as exc:
        await tool.run({"query": "test"})
    
    assert "connect" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_semantic_search_http_error_raises_error(monkeypatch: MonkeyPatch) -> None:
    """Test that Hayhooks HTTP error (500) raises ToolError."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    import requests

    class FakeResponse:
        def __init__(self) -> None:
            self.status_code = 500
            self.text = "Internal Server Error"

        def raise_for_status(self):
            raise requests.exceptions.HTTPError(response=self)

    def fake_post(url: str, json: Dict[str, Any], timeout: int, headers: Dict[str, str]):
        return FakeResponse()

    monkeypatch.setattr("fastmcp_server.bookstack.tools.requests.post", fake_post)
    monkeypatch.setenv("HAYHOOKS_SEARCH_URL", "http://test-hayhooks:1416/search")

    tool = await mcp.get_tool("bookstack_semantic_search")
    
    with pytest.raises(ToolError) as exc:
        await tool.run({"query": "test"})
    
    assert "500" in str(exc.value)


@pytest.mark.asyncio
async def test_semantic_search_non_json_response_raises_error(monkeypatch: MonkeyPatch) -> None:
    """Test that Hayhooks non-JSON response raises ToolError."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    class FakeResponse:
        def __init__(self) -> None:
            self.status_code = 200
            self.text = "This is not JSON"

        def json(self):
            raise ValueError("No JSON object could be decoded")

        def raise_for_status(self):
            pass

    def fake_post(url: str, json: Dict[str, Any], timeout: int, headers: Dict[str, str]):
        return FakeResponse()

    monkeypatch.setattr("fastmcp_server.bookstack.tools.requests.post", fake_post)
    monkeypatch.setenv("HAYHOOKS_SEARCH_URL", "http://test-hayhooks:1416/search")

    tool = await mcp.get_tool("bookstack_semantic_search")
    
    with pytest.raises(ToolError) as exc:
        await tool.run({"query": "test"})
    
    assert "non-JSON" in str(exc.value)


@pytest.mark.asyncio
async def test_semantic_search_empty_query_rejected(monkeypatch: MonkeyPatch) -> None:
    """Test that empty query is rejected by Pydantic validation."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    tool = await mcp.get_tool("bookstack_semantic_search")
    
    # Pydantic validation will raise ValidationError, not ToolError
    from pydantic_core import ValidationError
    
    with pytest.raises(ValidationError) as exc:
        await tool.run({"query": ""})
    
    # The validation error should mention query
    assert "query" in str(exc.value).lower()
