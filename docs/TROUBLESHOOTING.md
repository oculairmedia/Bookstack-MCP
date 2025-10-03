# Troubleshooting Guide

## Common Issues and Solutions

### Tool Hangs When Called from Letta

**Symptom**: Tool call shows "Executing..." indefinitely and never completes.

**Cause**: Parameter named `id` is a reserved keyword in Letta.

**Solution**: 
1. Check if your tool has a parameter named `id`
2. Rename it to `content_id`, `item_id`, or similar
3. Rebuild the container: `docker-compose down && docker-compose up --build -d`

**Example**:
```python
# Before (broken)
def my_tool(id: int) -> dict:
    ...

# After (fixed)
def my_tool(content_id: int) -> dict:
    ...
```

---

### JSON-RPC Validation Errors

**Symptom**: 
```
pydantic_core._pydantic_core.ValidationError: validation errors for JSONRPCMessage
```

**Cause**: Response size is too large (>200KB).

**Solution**: Implement response truncation in your tool:

```python
def truncate_recursive(obj, max_str_len=1000):
    if isinstance(obj, str) and len(obj) > max_str_len:
        return obj[:max_str_len] + "... (truncated)"
    elif isinstance(obj, dict):
        return {k: truncate_recursive(v, max_str_len) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [truncate_recursive(item, max_str_len) for item in obj[:50]]
    return obj

response = truncate_recursive(api_response)
```

---

### Tool Returns "Missing Required Arguments" Error

**Symptom**:
```
_build_content_operation() missing 10 required keyword-only arguments
```

**Cause**: Not passing all required keyword-only parameters to internal functions.

**Solution**: Explicitly pass all required parameters with `None` defaults:

```python
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
    **kwargs  # Override with actual values
)
```

---

### Tool Works in MCP Inspector But Not Letta

**Cause**: Letta has stricter requirements than other MCP clients.

**Checklist**:
- [ ] No parameters named `id`
- [ ] Tool accepts `request_heartbeat: Optional[bool] = None`
- [ ] Response size is under 100KB
- [ ] Parameter schemas are simple (avoid complex `oneOf`)
- [ ] Error handling returns objects instead of raising exceptions

**See**: [LETTA_COMPATIBILITY.md](LETTA_COMPATIBILITY.md) for full requirements.

---

### Container Fails to Start

**Symptom**: Docker container exits immediately or shows errors.

**Common Causes**:

1. **Missing environment variables**
   ```bash
   # Check if .env file exists
   ls -la .env
   
   # Verify required variables
   grep -E "BS_URL|BS_TOKEN_ID|BS_TOKEN_SECRET" .env
   ```

2. **Port already in use**
   ```bash
   # Check if port 3054 is in use
   lsof -i :3054
   
   # Kill the process or change the port in docker-compose.yml
   ```

3. **Python dependency issues**
   ```bash
   # Rebuild without cache
   docker-compose build --no-cache
   ```

---

### BookStack API Returns 401 Unauthorized

**Cause**: Invalid or expired API token.

**Solution**:
1. Log into BookStack as an admin
2. Go to Settings → Users → [Your User] → API Tokens
3. Create a new token or verify the existing one
4. Update `.env` with the correct `BS_TOKEN_ID` and `BS_TOKEN_SECRET`
5. Restart the container

---

### Tool Returns Empty or Unexpected Results

**Debugging Steps**:

1. **Check server logs**:
   ```bash
   docker logs bookstack-mcp-bookstackmcp-1 --tail=100
   ```

2. **Test BookStack API directly**:
   ```bash
   curl -H "Authorization: Token ${BS_TOKEN_ID}:${BS_TOKEN_SECRET}" \
        "${BS_URL}/api/pages/123"
   ```

3. **Enable debug logging**:
   Add to `fastmcp_server/my_server.py`:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

4. **Verify tool parameters**:
   - Check that `content_id` exists in BookStack
   - Verify `action` is spelled correctly
   - Ensure `data` is valid JSON if provided

---

## Getting Help

If you're still experiencing issues:

1. **Check the logs**:
   ```bash
   # BookStack MCP server logs
   docker logs bookstack-mcp-bookstackmcp-1 --tail=200
   
   # Letta logs (if using Letta)
   docker logs letta-letta-1 --tail=200
   ```

2. **Verify the setup**:
   ```bash
   # Check container status
   docker ps | grep bookstack
   
   # Test MCP endpoint
   curl http://localhost:3054/mcp
   ```

3. **Review documentation**:
   - [LETTA_COMPATIBILITY.md](LETTA_COMPATIBILITY.md) - Letta-specific requirements
   - [README.md](../README.md) - General setup and usage
   - [BookStack API Docs](https://demo.bookstackapp.com/api/docs) - API reference

4. **Create an issue**:
   - Include error messages and logs
   - Describe what you were trying to do
   - Mention your environment (Letta version, Docker version, etc.)

---

## Quick Diagnostic Commands

```bash
# Check if server is running
curl http://localhost:3054/mcp

# List all registered tools
docker exec bookstack-mcp-bookstackmcp-1 python3 -c "
import asyncio
import sys
sys.path.insert(0, '/app')
from fastmcp_server.my_server import mcp
async def main():
    tools = await mcp._mcp_list_tools()
    for t in tools:
        print(f'- {t.name}')
asyncio.run(main())
"

# Test BookStack API connection
docker exec bookstack-mcp-bookstackmcp-1 python3 -c "
import os
import requests
url = os.getenv('BS_URL')
token_id = os.getenv('BS_TOKEN_ID')
token_secret = os.getenv('BS_TOKEN_SECRET')
headers = {'Authorization': f'Token {token_id}:{token_secret}'}
response = requests.get(f'{url}/api/books', headers=headers)
print(f'Status: {response.status_code}')
print(f'Books: {len(response.json().get(\"data\", []))}')
"

# Check container health
docker inspect bookstack-mcp-bookstackmcp-1 | grep -A 10 "Health"
```

---

## Performance Tips

### Reduce Response Size

For large content, use pagination and filtering:

```python
# Instead of fetching all pages
bookstack_list_content(entity_type="pages", count=100)

# Fetch in smaller batches
bookstack_list_content(entity_type="pages", count=10, offset=0)
```

### Cache Frequently Accessed Data

If you're repeatedly reading the same content, consider caching:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_page_cached(page_id: int):
    return bookstack_content_crud(action="read_page", content_id=page_id)
```

### Use Batch Operations

For multiple updates, use batch operations instead of individual calls:

```python
# Instead of multiple individual updates
for page_id in [1, 2, 3]:
    bookstack_content_crud(action="update_page", content_id=page_id, ...)

# Use batch operation
bookstack_batch_operations(
    operation="bulk_update",
    entity_type="page",
    items=[
        {"id": 1, "data": {...}},
        {"id": 2, "data": {...}},
        {"id": 3, "data": {...}},
    ]
)
```

