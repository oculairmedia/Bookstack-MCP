from __future__ import annotations

import json
import os

import pytest
import requests
from fastmcp import FastMCP

from fastmcp_server.bookstack.tools import register_bookstack_tools


def _has_live_config() -> bool:
    required = ["BS_URL", "BS_TOKEN_ID", "BS_TOKEN_SECRET", "HAYHOOKS_SEARCH_URL"]
    return all(os.getenv(key) for key in required)


def _bookstack_headers() -> dict[str, str]:
    return {
        "Authorization": f"Token {os.environ['BS_TOKEN_ID']}:{os.environ['BS_TOKEN_SECRET']}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


@pytest.mark.asyncio
@pytest.mark.skipif(not _has_live_config(), reason="Live semantic-search E2E requires BS/Hayhooks environment variables")
async def test_semantic_search_roundtrip_live() -> None:
    mcp = FastMCP("test")
    register_bookstack_tools(mcp)

    tool = await mcp.get_tool("bookstack_semantic_search")
    query = os.getenv("TEST_SEARCH_QUERY", "Letta API Overview")
    result = await tool.run({"query": query, "response_mode": "raw", "top_k": 5})
    payload = json.loads(result.content[0].text)

    assert payload.get("success") is True
    results = payload.get("results") or payload.get("evidence") or []
    assert isinstance(results, list)
    assert results

    positive_page_ids = [int(item.get("bookstack_page_id", 0)) for item in results if isinstance(item, dict)]
    assert any(page_id > 0 for page_id in positive_page_ids)

    entities = payload.get("entities") or []
    assert isinstance(entities, list)
    assert entities

    top_entity = entities[0]
    page_id = int(top_entity.get("page_id", 0))
    assert page_id > 0

    page_resp = requests.get(
        f"{os.environ['BS_URL'].rstrip('/')}/api/pages/{page_id}",
        headers=_bookstack_headers(),
        timeout=30,
    )
    page_resp.raise_for_status()
    page_data = page_resp.json()
    assert int(page_data.get("id", 0)) == page_id

    book_id = int(top_entity.get("book_id", 0))
    if book_id > 0:
        book_resp = requests.get(
            f"{os.environ['BS_URL'].rstrip('/')}/api/books/{book_id}",
            headers=_bookstack_headers(),
            timeout=30,
        )
        book_resp.raise_for_status()
        book_data = book_resp.json()
        assert int(book_data.get("id", 0)) == book_id
