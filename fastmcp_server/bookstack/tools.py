"""BookStack tool definitions for the FastMCP server."""

from __future__ import annotations

import base64
import copy
import json
import mimetypes
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Any, Dict, Literal, Optional, Sequence, Tuple, Union
from urllib.parse import unquote, urlparse

import requests
from fastmcp import FastMCP
from pydantic import Field
from pydantic.json_schema import WithJsonSchema
from typing_extensions import TypedDict

try:  # FastMCP provides ToolError for structured failures
    from fastmcp import ToolError
except ImportError:  # pragma: no cover - fallback for older FastMCP releases
    class ToolError(RuntimeError):
        """Fallback ToolError if fastmcp.ToolError is unavailable."""


EntityType = Literal["book", "bookshelf", "chapter", "page"]
ListEntityType = Literal["books", "bookshelves", "chapters", "pages"]
OperationType = Literal["create", "read", "update", "delete"]
BatchOperationType = Literal["bulk_create", "bulk_update", "bulk_delete"]


class TagDict(TypedDict):
    """Tag representation expected by the BookStack API."""

    name: str
    value: str


class FilterEntry(TypedDict):
    """Image filter entry forward-compatible with BookStack API."""

    key: str
    value: str


_TAG_ITEM_SCHEMA: Dict[str, Any] = {
    "title": "Tag",
    "type": "object",
    "required": ["name", "value"],
    "properties": {
        "name": {"type": "string", "minLength": 1, "description": "Tag key."},
        "value": {"type": "string", "description": "Tag value."},
    },
    "additionalProperties": False,
}

_TAG_LIST_SCHEMA: Dict[str, Any] = {
    "title": "Tags",
    "description": "Tags to assign to the entity.",
    "type": "array",
    "items": {
        "type": "object",
        "required": ["name", "value"],
        "properties": {
            "name": {"type": "string", "minLength": 1, "description": "Tag key."},
            "value": {"type": "string", "description": "Tag value."},
        },
        "additionalProperties": False,
    },
}

_BOOK_ASSOCIATIONS_SCHEMA: Dict[str, Any] = {
    "title": "Books",
    "description": "IDs of books to associate with the bookshelf.",
    "type": "array",
    "items": {"type": "integer", "minimum": 1},
}

_RAW_OBJECT_PAYLOAD_SCHEMA: Dict[str, Any] = {
    "title": "Raw JSON object",
    "description": "Custom payload forwarded directly to BookStack.",
    "type": "object",
    "additionalProperties": True,
}

_JSON_STRING_PAYLOAD_SCHEMA: Dict[str, Any] = {
    "title": "JSON string payload",
    "description": "Provide a JSON string when constructing the payload manually.",
    "type": "string",
}


TagListInput = Annotated[list[TagDict], WithJsonSchema(copy.deepcopy(_TAG_LIST_SCHEMA))]
BooksAssociationList = Annotated[list[int], WithJsonSchema(copy.deepcopy(_BOOK_ASSOCIATIONS_SCHEMA))]

# Helper schemas for optional integers (MCP strict mode requires oneOf instead of type: ["integer", "null"])
_OPTIONAL_INT_SCHEMA: Dict[str, Any] = {
    "oneOf": [
        {"type": "integer", "minimum": 1},
        {"type": "null"}
    ]
}

_OPTIONAL_STRING_SCHEMA: Dict[str, Any] = {
    "oneOf": [
        {"type": "string", "minLength": 1},
        {"type": "null"}
    ]
}

_OPTIONAL_STRING_NO_MIN_SCHEMA: Dict[str, Any] = {
    "oneOf": [
        {"type": "string"},
        {"type": "null"}
    ]
}

_BOOK_PAYLOAD_SCHEMA: Dict[str, Any] = {
    "title": "Book payload",
    "description": "Fields accepted when creating or updating a book.",
    "type": "object",
    "additionalProperties": False,
    "unevaluatedProperties": False,
    "properties": {
        "name": {"type": "string", "minLength": 1, "description": "Book title."},
        "description": {"type": "string", "minLength": 1, "description": "Book description."},
        "tags": {
            "type": "array",
            "description": "Tags to assign to the entity.",
            "items": {
                "type": "object",
                "required": ["name", "value"],
                "properties": {
                    "name": {"type": "string", "minLength": 1, "description": "Tag key."},
                    "value": {"type": "string", "description": "Tag value."},
                },
                "additionalProperties": False,
            },
        },
        "image_id": {"type": "integer", "minimum": 1, "description": "Existing gallery image ID to reuse as the cover."},
        "cover_image": {"type": "string", "description": "Cover image payload (base64, data URL, or HTTP/HTTPS URL)."},
    },
}

_BOOKSHELF_PAYLOAD_SCHEMA: Dict[str, Any] = {
    "title": "Bookshelf payload",
    "description": "Fields accepted when creating or updating a bookshelf.",
    "type": "object",
    "additionalProperties": False,
    "unevaluatedProperties": False,
    "properties": {
        "name": {"type": "string", "minLength": 1, "description": "Bookshelf title."},
        "description": {"type": "string", "description": "Bookshelf description."},
        "books": {
            "type": "array",
            "description": "IDs of books to associate with the bookshelf.",
            "items": {"type": "integer", "minimum": 1},
        },
        "tags": {
            "type": "array",
            "description": "Tags to assign to the entity.",
            "items": {
                "type": "object",
                "required": ["name", "value"],
                "properties": {
                    "name": {"type": "string", "minLength": 1, "description": "Tag key."},
                    "value": {"type": "string", "description": "Tag value."},
                },
                "additionalProperties": False,
            },
        },
    },
}

_CHAPTER_PAYLOAD_SCHEMA: Dict[str, Any] = {
    "title": "Chapter payload",
    "description": "Fields accepted when creating or updating a chapter.",
    "type": "object",
    "additionalProperties": False,
    "unevaluatedProperties": False,
    "properties": {
        "name": {"type": "string", "minLength": 1, "description": "Chapter title."},
        "description": {"type": "string", "description": "Chapter description."},
        "book_id": {"type": "integer", "minimum": 1, "description": "Parent book identifier."},
        "priority": {"type": "integer", "minimum": 0, "description": "Ordering priority."},
        "tags": {
            "type": "array",
            "description": "Tags to assign to the entity.",
            "items": {
                "type": "object",
                "required": ["name", "value"],
                "properties": {
                    "name": {"type": "string", "minLength": 1, "description": "Tag key."},
                    "value": {"type": "string", "description": "Tag value."},
                },
                "additionalProperties": False,
            },
        },
    },
}

_PAGE_PAYLOAD_SCHEMA: Dict[str, Any] = {
    "title": "Page payload",
    "description": "Fields accepted when creating or updating a page.",
    "type": "object",
    "additionalProperties": False,
    "unevaluatedProperties": False,
    "properties": {
        "name": {"type": "string", "minLength": 1, "description": "Page title."},
        "book_id": {"type": "integer", "minimum": 1, "description": "Book that will contain the page."},
        "chapter_id": {"type": "integer", "minimum": 1, "description": "Chapter that will contain the page."},
        "markdown": {"type": "string", "description": "Markdown content."},
        "content": {"type": "string", "description": "Alias for markdown content."},
        "html": {"type": "string", "description": "HTML content."},
        "priority": {"type": "integer", "minimum": 0, "description": "Ordering priority."},
        "tags": {
            "type": "array",
            "description": "Tags to assign to the entity.",
            "items": {
                "type": "object",
                "required": ["name", "value"],
                "properties": {
                    "name": {"type": "string", "minLength": 1, "description": "Tag key."},
                    "value": {"type": "string", "description": "Tag value."},
                },
                "additionalProperties": False,
            },
        },
    },
}

_PAYLOAD_ONE_OF_WITH_STRING_AND_NULL: list[Dict[str, Any]] = [
    copy.deepcopy(_BOOK_PAYLOAD_SCHEMA),
    copy.deepcopy(_BOOKSHELF_PAYLOAD_SCHEMA),
    copy.deepcopy(_CHAPTER_PAYLOAD_SCHEMA),
    copy.deepcopy(_PAGE_PAYLOAD_SCHEMA),
    # Removed _RAW_OBJECT_PAYLOAD_SCHEMA to comply with MCP strict schema validation
    # Users can still pass custom fields via JSON string in _JSON_STRING_PAYLOAD_SCHEMA
    copy.deepcopy(_JSON_STRING_PAYLOAD_SCHEMA),
    {"type": "null"},
]

PayloadOverrides = Annotated[Any, WithJsonSchema({
    "oneOf": copy.deepcopy(_PAYLOAD_ONE_OF_WITH_STRING_AND_NULL),
})]

BATCH_ITEM_SCHEMA: Dict[str, Any] = {
    "title": "Batch item",
    "description": "Descriptor for a bulk content operation.",
    "type": "object",
    "additionalProperties": False,
    "unevaluatedProperties": False,
    "properties": {
        "id": {"type": "integer", "minimum": 1, "description": "Entity ID used for update/delete operations."},
        "data": {
            "title": "Item payload",
            "description": "Fields applied to the entity. Provide structured values or a JSON string.",
            "oneOf": copy.deepcopy(_PAYLOAD_ONE_OF_WITH_STRING_AND_NULL),
        },
    },
}

BATCH_ITEMS_LIST_SCHEMA: Dict[str, Any] = {
    "title": "Batch items",
    "description": "List of items to process.",
    "type": "array",
    "minItems": 1,
    "items": copy.deepcopy(BATCH_ITEM_SCHEMA),
}

BatchItemInput = Annotated[Dict[str, Any], WithJsonSchema(copy.deepcopy(BATCH_ITEM_SCHEMA))]
BatchItemsListInput = Annotated[list[Dict[str, Any]], WithJsonSchema(copy.deepcopy(BATCH_ITEMS_LIST_SCHEMA))]


@dataclass
class PreparedOperation:
    """Fully prepared request metadata for a content operation."""

    method: str
    path: str
    params: Optional[Dict[str, Any]] = None
    json: Optional[Dict[str, Any]] = None


@dataclass
class PreparedImage:
    """Binary payload and metadata for image uploads."""

    filename: str
    content: bytes
    mime_type: str


@dataclass
class CacheEntry:
    """Cached image list response."""

    timestamp: float
    data: Any
    metadata: Optional[Dict[str, Any]] = None


_ENTITY_BASE_PATHS: Dict[EntityType, str] = {
    "book": "/api/books",
    "bookshelf": "/api/bookshelves",
    "chapter": "/api/chapters",
    "page": "/api/pages",
}

_LIST_BASE_PATHS: Dict[ListEntityType, str] = {
    "books": _ENTITY_BASE_PATHS["book"],
    "bookshelves": _ENTITY_BASE_PATHS["bookshelf"],
    "chapters": _ENTITY_BASE_PATHS["chapter"],
    "pages": _ENTITY_BASE_PATHS["page"],
}

_LIST_CACHE: Dict[str, CacheEntry] = {}
_LIST_CACHE_TTL_SECONDS = 30
_DATA_URL_RE = re.compile(r"^data:([^;,]+)?(;base64)?,(.*)$", re.IGNORECASE)
_HTML_TAG_RE = re.compile(r"<[^>]+>")

_FALLBACK_FILE_NAME = "upload.bin"
_DEFAULT_MIME_TYPE = "application/octet-stream"

# Image URL fetching configuration
_MAX_IMAGE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB limit
_REQUEST_TIMEOUT_SECONDS = 30
_ALLOWED_URL_SCHEMES = {"http", "https"}
_ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/bmp",
    "image/tiff",
    "image/svg+xml",
}

_CONTENT_KNOWN_FIELDS = (
    "name",
    "description",
    "content",
    "markdown",
    "html",
    "book_id",
    "chapter_id",
    "books",
    "tags",
    "image_id",
    "cover_image",
    "priority",
)


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


def _coerce_json_object(
    value: Optional[Union[Dict[str, Any], str]],
    *,
    label: str,
) -> Dict[str, Any]:
    """Return a dictionary parsed from a mapping or JSON string."""

    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise _tool_error(
                f"{label} must contain valid JSON",
                hint="Provide an object such as {\"name\": \"Docs\"} or use the structured fields.",
                context={"received": text[:200]},
            ) from exc
        if not isinstance(parsed, dict):
            raise _tool_error(
                f"{label} must be a JSON object",
                hint="Wrap the payload in curly braces when supplying a string.",
                context={"received": parsed},
            )
        return dict(parsed)
    raise _tool_error(
        f"{label} must be an object or JSON string",
        context={"received_type": type(value).__name__},
    )


def _normalise_str(value: Optional[str]) -> Optional[str]:
    """Strip surrounding whitespace and return None when a string is empty."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _is_url(value: str) -> bool:
    """Check if a string is a valid HTTP/HTTPS URL."""
    try:
        parsed = urlparse(value.strip())
        return parsed.scheme.lower() in _ALLOWED_URL_SCHEMES and bool(parsed.netloc)
    except Exception:
        return False


def _extract_filename_from_url(url: str, fallback: str) -> str:
    """Extract a sensible filename from a URL."""
    try:
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        if path and "." in path:
            filename = path.split("/")[-1]
            # Sanitize filename - remove special characters
            filename = re.sub(r'[^\w\-_\.]', '_', filename)
            if filename and len(filename) <= 255:
                return filename
    except Exception:
        pass
    return fallback


def _fetch_image_from_url(url: str, fallback_name: str) -> PreparedImage:
    """Fetch image data from HTTP/HTTPS URL with security controls."""

    if not _is_url(url):
        raise _tool_error(
            "Invalid URL format",
            hint="Provide a valid HTTP or HTTPS URL.",
            context={"url": url}
        )

    try:
        # Security: Set reasonable timeout and size limits
        response = requests.get(
            url,
            timeout=_REQUEST_TIMEOUT_SECONDS,
            stream=True,
            headers={
                'User-Agent': 'BookStack-MCP/1.0',
                'Accept': 'image/*'
            }
        )
        response.raise_for_status()

        # Check content length before downloading
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > _MAX_IMAGE_SIZE_BYTES:
            raise _tool_error(
                f"Image too large: {content_length} bytes exceeds {_MAX_IMAGE_SIZE_BYTES} byte limit",
                hint="Use a smaller image or increase the size limit.",
                context={"url": url, "size": content_length}
            )

        # Download with size limit
        content = b""
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > _MAX_IMAGE_SIZE_BYTES:
                raise _tool_error(
                    f"Image download exceeded {_MAX_IMAGE_SIZE_BYTES} byte limit",
                    hint="Use a smaller image or increase the size limit.",
                    context={"url": url}
                )

        if not content:
            raise _tool_error(
                "Downloaded image is empty",
                hint="Verify the URL points to a valid image file.",
                context={"url": url}
            )

        # Determine MIME type
        mime_type = response.headers.get('content-type', '').split(';')[0].lower()
        if not mime_type or mime_type not in _ALLOWED_MIME_TYPES:
            # Fallback to guessing from URL extension
            guessed_type, _ = mimetypes.guess_type(url)
            if guessed_type and guessed_type in _ALLOWED_MIME_TYPES:
                mime_type = guessed_type
            else:
                mime_type = _DEFAULT_MIME_TYPE

        # Extract filename
        filename = _extract_filename_from_url(url, fallback_name)

        return PreparedImage(
            filename=filename,
            content=content,
            mime_type=mime_type
        )

    except requests.exceptions.Timeout as exc:
        raise _tool_error(
            f"Request timeout after {_REQUEST_TIMEOUT_SECONDS} seconds",
            hint="The image server may be slow or unreachable. Try again later.",
            context={"url": url}
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise _tool_error(
            "Failed to connect to image URL",
            hint="Check the URL and ensure the server is accessible.",
            context={"url": url}
        ) from exc
    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response else "unknown"
        raise _tool_error(
            f"HTTP error {status_code} when fetching image",
            hint="Verify the URL is correct and the image is publicly accessible.",
            context={"url": url, "status_code": status_code}
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise _tool_error(
            "Failed to fetch image from URL",
            hint="Check the URL format and network connectivity.",
            context={"url": url, "error": str(exc)}
        ) from exc
    except ToolError:
        # Re-raise ToolErrors (e.g., from size limit checks) without wrapping
        raise
    except Exception as exc:  # pragma: no cover - defensive guard
        raise _tool_error(
            "Unexpected error while fetching image from URL",
            context={"url": url, "error": str(exc)}
        ) from exc


def _validate_positive_int(value: Optional[Any], label: str) -> int:
    """Ensure a positive integer value is provided."""
    if value is None:
        raise _tool_error(
            f"{label} is required",
            hint=f"Provide a numeric value for {label}.",
        )
    try:
        int_value = int(value)
    except (TypeError, ValueError) as exc:
        raise _tool_error(
            f"{label} must be a positive integer",
            hint=f"Provide a numeric value greater than zero for {label}.",
            context={"received": value},
        ) from exc
    _ensure(
        int_value > 0,
        f"{label} must be a positive integer",
        hint=f"Provide a numeric value greater than zero for {label}.",
        context={"received": value},
    )
    return int_value


def _optional_positive_int(value: Optional[Any], label: str) -> Optional[int]:
    """Return a validated positive integer or None."""
    if value is None:
        return None
    return _validate_positive_int(value, label)


def _optional_non_negative_int(value: Optional[Any], label: str) -> Optional[int]:
    """Return a validated non-negative integer or None."""
    if value is None:
        return None
    try:
        int_value = int(value)
    except (TypeError, ValueError) as exc:
        raise _tool_error(
            f"{label} must be a non-negative integer",
            hint=f"Provide a zero or positive integer for {label}.",
            context={"received": value},
        ) from exc
    _ensure(
        int_value >= 0,
        f"{label} must be a non-negative integer",
        hint=f"Provide a zero or positive integer for {label}.",
        context={"received": value},
    )
    return int_value


def _normalise_books(collection: Optional[Sequence[Any]]) -> Optional[list[int]]:
    """Convert a sequence of book IDs into validated integers."""
    if collection is None:
        return None
    return [_validate_positive_int(item, "Book ID") for item in collection]


def _format_tags(tags: Optional[Sequence[TagDict]]) -> Optional[list[TagDict]]:
    """Return tags in the shape expected by BookStack, or None if absent."""
    if tags is None:
        return None

    formatted: list[TagDict] = []
    for tag in tags:
        name = tag.get("name") if isinstance(tag, dict) else getattr(tag, "name", None)
        value = tag.get("value") if isinstance(tag, dict) else getattr(tag, "value", None)
        if not name:
            raise _tool_error(
                "Tag entries require a non-empty 'name'",
                hint="Each tag must specify both 'name' and 'value'.",
            )
        if value is None:
            raise _tool_error(
                "Tag entries require a 'value'",
                hint="Each tag must specify both 'name' and 'value'.",
            )
        formatted.append({"name": str(name), "value": str(value)})
    return formatted


def _compact_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove keys with None values or empty strings."""
    compacted: Dict[str, Any] = {}
    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, str) and value == "":
            continue
        compacted[key] = value
    return compacted


def _filter_collection(
    data: Any,
    predicate: Optional[Any],
) -> Tuple[Any, Optional[int]]:
    """Filter a collection payload and return (filtered, match_count)."""

    if predicate is None:
        return data, None

    if isinstance(data, dict) and isinstance(data.get("data"), list):
        original_items = data["data"]
        filtered_items = [item for item in original_items if predicate(item)]
        match_count = len(filtered_items)
        new_payload = dict(data)
        new_payload["data"] = filtered_items
        if "count" in new_payload:
            new_payload["count"] = match_count
        return new_payload, match_count

    if isinstance(data, list):
        filtered_items = [item for item in data if predicate(item)]
        return filtered_items, len(filtered_items)

    return data, None


def _bookstack_request(
    method: str,
    path: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
) -> Any:
    """Execute a JSON request against the BookStack API."""

    url = f"{_bookstack_base_url()}{path}"
    try:
        response = requests.request(
            method,
            url,
            headers=_bookstack_headers(),
            params=params,
            json=json,
            timeout=60,
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        import logging
        logger = logging.getLogger(__name__)

        status = exc.response.status_code if exc.response is not None else "unknown"
        preview: Optional[str] = None
        error_detail = ""
        if exc.response is not None:
            try:
                preview = exc.response.text[:400]
                logger.error(f"BookStack API error {status}: {preview}")
                # Try to extract error message from JSON response
                try:
                    error_json = exc.response.json()
                    if isinstance(error_json, dict):
                        if 'error' in error_json:
                            error_detail = f": {error_json['error']}"
                        elif 'message' in error_json:
                            error_detail = f": {error_json['message']}"
                except Exception:
                    pass
            except Exception:  # pragma: no cover - defensive guard
                preview = None

        # Provide specific hints for common HTTP errors
        hint = "Verify the BookStack credentials, entity identifiers, and payload fields."
        if status == 409:
            hint = "Conflict error (409): This usually means a resource with the same name already exists, or there's a constraint violation. Check the response_preview for details."
        elif status == 404:
            hint = "Not found (404): The entity ID or endpoint doesn't exist. Verify the ID is correct."
        elif status == 401:
            hint = "Unauthorized (401): Check your BS_TOKEN_ID and BS_TOKEN_SECRET environment variables."
        elif status == 403:
            hint = "Forbidden (403): Your API token doesn't have permission for this operation."
        elif status == 422:
            hint = "Validation error (422): The request payload is invalid. Check the response_preview for field-specific errors."

        error_msg = f"BookStack API request failed with HTTP {status}{error_detail}"
        logger.error(f"{error_msg}\nHint: {hint}\nMethod: {method}, Path: {path}")

        raise _tool_error(
            error_msg,
            hint=hint,
            context={
                "method": method,
                "path": path,
                "params": params,
                "payload": json,
                "status": status,
                "response_preview": preview,
            },
        ) from exc
    except requests.RequestException as exc:  # pragma: no cover - network failure path
        raise _tool_error(
            "Unable to reach the BookStack API endpoint",
            hint="Check network connectivity and ensure the BS_URL host is reachable from the container.",
            context={"method": method, "path": path, "params": params},
        ) from exc

    if response.status_code == 204 or not response.content:
        return {"success": True, "status": response.status_code}

    try:
        return response.json()
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
        status = exc.response.status_code if exc.response is not None else "unknown"
        preview: Optional[str] = None
        error_detail = ""
        if exc.response is not None:
            try:
                preview = exc.response.text[:400]
                # Try to extract error message from JSON response
                try:
                    error_json = exc.response.json()
                    if isinstance(error_json, dict):
                        if 'error' in error_json:
                            error_detail = f": {error_json['error']}"
                        elif 'message' in error_json:
                            error_detail = f": {error_json['message']}"
                except Exception:
                    pass
            except Exception:  # pragma: no cover - defensive guard
                preview = None

        # Provide specific hints for common HTTP errors
        hint = "Confirm the image identifiers and ensure the API token grants image permissions."
        if status == 409:
            hint = "Conflict error (409): This usually means an image with the same name already exists. Check the response_preview for details."
        elif status == 404:
            hint = "Not found (404): The image ID doesn't exist. Verify the ID is correct."
        elif status == 401:
            hint = "Unauthorized (401): Check your BS_TOKEN_ID and BS_TOKEN_SECRET environment variables."
        elif status == 403:
            hint = "Forbidden (403): Your API token doesn't have permission for image operations."
        elif status == 422:
            hint = "Validation error (422): The image data is invalid. Check the response_preview for details."

        raise _tool_error(
            f"BookStack image endpoint returned HTTP {status}{error_detail}",
            hint=hint,
            context={
                "method": method,
                "path": path,
                "status": status,
                "data_keys": list((data or {}).keys()),
                "files_keys": list((files or {}).keys()),
                "response_preview": preview,
            },
        ) from exc
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


def _prepare_image_payload(
    image: str,
    fallback_name: str,
    fallback_type: str = _DEFAULT_MIME_TYPE,
) -> PreparedImage:
    """Prepare image payload from base64, data URL, or HTTP/HTTPS URL."""

    value = image.strip()

    # Check if it looks like a URL (has scheme and netloc)
    try:
        parsed = urlparse(value)
        if parsed.scheme and parsed.netloc:
            # It looks like a URL - check if it's allowed
            if parsed.scheme.lower() not in _ALLOWED_URL_SCHEMES:
                raise _tool_error(
                    f"URL scheme '{parsed.scheme}' is not supported",
                    hint="Only HTTP and HTTPS URLs are allowed for image fetching.",
                    context={"url": value, "scheme": parsed.scheme}
                )
            # It's a valid HTTP/HTTPS URL
            return _fetch_image_from_url(value, fallback_name)
    except ToolError:
        # Re-raise ToolErrors
        raise
    except Exception:
        # Not a valid URL, continue to other formats
        pass

    # Check if it's a data URL
    match = _DATA_URL_RE.match(value)
    if match:
        mime_type = match.group(1) or fallback_type
        is_base64 = bool(match.group(2))
        raw_payload = match.group(3) or ""
        if is_base64:
            content = _decode_base64_string(raw_payload)
        else:
            content = unquote(raw_payload).encode("utf-8")
        if not content:
            raise _tool_error(
                "Image payload is empty after decoding the provided data URL",
                hint="Ensure the data URL includes image bytes after the comma separator.",
            )
        return PreparedImage(filename=fallback_name, content=content, mime_type=mime_type)

    # Assume it's a base64 string
    content = _decode_base64_string(value)
    if not content:
        raise _tool_error(
            "Decoded image payload is empty",
            hint="Confirm the base64 string contains valid image data.",
        )
    return PreparedImage(filename=fallback_name, content=content, mime_type=fallback_type)



def _prepare_cover_image_from_gallery(
    image_id: Any,
    *,
    fallback_name: Optional[str],
) -> PreparedImage:
    """Fetch an existing gallery image and return it as a PreparedImage."""

    validated_id = _validate_positive_int(image_id, "'image_id'")
    metadata = _bookstack_request("GET", f"/api/image-gallery/{validated_id}")
    if not isinstance(metadata, dict):
        raise _tool_error(
            "Unexpected response when fetching gallery image metadata",
            hint="Ensure the image exists and the API token grants image permissions.",
            context={"image_id": validated_id, "payload_type": type(metadata).__name__},
        )

    raw_name = metadata.get("name")
    image_name = _normalise_str(raw_name) if isinstance(raw_name, str) else None

    image_url: Optional[str] = None
    raw_url = metadata.get("url")
    if isinstance(raw_url, str) and raw_url.strip():
        image_url = raw_url.strip()
    else:
        raw_path = metadata.get("path")
        if isinstance(raw_path, str) and raw_path.strip():
            image_url = f"{_bookstack_base_url()}{raw_path}"

    if not image_url:
        raise _tool_error(
            "Gallery image metadata did not include a usable URL",
            hint="Verify the image exists and is accessible via the BookStack instance.",
            context={"image_id": validated_id, "metadata_keys": list(metadata.keys())},
        )

    effective_name = image_name or fallback_name or f"book-cover-{validated_id}"
    return _fetch_image_from_url(image_url, effective_name)




def _prepare_form_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a JSON-style payload into form fields for multipart requests."""
    form_data: Dict[str, Any] = {}
    for key, value in payload.items():
        if value is None or key in {"image_id", "cover_image"}:
            continue
        if isinstance(value, (dict, list)):
            form_data[key] = json.dumps(value)
        else:
            form_data[key] = value if isinstance(value, str) else str(value)
    return form_data


def _decode_base64_string(payload: str) -> bytes:
    try:
        cleaned = re.sub(r"\s+", "", payload)
        return base64.b64decode(cleaned, validate=True)
    except (ValueError, binascii.Error) as exc:  # type: ignore[name-defined]
        raise _tool_error(
            "Failed to decode base64 image data",
            hint="Verify the string is base64 encoded without extra whitespace or URL encoding.",
            context={"error": str(exc)},
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        raise _tool_error(
            "Unexpected error while decoding base64 image data",
            context={"error": str(exc)},
        ) from exc


# Avoid importing binascii at module import time only if needed
import binascii  # noqa: E402  (after helper definition for mypy clarity)


def _normalize_image_list_response(
    api_response: Any,
    *,
    offset: int,
    count: int,
) -> Tuple[Any, Optional[Dict[str, Any]]]:
    if isinstance(api_response, dict) and isinstance(api_response.get("data"), list):
        images = api_response["data"]
        metadata: Dict[str, Any] = {}
        if isinstance(api_response.get("total"), int):
            metadata["total"] = api_response["total"]
        if isinstance(api_response.get("count"), int):
            metadata["count"] = api_response["count"]
        else:
            metadata["count"] = len(images)
        if isinstance(api_response.get("offset"), int):
            metadata["offset"] = api_response["offset"]
        else:
            metadata["offset"] = offset
        return images, metadata

    if isinstance(api_response, list):
        metadata = {"offset": offset, "count": len(api_response)}
        return api_response, metadata

    return api_response, None


def _build_list_cache_key(params: Dict[str, Any]) -> str:
    items: list[Tuple[str, Any]] = []
    for key, value in sorted(params.items()):
        if isinstance(value, list):
            items.append((key, tuple(value)))
        elif isinstance(value, dict):
            items.append((key, tuple(sorted(value.items()))))
        else:
            items.append((key, value))
    return repr(items)


def _get_cached_list(cache_key: str) -> Optional[CacheEntry]:
    entry = _LIST_CACHE.get(cache_key)
    if not entry:
        return None
    if time.time() - entry.timestamp > _LIST_CACHE_TTL_SECONDS:
        _LIST_CACHE.pop(cache_key, None)
        return None
    return entry


def _set_cached_list(cache_key: str, data: Any, metadata: Optional[Dict[str, Any]]) -> None:
    _LIST_CACHE[cache_key] = CacheEntry(timestamp=time.time(), data=data, metadata=metadata)


def _invalidate_list_cache() -> None:
    _LIST_CACHE.clear()


def _ensure_iso8601(value: str, label: str) -> datetime:
    try:
        normalised = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalised)
    except ValueError as exc:
        raise _tool_error(
            f"{label} must be an ISO-8601 datetime string",
            hint="Use formats like '2025-09-27T18:00:00Z' or '2025-09-27T18:00:00+00:00'.",
            context={"received": value},
        ) from exc


def _build_content_operation(
    operation: OperationType,
    entity_type: EntityType,
    *,
    entity_id: Optional[int],
    name: Optional[str],
    description: Optional[str],
    content: Optional[str],
    markdown: Optional[str],
    html: Optional[str],
    cover_image: Optional[str],
    updates: Optional[Dict[str, Any]],
    book_id: Optional[Any],
    chapter_id: Optional[Any],
    books: Optional[Sequence[Any]],
    tags: Optional[Sequence[TagDict]],
    image_id: Optional[Any],
    priority: Optional[Any],
) -> PreparedOperation:
    base_path = _ENTITY_BASE_PATHS[entity_type]

    if operation == "read":
        _ensure(entity_id is not None, "'id' is required when reading an entity")
        return PreparedOperation(method="GET", path=f"{base_path}/{entity_id}")

    if operation == "delete":
        _ensure(entity_id is not None, "'id' is required when deleting an entity")
        return PreparedOperation(method="DELETE", path=f"{base_path}/{entity_id}")

    payload: Dict[str, Any] = _coerce_json_object(updates, label="'updates'")
    formatted_tags = _format_tags(tags)
    if formatted_tags is not None:
        payload["tags"] = formatted_tags

    if operation == "create":
        name_value = _normalise_str(payload.get("name")) or _normalise_str(name)
        _ensure(name_value is not None, "'name' is required when creating an entity")
        payload["name"] = name_value

        if entity_type == "book":
            description_value = _normalise_str(payload.get("description")) or _normalise_str(description)
            _ensure(description_value is not None, "'description' is required when creating a book")
            payload["description"] = description_value
            image_value = payload.get("image_id") if payload.get("image_id") is not None else image_id
            if image_value is not None:
                payload["image_id"] = _validate_positive_int(image_value, "'image_id'")

        elif entity_type == "bookshelf":
            description_value = _normalise_str(description) or _normalise_str(payload.get("description"))
            if description_value is not None:
                payload["description"] = description_value
            shelf_books = books if books is not None else payload.get("books")
            normalised_books = _normalise_books(shelf_books)
            if normalised_books is not None:
                payload["books"] = normalised_books
            else:
                payload.pop("books", None)

        elif entity_type == "chapter":
            chapter_book_id = payload.get("book_id") if payload.get("book_id") is not None else book_id
            payload["book_id"] = _validate_positive_int(chapter_book_id, "'book_id'")
            description_value = _normalise_str(description) or _normalise_str(payload.get("description"))
            if description_value is not None:
                payload["description"] = description_value
            chapter_priority = priority if priority is not None else payload.get("priority")
            priority_value = _optional_non_negative_int(chapter_priority, "'priority'")
            if priority_value is not None:
                payload["priority"] = priority_value
            else:
                payload.pop("priority", None)

        elif entity_type == "page":
            page_book_id = payload.get("book_id") if payload.get("book_id") is not None else book_id
            page_chapter_id = payload.get("chapter_id") if payload.get("chapter_id") is not None else chapter_id
            book_value = _optional_positive_int(page_book_id, "'book_id'")
            chapter_value = _optional_positive_int(page_chapter_id, "'chapter_id'")
            if book_value is None and chapter_value is None:
                raise _tool_error(
                    "Provide either 'book_id' or 'chapter_id' when creating a page",
                    hint="Set 'book_id' for top-level pages or 'chapter_id' when nesting within a chapter.",
                    context={"operation": operation, "entity_type": entity_type},
                )
            if book_value is not None:
                payload["book_id"] = book_value
            else:
                payload.pop("book_id", None)
            if chapter_value is not None:
                payload["chapter_id"] = chapter_value
            else:
                payload.pop("chapter_id", None)

            markdown_value = payload.get("markdown")
            html_value = payload.get("html")
            if markdown is not None:
                markdown_value = markdown
            elif content is not None and markdown_value is None:
                markdown_value = content
            if html is not None:
                html_value = html

            if isinstance(markdown_value, str):
                markdown_value = _normalise_str(markdown_value)
            if isinstance(html_value, str):
                html_value = _normalise_str(html_value)

            if markdown_value and html_value:
                raise _tool_error(
                    "Provide either markdown/content or html, not both",
                    hint="Supply only one of 'markdown'/'content' or 'html' for a page.",
                    context={"operation": operation, "entity_type": entity_type},
                )
            if markdown_value is not None:
                payload["markdown"] = markdown_value
            else:
                payload.pop("markdown", None)
            if html_value is not None:
                payload["html"] = html_value
            else:
                payload.pop("html", None)

            page_priority = priority if priority is not None else payload.get("priority")
            priority_value = _optional_non_negative_int(page_priority, "'priority'")
            if priority_value is not None:
                payload["priority"] = priority_value
            else:
                payload.pop("priority", None)

        else:  # pragma: no cover - exhaustive guard
            raise _tool_error(
                f"Unsupported entity type: {entity_type}",
                context={"operation": operation},
            )

        payload = _compact_payload(payload)
        return PreparedOperation(method="POST", path=base_path, json=payload)

    if operation == "update":
        _ensure(
            entity_id is not None,
            "'id' is required when updating an entity",
            hint="Provide the entity identifier via the 'id' argument when updating.",
            context={"operation": operation, "entity_type": entity_type},
        )

        if name is not None:
            payload["name"] = _normalise_str(name) or name
        if description is not None:
            payload["description"] = _normalise_str(description) or description

        if entity_type == "book":
            image_value = image_id if image_id is not None else payload.get("image_id")
            if image_value is not None:
                payload["image_id"] = _validate_positive_int(image_value, "'image_id'")

        elif entity_type == "bookshelf":
            shelf_books = books if books is not None else payload.get("books")
            normalised_books = _normalise_books(shelf_books)
            if normalised_books is not None:
                payload["books"] = normalised_books
            else:
                payload.pop("books", None)

        elif entity_type == "chapter":
            chapter_book = book_id if book_id is not None else payload.get("book_id")
            if chapter_book is not None:
                payload["book_id"] = _validate_positive_int(chapter_book, "'book_id'")
            chapter_priority = priority if priority is not None else payload.get("priority")
            if chapter_priority is not None:
                payload["priority"] = _optional_non_negative_int(chapter_priority, "'priority'")

        elif entity_type == "page":
            page_book = book_id if book_id is not None else payload.get("book_id")
            page_chapter = chapter_id if chapter_id is not None else payload.get("chapter_id")
            if page_book is not None:
                payload["book_id"] = _validate_positive_int(page_book, "'book_id'")
            if page_chapter is not None:
                payload["chapter_id"] = _validate_positive_int(page_chapter, "'chapter_id'")

            markdown_value = payload.get("markdown")
            html_value = payload.get("html")

            if markdown is not None:
                markdown_value = markdown
            elif content is not None and markdown_value is None:
                markdown_value = content
            if html is not None:
                html_value = html

            if isinstance(markdown_value, str):
                markdown_value = _normalise_str(markdown_value)
            if isinstance(html_value, str):
                html_value = _normalise_str(html_value)

            if markdown_value and html_value:
                raise _tool_error(
                    "Provide either markdown/content or html, not both",
                    hint="Supply only one of 'markdown'/'content' or 'html' for a page update.",
                    context={"operation": operation, "entity_type": entity_type, "entity_id": entity_id},
                )
            if markdown_value is not None:
                payload["markdown"] = markdown_value
            elif "markdown" in payload:
                payload.pop("markdown")
            if html_value is not None:
                payload["html"] = html_value
            elif "html" in payload:
                payload.pop("html")

            page_priority = priority if priority is not None else payload.get("priority")
            if page_priority is not None:
                payload["priority"] = _optional_non_negative_int(page_priority, "'priority'")

        else:  # pragma: no cover - exhaustive guard
            raise _tool_error(
                f"Unsupported entity type: {entity_type}",
                context={"operation": operation, "entity_id": entity_id},
            )

        payload = _compact_payload(payload)
        allow_empty = entity_type == "book" and cover_image is not None
        if not payload and not allow_empty:
            _ensure(
                bool(payload),
                "Provide at least one field to update",
                hint="Include at least one non-empty field (e.g., 'name', 'description', or entries in 'updates').",
                context={"operation": operation, "entity_type": entity_type, "entity_id": entity_id},
            )
        return PreparedOperation(method="PUT", path=f"{base_path}/{entity_id}", json=payload)

    raise _tool_error(
        f"Unsupported operation '{operation}'",
        context={"entity_type": entity_type},
    )


def _extract_known_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    extracted: Dict[str, Any] = {}
    for field in _CONTENT_KNOWN_FIELDS:
        if field in data:
            extracted[field] = data[field]
    return extracted


def _normalise_filters(filters: Optional[Sequence[FilterEntry]]) -> Optional[list[Tuple[str, str]]]:
    if filters is None:
        return None
    normalised: list[Tuple[str, str]] = []
    for entry in filters:
        key = _normalise_str(entry.get("key")) if isinstance(entry, dict) else None
        value = entry.get("value") if isinstance(entry, dict) else None
        if not key:
            raise _tool_error(
                "Filter entries require a non-empty 'key'",
                hint="Provide each filter entry as {'key': 'field', 'value': 'match'}.",
            )
        if value is None:
            raise _tool_error(
                "Filter entries require a 'value'",
                hint="Provide each filter entry as {'key': 'field', 'value': 'match'}.",
            )
        normalised.append((key, str(value)))
    return normalised


def _as_string(value: Any) -> Optional[str]:
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    return None


def _trim_summary(raw: str) -> str:
    without_tags = _HTML_TAG_RE.sub("", raw).replace("\n", " ").strip()
    collapsed = re.sub(r"\s+", " ", without_tags)
    return f"{collapsed[:277]}..." if len(collapsed) > 280 else collapsed


def _extract_summary(item: Dict[str, Any]) -> str:
    preview = item.get("preview_html")
    if isinstance(preview, dict):
        content = _as_string(preview.get("content"))
        if content:
            return _trim_summary(content)
    description = _as_string(item.get("description"))
    if description:
        return _trim_summary(description)
    return "No summary available"


def register_bookstack_tools(mcp: FastMCP) -> None:
    """Register BookStack tools on the provided FastMCP instance."""

    @mcp.tool(
        annotations={
            "title": "Manage BookStack Content",
        }
    )
    def bookstack_manage_content(
        operation: Annotated[
            OperationType,
            Field(description="Operation to perform (create, read, update, delete)."),
        ],
        entity_type: Annotated[
            EntityType,
            Field(description="Entity to operate on (book, bookshelf, chapter, page)."),
        ],
        id: Annotated[
            Optional[int],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_INT_SCHEMA), "description": "Entity ID (required for read, update, delete)."}),
        ] = None,
        name: Annotated[
            Optional[str],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_STRING_SCHEMA), "description": "Entity name/title."}),
        ] = None,
        description: Annotated[
            Optional[str],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_STRING_SCHEMA), "description": "Entity description."}),
        ] = None,
        content: Annotated[
            Optional[str],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_STRING_NO_MIN_SCHEMA), "description": "Page content (alias for markdown)."}),
        ] = None,
        markdown: Annotated[
            Optional[str],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_STRING_NO_MIN_SCHEMA), "description": "Markdown content."}),
        ] = None,
        html: Annotated[
            Optional[str],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_STRING_NO_MIN_SCHEMA), "description": "HTML content."}),
        ] = None,
        cover_image: Annotated[
            Optional[str],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_STRING_NO_MIN_SCHEMA), "description": "Cover image payload (base64, data URL, or HTTP/HTTPS URL)."}),
        ] = None,
        updates: Annotated[
            PayloadOverrides,
            Field(default=None, description="Raw field overrides passed directly to the API."),
        ] = None,
        book_id: Annotated[
            Optional[int],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_INT_SCHEMA), "description": "Book ID context (required for chapter create, optional otherwise)."}),
        ] = None,
        chapter_id: Annotated[
            Optional[int],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_INT_SCHEMA), "description": "Chapter ID context (required for page create when no book_id)."}),
        ] = None,
        books: Annotated[
            Optional[BooksAssociationList],
            Field(
                default=None,
                description="Book IDs to associate with a bookshelf.",
            ),
        ] = None,
        tags: Annotated[
            Optional[TagListInput],
            Field(
                default=None,
                description="Tags to assign to the entity.",
            ),
        ] = None,
        image_id: Annotated[
            Optional[int],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_INT_SCHEMA), "description": "Image ID to use as cover (books only)."}),
        ] = None,
        priority: Annotated[
            Optional[int],
            WithJsonSchema({"oneOf": [{"type": "integer", "minimum": 0}, {"type": "null"}], "description": "Ordering priority for chapters/pages."}),
        ] = None,
    ) -> Dict[str, Any]:
        """Perform CRUD operations against BookStack content entities."""

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"bookstack_manage_content called: operation={operation}, entity_type={entity_type}, id={id}")

        prepared = _build_content_operation(
            operation,
            entity_type,
            entity_id=id,
            name=name,
            description=description,
            content=content,
            markdown=markdown,
            html=html,
            cover_image=cover_image,
            updates=updates,
            book_id=book_id,
            chapter_id=chapter_id,
            books=books,
            tags=tags,
            image_id=image_id,
            priority=priority,
        )

        prepared_image_payload: Optional[PreparedImage] = None
        if entity_type == "book" and operation in {"create", "update"}:
            fallback_name = name or ((prepared.json or {}).get("name") if isinstance(prepared.json, dict) else None)
            if not fallback_name:
                fallback_name = f"book-{id}-cover" if id is not None else "book-cover"
            if cover_image is not None:
                prepared_image_payload = _prepare_image_payload(cover_image, fallback_name)
            elif image_id is not None:
                prepared_image_payload = _prepare_cover_image_from_gallery(image_id, fallback_name=fallback_name)

        if prepared_image_payload is not None:
            form_data = _prepare_form_data(prepared.json or {})
            method = prepared.method
            if operation == "update":
                method = "POST"
                form_data["_method"] = "PUT"
            files = {"image": (
                prepared_image_payload.filename,
                prepared_image_payload.content,
                prepared_image_payload.mime_type,
            )}
            response = _bookstack_request_form(
                method,
                prepared.path,
                data=form_data or None,
                files=files,
            )
            result: Dict[str, Any] = {
                "operation": operation,
                "entity_type": entity_type,
                "success": True,
                "data": response,
            }
            if id is not None:
                result["id"] = id
            elif isinstance(response, dict) and isinstance(response.get("id"), int):
                result["id"] = response["id"]
            return result

        response = _bookstack_request(
            prepared.method,
            prepared.path,
            params=prepared.params,
            json=prepared.json,
        )

        result: Dict[str, Any] = {
            "operation": operation,
            "entity_type": entity_type,
            "success": True,
            "data": response,
        }
        if id is not None:
            result["id"] = id
        elif isinstance(response, dict) and isinstance(response.get("id"), int):
            result["id"] = response["id"]
        return result

    @mcp.tool(
        annotations={
            "title": "List BookStack Content",
            "readOnlyHint": True,
        }
    )
    def bookstack_list_content(
        entity_type: Annotated[
            ListEntityType,
            Field(description="Entity collection to list (books, bookshelves, chapters, pages)."),
        ],
        offset: Annotated[
            int,
            Field(ge=0, description="Number of records to skip."),
        ] = 0,
        count: Annotated[
            int,
            Field(ge=1, le=100, description="Number of records to take (1-100)."),
        ] = 50,
        sort: Annotated[
            Optional[str],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_STRING_NO_MIN_SCHEMA), "description": "Sort expression understood by BookStack (e.g. '-created_at')."}),
        ] = None,
        filters: Annotated[
            Optional[Dict[str, str]],
            Field(default=None, description="Additional filters forwarded as filter[<key>]=value."),
        ] = None,
        book_id: Annotated[
            Optional[int],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_INT_SCHEMA), "description": "Limit chapters/pages to a specific book."}),
        ] = None,
        chapter_id: Annotated[
            Optional[int],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_INT_SCHEMA), "description": "Limit pages to a specific chapter."}),
        ] = None,
        id: Annotated[
            Optional[str],
            Field(default=None, description="Ignored parameter (for MCP client compatibility)"),
        ] = None,
        request_heartbeat: Annotated[
            Optional[bool],
            Field(default=None, description="Ignored parameter (for MCP client compatibility)"),
        ] = None,
    ) -> Dict[str, Any]:
        """Return a paginated listing of BookStack entities."""

        base_path = _LIST_BASE_PATHS[entity_type]

        validated_book_id: Optional[int] = None
        validated_chapter_id: Optional[int] = None
        filter_scope: Dict[str, Any] = {}

        if entity_type in ("chapters", "pages") and book_id is not None:
            validated_book_id = _validate_positive_int(book_id, "'book_id'")
            filter_scope["book_id"] = validated_book_id
        if entity_type == "pages" and chapter_id is not None:
            validated_chapter_id = _validate_positive_int(chapter_id, "'chapter_id'")
            filter_scope["chapter_id"] = validated_chapter_id

        scoped_items: Optional[list] = None
        scoped_total: Optional[int] = None

        if entity_type == "chapters" and validated_book_id is not None:
            book_payload = _bookstack_request("GET", f"/api/books/{validated_book_id}")
            contents = book_payload.get("contents", [])
            chapters = [item for item in contents if isinstance(item, dict) and item.get("type") == "chapter"]
            scoped_items = chapters
            scoped_total = len(chapters)
        elif entity_type == "pages" and validated_chapter_id is not None:
            chapter_payload = _bookstack_request("GET", f"/api/chapters/{validated_chapter_id}")
            pages = chapter_payload.get("pages", [])
            scoped_items = pages
            scoped_total = len(pages)
        elif entity_type == "pages" and validated_book_id is not None:
            book_payload = _bookstack_request("GET", f"/api/books/{validated_book_id}")
            pages: list = []
            for entry in book_payload.get("contents", []):
                if not isinstance(entry, dict):
                    continue
                if entry.get("type") == "page":
                    pages.append(entry)
                elif entry.get("type") == "chapter":
                    pages.extend(entry.get("pages", []))
            scoped_items = pages
            scoped_total = len(pages)

        if scoped_items is not None:
            start = max(offset, 0)
            end = start + count
            paged_items = scoped_items[start:end]
            data = {
                "data": paged_items,
                "total": scoped_total,
                "count": len(paged_items),
            }
            metadata: Dict[str, Any] = {
                "offset": offset,
                "count": count,
                "total": scoped_total,
                "returned": len(paged_items),
                "scoped": True,
                "filter_context": filter_scope,
            }
        else:
            params: Dict[str, Any] = {"offset": offset, "count": count}
            if sort:
                params["sort"] = sort
            if filters:
                for key, value in filters.items():
                    key_clean = _normalise_str(key)
                    _ensure(
                        bool(key_clean),
                        "Filter keys must be non-empty strings",
                    )
                    params[f"filter[{key_clean}]"] = value

            if validated_book_id is not None:
                params["book_id"] = validated_book_id
            if validated_chapter_id is not None:
                params["chapter_id"] = validated_chapter_id

            data = _bookstack_request("GET", base_path, params=params)

            predicate = None
            if entity_type == "chapters" and validated_book_id is not None:
                predicate = lambda item: not isinstance(item, dict) or item.get("book_id") == validated_book_id
            elif entity_type == "pages" and (validated_book_id is not None or validated_chapter_id is not None):
                def predicate(item: Any) -> bool:
                    if not isinstance(item, dict):
                        return True
                    if validated_book_id is not None and item.get("book_id") != validated_book_id:
                        return False
                    if validated_chapter_id is not None and item.get("chapter_id") != validated_chapter_id:
                        return False
                    return True

            filtered_data, matched_count = _filter_collection(data, predicate)
            data = filtered_data

            metadata = {"offset": offset, "count": count}
            if isinstance(data, dict):
                if isinstance(data.get("total"), int):
                    metadata["total"] = data["total"]
                if isinstance(data.get("count"), int):
                    metadata["returned"] = data["count"]
            if matched_count is not None:
                metadata["returned"] = matched_count
            if predicate is not None:
                metadata["scoped"] = True
                metadata["filter_context"] = filter_scope

        result: Dict[str, Any] = {
            "operation": "list",
            "entity_type": entity_type,
            "success": True,
            "data": data,
            "metadata": metadata,
        }
        if sort:
            result["sort"] = sort
        if filters:
            result["filters"] = filters
        if book_id is not None:
            result["book_id"] = book_id
        if chapter_id is not None:
            result["chapter_id"] = chapter_id
        return result

    @mcp.tool(
        annotations={
            "title": "Search BookStack",
            "readOnlyHint": True,
        }
    )
    def bookstack_search(
        query: Annotated[
            str,
            Field(min_length=1, description="Search query text."),
        ],
        page: Annotated[
            Optional[int],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_INT_SCHEMA), "description": "Page number for pagination."}),
        ] = None,
        count: Annotated[
            Optional[int],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_INT_SCHEMA), "description": "Number of results per page (max 100)."}),
        ] = None,
        request_heartbeat: Annotated[
            Optional[bool],
            Field(default=None, description="Ignored parameter (for MCP client compatibility)"),
        ] = None,
    ) -> Dict[str, Any]:
        """Search across BookStack content."""

        params: Dict[str, Any] = {"query": query}
        if page is not None:
            params["page"] = page
        if count is not None:
            params["count"] = count

        response = _bookstack_request("GET", "/api/search", params=params)

        items = response.get("data") if isinstance(response, dict) else None
        items_list = items if isinstance(items, list) else []

        limit = count or 20
        results: list[Dict[str, Any]] = []
        for item in items_list:
            if not isinstance(item, dict):
                continue
            title = _as_string(item.get("name")) or _as_string(item.get("slug")) or "Untitled"
            summary = _extract_summary(item)
            result_item: Dict[str, Any] = {
                "id": item.get("id"),
                "type": _as_string(item.get("type")) or "unknown",
                "title": title,
                "url": _as_string(item.get("url")),
                "summary": summary,
            }
            book = item.get("book")
            if isinstance(book, dict):
                result_item["book"] = {
                    "id": book.get("id"),
                    "name": _as_string(book.get("name")),
                }
            chapter = item.get("chapter")
            if isinstance(chapter, dict):
                result_item["chapter"] = {
                    "id": chapter.get("id"),
                    "name": _as_string(chapter.get("name")),
                }
            results.append(result_item)
            if len(results) >= limit:
                break

        payload: Dict[str, Any] = {
            "query": query,
            "page": page,
            "count": limit,
            "returned": len(results),
            "results": results,
            "success": True,
        }
        if isinstance(response, dict) and isinstance(response.get("total"), int):
            payload["total"] = response["total"]
        return payload

    @mcp.tool(
        annotations={
            "title": "Manage Image Gallery",
        }
    )
    def bookstack_manage_images(
        operation: Annotated[
            Literal["create", "read", "update", "delete", "list"],
            Field(description="Image workflow operation to execute."),
        ],
        name: Annotated[
            Optional[str],
            Field(default=None, min_length=1, description="Display name for the stored image (required for create)."),
        ] = None,
        image: Annotated[
            Optional[str],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_STRING_NO_MIN_SCHEMA), "description": "Image payload as a base64 string, data URL, or HTTP/HTTPS URL for create/update operations."}),
        ] = None,
        image_type: Annotated[
            Optional[str],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_STRING_SCHEMA), "description": "Image storage type accepted by BookStack (defaults to 'gallery')."}),
        ] = "gallery",
        uploaded_to: Annotated[
            Optional[int],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_INT_SCHEMA), "description": "Entity (page) ID to attach the image to. Provide a valid page ID for uploads."}),
        ] = None,
        id: Annotated[
            Optional[int],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_INT_SCHEMA), "description": "Image ID used by read/update/delete operations."}),
        ] = None,
        new_name: Annotated[
            Optional[str],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_STRING_SCHEMA), "description": "Replacement image name for update operations."}),
        ] = None,
        new_image: Annotated[
            Optional[str],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_STRING_NO_MIN_SCHEMA), "description": "Replacement image payload as a base64 string, data URL, or HTTP/HTTPS URL."}),
        ] = None,
        offset: Annotated[
            Optional[int],
            WithJsonSchema({"oneOf": [{"type": "integer", "minimum": 0}, {"type": "null"}], "description": "Number of records to skip when listing images."}),
        ] = None,
        count: Annotated[
            Optional[int],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_INT_SCHEMA), "description": "Number of records to return when listing images."}),
        ] = None,
        sort: Annotated[
            Optional[str],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_STRING_NO_MIN_SCHEMA), "description": "Sort expression understood by BookStack (e.g. '-created_at')."}),
        ] = None,
        filters: Annotated[
            Optional[list[dict]],
            Field(
                default=None,
                description="Collection of filters forwarded to BookStack as filter[<key>] parameters.",
                json_schema_extra={
                    "items": {
                        "type": "object",
                        "required": ["key", "value"],
                        "properties": {
                            "key": {"type": "string"},
                            "value": {"type": "string"}
                        },
                        "additionalProperties": False
                    }
                },
            ),
        ] = None,
        request_heartbeat: Annotated[
            Optional[bool],
            Field(default=None, description="Ignored parameter (for MCP client compatibility)"),
        ] = None,
    ) -> Dict[str, Any]:
        """Unified CRUD interface for BookStack image gallery."""

        if operation in {"read", "delete", "update"}:
            _ensure(id is not None, "'id' is required for read/update/delete operations")
        target_page_id = None if uploaded_to is None else _validate_positive_int(uploaded_to, "'uploaded_to'")

        if operation == "create":
            _ensure(bool(name), "'name' is required when creating an image")
            _ensure(bool(image), "Provide an image payload for create operations")
            _ensure(
                target_page_id is not None,
                "'uploaded_to' is required when creating an image",
                hint="Provide the page ID the image should be attached to.",
                context={"operation": operation},
            )

            prepared = _prepare_image_payload(image or "", name or _FALLBACK_FILE_NAME)
            files = {"image": (prepared.filename, prepared.content, prepared.mime_type)}
            payload: Dict[str, Any] = {"name": name}
            if image_type:
                payload["type"] = image_type
            payload["uploaded_to"] = target_page_id
            response = _bookstack_request_form(
                "POST",
                "/api/image-gallery",
                data=payload,
                files=files,
            )
            _invalidate_list_cache()
            return {"operation": operation, "success": True, "data": response}

        if operation == "read":
            response = _bookstack_request("GET", f"/api/image-gallery/{id}")
            return {"operation": operation, "success": True, "data": response}

        if operation == "update":
            _ensure(bool(new_name) or bool(new_image), "Provide new_name, new_image, or both for update operations")

            data_payload: Dict[str, Any] = {}
            files_payload: Dict[str, Tuple[str, bytes, str]] = {}
            if new_name:
                data_payload["name"] = new_name
            if new_image:
                prepared = _prepare_image_payload(new_image, new_name or f"image-{id}")
                files_payload["image"] = (prepared.filename, prepared.content, prepared.mime_type)
            response = _bookstack_request_form(
                "PUT",
                f"/api/image-gallery/{id}",
                data=data_payload or None,
                files=files_payload or None,
            )
            _invalidate_list_cache()
            return {"operation": operation, "success": True, "data": response}

        if operation == "delete":
            response = _bookstack_request("DELETE", f"/api/image-gallery/{id}")
            _invalidate_list_cache()
            return {"operation": operation, "success": True, "data": response}

        # operation == "list"
        resolved_offset = offset or 0
        resolved_count = count or 20
        query: Dict[str, Any] = {"offset": resolved_offset, "count": resolved_count}
        if sort:
            query["sort"] = sort
        normalised_filters = _normalise_filters(filters)
        if normalised_filters:
            for key, value in normalised_filters:
                query[f"filter[{key}]"] = value

        cache_key = _build_list_cache_key(query)
        cached = _get_cached_list(cache_key)
        if cached:
            metadata = dict(cached.metadata or {})
            metadata["cached"] = True
            return {
                "operation": operation,
                "success": True,
                "data": cached.data,
                "metadata": metadata,
            }

        response = _bookstack_request("GET", "/api/image-gallery", params=query)
        data, metadata = _normalize_image_list_response(response, offset=resolved_offset, count=resolved_count)
        _set_cached_list(cache_key, data, metadata)
        result: Dict[str, Any] = {
            "operation": operation,
            "success": True,
            "data": data,
        }
        if metadata:
            result["metadata"] = metadata
        return result

    @mcp.tool(
        annotations={
            "title": "Search Image Gallery",
            "readOnlyHint": True,
        }
    )
    def bookstack_search_images(
        query: Annotated[
            Optional[str],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_STRING_NO_MIN_SCHEMA), "description": "Text search across image names and descriptions."}),
        ] = None,
        extension: Annotated[
            Optional[str],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_STRING_NO_MIN_SCHEMA), "description": "File extension filter (e.g. .jpg, .png)."}),
        ] = None,
        size_min: Annotated[
            Optional[int],
            WithJsonSchema({"oneOf": [{"type": "integer", "minimum": 0}, {"type": "null"}], "description": "Minimum size in bytes."}),
        ] = None,
        size_max: Annotated[
            Optional[int],
            WithJsonSchema({"oneOf": [{"type": "integer", "minimum": 0}, {"type": "null"}], "description": "Maximum size in bytes."}),
        ] = None,
        created_after: Annotated[
            Optional[str],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_STRING_NO_MIN_SCHEMA), "description": "Only return images created after this timestamp."}),
        ] = None,
        created_before: Annotated[
            Optional[str],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_STRING_NO_MIN_SCHEMA), "description": "Only return images created before this timestamp."}),
        ] = None,
        used_in: Annotated[
            Optional[Literal["books", "pages", "chapters"]],
            Field(default=None, description="Filter by entity usage."),
        ] = None,
        count: Annotated[
            Optional[int],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_INT_SCHEMA), "description": "Results per page (default 20)."}),
        ] = None,
        offset: Annotated[
            Optional[int],
            WithJsonSchema({"oneOf": [{"type": "integer", "minimum": 0}, {"type": "null"}], "description": "Pagination offset (default 0)."}),
        ] = None,
        sort: Annotated[
            Optional[str],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_STRING_NO_MIN_SCHEMA), "description": "Sort expression supported by BookStack (e.g. '-created_at')."}),
        ] = None,
        request_heartbeat: Annotated[
            Optional[bool],
            Field(default=None, description="Ignored parameter (for MCP client compatibility)"),
        ] = None,
    ) -> Dict[str, Any]:
        """Advanced discovery tool for BookStack image gallery."""

        if size_min is not None and size_max is not None and size_min > size_max:
            raise _tool_error(
                "size_min cannot be greater than size_max",
                hint="Swap the values or adjust them so size_min <= size_max.",
                context={"size_min": size_min, "size_max": size_max},
            )

        after_dt = _ensure_iso8601(created_after, "'created_after'") if created_after else None
        before_dt = _ensure_iso8601(created_before, "'created_before'") if created_before else None
        if after_dt and before_dt and after_dt > before_dt:
            raise _tool_error(
                "created_after must be earlier than created_before",
                hint="Ensure the 'created_after' timestamp is before 'created_before'.",
                context={"created_after": created_after, "created_before": created_before},
            )

        resolved_count = count or 20
        resolved_offset = offset or 0

        params: Dict[str, Any] = {"offset": resolved_offset, "count": resolved_count}
        if query:
            params["query"] = query
        if extension:
            params["extension"] = extension if extension.startswith(".") else f".{extension}"
        if size_min is not None:
            params["size_min"] = size_min
        if size_max is not None:
            params["size_max"] = size_max
        if created_after:
            params["created_after"] = created_after
        if created_before:
            params["created_before"] = created_before
        if used_in:
            params["used_in"] = used_in
        if sort:
            params["sort"] = sort

        response = _bookstack_request("GET", "/api/image-gallery", params=params)
        data, metadata = _normalize_image_list_response(response, offset=resolved_offset, count=resolved_count)

        payload: Dict[str, Any] = {
            "operation": "search",
            "success": True,
            "data": data,
            "metadata": metadata,
        }
        if query:
            payload["query"] = query
        if extension:
            payload["extension"] = params["extension"]
        if size_min is not None:
            payload["size_min"] = size_min
        if size_max is not None:
            payload["size_max"] = size_max
        if created_after:
            payload["created_after"] = created_after
        if created_before:
            payload["created_before"] = created_before
        if used_in:
            payload["used_in"] = used_in
        if sort:
            payload["sort"] = sort
        return payload

    @mcp.tool(
        annotations={
            "title": "Batch Content Operations",
        }
    )
    def bookstack_batch_operations(
        operation: Annotated[
            BatchOperationType,
            Field(description="Bulk operation to perform (bulk_create, bulk_update, bulk_delete)."),
        ],
        entity_type: Annotated[
            EntityType,
            Field(description="Entity to operate on (book, bookshelf, chapter, page)."),
        ],
        items: BatchItemsListInput,
        continue_on_error: Annotated[
            bool,
            Field(default=True, description="Continue processing when an item fails."),
        ] = True,
        batch_size: Annotated[
            Optional[int],
            WithJsonSchema({**copy.deepcopy(_OPTIONAL_INT_SCHEMA), "description": "Number of items per batch (processed sequentially)."}),
        ] = None,
        dry_run: Annotated[
            bool,
            Field(default=False, description="When true, validate input without performing API calls."),
        ] = False,
    ) -> Dict[str, Any]:
        """Execute bulk operations across BookStack content entities."""

        if batch_size is not None:
            batch_size = _validate_positive_int(batch_size, "'batch_size'")

        total = len(items)
        successes: list[Dict[str, Any]] = []
        errors: list[Dict[str, Any]] = []

        def build_prepared(item: Dict[str, Any]) -> PreparedOperation:
            item_id = item.get("id")
            data = _coerce_json_object(item.get("data"), label="batch item 'data'")
            kwargs = _extract_known_fields(data)
            kwargs["updates"] = data
            if operation == "bulk_create":
                return _build_content_operation(
                    "create",
                    entity_type,
                    entity_id=None,
                    name=kwargs.get("name"),
                    description=kwargs.get("description"),
                    content=kwargs.get("content"),
                    markdown=kwargs.get("markdown"),
                    html=kwargs.get("html"),
                    cover_image=kwargs.get("cover_image"),
                    updates=kwargs.get("updates"),
                    book_id=kwargs.get("book_id"),
                    chapter_id=kwargs.get("chapter_id"),
                    books=kwargs.get("books"),
                    tags=kwargs.get("tags"),
                    image_id=kwargs.get("image_id"),
                    priority=kwargs.get("priority"),
                )
            if operation == "bulk_update":
                _ensure(item_id is not None, "Each update item requires an 'id'")
                return _build_content_operation(
                    "update",
                    entity_type,
                    entity_id=_validate_positive_int(item_id, "'id'"),
                    name=kwargs.get("name"),
                    description=kwargs.get("description"),
                    content=kwargs.get("content"),
                    markdown=kwargs.get("markdown"),
                    html=kwargs.get("html"),
                    cover_image=kwargs.get("cover_image"),
                    updates=kwargs.get("updates"),
                    book_id=kwargs.get("book_id"),
                    chapter_id=kwargs.get("chapter_id"),
                    books=kwargs.get("books"),
                    tags=kwargs.get("tags"),
                    image_id=kwargs.get("image_id"),
                    priority=kwargs.get("priority"),
                )
            # bulk_delete
            _ensure(item_id is not None, "Each delete item requires an 'id'")
            return _build_content_operation(
                "delete",
                entity_type,
                entity_id=_validate_positive_int(item_id, "'id'"),
                name=None,
                description=None,
                content=None,
                markdown=None,
                html=None,
                updates=None,
                book_id=None,
                chapter_id=None,
                books=None,
                tags=None,
                image_id=None,
                priority=None,
            )

        index = 0
        while index < total:
            batch_slice = items[index : index + (batch_size or total)]
            for offset_within_batch, item in enumerate(batch_slice):
                item_index = index + offset_within_batch
                try:
                    prepared = build_prepared(item)
                    if dry_run:
                        successes.append(
                            {
                                "index": item_index,
                                "method": prepared.method,
                                "path": prepared.path,
                                "params": prepared.params,
                                "payload": prepared.json,
                            }
                        )
                        continue

                    response = _bookstack_request(
                        prepared.method,
                        prepared.path,
                        params=prepared.params,
                        json=prepared.json,
                    )
                    successes.append(
                        {
                            "index": item_index,
                            "result": response,
                        }
                    )
                except ToolError as exc:
                    errors.append({"index": item_index, "error": str(exc)})
                    if not continue_on_error:
                        break
                except Exception as exc:  # pragma: no cover - defensive guard
                    errors.append({"index": item_index, "error": str(exc)})
                    if not continue_on_error:
                        break
            else:
                index += len(batch_slice)
                continue
            break  # loop terminated early due to error and continue_on_error=False

        return {
            "operation": operation,
            "entity_type": entity_type,
            "dry_run": dry_run,
            "total": total,
            "success_count": len(successes),
            "failure_count": len(errors),
            "results": successes,
            "errors": errors,
        }
