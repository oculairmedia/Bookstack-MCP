"""Tests for BookStack search-oriented FastMCP tools."""
from __future__ import annotations

import json
from datetime import datetime

import pytest
from fastmcp import FastMCP
from pytest import MonkeyPatch

import fastmcp_server.bookstack.tools as tools
from fastmcp_server.bookstack.tools import ToolError, register_bookstack_tools


@pytest.mark.asyncio
async def test_content_search_returns_formatted_results(monkeypatch: MonkeyPatch) -> None:
    response_payload = {
        "total": 2,
        "data": [
            {
                "id": 1,
                "type": "page",
                "name": "Install Guide",
                "url": "https://example/book/page/1",
                "preview_html": {"content": "<p>Install steps</p>"},
                "book": {"id": 10, "name": "Docs"},
            },
            {
                "id": 2,
                "type": "chapter",
                "slug": "overview",
                "url": "https://example/book/chapter/2",
                "description": "Overview chapter",
            },
        ],
    }

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    def fake_request(method: str, path: str, *, params=None, json=None):
        assert method == "GET"
        assert path == "/api/search"
        assert params == {"query": "docs", "page": 2, "count": 1}
        return response_payload

    monkeypatch.setattr(tools, "_bookstack_request", fake_request)

    tool = await mcp.get_tool("bookstack_search")
    result = await tool.run({"query": "docs", "page": 2, "count": 1})

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["returned"] == 1
    assert data["total"] == 2
    first = data["results"][0]
    assert first["title"] == "Install Guide"
    assert first["book"] == {"id": 10, "name": "Docs"}
    assert first["summary"].startswith("Install steps")


@pytest.mark.asyncio
async def test_image_search_normalises_extension_and_dates(monkeypatch: MonkeyPatch) -> None:
    payload = {
        "data": [
            {"id": 7, "name": "diagram.png", "created_at": datetime.now().isoformat()},
        ],
        "total": 1,
        "count": 1,
        "offset": 0,
    }

    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    def fake_request(method: str, path: str, *, params=None, json=None):
        assert method == "GET"
        assert path == "/api/image-gallery"
        assert params == {
            "offset": 5,
            "count": 10,
            "query": "diagram",
            "extension": ".png",
            "size_min": 100,
            "size_max": 1000,
            "created_after": "2024-01-01T00:00:00Z",
            "created_before": "2024-12-31T23:59:59Z",
            "used_in": "pages",
            "sort": "-created_at",
        }
        return payload

    monkeypatch.setattr(tools, "_bookstack_request", fake_request)

    tool = await mcp.get_tool("bookstack_search_images")
    result = await tool.run(
        {
            "query": "diagram",
            "extension": "png",
            "size_min": 100,
            "size_max": 1000,
            "created_after": "2024-01-01T00:00:00Z",
            "created_before": "2024-12-31T23:59:59Z",
            "used_in": "pages",
            "sort": "-created_at",
            "offset": 5,
            "count": 10,
        }
    )

    data = json.loads(result.content[0].text)
    assert data["success"] is True
    assert data["metadata"]["count"] == 1
    assert data["extension"] == ".png"
    assert data["used_in"] == "pages"


@pytest.mark.asyncio
async def test_image_search_rejects_invalid_ranges(monkeypatch: MonkeyPatch) -> None:
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)
    tool = await mcp.get_tool("bookstack_search_images")

    with MonkeyPatch.context() as patch:
        patch.setattr(tools, "_bookstack_request", pytest.fail)

        with pytest.raises(ToolError) as exc:
            await tool.run({"size_min": 200, "size_max": 100})

    assert "size_min cannot be greater" in str(exc.value)


def test_attach_entity_summary_deduplicates_page_ids() -> None:
    payload = {
        "results": [
            {
                "chunk_id": "a",
                "score": 0.44,
                "bookstack_page_id": 12,
                "book_id": 3,
                "chapter_id": 8,
                "name": "Architecture",
                "book_name": "Infra",
            },
            {
                "chunk_id": "b",
                "score": 0.91,
                "bookstack_page_id": 12,
                "book_id": 3,
                "chapter_id": 8,
                "name": "Architecture",
                "book_name": "Infra",
            },
            {
                "chunk_id": "c",
                "score": 0.67,
                "bookstack_page_id": 42,
                "book_id": 7,
                "chapter_id": 0,
                "name": "Operations",
                "book_name": "Runbooks",
            },
        ]
    }

    result = tools._attach_entity_summary(payload)
    entities = result.get("entities")
    assert isinstance(entities, list)
    assert len(entities) == 2

    first = entities[0]
    assert first["page_id"] == 12
    assert first["chunks"] == 2
    assert first["best_score"] == 0.91


def test_attach_entity_summary_ignores_missing_page_ids() -> None:
    payload = {
        "results": [
            {"score": 0.9, "name": "No page id"},
            {"score": 0.8, "bookstack_page_id": 0, "name": "Zero page id"},
        ]
    }

    result = tools._attach_entity_summary(payload)
    assert "entities" not in result
