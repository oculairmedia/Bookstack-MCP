"""BookStack tool definitions for the FastMCP server."""

from __future__ import annotations

# Module-level imports needed for monkeypatching compatibility
import copy
import json
import os
import re
import requests  # CRITICAL: tests monkeypatch fastmcp_server.bookstack.tools.requests.post
import socket    # CRITICAL: tests monkeypatch tools.socket.getaddrinfo
import time
from typing import Annotated, Any, Dict, Literal, Optional, Sequence, Tuple

from fastmcp import FastMCP
from pydantic import Field
from pydantic.json_schema import WithJsonSchema

# Import everything from new modules for backward compatibility
from .schemas import (
    EntityType, ListEntityType, OperationType, BatchOperationType,
    TagDict, FilterEntry,
    TagListInput, BooksAssociationList, PayloadOverrides,
    BatchItemInput, BatchItemsListInput,
    PreparedOperation, PreparedImage, CacheEntry,
    _TAG_ITEM_SCHEMA, _TAG_SCHEMA, _TAG_LIST_SCHEMA,
    _BOOK_ASSOCIATIONS_SCHEMA,
    _RAW_OBJECT_PAYLOAD_SCHEMA, _JSON_STRING_PAYLOAD_SCHEMA,
    _OPTIONAL_INT_SCHEMA, _OPTIONAL_STRING_SCHEMA, _OPTIONAL_STRING_NO_MIN_SCHEMA,
    _BOOK_PAYLOAD_SCHEMA, _BOOKSHELF_PAYLOAD_SCHEMA, _CHAPTER_PAYLOAD_SCHEMA, _PAGE_PAYLOAD_SCHEMA,
    _PAYLOAD_ONE_OF_WITH_STRING_AND_NULL,
    BATCH_ITEM_SCHEMA, BATCH_ITEMS_LIST_SCHEMA,
    _ENTITY_BASE_PATHS, _LIST_BASE_PATHS,
    _DATA_URL_RE, _HTML_TAG_RE,
    _FALLBACK_FILE_NAME, _DEFAULT_MIME_TYPE,
    _MAX_IMAGE_SIZE_BYTES, _REQUEST_TIMEOUT_SECONDS, _MAX_URL_REDIRECTS,
    _ALLOWED_URL_SCHEMES, _ALLOWED_MIME_TYPES,
    _CONTENT_KNOWN_FIELDS,
)

from .api_client import (
    JSONFormatter, logger, ToolError,
    _require_env,
    _bookstack_base_url as _api_bookstack_base_url,
    _bookstack_headers as _api_bookstack_headers,
    _tool_error, _ensure,
    _select_cache_bucket, _cache_ttl_for, _build_cache_key,
    _cache_tags_for_request, _invalidate_entity_cache,
    _handle_bookstack_http_error,
    _bookstack_request as _api_bookstack_request,
    _bookstack_request_form as _api_bookstack_request_form,
)

from .image_handling import (
    _is_url, _extract_filename_from_url, _decode_base64_string,
    _classify_disallowed_ip, _resolve_url_targets, _validate_remote_image_target,
    _fetch_image_from_url as _img_fetch_image_from_url,
    _prepare_image_payload, _prepare_form_data,
    _prepare_cover_image_from_gallery as _img_prepare_cover_image_from_gallery,
    _normalize_image_list_response,
    _build_list_cache_key,
    _get_cached_list, _set_cached_list, _invalidate_list_cache,
    _ensure_iso8601,
)

from .content_operations import (
    _validated_name, _validated_description, _validated_markdown, _validated_html,
    _normalise_str, _normalise_optional_parent_id,
    _coerce_json_object,
    _validate_positive_int, _optional_positive_int, _optional_non_negative_int,
    _normalise_books, _format_tags,
    _compact_payload, _extract_known_fields,
    _build_content_operation,
    _filter_collection, _normalise_filters,
    _as_string, _trim_summary, _extract_summary,
    _coerce_int, _coerce_float,
    _extract_candidate_chunks, _attach_entity_summary,
)

from .cache import bookstack_cache
from .metrics import get_metrics_collector, track_tool
from .validators import BookStackValidator, InputValidator, ValidationError

# Wrappers resolve dependencies through THIS module's globals so that
# monkeypatch.setattr(tools, "_bookstack_base_url", …) is honoured.
# Do NOT replace with plain re-exports — tests will break.

_bookstack_base_url = _api_bookstack_base_url
_bookstack_headers = _api_bookstack_headers

import sys as _sys


def _bookstack_request(method, path, *, params=None, json=None):
    _mod = _sys.modules[__name__]
    return _api_bookstack_request(
        method, path, params=params, json=json,
        _base_url_fn=_mod._bookstack_base_url,
        _headers_fn=_mod._bookstack_headers,
    )


def _bookstack_request_form(method, path, *, data=None, files=None):
    _mod = _sys.modules[__name__]
    return _api_bookstack_request_form(
        method, path, data=data, files=files,
        _base_url_fn=_mod._bookstack_base_url,
        _headers_fn=_mod._bookstack_headers,
    )


_fetch_image_from_url = _img_fetch_image_from_url


def _prepare_cover_image_from_gallery(image_id, *, fallback_name=None):
    _mod = _sys.modules[__name__]
    return _img_prepare_cover_image_from_gallery(
        image_id, fallback_name=fallback_name,
        _request_fn=_mod._bookstack_request,
        _fetch_fn=_mod._fetch_image_from_url,
    )


def register_bookstack_tools(mcp: FastMCP, exclude: Optional[set[str]] = None) -> None:
    """Register BookStack tools on the provided FastMCP instance.
    
    Args:
        mcp: The FastMCP instance to register tools on.
        exclude: Optional set of tool names to exclude from registration.
    """
    exclude = exclude or set()

    if "bookstack_manage_content" not in exclude:
        @track_tool("bookstack_manage_content")
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

            collector = get_metrics_collector()
            logger.info(
                "bookstack.manage_content",
                extra={
                    "context": {
                        "operation": operation,
                        "entity_type": entity_type,
                        "entity_id": id,
                    }
                },
            )

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
                if operation in {"create", "update", "delete"}:
                    result_id = result.get("id")
                    _invalidate_entity_cache(entity_type, result_id if isinstance(result_id, int) else None)
                    collector.record_entity_operation(entity_type, operation)
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
            if operation in {"create", "update", "delete"}:
                result_id = result.get("id")
                _invalidate_entity_cache(entity_type, result_id if isinstance(result_id, int) else None)
                collector.record_entity_operation(entity_type, operation)
            return result

    if "bookstack_list_content" not in exclude:
        @track_tool("bookstack_list_content")
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
        ) -> Dict[str, Any]:
            """Return a paginated listing of BookStack entities."""

            logger.info(
                "bookstack.list_content",
                extra={
                    "context": {
                        "entity_type": entity_type,
                        "offset": offset,
                        "count": count,
                        "filters": filters,
                    }
                },
            )

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

    if "bookstack_search" not in exclude:
        @track_tool("bookstack_search")
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
        ) -> Dict[str, Any]:
            """Search across BookStack content."""

            logger.info(
                "bookstack.search",
                extra={
                    "context": {
                        "query": query,
                        "page": page,
                        "count": count,
                    }
                },
            )

            try:
                query = InputValidator.validate_string(
                    query,
                    "query",
                    min_length=1,
                    max_length=500,
                )
            except ValidationError as exc:
                raise _tool_error(str(exc), context={"field": "query"}) from exc

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

    if "bookstack_manage_images" not in exclude:
        @track_tool("bookstack_manage_images")
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
        ) -> Dict[str, Any]:
            """Unified CRUD interface for BookStack image gallery."""

            collector = get_metrics_collector()
            logger.info(
                "bookstack.manage_images",
                extra={
                    "context": {
                        "operation": operation,
                        "image_id": id,
                        "uploaded_to": uploaded_to,
                    }
                },
            )

            if operation in {"read", "delete", "update"}:
                _ensure(id is not None, "'id' is required for read/update/delete operations")
            target_page_id = None if uploaded_to is None else _validate_positive_int(uploaded_to, "'uploaded_to'")

            if operation == "create":
                if name is not None:
                    try:
                        name = InputValidator.validate_string(
                            name,
                            "image_name",
                            min_length=1,
                            max_length=255,
                        )
                    except ValidationError as exc:
                        raise _tool_error(str(exc), context={"field": "name"}) from exc
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
                bookstack_cache.images.invalidate()
                collector.record_entity_operation("image", operation)
                return {"operation": operation, "success": True, "data": response}

            if operation == "read":
                response = _bookstack_request("GET", f"/api/image-gallery/{id}")
                return {"operation": operation, "success": True, "data": response}

            if operation == "update":
                _ensure(bool(new_name) or bool(new_image), "Provide new_name, new_image, or both for update operations")

                data_payload: Dict[str, Any] = {}
                files_payload: Dict[str, Tuple[str, bytes, str]] = {}
                if new_name:
                    try:
                        new_name = InputValidator.validate_string(
                            new_name,
                            "new_image_name",
                            min_length=1,
                            max_length=255,
                        )
                    except ValidationError as exc:
                        raise _tool_error(str(exc), context={"field": "new_name"}) from exc
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
                bookstack_cache.images.invalidate()
                collector.record_entity_operation("image", operation)
                return {"operation": operation, "success": True, "data": response}

            if operation == "delete":
                response = _bookstack_request("DELETE", f"/api/image-gallery/{id}")
                bookstack_cache.images.invalidate()
                collector.record_entity_operation("image", operation)
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
            cached_entry = _get_cached_list(cache_key)
            if cached_entry is not None:
                cached_metadata = dict(cached_entry.metadata or {})
                cached_metadata["cached"] = True
                return {
                    "operation": operation,
                    "success": True,
                    "data": cached_entry.data,
                    "metadata": cached_metadata,
                }

            response = _bookstack_request("GET", "/api/image-gallery", params=query)
            data, metadata = _normalize_image_list_response(response, offset=resolved_offset, count=resolved_count)
            _set_cached_list(cache_key, data, metadata)
            result_metadata = dict(metadata) if metadata else {}
            result: Dict[str, Any] = {
                "operation": operation,
                "success": True,
                "data": data,
                "metadata": result_metadata,
            }
            return result

    if "bookstack_search_images" not in exclude:
        @track_tool("bookstack_search_images")
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
        ) -> Dict[str, Any]:
            """Advanced discovery tool for BookStack image gallery."""

            logger.info(
                "bookstack.search_images",
                extra={
                    "context": {
                        "query": query,
                        "extension": extension,
                        "used_in": used_in,
                    }
                },
            )

            if query:
                try:
                    query = InputValidator.validate_string(
                        query,
                        "image_query",
                        min_length=1,
                        max_length=255,
                        allow_empty=False,
                    )
                except ValidationError as exc:
                    raise _tool_error(str(exc), context={"field": "query"}) from exc

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

    if "bookstack_batch_operations" not in exclude:
        @track_tool("bookstack_batch_operations")
        @mcp.tool(
            annotations={
                "title": "BookStack Batch Operations",
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

            collector = get_metrics_collector()
            logger.info(
                "bookstack.batch_operations",
                extra={
                    "context": {
                        "operation": operation,
                        "entity_type": entity_type,
                        "item_count": total,
                        "dry_run": dry_run,
                    }
                },
            )

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
                        logical_op = (
                            "create" if operation == "bulk_create"
                            else "update" if operation == "bulk_update"
                            else "delete"
                        )
                        cache_target = None
                        if logical_op == "create" and isinstance(response, dict) and isinstance(response.get("id"), int):
                            cache_target = response["id"]
                        elif logical_op in {"update", "delete"} and isinstance(item.get("id"), int):
                            cache_target = item["id"]
                        _invalidate_entity_cache(entity_type, cache_target)
                        collector.record_entity_operation(entity_type, logical_op)
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

    if "bookstack_get_metrics" not in exclude:
        @track_tool("bookstack_get_metrics")
        @mcp.tool(
            annotations={
                "title": "Get Server Metrics",
                "readOnlyHint": True,
            }
        )
        def bookstack_get_metrics() -> Dict[str, Any]:
            """Expose runtime metrics for the BookStack MCP server."""

            collector = get_metrics_collector()
            logger.info("bookstack.metrics_report")

            return {
                "summary": collector.get_summary(),
                "tools": collector.get_tool_metrics(),
                "entities": collector.get_entity_metrics(),
                "cache": bookstack_cache.get_all_stats(),
                "recent_errors": collector.get_recent_errors(limit=10),
                "slow_requests": collector.get_slow_requests(limit=10),
                "top_endpoints": collector.get_top_endpoints(limit=10),
            }

    if "bookstack_health_check" not in exclude:
        @track_tool("bookstack_health_check")
        @mcp.tool(
            annotations={
                "title": "BookStack Health Check",
                "readOnlyHint": True,
            }
        )
        def bookstack_health_check() -> Dict[str, Any]:
            """Return health information for the MCP server and BookStack API."""

            collector = get_metrics_collector()
            start_time = time.time()
            api_healthy = True
            api_error: Optional[str] = None

            # Ensure the next request bypasses cache so we measure real latency
            bookstack_cache.books.invalidate()
            try:
                _bookstack_request("GET", "/api/books", params={"count": 1})
            except ToolError as exc:
                api_healthy = False
                api_error = str(exc)
            except Exception as exc:  # pragma: no cover - defensive guard
                api_healthy = False
                api_error = str(exc)

            latency_ms = (time.time() - start_time) * 1000 if api_healthy else None
            summary = collector.get_summary()
            cache_stats = bookstack_cache.get_all_stats()

            payload: Dict[str, Any] = {
                "status": "healthy" if api_healthy else "degraded",
                "bookstack_api": {
                    "healthy": api_healthy,
                    "latency_ms": f"{latency_ms:.2f}" if latency_ms is not None else None,
                    "error": api_error,
                },
                "server": {
                    "uptime": summary.get("uptime_formatted"),
                    "total_requests": summary.get("total_requests"),
                    "error_rate": summary.get("error_rate"),
                },
                "cache": cache_stats,
            }
            return payload

    if "bookstack_semantic_search" not in exclude:
        @track_tool("bookstack_semantic_search")
        @mcp.tool(
            annotations={
                "title": "Semantic Search BookStack",
                "readOnlyHint": True,
            }
        )
        def bookstack_semantic_search(
            query: Annotated[
                str,
                Field(min_length=1, description="Search query for semantic/hybrid search across BookStack documents."),
            ],
            top_k: Annotated[
                Optional[int],
                WithJsonSchema({**copy.deepcopy(_OPTIONAL_INT_SCHEMA), "description": "Maximum number of document chunks to return (default: 5)."}),
            ] = None,
            response_mode: Annotated[
                Optional[str],
                Field(default=None, description="Response mode: 'synthesis' (default), 'raw', or 'both'."),
            ] = None,
            book_filter: Annotated[
                Optional[str],
                Field(default=None, description="Filter results by book name."),
            ] = None,
            score_threshold: Annotated[
                Optional[float],
                Field(default=None, description="Minimum confidence score threshold (0.0-1.0, default: 0.3)."),
            ] = None,
        ) -> Dict[str, Any]:
            """Perform semantic/hybrid search across BookStack wiki content using Hayhooks."""

            logger.info(
                "bookstack.semantic_search",
                extra={
                    "context": {
                        "query": query,
                        "top_k": top_k,
                        "response_mode": response_mode,
                        "book_filter": book_filter,
                        "score_threshold": score_threshold,
                    }
                },
            )

            try:
                query = InputValidator.validate_string(
                    query,
                    "query",
                    min_length=1,
                    max_length=500,
                )
            except ValidationError as exc:
                raise _tool_error(str(exc), context={"field": "query"}) from exc

            # Build request payload for Hayhooks
            payload: Dict[str, Any] = {
                "query": query,
            }

            # Add optional parameters
            if top_k is not None:
                try:
                    payload["top_k"] = _validate_positive_int(top_k, "top_k")
                except ToolError:
                    payload["top_k"] = 5  # fallback to default
            else:
                payload["top_k"] = 5

            if response_mode is not None:
                mode = str(response_mode).strip().lower()
                if mode in ("synthesis", "raw", "both"):
                    payload["response_mode"] = mode
                else:
                    payload["response_mode"] = "synthesis"
            else:
                payload["response_mode"] = "synthesis"

            if score_threshold is not None:
                try:
                    threshold = float(score_threshold)
                    if 0.0 <= threshold <= 1.0:
                        payload["score_threshold"] = threshold
                    else:
                        payload["score_threshold"] = 0.3
                except (TypeError, ValueError):
                    payload["score_threshold"] = 0.3
            else:
                payload["score_threshold"] = 0.3

            # Add book filter if provided (maps to filename_filter in Hayhooks)
            if book_filter is not None:
                book_filter_str = _normalise_str(book_filter)
                if book_filter_str:
                    payload["filename_filter"] = book_filter_str

            # Get Hayhooks endpoint URL from environment
            hayhooks_url = os.environ.get(
                "HAYHOOKS_SEARCH_URL",
                "http://192.168.50.90:1416/search_documents/run"
            ).rstrip("/")

            try:
                response = requests.post(
                    hayhooks_url,
                    json=payload,
                    timeout=60,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
            except requests.exceptions.Timeout as exc:
                raise _tool_error(
                    "Hayhooks semantic search request timed out",
                    hint="The search service may be slow or unreachable. Try again later.",
                    context={"url": hayhooks_url, "query": query},
                ) from exc
            except requests.exceptions.ConnectionError as exc:
                raise _tool_error(
                    "Failed to connect to Hayhooks search service",
                    hint="Check that HAYHOOKS_SEARCH_URL is set correctly and the service is running.",
                    context={"url": hayhooks_url},
                ) from exc
            except requests.exceptions.HTTPError as exc:
                status = exc.response.status_code if exc.response else "unknown"
                preview = None
                if exc.response is not None:
                    try:
                        preview = exc.response.text[:400]
                    except Exception:
                        pass
                raise _tool_error(
                    f"Hayhooks search failed with HTTP {status}",
                    hint="Verify the search query and Hayhooks configuration.",
                    context={
                        "url": hayhooks_url,
                        "status": status,
                        "response_preview": preview,
                    },
                ) from exc
            except requests.exceptions.RequestException as exc:
                raise _tool_error(
                    "Hayhooks search request failed",
                    hint="Check network connectivity and Hayhooks service status.",
                    context={"url": hayhooks_url, "error": str(exc)},
                ) from exc

            # Parse and return the response
            try:
                result = response.json()
            except ValueError as exc:
                raise _tool_error(
                    "Hayhooks returned a non-JSON response",
                    hint="Verify the Hayhooks service is functioning correctly.",
                    context={"url": hayhooks_url, "raw": response.text[:400]},
                ) from exc

            # Ensure we return a dict with success indicator
            if isinstance(result, dict):
                result = _attach_entity_summary(result)
                if "success" not in result:
                    result["success"] = True
                return result
            else:
                return {"success": True, "data": result}

    if "bookstack_dashboard" not in exclude:
        @track_tool("bookstack_dashboard")
        @mcp.tool(
            annotations={
                "title": "BookStack Metrics Dashboard",
                "readOnlyHint": True,
            }
        )
        def bookstack_dashboard() -> str:
            """Produce a human-friendly dashboard summarizing server status."""

            collector = get_metrics_collector()
            summary = collector.get_summary()
            tools = collector.get_tool_metrics()
            cache_stats = bookstack_cache.get_all_stats()

            sorted_tools = sorted(
                tools.items(),
                key=lambda item: item[1].get("call_count", 0),
                reverse=True,
            )[:5]

            lines = [
                "╔══════════════════════════════════════════════════════════════╗",
                "║           BookStack MCP Server - Dashboard                   ║",
                "╚══════════════════════════════════════════════════════════════╝",
                "",
                "📊 Server Status",
                f"  Uptime:              {summary.get('uptime_formatted')}",
                f"  Total Requests:      {summary.get('total_requests')}",
                f"  Requests/sec:        {summary.get('requests_per_second')}",
                f"  Avg Duration:        {summary.get('avg_duration_ms')} ms",
                f"  Error Rate:          {summary.get('error_rate')}",
                "",
                "🔧 Top Tools",
            ]

            if sorted_tools:
                for tool_name, metrics_info in sorted_tools:
                    lines.extend(
                        [
                            f"  {tool_name}",
                            f"    Calls:             {metrics_info.get('call_count')}",
                            f"    Success Rate:      {metrics_info.get('success_rate')}",
                            f"    Avg Duration:      {metrics_info.get('avg_duration_ms')} ms",
                        ]
                    )
            else:
                lines.append("  No tool invocations recorded yet.")

            lines.extend(
                [
                    "",
                    "💾 Cache Performance",
                    f"  Books Hit Rate:      {cache_stats['books'].get('hit_rate')}",
                    f"  Pages Hit Rate:      {cache_stats['pages'].get('hit_rate')}",
                    f"  Images Hit Rate:     {cache_stats['images'].get('hit_rate')}",
                    f"  Search Hit Rate:     {cache_stats['search'].get('hit_rate')}",
                    "",
                    f"⚠️  Recent Errors:      {len(collector.get_recent_errors(limit=5))}",
                    f"🐌 Slow Requests:       {summary.get('slow_requests_count')}",
                ]
            )

            return "\n".join(lines)

    @mcp.resource(
        "resource://bookstack/books/{book_id}",
        title="BookStack Book",
        description="Retrieve a BookStack book with its contents for contextual grounding.",
        mime_type="application/json",
        annotations={"readOnlyHint": True},
    )
    def bookstack_book_resource(book_id: int) -> Dict[str, Any]:
        safe_book_id = BookStackValidator.validate_entity_id(book_id, "book")
        logger.info(
            "bookstack.resource.book",
            extra={"context": {"book_id": safe_book_id}},
        )
        return _bookstack_request("GET", f"/api/books/{safe_book_id}")

    @mcp.resource(
        "resource://bookstack/pages/{page_id}",
        title="BookStack Page",
        description="Retrieve a BookStack page for use as MCP resource content.",
        mime_type="application/json",
        annotations={"readOnlyHint": True},
    )
    def bookstack_page_resource(page_id: int) -> Dict[str, Any]:
        safe_page_id = BookStackValidator.validate_entity_id(page_id, "page")
        logger.info(
            "bookstack.resource.page",
            extra={"context": {"page_id": safe_page_id}},
        )
        return _bookstack_request("GET", f"/api/pages/{safe_page_id}")
