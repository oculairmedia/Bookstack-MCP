"""Simplified BookStack tool schemas to avoid MCP character limits."""

from __future__ import annotations

import copy
from typing import Annotated, Any, Dict, Literal, Optional

from fastmcp import FastMCP
from pydantic import Field
from pydantic.json_schema import WithJsonSchema

# Import the actual implementation functions from the original tools module
from .tools import (
    _build_content_operation,
    _bookstack_request,
    _bookstack_request_form,
    _coerce_json_object,
    _ensure,
    _extract_known_fields,
    _prepare_cover_image_from_gallery,
    _prepare_form_data,
    _prepare_image_payload,
    _validate_positive_int,
    EntityType,
    OperationType,
    BatchOperationType,
    PreparedOperation,
    PreparedImage,
    ToolError,
)


# Simplified schemas - use string type for complex payloads to avoid deep nesting
_SIMPLE_OPTIONAL_INT_SCHEMA: Dict[str, Any] = {
    "oneOf": [
        {"type": "integer", "minimum": 1},
        {"type": "null"}
    ]
}

_SIMPLE_OPTIONAL_STRING_SCHEMA: Dict[str, Any] = {
    "oneOf": [
        {"type": "string", "minLength": 1},
        {"type": "null"}
    ]
}

_SIMPLE_OPTIONAL_STRING_NO_MIN_SCHEMA: Dict[str, Any] = {
    "oneOf": [
        {"type": "string"},
        {"type": "null"}
    ]
}

# Simplified payload schema - just accept a JSON string (simpler for MCP clients)
_SIMPLE_PAYLOAD_SCHEMA: Dict[str, Any] = {
    "oneOf": [
        {
            "type": "string",
            "description": "JSON string with entity fields (e.g. '{\"content\":\"...\",\"book_id\":1}')",
        },
        {"type": "null"},
    ]
}

# Simplified batch item schema - MCP strict mode compliant
_SIMPLE_BATCH_ITEM_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "description": "Batch operation item",
    "additionalProperties": False,  # MCP strict mode requirement
    "properties": {
        "id": {
            "type": "integer",
            "minimum": 1,
            "description": "Entity ID (required for update/delete)",
        },
        "data": {
            "oneOf": [
                {
                    "type": "string",
                    "description": "Entity data as JSON string (e.g. '{\"name\":\"...\",\"content\":\"...\"}')",
                },
                {
                    "type": "null",
                },
            ],
            "description": "Entity data as JSON string",
        },
    },
}

_SIMPLE_BATCH_ITEMS_SCHEMA: Dict[str, Any] = {
    "type": "array",
    "description": "List of batch items",
    "minItems": 1,
    "maxItems": 100,
    "items": copy.deepcopy(_SIMPLE_BATCH_ITEM_SCHEMA),
}


def register_simplified_bookstack_tools(mcp: FastMCP) -> None:
    """Register simplified BookStack tools with reduced schema complexity."""

    @mcp.tool()
    def bookstack_content_crud(
        action: Literal[
            "read_page", "create_page", "update_page", "delete_page",
            "read_book", "create_book", "update_book", "delete_book",
            "read_chapter", "create_chapter", "update_chapter", "delete_chapter",
            "read_shelf", "create_shelf", "update_shelf", "delete_shelf"
        ],
        content_id: Optional[int] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        data: Optional[str] = None,
        request_heartbeat: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """CRUD operations for BookStack content.

        Args:
            action: Operation like 'read_page', 'create_book', 'update_chapter', 'delete_shelf'
            content_id: Entity ID (required for read/update/delete operations)
            name: Entity name/title (for create/update)
            description: Entity description (for create/update)
            data: Additional fields as JSON string (e.g. '{"content":"...","book_id":1}')
            request_heartbeat: Ignored (for MCP client compatibility)
        """
        import logging
        import json as json_module
        logger = logging.getLogger(__name__)
        logger.info(f"bookstack_content_crud CALLED: action={action}, content_id={content_id}")

        # Parse action into operation and entity_type
        parts = action.split("_", 1)
        operation = parts[0]
        entity_map = {"page": "page", "book": "book", "chapter": "chapter", "shelf": "bookshelf"}
        entity_type = entity_map.get(parts[1], parts[1])

        try:
            # Parse data if it's a JSON string
            parsed_data = _coerce_json_object(data, label="data") if data else {}

            # Merge simple params with data
            kwargs = {
                "name": name,
                "description": description,
            }

            # Extract known fields from data
            if isinstance(parsed_data, dict):
                kwargs.update(_extract_known_fields(parsed_data))
                kwargs["updates"] = parsed_data

            prepared = _build_content_operation(
                operation,
                entity_type,
                entity_id=content_id,
                content=None,
                markdown=None,
                html=None,
                cover_image=None,
                book_id=None,
                chapter_id=None,
                books=None,
                tags=None,
                image_id=None,
                priority=None,
                **kwargs  # This will override None values with actual data
            )

            response = _bookstack_request(
                prepared.method,
                prepared.path,
                params=prepared.params,
                json=prepared.json,
            )
        except Exception as e:
            logger.error(f"Error in bookstack_content_crud: {e}", exc_info=True)
            return {
                "action": action,
                "operation": operation,
                "entity_type": entity_type,
                "success": False,
                "error": str(e),
                "content_id": content_id,
            }

        # Aggressively truncate response to prevent JSON-RPC message size issues
        def truncate_recursive(obj: Any, max_str_len: int = 1000, max_depth: int = 10, current_depth: int = 0) -> Any:
            """Recursively truncate all strings in a nested structure."""
            if current_depth > max_depth:
                return "... (max depth reached)"

            if isinstance(obj, str):
                if len(obj) > max_str_len:
                    return obj[:max_str_len] + f"... (truncated from {len(obj)} chars)"
                return obj
            elif isinstance(obj, dict):
                return {k: truncate_recursive(v, max_str_len, max_depth, current_depth + 1) for k, v in obj.items()}
            elif isinstance(obj, list):
                if len(obj) > 50:
                    return [truncate_recursive(item, max_str_len, max_depth, current_depth + 1) for item in obj[:50]] + [f"... ({len(obj) - 50} more items)"]
                return [truncate_recursive(item, max_str_len, max_depth, current_depth + 1) for item in obj]
            else:
                return obj

        # Apply aggressive truncation for read operations
        if operation == "read":
            original_size = len(json_module.dumps(response))
            logger.info(f"Original response size: {original_size} bytes")

            response = truncate_recursive(response, max_str_len=1000)

            truncated_size = len(json_module.dumps(response))
            logger.info(f"Truncated response size: {truncated_size} bytes (reduced by {original_size - truncated_size} bytes)")

        result: Dict[str, Any] = {
            "action": action,
            "operation": operation,
            "entity_type": entity_type,
            "success": True,
            "data": response,
        }
        if content_id is not None:
            result["content_id"] = content_id
        elif isinstance(response, dict) and isinstance(response.get("id"), int):
            result["content_id"] = response["id"]

        result_size = len(json_module.dumps(result))
        logger.info(f"bookstack_content_crud RETURNING: success=True, result_size={result_size} bytes")

        return result

    @mcp.tool(
        annotations={
            "title": "Batch Content Operations",
        },
    )
    def bookstack_batch_operations(
        operation: Annotated[
            BatchOperationType,
            Field(description="Bulk operation: bulk_create, bulk_update, bulk_delete"),
        ],
        entity_type: Annotated[
            EntityType,
            Field(description="Entity: book, bookshelf, chapter, page"),
        ],
        items: Annotated[
            list[Dict[str, Any]],
            WithJsonSchema({
                **copy.deepcopy(_SIMPLE_BATCH_ITEMS_SCHEMA),
                "description": "List of items to process"
            }),
        ],
        continue_on_error: Annotated[
            bool,
            Field(default=True, description="Continue on item failure"),
        ] = True,
        dry_run: Annotated[
            bool,
            Field(default=False, description="Validate without executing"),
        ] = False,
        request_heartbeat: Annotated[
            Optional[bool],
            Field(default=None, description="Ignored parameter (for MCP client compatibility)"),
        ] = None,
    ) -> Dict[str, Any]:
        """Simplified bulk operations for BookStack content.
        
        Each item should have:
        - id: Entity ID (required for update/delete)
        - data: Object or JSON string with entity fields
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"bookstack_batch_operations_simple: operation={operation}, entity_type={entity_type}, items={len(items)}")

        total = len(items)
        successes: list[Dict[str, Any]] = []
        errors: list[Dict[str, Any]] = []

        def build_prepared(item: Dict[str, Any]) -> PreparedOperation:
            item_id = item.get("id")
            data = _coerce_json_object(item.get("data"), label="batch item 'data'")
            kwargs = _extract_known_fields(data) if isinstance(data, dict) else {}
            kwargs["updates"] = data
            
            if operation == "bulk_create":
                return _build_content_operation(
                    "create",
                    entity_type,
                    entity_id=None,
                    **kwargs
                )
            if operation == "bulk_update":
                _ensure(item_id is not None, "Each update item requires an 'id'")
                return _build_content_operation(
                    "update",
                    entity_type,
                    entity_id=_validate_positive_int(item_id, "'id'"),
                    **kwargs
                )
            # bulk_delete
            _ensure(item_id is not None, "Each delete item requires an 'id'")
            return _build_content_operation(
                "delete",
                entity_type,
                entity_id=_validate_positive_int(item_id, "'id'"),
                name=None,
                description=None,
                updates=None,
            )

        for item_index, item in enumerate(items):
            try:
                prepared = build_prepared(item)
                if dry_run:
                    successes.append({
                        "index": item_index,
                        "method": prepared.method,
                        "path": prepared.path,
                        "params": prepared.params,
                        "payload": prepared.json,
                    })
                    continue

                response = _bookstack_request(
                    prepared.method,
                    prepared.path,
                    params=prepared.params,
                    json=prepared.json,
                )
                successes.append({
                    "index": item_index,
                    "result": response,
                })
            except (ToolError, Exception) as exc:
                errors.append({"index": item_index, "error": str(exc)})
                if not continue_on_error:
                    break

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

