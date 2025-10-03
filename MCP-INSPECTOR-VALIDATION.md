# MCP Inspector Validation Guide for BookStack FastMCP Server

This guide provides step-by-step instructions for validating the BookStack FastMCP server using the MCP Inspector tool.

## Prerequisites

1. **Node.js and npm** installed (for running the MCP Inspector)
2. **Python 3.11+** installed
3. **FastMCP dependencies** installed:
   ```bash
   cd Bookstack-MCP/fastmcp_server
   pip install -r requirements.txt
   ```
4. **Environment variables** configured in `Bookstack-MCP/.env`:
   ```
   BS_URL=https://your-bookstack.example.com
   BS_TOKEN_ID=your_token_id
   BS_TOKEN_SECRET=your_token_secret
   ```

## Method 1: Inspect the FastMCP Server via HTTP Transport

The FastMCP server runs on HTTP transport by default (port 3054). The MCP Inspector can connect to it as a running HTTP server.

### Step 1: Start the FastMCP Server

In one terminal, start the server:

```bash
cd Bookstack-MCP/fastmcp_server
python -m fastmcp_server.my_server
```

You should see output like:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:3054 (Press CTRL+C to quit)
```

### Step 2: Connect MCP Inspector to the Running Server

In another terminal, run the MCP Inspector pointing to your HTTP server:

```bash
npx @modelcontextprotocol/inspector
```

Then in the Inspector UI:
1. Select **"HTTP"** as the transport type
2. Enter the server URL: `http://localhost:3054/mcp/v1`
3. Click **Connect**

## Method 2: Inspect via Python Command (Stdio Transport)

The MCP Inspector can also launch the server directly using stdio transport.

### Using the Inspector with Python Module

```bash
npx @modelcontextprotocol/inspector python -m fastmcp_server.my_server
```

**Note**: This requires the FastMCP server to support stdio transport. If it doesn't, you'll need to modify `my_server.py` to accept a `--stdio` flag.

## Method 3: Create a Stdio-Compatible Launcher Script

Create a launcher script that the Inspector can execute:

### Step 1: Create `run_stdio.py`

```python
#!/usr/bin/env python3
"""Stdio launcher for MCP Inspector."""

from fastmcp import FastMCP
from fastmcp_server.bookstack import register_bookstack_tools

mcp = FastMCP("BookStack MCP (FastMCP)")
register_bookstack_tools(mcp)

if __name__ == "__main__":
    # Run with stdio transport for MCP Inspector
    mcp.run(transport="stdio")
```

### Step 2: Run the Inspector

```bash
cd Bookstack-MCP/fastmcp_server
npx @modelcontextprotocol/inspector python run_stdio.py
```

## What to Validate in the Inspector

Once connected, validate the following:

### 1. **Server Connection Pane**
- ✅ Server connects successfully
- ✅ No connection errors in the logs
- ✅ Server capabilities are negotiated

### 2. **Tools Tab**
Verify all BookStack tools are listed:

- ✅ `bookstack_manage_content` - CRUD operations for books, bookshelves, chapters, pages, comments
- ✅ `bookstack_list_content` - List entities with pagination
- ✅ `bookstack_search` - Search across content
- ✅ `bookstack_manage_images` - Image gallery CRUD operations
- ✅ `bookstack_search_images` - Advanced image discovery
- ✅ `bookstack_batch_operations` - Bulk operations
- ✅ `bookstack_entity` (Huly integration if present)
- ✅ `bookstack_query` (Huly integration if present)
- ✅ `bookstack_issue_ops` (Huly integration if present)

For each tool:
- ✅ Tool schema is displayed correctly
- ✅ Tool description is clear
- ✅ Input parameters are documented
- ✅ Required vs optional parameters are marked

### 3. **Test Tool Execution**

#### Test 1: List Books
1. Select `bookstack_list_content` tool
2. Set parameters:
   ```json
   {
     "entity_type": "books",
     "count": 10
   }
   ```
3. Execute and verify:
   - ✅ Returns a list of books
   - ✅ No errors in response
   - ✅ Response format is valid JSON

#### Test 2: Search Content
1. Select `bookstack_search` tool
2. Set parameters:
   ```json
   {
     "query": "test"
   }
   ```
3. Execute and verify:
   - ✅ Returns search results
   - ✅ Results include relevant metadata

#### Test 3: List Images
1. Select `bookstack_manage_images` tool
2. Set parameters:
   ```json
   {
     "operation": "list",
     "count": 5
   }
   ```
3. Execute and verify:
   - ✅ Returns image list
   - ✅ Images have proper metadata (name, url, thumbnails)

### 4. **Resources Tab** (if applicable)
- Check if any resources are exposed
- Verify resource URIs and MIME types

### 5. **Prompts Tab** (if applicable)
- Check if any prompt templates are registered
- Test prompt generation with sample arguments

### 6. **Notifications Pane**
- ✅ Monitor for any error logs
- ✅ Check for proper logging output
- ✅ Verify no unexpected warnings

## Common Issues and Troubleshooting

### Issue: Inspector can't connect to HTTP server
**Solution**: Ensure the server is running on the correct port (3054) and the URL is `http://localhost:3054/mcp/v1`

### Issue: "Module not found" error
**Solution**: Make sure you're running the Inspector from the correct directory and Python dependencies are installed

### Issue: Authentication errors
**Solution**: Verify your `.env` file has correct BookStack credentials:
```bash
cd Bookstack-MCP
cat .env
```

### Issue: Tools not appearing
**Solution**: Check that `register_bookstack_tools(mcp)` is called in `my_server.py`

### Issue: Tool execution fails
**Solution**: 
1. Check the Notifications pane for error details
2. Verify BookStack server is accessible
3. Test credentials with a simple API call:
   ```bash
   curl -H "Authorization: Token ${BS_TOKEN_ID}:${BS_TOKEN_SECRET}" ${BS_URL}/api/books
   ```

## Best Practices for Validation

1. **Start Simple**: Test basic list operations before complex CRUD operations
2. **Check Schemas**: Verify all tool schemas match the expected parameters
3. **Test Edge Cases**: Try invalid inputs to verify error handling
4. **Monitor Logs**: Keep an eye on the Notifications pane for warnings
5. **Test All Tools**: Don't skip any tools - validate each one works
6. **Verify Responses**: Check that response formats match expectations

## Next Steps After Validation

Once validation is complete:
1. Document any issues found
2. Test integration with actual MCP clients (Claude Desktop, etc.)
3. Run automated tests: `pytest tests/`
4. Update documentation based on findings

## References

- [MCP Inspector Documentation](https://modelcontextprotocol.io/docs/tools/inspector)
- [FastMCP Documentation](https://gofastmcp.com/)
- [BookStack API Reference](https://www.bookstackapp.com/docs/api/)

