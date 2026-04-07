"""BookStack API client, error handling, and cache helpers."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, NoReturn, Optional, Tuple

import requests

from .cache import bookstack_cache
from .metrics import get_metrics_collector

try:  # FastMCP provides ToolError for structured failures
    from fastmcp import ToolError
except ImportError:  # pragma: no cover - fallback for older FastMCP releases
    class ToolError(RuntimeError):
        """Fallback ToolError if fastmcp.ToolError is unavailable."""


class JSONFormatter(logging.Formatter):
    """Minimal JSON log formatter for structured log output."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 - simple override
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        context = getattr(record, "context", None)
        if context:
            log_entry["context"] = context
        return json.dumps(log_entry, ensure_ascii=False)


logger = logging.getLogger("bookstack.mcp")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


def _require_env(var: str) -> str:
    """Return the value of an environment variable or raise a ToolError."""
    try:
        value = os.environ[var].strip()
    except KeyError as exc:  # pragma: no cover - fast failure path
        raise _tool_error(
            f"Environment variable '{var}' is required",
            hint=f"Set '{var}' in the container environment or .env file before invoking the tool.",
        ) from exc
    if not value:
        raise _tool_error(
            f"Environment variable '{var}' cannot be empty",
            hint=f"Provide a non-empty value for '{var}' in your environment configuration.",
        )
    return value


def _bookstack_base_url() -> str:
    base = _require_env("BS_URL").rstrip("/")
    return base


def _bookstack_headers() -> Dict[str, str]:
    token_id = _require_env("BS_TOKEN_ID")
    token_secret = _require_env("BS_TOKEN_SECRET")
    return {
        "Authorization": f"Token {token_id}:{token_secret}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def _tool_error(
    message: str,
    *,
    hint: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> ToolError:
    """Create a ToolError with optional hint and serialized context."""

    sections: list[str] = [message]
    if hint:
        sections.append(f"Hint: {hint}")
    if context:
        try:
            context_blob = json.dumps(context, default=str, indent=2)
        except TypeError:
            context_blob = str(context)
        sections.append(f"Context:\n{context_blob}")
    return ToolError("\n".join(sections))


def _ensure(
    condition: bool,
    message: str,
    *,
    hint: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Raise ToolError with optional hint/context when a condition is false."""

    if not condition:
        raise _tool_error(message, hint=hint, context=context)


def _select_cache_bucket(method: str, path: str):
    """Return the SmartCache bucket for a request path."""

    if method.upper() != "GET":
        return None

    if path.startswith("/api/books") or path.startswith("/api/bookshelves"):
        return bookstack_cache.books
    if path.startswith("/api/pages") or path.startswith("/api/chapters"):
        return bookstack_cache.pages
    if path.startswith("/api/image-gallery"):
        return bookstack_cache.images
    if path.startswith("/api/search"):
        return bookstack_cache.search
    return None


def _cache_ttl_for(path: str) -> float:
    """Determine a TTL for cached content based on endpoint."""

    if "/image" in path:
        return 900.0  # 15 minutes
    if "/search" in path:
        return 180.0  # 3 minutes
    if path.startswith("/api/pages") or path.startswith("/api/chapters"):
        return 300.0  # 5 minutes
    return 600.0  # default 10 minutes


def _build_cache_key(method: str, path: str, params: Optional[Dict[str, Any]], json_payload: Optional[Dict[str, Any]]) -> str:
    """Create a deterministic cache key for a BookStack request."""

    payload = {
        "method": method.upper(),
        "path": path,
        "params": params or {},
        "json": json_payload or {},
    }
    encoded = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _cache_tags_for_request(method: str, path: str) -> set[str]:
    """Annotate cached GET requests with entity tags for targeted invalidation."""

    if method.upper() != "GET":
        return set()

    entity_tag_map = {
        "/api/bookshelves": "bookshelf",
        "/api/books": "book",
        "/api/chapters": "chapter",
        "/api/pages": "page",
        "/api/image-gallery": "image",
    }

    for prefix, entity_type in entity_tag_map.items():
        if path == prefix or path.startswith(f"{prefix}/"):
            tags = {f"entity:{entity_type}", f"collection:{entity_type}"}
            suffix = path[len(prefix):].strip("/")
            if suffix and suffix.isdigit():
                tags.add(f"entity:{entity_type}:{suffix}")
            return tags

    return set()


def _invalidate_entity_cache(entity_type: str, entity_id: Optional[int] = None) -> None:
    """Invalidate cached payloads for a given entity type."""

    try:
        bookstack_cache.invalidate_entity(entity_type, entity_id)
    except Exception:
        logger.warning(
            "bookstack.cache_invalidation_failed",
            extra={
                "context": {
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                }
            },
        )


def _handle_bookstack_http_error(
    exc: requests.HTTPError,
    default_hint: str,
    method: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    hint_401: Optional[str] = None,
    hint_403: Optional[str] = None,
    hint_404: Optional[str] = None,
    hint_409: Optional[str] = None,
    hint_422: Optional[str] = None,
) -> NoReturn:
    """Extract error details from HTTP error and raise formatted tool error.
    
    Args:
        exc: The HTTPError exception from requests
        default_hint: Default hint message to use if no status-specific hint matches
        method: HTTP method used
        path: API path
        params: Query parameters (for JSON requests)
        json: JSON payload (for JSON requests)
        data: Form data (for multipart/form requests)
        files: Files dict (for multipart/form requests)
        hint_401: Custom hint for 401 errors (uses default if None)
        hint_403: Custom hint for 403 errors (uses default if None)
        hint_404: Custom hint for 404 errors (uses default if None)
        hint_409: Custom hint for 409 errors (uses default if None)
        hint_422: Custom hint for 422 errors (uses default if None)
        
    Raises:
        McpError: Always raises with formatted error message and context
    """
    status = exc.response.status_code if exc.response is not None else "unknown"
    status_code = status if isinstance(status, int) else 0
    preview: Optional[str] = None
    error_detail = ""
    if exc.response is not None:
        try:
            preview = exc.response.text[:400]
            # Try to extract error message from JSON response
            try:
                error_json = exc.response.json()
                if isinstance(error_json, dict):
                    if "error" in error_json:
                        error_detail = f": {error_json['error']}"
                    elif "message" in error_json:
                        error_detail = f": {error_json['message']}"
            except Exception as json_exc:
                logger.debug("_handle_bookstack_http_error: could not parse error JSON: %s", json_exc)
        except Exception as preview_exc:  # pragma: no cover - defensive guard
            logger.debug("_handle_bookstack_http_error: could not extract response preview: %s", preview_exc)
            preview = None

    # Provide specific hints for common HTTP errors
    hint = default_hint
    if status == 409:
        hint = hint_409 if hint_409 is not None else (
            "Conflict error (409): This usually means a resource with the same name already exists, "
            "or there's a constraint violation. Check the response_preview for details."
        )
    elif status == 404:
        hint = hint_404 if hint_404 is not None else "Not found (404): The entity ID or endpoint doesn't exist. Verify the ID is correct."
    elif status == 401:
        hint = hint_401 if hint_401 is not None else "Unauthorized (401): Check your BS_TOKEN_ID and BS_TOKEN_SECRET environment variables."
    elif status == 403:
        hint = hint_403 if hint_403 is not None else "Forbidden (403): Your API token doesn't have permission for this operation."
    elif status == 422:
        hint = hint_422 if hint_422 is not None else (
            "Validation error (422): The request payload is invalid. "
            "Check the response_preview for field-specific errors."
        )

    error_msg = f"BookStack API request failed with HTTP {status}{error_detail}"
    error_message = error_msg
    
    # Build context dict based on what was provided
    context: Dict[str, Any] = {
        "method": method,
        "path": path,
        "status": status,
        "response_preview": preview,
    }
    
    if params is not None:
        context["params"] = params
    if json is not None:
        context["payload"] = json
    if data is not None:
        context["data_keys"] = list(data.keys())
    if files is not None:
        context["files_keys"] = list(files.keys())
    
    logger.error(
        "bookstack.api_error",
        extra={"context": {**context, "message": error_msg, "hint": hint}},
    )

    raise _tool_error(error_msg, hint=hint, context=context) from exc


def _bookstack_request(
    method: str,
    path: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
) -> Any:
    """Execute a JSON request against the BookStack API."""

    method = method.upper()
    cache_bucket = _select_cache_bucket(method, path)
    cache_key: Optional[str] = None
    if cache_bucket is not None:
        cache_key = _build_cache_key(method, path, params, json)
        cached_payload = cache_bucket.get(cache_key)
        if cached_payload is not None:
            logger.info(
                "bookstack.cache_hit",
                extra={
                    "context": {
                        "method": method,
                        "path": path,
                        "params": params,
                    }
                },
            )
            return cached_payload

    url = f"{_bookstack_base_url()}{path}"
    collector = get_metrics_collector()
    start_time = time.time()
    status_code: int = 0
    error_message: Optional[str] = None

    try:
        response = requests.request(
            method,
            url,
            headers=_bookstack_headers(),
            params=params,
            json=json,
            timeout=60,
        )
        status_code = response.status_code
        response.raise_for_status()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        status_code = status if isinstance(status, int) else 0
        _handle_bookstack_http_error(
            exc,
            default_hint="Verify the BookStack credentials, entity identifiers, and payload fields.",
            method=method,
            path=path,
            params=params,
            json=json,
        )
    except requests.RequestException as exc:  # pragma: no cover - network failure path
        error_message = str(exc)
        logger.error(
            "bookstack.transport_error",
            extra={
                "context": {
                    "message": error_message,
                    "method": method,
                    "path": path,
                    "params": params,
                }
            },
        )
        raise _tool_error(
            "Unable to reach the BookStack API endpoint",
            hint="Check network connectivity and ensure the BS_URL host is reachable from the container.",
            context={"method": method, "path": path, "params": params},
        ) from exc
    finally:
        duration = time.time() - start_time
        # Only record metrics when we actually contacted the API
        collector.record_request(method, path, duration, status_code, error_message)

    if response.status_code == 204 or not response.content:
        payload: Any = {"success": True, "status": response.status_code}
    else:
        try:
            payload = response.json()
        except ValueError as exc:  # pragma: no cover - unexpected payload
            raise _tool_error(
                "BookStack API returned a non-JSON response",
                hint="Inspect the response body to confirm the endpoint and authentication are correct.",
                context={
                    "method": method,
                    "path": path,
                    "status": response.status_code,
                    "raw": response.text[:400],
                },
            ) from exc

    if cache_bucket is not None and cache_key is not None:
        cache_bucket.set(
            cache_key,
            payload,
            ttl=_cache_ttl_for(path),
            tags=_cache_tags_for_request(method, path),
        )

    return payload


def _bookstack_request_form(
    method: str,
    path: str,
    *,
    data: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Tuple[str, bytes, str]]] = None,
) -> Any:
    """Execute a multipart/form-data request against the BookStack API."""

    url = f"{_bookstack_base_url()}{path}"
    headers = _bookstack_headers()
    headers.pop("Content-Type", None)
    try:
        response = requests.request(
            method,
            url,
            headers=headers,
            data=data,
            files=files,
            timeout=120,
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        _handle_bookstack_http_error(
            exc,
            default_hint="Confirm the image identifiers and ensure the API token grants image permissions.",
            method=method,
            path=path,
            data=data,
            files=files,
            hint_403="Forbidden (403): Your API token doesn't have permission for image operations.",
            hint_404="Not found (404): The image ID doesn't exist. Verify the ID is correct.",
            hint_409="Conflict error (409): This usually means an image with the same name already exists. Check the response_preview for details.",
            hint_422="Validation error (422): The image data is invalid. Check the response_preview for details.",
        )
    except requests.RequestException as exc:  # pragma: no cover - network failure path
        raise _tool_error(
            "Unable to reach the BookStack image endpoint",
            hint="Check network connectivity and ensure BS_URL is accessible.",
            context={"method": method, "path": path},
        ) from exc

    if response.status_code == 204 or not response.content:
        return {"success": True, "status": response.status_code}

    try:
        return response.json()
    except ValueError as exc:  # pragma: no cover - unexpected payload
        raise _tool_error(
            "BookStack image endpoint returned a non-JSON response",
            hint="Inspect the raw response to confirm the upload/download succeeded.",
            context={
                "method": method,
                "path": path,
                "status": response.status_code,
                "raw": response.text[:400],
            },
        ) from exc
