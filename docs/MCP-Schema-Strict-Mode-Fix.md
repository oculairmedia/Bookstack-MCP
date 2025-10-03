# MCP Schema Strict Mode Fix

## Issue

The `bookstack_manage_content` and `bookstack_batch_operations` tools were throwing MCP schema validation warnings in strict mode:

```
"mcp:SCHEMA_STATUS": "NON_STRICT_ONLY",
"mcp:SCHEMA_WARNINGS": [
  "root: 'additionalProperties' not explicitly set",
  "root.properties.items.items: 'additionalProperties' not explicitly set",
  "root.properties.items.items.properties.data.oneOf[0]: 'additionalProperties' not explicitly set",
  "root.properties.items.items.properties.data.oneOf[0].properties.tags.items: 'additionalProperties' not explicitly set",
  ...
  "root.properties.items.items.properties.data.oneOf[4]: 'additionalProperties' is not false (free-form object)"
]
```

This meant the tools would only work in **non-strict mode**, preventing some MCP clients from using them.

## Root Cause

1. **Missing `unevaluatedProperties` in payload schemas**: The Book, Bookshelf, Chapter, and Page payload schemas had `additionalProperties: False` but MCP strict mode requires `unevaluatedProperties: False` for schemas used in `oneOf` contexts.

2. **Raw object payload with `additionalProperties: True`**: The `_RAW_OBJECT_PAYLOAD_SCHEMA` was included in the `oneOf` list with `additionalProperties: True`, which MCP strict mode explicitly rejects.

## Solution

### 1. Changed `additionalProperties` to `unevaluatedProperties`

Updated all payload schemas to use `unevaluatedProperties: False` instead of `additionalProperties: False`:

- `_BOOK_PAYLOAD_SCHEMA`
- `_BOOKSHELF_PAYLOAD_SCHEMA`
- `_CHAPTER_PAYLOAD_SCHEMA`
- `_PAGE_PAYLOAD_SCHEMA`
- `BATCH_ITEM_SCHEMA`

**Why `unevaluatedProperties`?**
- `additionalProperties` applies to properties not defined in the schema
- `unevaluatedProperties` applies to properties not evaluated by any schema keywords (including `oneOf`, `anyOf`, etc.)
- When using `oneOf`, `unevaluatedProperties` is the correct choice to prevent additional properties

### 2. Removed raw object payload schema

Removed `_RAW_OBJECT_PAYLOAD_SCHEMA` from the `_PAYLOAD_ONE_OF_WITH_STRING_AND_NULL` list because it had `additionalProperties: True`, which violates MCP strict mode requirements.

**Impact:**
- Users can no longer pass free-form objects directly in the `updates` parameter
- **Workaround**: Users can still pass custom fields via JSON string using `_JSON_STRING_PAYLOAD_SCHEMA`

**Example:**
```python
# Before (no longer supported):
await tool.run({
    "operation": "update",
    "entity_type": "book",
    "id": 123,
    "updates": {"custom_field": "value"}  # Free-form object
})

# After (use JSON string):
import json
await tool.run({
    "operation": "update",
    "entity_type": "book",
    "id": 123,
    "updates": json.dumps({"custom_field": "value"})  # JSON string
})
```

## Changes Made

### Files Modified

1. **`fastmcp_server/bookstack/tools.py`**:
   - Changed `additionalProperties: False` to `unevaluatedProperties: False` in:
     - `_BOOK_PAYLOAD_SCHEMA` (line 103)
     - `_BOOKSHELF_PAYLOAD_SCHEMA` (line 129)
     - `_CHAPTER_PAYLOAD_SCHEMA` (line 158)
     - `_PAGE_PAYLOAD_SCHEMA` (line 184)
     - `BATCH_ITEM_SCHEMA` (line 228)
   - Removed `_RAW_OBJECT_PAYLOAD_SCHEMA` from `_PAYLOAD_ONE_OF_WITH_STRING_AND_NULL` (line 215)

2. **`fastmcp_server/tests/test_schema_shapes.py`**:
   - Updated tests to reflect removal of raw object payload schema
   - Removed assertions checking for "Custom payload forwarded directly to BookStack" description

## Verification

### Test Results

All tests pass:
```bash
$ python3 -m pytest fastmcp_server/tests/ -v
======================== 37 passed, 1 warning in 2.08s =========================
```

### Schema Validation

The schemas now correctly have `unevaluatedProperties: False`:

```python
# Batch operations data oneOf schemas:
[0] type=object, unevaluatedProperties=False  # Book payload
[1] type=object, unevaluatedProperties=False  # Bookshelf payload
[2] type=object, unevaluatedProperties=False  # Chapter payload
[3] type=object, unevaluatedProperties=False  # Page payload
[4] type=string                                # JSON string payload
[5] type=null                                  # Null payload
```

## MCP Strict Mode Compliance

After these changes, the tools should now work in **MCP strict mode** without warnings. The schema status should change from:

```
"mcp:SCHEMA_STATUS": "NON_STRICT_ONLY"
```

To:

```
"mcp:SCHEMA_STATUS": "STRICT"
```

## Migration Guide for Users

If you were using the raw object payload feature, you need to update your code:

### Before
```python
# Passing a free-form object
result = await tool.run({
    "operation": "create",
    "entity_type": "book",
    "updates": {
        "name": "My Book",
        "custom_field": "custom_value"
    }
})
```

### After
```python
import json

# Pass as JSON string
result = await tool.run({
    "operation": "create",
    "entity_type": "book",
    "updates": json.dumps({
        "name": "My Book",
        "custom_field": "custom_value"
    })
})
```

Or use the structured parameters directly:

```python
# Use structured parameters
result = await tool.run({
    "operation": "create",
    "entity_type": "book",
    "name": "My Book",
    "description": "Book description"
})
```

## References

- [JSON Schema: unevaluatedProperties](https://json-schema.org/understanding-json-schema/reference/object.html#unevaluatedproperties)
- [MCP Schema Validation](https://modelcontextprotocol.io/docs/concepts/schemas)
- [FastMCP Schema Generation](https://gofastmcp.com/servers/tools)

