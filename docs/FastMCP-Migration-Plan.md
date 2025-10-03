# FastMCP 2.0 Research & Migration Plan

> **✅ MIGRATION COMPLETE**: This migration has been successfully completed. The Python FastMCP server is now the primary and only supported server. The TypeScript/mcp-framework server is deprecated.

This document captures our evaluation of FastMCP 2.0 and the completed migration from the Node/TypeScript `mcp-framework` server to a Python-based FastMCP server.

## Objectives

- Resolve JSON Schema (draft 2020-12) validation friction and simplify tool schema definitions.
- Reduce boilerplate for HTTP transport and session handling.
- Provide a clear, incremental migration path without disrupting current workflows.
- Enable richer, typed structured outputs aligned with the latest MCP spec (2025-06-18).

## Why FastMCP

- Pythonic tool model: `@mcp.tool` on normal Python functions.
- Automatic JSON Schema generation from Python type hints (incl. `typing.Annotated` and `pydantic.Field`).
- Built-in HTTP transport; simpler run/ops model, no manual session headers required.
- Structured outputs are first-class: dicts/dataclasses/Pydantic models become machine-readable JSON automatically (plus traditional content).
- Async-first with good ergonomics; sync tools supported.

References:
- Docs: https://gofastmcp.com/
- Tools (schema/annotations/output): https://gofastmcp.com/servers/tools
- PyPI: https://pypi.org/project/fastmcp/

## Minimal Examples

### Server (HTTP)

```python
from fastmcp import FastMCP

mcp = FastMCP("BookStack MCP")

@mcp.tool
def ping(name: str) -> str:
    """Health check"""
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
```

CLI alternative:

```bash
fastmcp run path/to/server.py:mcp --transport http --port 8000
```

### Client (HTTP)

```python
import asyncio
from fastmcp import Client

async def main():
    async with Client("http://localhost:8000/mcp") as client:
        res = await client.call_tool("ping", {"name": "world"})
        print(res)

asyncio.run(main())
```

## Tool Design Principles in FastMCP

- Parameters
  - Derived from function signature + type hints.
  - Use `Annotated[T, "description"]` for concise docstrings.
  - Use `Annotated[T, Field(...)]` (Pydantic) for constraints: `ge/le`, `min_length`, `pattern`, etc.
- Optional vs required
  - Parameters without defaults are required.
  - Defaults make parameters optional.
- Excluding args
  - `@mcp.tool(exclude_args=["user_id"])` to hide runtime-injected parameters.
- Annotations (client hints)
  - `title`, `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`.
- Return values and structured output
  - Returning `dict`/dataclass/Pydantic → structured content automatically (plus text content).
  - Primitive returns (int/str/etc.) → structured content created when a return type is provided (wrapped under `result`) or when `output_schema` is defined.
- Error handling
  - Raise Python exceptions or `ToolError`. `mask_error_details=True` on `FastMCP` can hide internals.

## BookStack: List Books Tool (Reference)

```python
from fastmcp import FastMCP
import os, requests

mcp = FastMCP("BookStack MCP")

@mcp.tool(
    annotations={"title": "List Books", "readOnlyHint": True}
)
def bookstack_list_books(offset: int = 0, count: int = 50) -> dict:
    """List books from BookStack."""
    base = os.environ["BS_URL"].rstrip("/")
    url = f"{base}/api/books?offset={offset}&count={count}"
    headers = {
        "Authorization": f"Token {os.environ['BS_TOKEN_ID']}:{os.environ['BS_TOKEN_SECRET']}"
    }
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()
```

Environment variables expected:
- `BS_URL` (e.g., `https://your.bookstack.local`)
- `BS_TOKEN_ID`
- `BS_TOKEN_SECRET`

## Migration Plan (Phased)

We will migrate incrementally while keeping the existing Node server operational.

### Phase 0: Repo Layout & Prep (no runtime changes)

- Create a new Python server folder without affecting current Node codebase, e.g.:

```
fastmcp_server/
  my_server.py        # FastMCP instance and tool registrations
  bookstack/
    __init__.py
    tools.py          # Tools implemented here (list/read/create/update/delete/search/images)
  requirements.txt    # Or use uv/poetry to manage deps
```

- Decide on HTTP client: `requests` (simple) or `httpx` (async). Example above uses `requests`.
- Pin versions for stability (e.g., `fastmcp==2.11.x`).

### Phase 1: First Tool & Validation

1) Implement `bookstack_list_books` in `bookstack/tools.py`.
2) Wire up `my_server.py` to register the tool.
3) Run locally over HTTP: `fastmcp run fastmcp_server/my_server.py:mcp --transport http --port 8000`.
4) Validate via FastMCP client and/or Claude Desktop HTTP MCP.

### Phase 2: Read Tools

- Implement read-only tools:
  - `read_book`, `read_bookshelf`, `read_chapter`, `read_page`
  - `list_bookshelves`, `list_chapters`, `list_pages`
  - `search` and `search_images` (if applicable)
- Confirm schemas and outputs (prefer returning `dict` for automatic structured content).

### Phase 3: Write Tools

- Implement create/update/delete tools for Books, Bookshelves, Chapters, Pages, and Image management.
- Add annotations: `destructiveHint=True` for delete/mutations; `idempotentHint=True` where applicable.
- Add careful error handling and input validation (e.g., range checks, enum choices).

### Phase 4: Structured Output Types (Optional, Recommended)

- Replace loose `dict` returns with dataclasses or Pydantic models for predictable schemas (useful for clients expecting strict shapes).
- Example dataclass result for a list response:

```python
from dataclasses import dataclass
from typing import List

@dataclass
class Book:
    id: int
    name: str
    slug: str

@dataclass
class ListBooksResult:
    total: int
    data: List[Book]
```

### Phase 5: Cutover & Decommission

- Update clients to point at the FastMCP HTTP endpoint.
- Run both servers in parallel for a period; compare outputs and stability.
- Decommission the Node server after acceptance.

## Testing & Validation

- Local FastMCP client smoke tests (HTTP) as above.
- Add Python unit tests at the function level (mock BookStack API responses) to keep iterations fast.
- Consider contract tests for critical tool schemas and outputs.

## Deployment

- Options:
  - Self-host: run FastMCP with `--transport http` behind your reverse proxy.
  - FastMCP Cloud: managed hosting (see docs) for quick deployments.
- Add health checks and basic logging.

## Risks & Mitigations

- Python runtime/dependencies: use venv/uv/poetry and pin versions.
- Behavior parity: run parallel validation with the Node server; compare outputs for key tools.
- Auth/secrets: continue using env vars; consider secret management solutions for production.

## Next Steps (Action Items)

1) Create `fastmcp_server/` with `my_server.py` and `bookstack/tools.py` skeletons.
2) Implement and verify `bookstack_list_books` tool.
3) Port read tools, then write tools.
4) Optionally introduce dataclasses/Pydantic for structured outputs.
5) Plan cutover window and update clients.

