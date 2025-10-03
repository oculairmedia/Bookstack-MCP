# BookStack MCP Server

This repository hosts a **Python FastMCP-based server** that exposes consolidated tools for managing a BookStack instance. The flagship capabilities are the image gallery management workflows that power authoring experiences in downstream MCP clients.

> **⚠️ DEPRECATION NOTICE**: The TypeScript/mcp-framework server (`src/` directory) is deprecated and no longer maintained. All development has moved to the Python FastMCP server (`fastmcp_server/` directory). Please migrate to the Python server for the latest features and bug fixes.

## Quick start

```bash
# Install Python dependencies for the FastMCP server
pip install -r fastmcp_server/requirements.txt
```

Launch the FastMCP server after exporting your BookStack credentials (see below):

```bash
cd fastmcp_server
python3 -m fastmcp_server
```

### Required environment

Copy `.env.example` to `.env` and populate these variables before invoking any BookStack tools:

```
BS_URL=https://your-bookstack.example.com
BS_TOKEN_ID=...
BS_TOKEN_SECRET=...
```

The API token must belong to a user that can view and manage the image gallery. Local helper scripts use `set -a && source .env` so the values apply to ad-hoc Python snippets as well.

## BookStack tools

The Python FastMCP server provides comprehensive BookStack management through consolidated tools:

### Content Management
- `bookstack_content_crud` — unified CRUD operations for books, bookshelves, chapters, and pages (Letta-compatible)
- `bookstack_list_content` — list and filter content entities with pagination
- `bookstack_search` — full-text search across BookStack content
- `bookstack_batch_operations` — bulk create, update, and delete operations

### Image Gallery Management
- `bookstack_manage_images` — unified create/read/update/delete/list interface for images
- `bookstack_search_images` — advanced discovery with extension, date, size, and usage filters

All tools are registered by `fastmcp_server/bookstack/tools.py` and surfaced automatically when the FastMCP server starts.

> **📘 Letta Compatibility**: If you're using Letta as your MCP client, please read [docs/LETTA_COMPATIBILITY.md](docs/LETTA_COMPATIBILITY.md) for important compatibility requirements and best practices.

### Image uploads from URLs

`bookstack_manage_images` accepts three input shapes for the `image`/`new_image` fields during create and update operations:

1. Plain base64 strings
2. Data URLs (`data:image/png;base64,...`)
3. HTTP or HTTPS URLs

When a URL is supplied the tool:

- Streams the remote image with a 30 second timeout and a 50 MB limit
- Restricts schemes to HTTP/HTTPS to avoid SSRF
- Validates the MIME type against BookStack's accepted formats (jpeg, png, gif, webp, bmp, tiff, svg+xml)
- Infers a filename from the URL path when one is not supplied

### Required BookStack parameters

BookStack's `POST /api/image-gallery` endpoint enforces two additional fields beyond the binary payload:

- `type` — must be `gallery` for standard content images (use `drawio` only when uploading diagrams.net PNGs)
- `uploaded_to` — the numeric page ID to attach the image to. BookStack rejects uploads without a real page context.

The tool surfaces these as optional inputs named `image_type` and `uploaded_to`. Default values of `gallery` and `0` preserve backward compatibility while allowing callers to target specific pages when required.

### Manual verification against a live instance

After exporting your environment variables you can confirm an end-to-end URL upload with the following snippet (replace `PAGE_ID` with an existing page id):

```bash
cd /opt/stacks/bookstack-mcp/Bookstack-MCP
set -a && source .env && set +a
python3 - <<'PY'
import asyncio, json, time
from fastmcp import FastMCP
from fastmcp_server.bookstack.tools import register_bookstack_tools

TEST_IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png"
PAGE_ID = 39  # replace with a page id from your BookStack instance

async def main():
    mcp = FastMCP("manual-test")
    register_bookstack_tools(mcp)
    tool = await mcp.get_tool("bookstack_manage_images")
    result = await tool.run({
        "operation": "create",
        "name": f"URL Upload Test {int(time.time())}",
        "image": TEST_IMAGE_URL,
        "uploaded_to": PAGE_ID,
    })
    print(json.dumps(json.loads(result.content[0].text), indent=2))

asyncio.run(main())
PY
```

You should receive a JSON payload describing the uploaded image, including thumbnails and the `uploaded_to` identifier. A `422` error means BookStack rejected the request (common causes: missing `uploaded_to`, disallowed MIME type, image exceeding the 50 MB limit). A `404` response typically indicates the API token lacks gallery permissions.

## Testing

Run the Python unit tests for the BookStack tools:

```bash
cd fastmcp_server
python3 -m pytest tests/test_manage_images.py -v
```

The suite covers URL handling, timeout and size enforcement, invalid scheme rejection, and the forwarding of `type`/`uploaded_to` metadata.

## Additional references

- FastMCP docs: https://gofastmcp.com/
- BookStack API reference: https://www.bookstackapp.com/docs/api/
- Product requirements for the image gallery tools: `docs/PRD-Image-Gallery-Management.md`
