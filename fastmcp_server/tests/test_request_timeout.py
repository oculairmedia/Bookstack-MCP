"""Tests for payload-aware HTTP timeouts (large page edit stability)."""
from __future__ import annotations

import fastmcp_server.bookstack.api_client as api_client


def test_get_uses_read_timeout(monkeypatch):
    monkeypatch.delenv("BS_HTTP_TIMEOUT", raising=False)
    assert api_client._request_timeout("GET", None) == 60


def test_write_uses_higher_base_timeout(monkeypatch):
    monkeypatch.delenv("BS_HTTP_WRITE_TIMEOUT", raising=False)
    assert api_client._request_timeout("PUT", {"markdown": "small"}) == 120
    assert api_client._request_timeout("POST", None) == 120


def test_write_timeout_scales_with_payload(monkeypatch):
    monkeypatch.delenv("BS_HTTP_WRITE_TIMEOUT", raising=False)
    big = {"markdown": "x" * 250_000}  # ~250 KB -> +60s
    assert api_client._request_timeout("PUT", big) == 120 + 60


def test_write_timeout_env_override(monkeypatch):
    monkeypatch.setenv("BS_HTTP_WRITE_TIMEOUT", "200")
    assert api_client._request_timeout("PUT", {"a": 1}) == 200
