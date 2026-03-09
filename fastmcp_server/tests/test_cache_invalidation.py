"""Regression tests for cache invalidation after BookStack mutations."""
from __future__ import annotations

import json

import pytest

from fastmcp_server.bookstack.cache import SmartCache, bookstack_cache
import fastmcp_server.bookstack.tools as tools


@pytest.fixture(autouse=True)
def clear_caches() -> None:
    """Keep cache state isolated between tests."""
    bookstack_cache.books.invalidate()
    bookstack_cache.pages.invalidate()
    bookstack_cache.images.invalidate()
    bookstack_cache.search.invalidate()
    yield
    bookstack_cache.books.invalidate()
    bookstack_cache.pages.invalidate()
    bookstack_cache.images.invalidate()
    bookstack_cache.search.invalidate()


def test_smart_cache_invalidate_by_tags() -> None:
    cache = SmartCache()

    cache.set("page-detail", {"id": 7}, tags={"entity:page", "entity:page:7"})
    cache.set("page-list", {"data": []}, tags={"entity:page", "collection:page"})
    cache.set("book-detail", {"id": 3}, tags={"entity:book", "entity:book:3"})

    invalidated = cache.invalidate(tags={"entity:page:7", "collection:page"})

    assert invalidated == 2
    assert cache.get("page-detail") is None
    assert cache.get("page-list") is None
    assert cache.get("book-detail") == {"id": 3}


def test_page_update_invalidates_cached_detail_read(monkeypatch: pytest.MonkeyPatch) -> None:
    """A write should evict the cached GET for the same entity."""
    state = {"get_count": 0, "name": "Page v1"}

    class FakeResponse:
        def __init__(self, payload: dict[str, object], status_code: int = 200):
            self._payload = payload
            self.status_code = status_code
            self.content = b"json"
            self.text = json.dumps(payload)

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return dict(self._payload)

    def fake_request(method: str, url: str, *, headers=None, params=None, json=None, timeout=None):
        if method == "GET" and url.endswith("/api/pages/7"):
            state["get_count"] += 1
            return FakeResponse({"id": 7, "name": state["name"]})
        if method == "PUT" and url.endswith("/api/pages/7"):
            state["name"] = json["name"] if isinstance(json, dict) else state["name"]
            return FakeResponse({"id": 7, "name": state["name"]})
        raise AssertionError(f"Unexpected request: {method} {url}")

    monkeypatch.setattr("requests.request", fake_request)
    monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://bookstack.example.com")
    monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

    first_payload = tools._bookstack_request("GET", "/api/pages/7")
    second_payload = tools._bookstack_request("GET", "/api/pages/7")
    updated_payload = tools._bookstack_request("PUT", "/api/pages/7", json={"name": "Page v2"})
    tools._invalidate_entity_cache("page", 7)
    third_payload = tools._bookstack_request("GET", "/api/pages/7")

    assert state["get_count"] == 2
    assert first_payload["name"] == "Page v1"
    assert second_payload["name"] == "Page v1"
    assert updated_payload["name"] == "Page v2"
    assert third_payload["name"] == "Page v2"
