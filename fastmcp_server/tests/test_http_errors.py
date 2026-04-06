"""Comprehensive tests for HTTP error handling in BookStack request functions."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

import pytest
import requests
from pytest import MonkeyPatch

import fastmcp_server.bookstack.tools as tools
from fastmcp_server.bookstack.tools import ToolError


class FakeResponse:
    """Mock response object for testing HTTP error paths."""

    def __init__(
        self,
        status_code: int,
        json_data: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None,
        content: Optional[bytes] = None,
    ):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text or (json.dumps(json_data) if json_data else "")
        self.content = content or self.text.encode("utf-8")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            exc = requests.HTTPError()
            exc.response = self
            raise exc

    def json(self) -> Dict[str, Any]:
        if self._json_data is not None:
            return self._json_data
        raise ValueError("Not JSON")


class TestBookstackRequestHTTPErrors:
    """Test _bookstack_request HTTP error handling."""

    def test_http_401_unauthorized_error(self, monkeypatch: MonkeyPatch) -> None:
        """Test HTTP 401 returns ToolError with auth token hint."""

        def fake_request(method: str, url: str, **kwargs: Any) -> FakeResponse:
            return FakeResponse(401, {"error": "Unauthorized"})

        monkeypatch.setattr("requests.request", fake_request)
        monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://test.example.com")
        monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

        with pytest.raises(ToolError) as exc:
            tools._bookstack_request("GET", "/api/books")

        error_msg = str(exc.value)
        assert "HTTP 401" in error_msg
        assert "Unauthorized (401)" in error_msg
        assert "BS_TOKEN_ID" in error_msg
        assert "BS_TOKEN_SECRET" in error_msg

    def test_http_403_forbidden_error(self, monkeypatch: MonkeyPatch) -> None:
        """Test HTTP 403 returns ToolError with permissions hint."""

        def fake_request(method: str, url: str, **kwargs: Any) -> FakeResponse:
            return FakeResponse(403, {"error": "Forbidden"})

        monkeypatch.setattr("requests.request", fake_request)
        monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://test.example.com")
        monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

        with pytest.raises(ToolError) as exc:
            tools._bookstack_request("GET", "/api/pages/5")

        error_msg = str(exc.value)
        assert "HTTP 403" in error_msg
        assert "Forbidden (403)" in error_msg
        assert "doesn't have permission" in error_msg

    def test_http_404_not_found_error(self, monkeypatch: MonkeyPatch) -> None:
        """Test HTTP 404 returns ToolError with entity ID hint."""

        def fake_request(method: str, url: str, **kwargs: Any) -> FakeResponse:
            return FakeResponse(404, {"error": "Not found"})

        monkeypatch.setattr("requests.request", fake_request)
        monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://test.example.com")
        monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

        with pytest.raises(ToolError) as exc:
            tools._bookstack_request("GET", "/api/books/999")

        error_msg = str(exc.value)
        assert "HTTP 404" in error_msg
        assert "Not found (404)" in error_msg
        assert "doesn't exist" in error_msg
        assert "Verify the ID is correct" in error_msg

    def test_http_409_conflict_error(self, monkeypatch: MonkeyPatch) -> None:
        """Test HTTP 409 returns ToolError with conflict hint."""

        def fake_request(method: str, url: str, **kwargs: Any) -> FakeResponse:
            return FakeResponse(409, {"error": "Conflict: name already exists"})

        monkeypatch.setattr("requests.request", fake_request)
        monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://test.example.com")
        monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

        with pytest.raises(ToolError) as exc:
            tools._bookstack_request("POST", "/api/books", json={"name": "Duplicate"})

        error_msg = str(exc.value)
        assert "HTTP 409" in error_msg
        assert "Conflict error (409)" in error_msg
        assert "already exists" in error_msg or "constraint violation" in error_msg

    def test_http_422_validation_error(self, monkeypatch: MonkeyPatch) -> None:
        """Test HTTP 422 returns ToolError with payload hint."""

        def fake_request(method: str, url: str, **kwargs: Any) -> FakeResponse:
            return FakeResponse(422, {"error": "Validation failed", "details": {"name": "required"}})

        monkeypatch.setattr("requests.request", fake_request)
        monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://test.example.com")
        monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

        with pytest.raises(ToolError) as exc:
            tools._bookstack_request("POST", "/api/pages", json={"content": "test"})

        error_msg = str(exc.value)
        assert "HTTP 422" in error_msg
        assert "Validation error (422)" in error_msg
        assert "payload is invalid" in error_msg

    def test_http_500_server_error(self, monkeypatch: MonkeyPatch) -> None:
        """Test HTTP 500 returns generic server error."""

        def fake_request(method: str, url: str, **kwargs: Any) -> FakeResponse:
            return FakeResponse(500, {"error": "Internal server error"})

        monkeypatch.setattr("requests.request", fake_request)
        monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://test.example.com")
        monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

        with pytest.raises(ToolError) as exc:
            tools._bookstack_request("GET", "/api/books")

        error_msg = str(exc.value)
        assert "HTTP 500" in error_msg

    def test_connection_timeout_error(self, monkeypatch: MonkeyPatch) -> None:
        """Test connection timeout raises ToolError."""

        def fake_request(method: str, url: str, **kwargs: Any) -> None:
            raise requests.exceptions.Timeout("Connection timed out")

        monkeypatch.setattr("requests.request", fake_request)
        monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://test.example.com")
        monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

        with pytest.raises(ToolError) as exc:
            tools._bookstack_request("GET", "/api/books")

        error_msg = str(exc.value)
        assert "Unable to reach the BookStack API endpoint" in error_msg
        assert "network connectivity" in error_msg

    def test_connection_error(self, monkeypatch: MonkeyPatch) -> None:
        """Test connection error raises ToolError."""

        def fake_request(method: str, url: str, **kwargs: Any) -> None:
            raise requests.exceptions.ConnectionError("Failed to connect")

        monkeypatch.setattr("requests.request", fake_request)
        monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://test.example.com")
        monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

        with pytest.raises(ToolError) as exc:
            tools._bookstack_request("GET", "/api/books")

        error_msg = str(exc.value)
        assert "Unable to reach the BookStack API endpoint" in error_msg
        assert "network connectivity" in error_msg

    def test_non_json_response_body_fallback(self, monkeypatch: MonkeyPatch) -> None:
        """Test non-JSON response body returns ToolError with raw text."""

        class NonJSONResponse:
            def __init__(self) -> None:
                self.status_code = 200
                self.content = b"<html>Not JSON</html>"
                self.text = "<html>Not JSON</html>"

            def raise_for_status(self) -> None:
                pass

            def json(self) -> None:
                raise ValueError("Not JSON")

        def fake_request(method: str, url: str, **kwargs: Any) -> NonJSONResponse:
            return NonJSONResponse()

        monkeypatch.setattr("requests.request", fake_request)
        monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://test.example.com")
        monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

        with pytest.raises(ToolError) as exc:
            tools._bookstack_request("GET", "/api/books")

        error_msg = str(exc.value)
        assert "non-JSON response" in error_msg
        assert "raw" in error_msg.lower() or "html" in error_msg.lower()

    def test_http_error_includes_error_detail_from_json(self, monkeypatch: MonkeyPatch) -> None:
        """Test HTTP error extracts error detail from JSON response."""

        def fake_request(method: str, url: str, **kwargs: Any) -> FakeResponse:
            return FakeResponse(404, {"error": "Book not found", "message": "No book with ID 999"})

        monkeypatch.setattr("requests.request", fake_request)
        monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://test.example.com")
        monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

        with pytest.raises(ToolError) as exc:
            tools._bookstack_request("GET", "/api/books/999")

        error_msg = str(exc.value)
        assert "Book not found" in error_msg or "No book with ID 999" in error_msg


class TestBookstackRequestFormHTTPErrors:
    """Test _bookstack_request_form HTTP error handling."""

    def test_form_http_401_unauthorized_error(self, monkeypatch: MonkeyPatch) -> None:
        """Test form request HTTP 401 returns ToolError with auth token hint."""

        def fake_request(method: str, url: str, **kwargs: Any) -> FakeResponse:
            return FakeResponse(401, {"error": "Unauthorized"})

        monkeypatch.setattr("requests.request", fake_request)
        monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://test.example.com")
        monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

        with pytest.raises(ToolError) as exc:
            tools._bookstack_request_form("POST", "/api/image-gallery")

        error_msg = str(exc.value)
        assert "HTTP 401" in error_msg
        assert "Unauthorized (401)" in error_msg
        assert "BS_TOKEN_ID" in error_msg
        assert "BS_TOKEN_SECRET" in error_msg

    def test_form_http_403_forbidden_error(self, monkeypatch: MonkeyPatch) -> None:
        """Test form request HTTP 403 returns ToolError with permissions hint."""

        def fake_request(method: str, url: str, **kwargs: Any) -> FakeResponse:
            return FakeResponse(403, {"error": "Forbidden"})

        monkeypatch.setattr("requests.request", fake_request)
        monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://test.example.com")
        monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

        with pytest.raises(ToolError) as exc:
            tools._bookstack_request_form("POST", "/api/image-gallery")

        error_msg = str(exc.value)
        assert "HTTP 403" in error_msg
        assert "Forbidden (403)" in error_msg
        assert "doesn't have permission" in error_msg

    def test_form_http_404_not_found_error(self, monkeypatch: MonkeyPatch) -> None:
        """Test form request HTTP 404 returns ToolError with entity ID hint."""

        def fake_request(method: str, url: str, **kwargs: Any) -> FakeResponse:
            return FakeResponse(404, {"error": "Image not found"})

        monkeypatch.setattr("requests.request", fake_request)
        monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://test.example.com")
        monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

        with pytest.raises(ToolError) as exc:
            tools._bookstack_request_form("PUT", "/api/image-gallery/999")

        error_msg = str(exc.value)
        assert "HTTP 404" in error_msg
        assert "Not found (404)" in error_msg
        assert "doesn't exist" in error_msg
        assert "Verify the ID is correct" in error_msg

    def test_form_http_409_conflict_error(self, monkeypatch: MonkeyPatch) -> None:
        """Test form request HTTP 409 returns ToolError with conflict hint."""

        def fake_request(method: str, url: str, **kwargs: Any) -> FakeResponse:
            return FakeResponse(409, {"error": "Image name already exists"})

        monkeypatch.setattr("requests.request", fake_request)
        monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://test.example.com")
        monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

        with pytest.raises(ToolError) as exc:
            tools._bookstack_request_form("POST", "/api/image-gallery")

        error_msg = str(exc.value)
        assert "HTTP 409" in error_msg
        assert "Conflict error (409)" in error_msg
        assert "already exists" in error_msg

    def test_form_http_422_validation_error(self, monkeypatch: MonkeyPatch) -> None:
        """Test form request HTTP 422 returns ToolError with payload hint."""

        def fake_request(method: str, url: str, **kwargs: Any) -> FakeResponse:
            return FakeResponse(422, {"error": "Invalid image data"})

        monkeypatch.setattr("requests.request", fake_request)
        monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://test.example.com")
        monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

        with pytest.raises(ToolError) as exc:
            tools._bookstack_request_form("POST", "/api/image-gallery")

        error_msg = str(exc.value)
        assert "HTTP 422" in error_msg
        assert "Validation error (422)" in error_msg
        assert "image data is invalid" in error_msg

    def test_form_connection_timeout_error(self, monkeypatch: MonkeyPatch) -> None:
        """Test form request connection timeout raises ToolError."""

        def fake_request(method: str, url: str, **kwargs: Any) -> None:
            raise requests.exceptions.Timeout("Connection timed out")

        monkeypatch.setattr("requests.request", fake_request)
        monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://test.example.com")
        monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

        with pytest.raises(ToolError) as exc:
            tools._bookstack_request_form("POST", "/api/image-gallery")

        error_msg = str(exc.value)
        assert "Unable to reach the BookStack image endpoint" in error_msg
        assert "network connectivity" in error_msg

    def test_form_connection_error(self, monkeypatch: MonkeyPatch) -> None:
        """Test form request connection error raises ToolError."""

        def fake_request(method: str, url: str, **kwargs: Any) -> None:
            raise requests.exceptions.ConnectionError("Failed to connect")

        monkeypatch.setattr("requests.request", fake_request)
        monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://test.example.com")
        monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

        with pytest.raises(ToolError) as exc:
            tools._bookstack_request_form("POST", "/api/image-gallery")

        error_msg = str(exc.value)
        assert "Unable to reach the BookStack image endpoint" in error_msg
        assert "network connectivity" in error_msg

    def test_form_non_json_response_body_fallback(self, monkeypatch: MonkeyPatch) -> None:
        """Test form request non-JSON response body returns ToolError with raw text."""

        class NonJSONResponse:
            def __init__(self) -> None:
                self.status_code = 200
                self.content = b"<html>Image uploaded</html>"
                self.text = "<html>Image uploaded</html>"

            def raise_for_status(self) -> None:
                pass

            def json(self) -> None:
                raise ValueError("Not JSON")

        def fake_request(method: str, url: str, **kwargs: Any) -> NonJSONResponse:
            return NonJSONResponse()

        monkeypatch.setattr("requests.request", fake_request)
        monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://test.example.com")
        monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

        with pytest.raises(ToolError) as exc:
            tools._bookstack_request_form("POST", "/api/image-gallery")

        error_msg = str(exc.value)
        assert "non-JSON response" in error_msg
        assert "raw" in error_msg.lower() or "html" in error_msg.lower()

    def test_form_http_error_includes_message_detail(self, monkeypatch: MonkeyPatch) -> None:
        """Test form request HTTP error extracts message detail from JSON response."""

        def fake_request(method: str, url: str, **kwargs: Any) -> FakeResponse:
            return FakeResponse(404, {"message": "Image ID 999 not found in gallery"})

        monkeypatch.setattr("requests.request", fake_request)
        monkeypatch.setattr(tools, "_bookstack_base_url", lambda: "https://test.example.com")
        monkeypatch.setattr(tools, "_bookstack_headers", lambda: {"Authorization": "Token test"})

        with pytest.raises(ToolError) as exc:
            tools._bookstack_request_form("DELETE", "/api/image-gallery/999")

        error_msg = str(exc.value)
        assert "Image ID 999 not found" in error_msg
