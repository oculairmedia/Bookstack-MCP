# MCP Tools and Write Operations - Analysis

## Summary: YES, MCP Tools CAN Submit/Write Data

**The Model Context Protocol (MCP) fully supports tools that perform write operations, mutations, and data submission.** This is a core feature of the protocol, not a limitation.

## Evidence from MCP Specification

### 1. Tool Annotations for Write Operations

The MCP specification (version 2025-06-18) includes explicit support for describing tool behavior through **ToolAnnotations**:

```typescript
interface ToolAnnotations {
  destructiveHint?: boolean;    // Tool may perform destructive updates
  idempotentHint?: boolean;     // Calling repeatedly has no additional effect
  openWorldHint?: boolean;      // Tool interacts with external entities
  readOnlyHint?: boolean;       // Tool performs read-only operations
  title?: string;
}
```

### Key Points:

- **`readOnlyHint`**: If `false`, the tool **may perform write operations**
- **`destructiveHint`**: If `true`, the tool **may perform destructive updates** (delete, overwrite)
- **`idempotentHint`**: Indicates if repeated calls with same args have additional effects

### 2. Default Behavior

According to the specification:

> **`readOnlyHint`** (boolean) - Optional - If true, the tool performs read-only operations. **If false, the tool may perform write operations.**

> **`destructiveHint`** (boolean) - Optional - If true, the tool may perform destructive updates. If false, the tool performs only additive updates. (Meaningful only when `readOnlyHint == false`). **Default: true**.

This means:
- Tools are **assumed to be writable by default** (readOnlyHint defaults to false)
- Tools are **assumed to be potentially destructive by default** (destructiveHint defaults to true)

## Your BookStack MCP Server

Your BookStack MCP server implements **many write operations**:

### Create Operations (Write)
- `bookstack_manage_content` with `operation: "create"`
  - Create books, bookshelves, chapters, pages, comments
- `bookstack_manage_images` with `operation: "create"`
  - Upload images to the gallery

### Update Operations (Write)
- `bookstack_manage_content` with `operation: "update"`
  - Update books, bookshelves, chapters, pages
- `bookstack_manage_images` with `operation: "update"`
  - Update image metadata

### Delete Operations (Destructive Write)
- `bookstack_manage_content` with `operation: "delete"`
  - Delete books, bookshelves, chapters, pages
- `bookstack_manage_images` with `operation: "delete"`
  - Delete images

### Batch Operations (Bulk Write)
- `bookstack_batch_operations`
  - `bulk_create`, `bulk_update`, `bulk_delete`

## Why Letta Might Have Issues

If Letta is having problems with your MCP server's write operations, it's likely **NOT** because MCP doesn't support writes. Possible reasons:

### 1. **Client-Side Restrictions**

Some MCP clients (like Letta) might:
- Restrict which tools they allow to be called
- Require explicit user approval for write operations
- Have safety mechanisms that block destructive operations
- Filter tools based on annotations

### 2. **Missing Tool Annotations**

Your tools might not be declaring their write behavior properly. Check if your tools include annotations:

```python
# Example: How to declare a write tool in FastMCP
@mcp.tool(
    annotations={
        "readOnlyHint": False,      # This tool writes data
        "destructiveHint": True,    # This tool can delete/overwrite
        "idempotentHint": False     # Repeated calls have effects
    }
)
def create_page(book_id: int, name: str, content: str):
    """Create a new page in BookStack."""
    # ... implementation
```

### 3. **Authentication/Permission Issues**

- Letta might not have proper credentials to perform writes
- The BookStack API token might have read-only permissions
- CORS or network policies might block write requests

### 4. **Error Handling**

- Write operations might be failing silently
- Error responses might not be properly formatted
- Letta might not be handling error responses correctly

## Recommendations

### 1. Add Tool Annotations to Your Server

Update your FastMCP tools to include proper annotations:

```python
# In fastmcp_server/bookstack/tools.py

# Read-only tool
@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "title": "List Books"
    }
)
def list_books(...):
    pass

# Write tool (non-destructive)
@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "title": "Create Page"
    }
)
def create_page(...):
    pass

# Destructive write tool
@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "title": "Delete Page"
    }
)
def delete_page(...):
    pass
```

### 2. Test with MCP Inspector

Use the MCP Inspector to verify:
1. Tools are properly declared with annotations
2. Write operations execute successfully
3. Error responses are properly formatted

### 3. Check Letta's Configuration

Review Letta's documentation for:
- Tool execution policies
- Write operation restrictions
- Required tool annotations
- User approval workflows

### 4. Enable Detailed Logging

Add logging to see what Letta is actually requesting:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@mcp.tool()
def create_page(...):
    logger.info(f"create_page called with args: {locals()}")
    try:
        result = # ... perform operation
        logger.info(f"create_page succeeded: {result}")
        return result
    except Exception as e:
        logger.error(f"create_page failed: {e}")
        raise
```

## Conclusion

**MCP absolutely supports write operations.** The issue with Letta is likely:

1. **Client-side restrictions** in Letta
2. **Missing tool annotations** in your server
3. **Configuration issues** (auth, permissions, CORS)
4. **Error handling** problems

The MCP protocol itself is designed to support full CRUD operations, including:
- ✅ Create (write)
- ✅ Read (read-only)
- ✅ Update (write)
- ✅ Delete (destructive write)

Your BookStack MCP server is correctly implementing write operations. The problem is elsewhere in the stack.

## Next Steps

1. ✅ Validate with MCP Inspector (already running)
2. Add tool annotations to your FastMCP server
3. Check Letta's logs for specific error messages
4. Review Letta's tool execution policies
5. Test with a simpler MCP client (like Claude Desktop) to isolate the issue

## References

- [MCP Specification - Tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
- [MCP Specification - Tool Annotations](https://modelcontextprotocol.io/specification/2025-06-18/schema#toolannotations)
- [FastMCP Documentation](https://gofastmcp.com/)

