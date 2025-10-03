# MCP Inspector Quick Start Guide

## 🚀 Launch the Inspector

```bash
cd Bookstack-MCP/fastmcp_server
npx @modelcontextprotocol/inspector python run_stdio.py
```

The Inspector will:
1. Install dependencies (first time only)
2. Start the proxy server
3. Open your browser automatically
4. Connect to your FastMCP server

## 🌐 Access the Inspector

If the browser doesn't open automatically, navigate to:
```
http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=<your-token>
```

The token is displayed in the terminal output.

## 🔍 Quick Validation Tests

### Test 1: List Books (Safe)
**Tool**: `bookstack_list_content`
```json
{
  "entity_type": "books",
  "count": 10
}
```

### Test 2: Search Content (Safe)
**Tool**: `bookstack_search`
```json
{
  "query": "documentation"
}
```

### Test 3: List Images (Safe)
**Tool**: `bookstack_manage_images`
```json
{
  "operation": "list",
  "count": 5
}
```

### Test 4: Read a Book (Safe)
**Tool**: `bookstack_manage_content`
```json
{
  "operation": "read",
  "entity_type": "book",
  "id": 1
}
```

### Test 5: Search Images (Safe)
**Tool**: `bookstack_search_images`
```json
{
  "query": "logo",
  "extension": ".png"
}
```

## ⚠️ Destructive Operations (Use with Caution)

Only test these if you're comfortable creating/modifying data:

### Create a Test Page
**Tool**: `bookstack_manage_content`
```json
{
  "operation": "create",
  "entity_type": "page",
  "book_id": 1,
  "data": {
    "name": "MCP Inspector Test",
    "markdown": "# Test Page\n\nCreated via MCP Inspector for validation."
  }
}
```

### Update a Page
**Tool**: `bookstack_manage_content`
```json
{
  "operation": "update",
  "entity_type": "page",
  "id": <page_id>,
  "data": {
    "name": "Updated Test Page"
  }
}
```

### Delete a Test Page
**Tool**: `bookstack_manage_content`
```json
{
  "operation": "delete",
  "entity_type": "page",
  "id": <page_id>
}
```

## 📊 What to Check

### ✅ Connection
- Green status indicator in top-right
- No error messages in Notifications pane
- Server capabilities displayed

### ✅ Tools
- All expected tools are listed
- Each tool has a description
- Parameters are documented
- Required vs optional fields are clear

### ✅ Execution
- Tools execute without errors
- Responses are valid JSON
- Response data matches expectations
- Error messages are helpful

### ✅ Performance
- Tools respond quickly (< 5 seconds)
- No timeout errors
- Server remains stable

## 🐛 Troubleshooting

### Inspector won't start
```bash
# Clear npm cache and try again
npx clear-npx-cache
npx @modelcontextprotocol/inspector python run_stdio.py
```

### Connection errors
1. Check that `.env` file has correct credentials
2. Verify BookStack server is accessible
3. Check terminal for error messages

### Tool execution fails
1. Check Notifications pane for error details
2. Verify parameter format matches schema
3. Test with simpler parameters first

### Browser doesn't open
1. Copy the URL from terminal output
2. Paste into your browser manually
3. Make sure to include the auth token

## 🛑 Stop the Inspector

Press `Ctrl+C` in the terminal where the Inspector is running.

## 📝 Document Your Findings

Use the checklist in `INSPECTOR-SESSION-RESULTS.md` to track:
- Which tools you tested
- Any issues found
- Performance observations
- Schema validation results

## 🔄 Re-run After Changes

If you modify the server code:

1. Stop the Inspector (`Ctrl+C`)
2. Rebuild if needed: `cd .. && npm run build`
3. Restart the Inspector:
   ```bash
   cd fastmcp_server
   npx @modelcontextprotocol/inspector python run_stdio.py
   ```

## 📚 Additional Resources

- Full validation guide: `MCP-INSPECTOR-VALIDATION.md`
- Session results template: `INSPECTOR-SESSION-RESULTS.md`
- [MCP Inspector Docs](https://modelcontextprotocol.io/docs/tools/inspector)
- [FastMCP Docs](https://gofastmcp.com/)

