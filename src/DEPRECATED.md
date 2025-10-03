# ⚠️ DEPRECATED: TypeScript/mcp-framework Server

**This TypeScript server implementation is deprecated and no longer maintained.**

## Migration Required

All development has moved to the **Python FastMCP server** located in the `fastmcp_server/` directory.

### Why the change?

1. **Better tooling**: FastMCP provides superior schema generation and validation
2. **Consolidated tools**: Python server offers unified tools (`bookstack_manage_content`, `bookstack_batch_operations`) instead of individual CRUD operations
3. **Easier maintenance**: Single Python codebase vs. multiple TypeScript tool files
4. **Better testing**: Comprehensive pytest suite with better coverage
5. **Active development**: All new features and bug fixes go to the Python server

### How to migrate

1. **Stop using the TypeScript server**:
   - Remove any references to `npm run start` or `node dist/index.js`
   - Remove TypeScript server from your MCP client configuration

2. **Switch to the Python FastMCP server**:
   ```bash
   cd fastmcp_server
   pip install -r requirements.txt
   python3 -m fastmcp_server
   ```

3. **Update your tool calls**:
   - Old: Individual tools like `bookstack_create_book`, `bookstack_update_page`, etc.
   - New: Consolidated tools like `bookstack_manage_content` with operation parameters

### Tool mapping

| Old TypeScript Tools | New Python Tool | Operation |
|---------------------|-----------------|-----------|
| `bookstack_create_book` | `bookstack_manage_content` | `operation: "create", entity_type: "book"` |
| `bookstack_read_book` | `bookstack_manage_content` | `operation: "read", entity_type: "book"` |
| `bookstack_update_book` | `bookstack_manage_content` | `operation: "update", entity_type: "book"` |
| `bookstack_delete_book` | `bookstack_manage_content` | `operation: "delete", entity_type: "book"` |
| `bookstack_list_books` | `bookstack_list_content` | `entity_type: "books"` |
| *(same pattern for bookshelves, chapters, pages)* | | |

### Need help?

See the main [README.md](../README.md) for complete Python server documentation.

---

**Last updated**: 2025-10-02  
**Removal planned**: This directory may be removed in a future release.

