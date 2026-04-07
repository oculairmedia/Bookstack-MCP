"""Schema definitions, type aliases, and constants for BookStack tools."""

from __future__ import annotations

import copy
import os
import re
from dataclasses import dataclass
from typing import Annotated, Any, Dict, Literal, Optional, Sequence, Tuple, Union

from pydantic import Field
from pydantic.json_schema import WithJsonSchema
from typing_extensions import TypedDict

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

# Reusable tag schema for inline items (without title/additionalProperties)
_TAG_SCHEMA: Dict[str, Any] = {
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
    "items": copy.deepcopy(_TAG_SCHEMA),
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
            "items": copy.deepcopy(_TAG_SCHEMA),
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
            "items": copy.deepcopy(_TAG_SCHEMA),
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
            "items": copy.deepcopy(_TAG_SCHEMA),
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
            "items": copy.deepcopy(_TAG_SCHEMA),
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
    """Compatibility wrapper for cached image list responses."""

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

_DATA_URL_RE = re.compile(r"^data:([^;,]+)?(;base64)?,(.*)$", re.IGNORECASE)
_HTML_TAG_RE = re.compile(r"<[^>]+>")

_FALLBACK_FILE_NAME = "upload.bin"
_DEFAULT_MIME_TYPE = "application/octet-stream"

# Image URL fetching configuration
_MAX_IMAGE_SIZE_BYTES = int(os.environ.get("BS_MAX_IMAGE_SIZE", str(50 * 1024 * 1024)))  # 50MB limit
_REQUEST_TIMEOUT_SECONDS = int(os.environ.get("BS_FETCH_TIMEOUT", "30"))
_MAX_URL_REDIRECTS = int(os.environ.get("BS_MAX_REDIRECTS", "3"))
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
