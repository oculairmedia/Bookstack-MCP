# Letta MCP Client Compatibility Guide

## Overview

This document describes compatibility requirements and best practices for creating MCP tools that work with Letta's MCP client implementation.

**Last Updated**: 2025-10-03  
**Letta Version Tested**: Latest (as of October 2025)  
**MCP Protocol Version**: 2024-11-05

---

## Critical Requirements

### 1. ⚠️ NEVER Use `id` as a Parameter Name

**Issue**: The parameter name `id` is a **reserved keyword** in Letta's MCP client implementation.

**Symptom**: Tools with an `id` parameter will **hang indefinitely** when called from Letta. The tool call never reaches the MCP server - Letta hangs during its internal processing.

**Solution**: Use alternative parameter names like:
- `content_id`
- `item_id`
- `entity_id`
- `record_id`
- `resource_id`

**Example - WRONG ❌**:
```python
@mcp.tool()
def my_tool(
    id: int,  # ❌ This will cause Letta to hang!
    name: str
) -> dict:
    ...
```

**Example - CORRECT ✅**:
```python
@mcp.tool()
def my_tool(
    content_id: int,  # ✅ Works perfectly
    name: str
) -> dict:
    ...
```

### 2. Keep Parameter Count Low

**Recommendation**: Limit tools to **5 or fewer parameters** when possible.

**Reason**: Letta may have issues with tools that have many parameters. While not a hard limit, simpler tools are more reliable.

**Strategy**: Combine related parameters or use a single JSON string parameter for complex data:

```python
@mcp.tool()
def bookstack_content_crud(
    action: Literal["read_page", "create_page", "update_page", ...],  # Combined operation+entity
    content_id: Optional[int] = None,
    name: Optional[str] = None,
    data: Optional[str] = None,  # JSON string for additional fields
) -> dict:
    ...
```

### 3. Handle `request_heartbeat` Parameter

**Issue**: Letta automatically adds a `request_heartbeat: true` parameter to all tool calls.

**Solution**: Add `request_heartbeat` as an optional parameter to all tools:

```python
@mcp.tool()
def my_tool(
    content_id: int,
    request_heartbeat: Optional[bool] = None,  # ✅ Accept and ignore
) -> dict:
    # Just ignore request_heartbeat - it's for Letta's internal use
    ...
```

### 4. Avoid Complex Schema Types

**Issue**: Complex JSON schemas with `oneOf`, `anyOf`, or deeply nested `additionalProperties` may cause issues.

**Recommendation**: Use simple types when possible:
- ✅ `str`, `int`, `bool`, `Optional[str]`
- ✅ `Literal["option1", "option2", ...]`
- ⚠️ Avoid: Complex `oneOf` with multiple object types
- ⚠️ Avoid: `additionalProperties: true` on nested objects

**Example - Simplified Schema**:
```python
# Instead of accepting both object and string:
data: Union[Dict[str, Any], str]  # ❌ May cause issues

# Use just string and parse it:
data: Optional[str] = None  # ✅ Simpler, more reliable
```

---

## Response Size Limits

### Issue: Large Responses Cause JSON-RPC Errors

**Symptom**: Letta shows validation errors like:
```
pydantic_core._pydantic_core.ValidationError: validation errors for JSONRPCMessage
```

**Cause**: MCP responses over ~200KB can cause Letta's JSON-RPC parser to fail.

**Solution**: Implement aggressive response truncation:

```python
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

# Apply to responses
response = truncate_recursive(api_response, max_str_len=1000)
```

**Recommended Limits**:
- **String length**: 1,000 characters max
- **Array length**: 50 items max
- **Nesting depth**: 10 levels max
- **Total response size**: Keep under 100KB

---

## Error Handling Best Practices

### Return Error Objects Instead of Raising Exceptions

**Recommendation**: Catch exceptions and return structured error responses:

```python
@mcp.tool()
def my_tool(content_id: int) -> dict:
    try:
        result = perform_operation(content_id)
        return {
            "success": True,
            "data": result,
            "content_id": content_id,
        }
    except Exception as e:
        logger.error(f"Error in my_tool: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "content_id": content_id,
        }
```

**Benefits**:
- Letta can display the error to the user
- The agent can retry or take alternative actions
- Better debugging information

---

## Testing Checklist

Before deploying MCP tools for Letta, verify:

- [ ] No parameters named `id`
- [ ] All tools accept `request_heartbeat: Optional[bool] = None`
- [ ] Parameter count is 5 or fewer (if possible)
- [ ] Response truncation is implemented for large data
- [ ] Error handling returns structured error objects
- [ ] Tool descriptions are clear and concise
- [ ] All enum/Literal values are documented in descriptions

---

## Debugging Letta Tool Issues

### Tool Hangs Indefinitely

**Likely Cause**: Parameter named `id`

**How to Verify**:
1. Check MCP server logs - if no request arrives, it's a Letta-side issue
2. Review tool parameters for reserved keywords
3. Try renaming `id` to `content_id` or similar

### Tool Returns Validation Errors

**Likely Cause**: Response too large or complex schema

**How to Verify**:
1. Check response size in server logs
2. Implement response truncation
3. Simplify parameter schemas

### Tool Works in Other Clients But Not Letta

**Likely Cause**: Letta-specific compatibility issue

**How to Verify**:
1. Test with MCP Inspector or other MCP clients
2. Compare working vs non-working tool schemas
3. Simplify the tool progressively until it works

---

## Example: BookStack CRUD Tool

Here's a complete example of a Letta-compatible tool:

```python
@mcp.tool()
def bookstack_content_crud(
    action: Literal[
        "read_page", "create_page", "update_page", "delete_page",
        "read_book", "create_book", "update_book", "delete_book",
        "read_chapter", "create_chapter", "update_chapter", "delete_chapter",
        "read_shelf", "create_shelf", "update_shelf", "delete_shelf"
    ],
    content_id: Optional[int] = None,  # ✅ NOT 'id'
    name: Optional[str] = None,
    description: Optional[str] = None,
    data: Optional[str] = None,  # JSON string for complex data
    request_heartbeat: Optional[bool] = None,  # ✅ Accept Letta's parameter
) -> Dict[str, Any]:
    """CRUD operations for BookStack content."""
    try:
        # Parse action
        parts = action.split("_", 1)
        operation = parts[0]
        entity_type = parts[1]
        
        # Perform operation
        result = perform_bookstack_operation(operation, entity_type, content_id, name, description, data)
        
        # Truncate large responses
        if operation == "read":
            result = truncate_recursive(result, max_str_len=1000)
        
        return {
            "success": True,
            "action": action,
            "data": result,
            "content_id": content_id,
        }
    except Exception as e:
        return {
            "success": False,
            "action": action,
            "error": str(e),
            "content_id": content_id,
        }
```

---

## Known Issues

### Issue: DeepSeek Client Error

**Symptom**:
```
NameError: name '_Message' is not defined
```

**Cause**: Bug in Letta's DeepSeek client implementation

**Workaround**: Use a different LLM provider (OpenAI, Anthropic, etc.)

### Issue: MCP Strict Mode Schema Warnings

**Symptom**:
```
mcp:SCHEMA_STATUS: NON_STRICT_ONLY
mcp:SCHEMA_WARNINGS: 'additionalProperties' not explicitly set
```

**Cause**: FastMCP doesn't automatically add `additionalProperties: False` to root schemas

**Impact**: Tools work correctly but show warnings in strict mode validators

**Status**: This is a FastMCP limitation, not a functional issue. Tools work perfectly with Letta despite the warnings.

**Future**: Will be resolved when FastMCP adds strict mode support

---

## Additional Resources

- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://gofastmcp.com)
- [Letta Documentation](https://docs.letta.com/)

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-10-03 | 1.0 | Initial documentation of Letta compatibility requirements |

---

## Contributing

If you discover additional Letta compatibility issues or best practices, please update this document and submit a pull request.

