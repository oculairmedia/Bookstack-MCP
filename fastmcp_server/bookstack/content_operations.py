"""Content operation builders, validators, and helper functions for BookStack tools."""

from __future__ import annotations
import json
import re
from typing import Any, Callable, Dict, Optional, Sequence, Tuple

from .api_client import _tool_error, _ensure, logger, ToolError
from .schemas import (
    EntityType,
    OperationType,
    PreparedOperation,
    TagDict,
    FilterEntry,
    _CONTENT_KNOWN_FIELDS,
    _ENTITY_BASE_PATHS,
    _HTML_TAG_RE,
)
from .validators import BookStackValidator, InputValidator, ValidationError


def _validated_name(value: Optional[str], entity_type: EntityType) -> Optional[str]:
    """Validate and sanitize entity names."""

    if value is None:
        return None
    try:
        return BookStackValidator.validate_entity_name(value, entity_type)
    except ValidationError as exc:
        raise _tool_error(
            str(exc),
            hint="Ensure the name is 1-500 characters without embedded scripts.",
            context={"entity_type": entity_type, "value": value},
        ) from exc


def _validated_description(value: Optional[str], entity_type: EntityType) -> Optional[str]:
    """Validate descriptions with generous length limits."""

    if value is None:
        return None
    try:
        return InputValidator.validate_string(
            value,
            f"{entity_type}_description",
            min_length=1 if entity_type == "book" else None,
            max_length=20_000,
            allow_empty=entity_type != "book",
        )
    except ValidationError as exc:
        raise _tool_error(
            str(exc),
            hint="Descriptions must be text up to 20k characters without scripts.",
            context={"entity_type": entity_type},
        ) from exc


def _validated_markdown(value: Optional[str]) -> Optional[str]:
    """Validate markdown content."""

    if value is None:
        return None
    try:
        return InputValidator.validate_markdown(value, "markdown")
    except ValidationError as exc:
        raise _tool_error(str(exc), hint="Review markdown content for unsafe HTML.") from exc


def _validated_html(value: Optional[str]) -> Optional[str]:
    """Sanitize HTML blocks before submission."""

    if value is None:
        return None
    sanitized = InputValidator.sanitize_html(value, "html")
    try:
        return InputValidator.validate_string(
            sanitized,
            "html",
            max_length=500_000,
            allow_empty=True,
            check_sql_injection=False,
            check_path_traversal=False,
        )
    except ValidationError as exc:
        raise _tool_error(str(exc), hint="Ensure HTML content is well-formed and safe.") from exc


def _normalise_str(value: Optional[str]) -> Optional[str]:
    """Strip surrounding whitespace and return None when a string is empty."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _normalise_optional_parent_id(value: Optional[Any]) -> Optional[Any]:
    """Treat zero/blank id values as absent when targeting parent locations."""

    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped or stripped == "0":
            return None
        try:
            numeric = int(stripped, 10)
        except ValueError:
            return stripped
        return numeric
    if isinstance(value, bool):
        return 1 if value else None
    if isinstance(value, (int, float)):
        numeric = int(value)
        return None if numeric == 0 else numeric
    return value


def _coerce_json_object(
    value: Optional[Any],
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
    normalised: list[Dict[str, str]] = []
    for tag in tags:
        if isinstance(tag, dict):
            normalised.append({"name": str(tag.get("name", "")), "value": str(tag.get("value", ""))})
        else:
            name = getattr(tag, "name", "")
            value = getattr(tag, "value", "")
            normalised.append({"name": str(name), "value": str(value)})

    try:
        validated = BookStackValidator.validate_tags(normalised)
    except ValidationError as exc:
        raise _tool_error(
            str(exc),
            hint="Verify that each tag includes 'name' (1-100 chars) and optional 'value'.",
            context={"tags": normalised},
        ) from exc

    return validated


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


def _extract_known_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    extracted: Dict[str, Any] = {}
    for field in _CONTENT_KNOWN_FIELDS:
        if field in data:
            extracted[field] = data[field]
    return extracted


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
        payload["name"] = _validated_name(name_value, entity_type)

        if entity_type == "book":
            description_value = _normalise_str(payload.get("description")) or _normalise_str(description)
            _ensure(description_value is not None, "'description' is required when creating a book")
            payload["description"] = _validated_description(description_value, entity_type)
            image_value = payload.get("image_id") if payload.get("image_id") is not None else image_id
            if image_value is not None:
                payload["image_id"] = _validate_positive_int(image_value, "'image_id'")

        elif entity_type == "bookshelf":
            description_value = _normalise_str(description) or _normalise_str(payload.get("description"))
            if description_value is not None:
                payload["description"] = _validated_description(description_value, entity_type)
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
                payload["description"] = _validated_description(description_value, entity_type)
            chapter_priority = priority if priority is not None else payload.get("priority")
            priority_value = _optional_non_negative_int(chapter_priority, "'priority'")
            if priority_value is not None:
                payload["priority"] = priority_value
            else:
                payload.pop("priority", None)

        elif entity_type == "page":
            raw_page_book_id = payload.get("book_id") if payload.get("book_id") is not None else book_id
            raw_page_chapter_id = payload.get("chapter_id") if payload.get("chapter_id") is not None else chapter_id
            page_book_id = _normalise_optional_parent_id(raw_page_book_id)
            page_chapter_id = _normalise_optional_parent_id(raw_page_chapter_id)
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
                markdown_value = _validated_markdown(_normalise_str(markdown_value))
            if isinstance(html_value, str):
                html_value = _validated_html(_normalise_str(html_value))

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
            payload["name"] = _validated_name(_normalise_str(name) or name, entity_type)
        if description is not None:
            payload["description"] = _validated_description(_normalise_str(description) or description, entity_type)

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
            raw_page_book = book_id if book_id is not None else payload.get("book_id")
            raw_page_chapter = chapter_id if chapter_id is not None else payload.get("chapter_id")
            page_book = _normalise_optional_parent_id(raw_page_book)
            page_chapter = _normalise_optional_parent_id(raw_page_chapter)
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
                markdown_value = _validated_markdown(_normalise_str(markdown_value))
            if isinstance(html_value, str):
                html_value = _validated_html(_normalise_str(html_value))

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


def _coerce_int(value: Any) -> int:
    try:
        if value is None:
            return 0
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def _coerce_float(value: Any) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _extract_candidate_chunks(result: Dict[str, Any]) -> list[Dict[str, Any]]:
    chunks: list[Dict[str, Any]] = []
    for key in ("results", "evidence", "data", "documents"):
        value = result.get(key)
        if isinstance(value, list):
            chunks.extend(item for item in value if isinstance(item, dict))

    nested = result.get("result")
    if isinstance(nested, dict):
        for key in ("results", "evidence", "data", "documents"):
            value = nested.get(key)
            if isinstance(value, list):
                chunks.extend(item for item in value if isinstance(item, dict))

    return chunks


def _attach_entity_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    chunks = _extract_candidate_chunks(result)
    if not chunks:
        return result

    by_page: Dict[int, Dict[str, Any]] = {}
    for chunk in chunks:
        source = chunk.get("source")
        source_data = source if isinstance(source, dict) else {}

        page_id = _coerce_int(chunk.get("bookstack_page_id") or source_data.get("bookstack_page_id"))
        if page_id <= 0:
            continue

        score = _coerce_float(chunk.get("score") or source_data.get("score"))
        book_id = _coerce_int(chunk.get("book_id") or source_data.get("book_id"))
        chapter_id = _coerce_int(chunk.get("chapter_id") or source_data.get("chapter_id"))
        name = _as_string(chunk.get("title") or chunk.get("name") or source_data.get("name")) or ""
        book_name = _as_string(chunk.get("book_name") or source_data.get("book_name")) or ""

        current = by_page.get(page_id)
        if current is None:
            by_page[page_id] = {
                "page_id": page_id,
                "book_id": book_id,
                "chapter_id": chapter_id,
                "name": name,
                "book_name": book_name,
                "best_score": score,
                "chunks": 1,
            }
            continue

        current["chunks"] = int(current["chunks"]) + 1
        if score > _coerce_float(current.get("best_score")):
            current["best_score"] = score
        if not current.get("book_id") and book_id > 0:
            current["book_id"] = book_id
        if not current.get("chapter_id") and chapter_id > 0:
            current["chapter_id"] = chapter_id
        if not current.get("name") and name:
            current["name"] = name
        if not current.get("book_name") and book_name:
            current["book_name"] = book_name

    if not by_page:
        return result

    entities = sorted(
        by_page.values(),
        key=lambda item: (_coerce_float(item.get("best_score")), _coerce_int(item.get("chunks"))),
        reverse=True,
    )
    result["entities"] = entities
    return result
