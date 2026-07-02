# BookStack MCP Server - Expanded Version!

This repository hosts a **Python FastMCP-based server** that exposes consolidated tools for managing a BookStack instance. The flagship capabilities are the image gallery management workflows that power authoring experiences in downstream MCP clients.

## Quick start

```bash
# Install Python dependencies for the FastMCP server
pip install -r fastmcp_server/requirements.txt
```

Launch the FastMCP server after exporting your BookStack credentials (see below):

```bash
# From the repository root
fastmcp run fastmcp_server/my_server.py:mcp --transport http --host 0.0.0.0 --port 3054
```

Alternatively, run the module directly (honors the `PORT` env var, defaults to 3054):

```bash
PYTHONPATH="$PWD" python3 fastmcp_server/my_server.py
```

Or use Docker Compose:

```bash
docker compose up --build
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

### Direct Page Tools
- `bookstack_create_page_direct` / `bookstack_update_page_direct` — create/update pages with typed arguments
- `bookstack_create_page_from_file` / `bookstack_update_page_from_file` — create/update pages from a Markdown file under `/data`

> **Large page edits:** for content larger than ~50 KB, prefer the `*_from_file`
> tools. Writing the markdown to a file under `/data` and passing its path avoids
> embedding a huge string in the tool call (which some MCP clients truncate) and is
> more reliable. Write requests also get a larger, payload-scaled timeout
> (`BS_HTTP_WRITE_TIMEOUT`, default 120s) so big edits don't time out prematurely.

### PDF & Attachment Tools
- `bookstack_get_attachment_to_file` — download an attachment (base64 API content) to a file under `/data`
- `bookstack_extract_pdf_attachment_text_to_file` — extract text from a PDF attachment via `pdftotext`
- `bookstack_extract_embedded_page_pdfs` — extract all embedded PDF attachments referenced by a page
- `bookstack_append_pdf_text_page` — append a title/bullet summary page to a PDF under `/data`

### Observability
- `bookstack_health_check`, `bookstack_get_metrics`, `bookstack_dashboard` — health and runtime metrics
- `bookstack_semantic_search` — optional Hayhooks-backed semantic search (requires `HAYHOOKS_SEARCH_URL`)

The production tool stack is registered by `register_production_tools()` in `fastmcp_server/bookstack/__init__.py`, used by both the HTTP server (`my_server.py`) and the stdio/Inspector launcher (`run_stdio.py`).

> **📘 Letta Compatibility**: If you're using Letta as your MCP client, please read [docs/LETTA_COMPATIBILITY.md](docs/LETTA_COMPATIBILITY.md) for important compatibility requirements and best practices.

### Image uploads from URLs

`bookstack_manage_images` accepts three input shapes for the `image`/`new_image` fields during create and update operations:

1. Plain base64 strings
2. Data URLs (`data:image/png;base64,...`)
3. HTTP or HTTPS URLs

When a URL is supplied the tool:

- Streams the remote image with a 30 second timeout and a 50 MB limit
- Restricts schemes to HTTP/HTTPS and blocks loopback, private, link-local, reserved, and redirect-based internal targets
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
