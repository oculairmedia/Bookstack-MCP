"""Tests covering scoped list behaviour for BookStack content tools."""
from __future__ import annotations

import json
from typing import Any, Mapping
from unittest.mock import patch

import pytest
from fastmcp import FastMCP

from fastmcp_server.bookstack.tools import register_bookstack_tools


FAKE_BOOK_RESPONSE = {
    "id": 1,
    "contents": [
        {"type": "page", "id": 101, "name": "Page A"},
        {
            "type": "chapter",
            "id": 20,
            "name": "Chapter",
            "pages": [
                {"type": "page", "id": 102, "name": "Page B"},
            ],
        },
    ],
}


async def _invoke_list_tool(
    payload: Mapping[str, Any],
    mock_value: Mapping[str, Any],
) -> tuple[dict[str, Any], tuple[Any, ...], dict[str, Any]]:
    """Execute the FastMCP list tool and decode the JSON payload for assertions."""
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    with patch("fastmcp_server.bookstack.tools._bookstack_request", return_value=mock_value) as mock_request:
        tool = await mcp.get_tool("bookstack_list_content")
        result = await tool.run(dict(payload))

    mock_request.assert_called_once()
    call_args = mock_request.call_args
    assert call_args is not None
    args, kwargs = call_args

    assert result.content, "ToolResult should include textual content"
    response_blob = result.content[0].text
    return json.loads(response_blob), args, kwargs


@pytest.mark.asyncio
async def test_pages_with_book_scope_returns_flattened() -> None:
    response, args, kwargs = await _invoke_list_tool(
        {
            "entity_type": "pages",
            "book_id": 1,
            "offset": 0,
            "count": 10,
        },
        FAKE_BOOK_RESPONSE,
    )

    assert args == ("GET", "/api/books/1")
    assert kwargs == {}
    assert response["success"] is True
    assert response["data"]["total"] == 2
    ids = [item["id"] for item in response["data"]["data"]]
    assert ids == [101, 102]
    assert response["metadata"]["scoped"] is True
    assert response["metadata"]["filter_context"] == {"book_id": 1}


@pytest.mark.asyncio
async def test_chapters_with_book_scope_filters_pages() -> None:
    response, args, kwargs = await _invoke_list_tool(
        {
            "entity_type": "chapters",
            "book_id": 1,
        },
        FAKE_BOOK_RESPONSE,
    )

    assert args == ("GET", "/api/books/1")
    assert kwargs == {}
    assert response["success"] is True
    items = response["data"]["data"]
    assert len(items) == 1
    assert items[0]["id"] == 20
    assert response["metadata"]["scoped"] is True
    assert response["metadata"]["filter_context"] == {"book_id": 1}


@pytest.mark.asyncio
async def test_books_listing_returns_metadata() -> None:
    api_response = {
        "data": [
            {"id": 10, "name": "Book A"},
            {"id": 11, "name": "Book B"},
        ],
        "total": 2,
        "count": 2,
        "offset": 0,
    }

    response, args, kwargs = await _invoke_list_tool(
        {
            "entity_type": "books",
            "offset": 0,
            "count": 2,
        },
        api_response,
    )

    assert args == ("GET", "/api/books")
    assert kwargs["params"] == {"offset": 0, "count": 2}
    assert response["success"] is True
    assert response["data"] == api_response
    assert response["metadata"]["total"] == 2
    assert response["metadata"]["returned"] == 2
