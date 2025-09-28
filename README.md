# mcp-framework-server

A Model Context Protocol (MCP) server built with mcp-framework.

## Quick Start

```bash
# Install dependencies
npm install

# Build the project
npm run build

```

## Project Structure

```
mcp-framework-server/
├── src/
│   ├── tools/        # MCP Tools
│   │   └── ExampleTool.ts
│   └── index.ts      # Server entry point
├── package.json
└── tsconfig.json
```

## Adding Components

The project comes with an example tool in `src/tools/ExampleTool.ts`. You can add more tools using the CLI:

```bash
# Add a new tool
mcp add tool my-tool

# Example tools you might create:
mcp add tool data-processor
mcp add tool api-client
mcp add tool file-handler
```

## Tool Development

Example tool structure:

```typescript
import { MCPTool } from "mcp-framework";
import { z } from "zod";

interface MyToolInput {
  message: string;
}

class MyTool extends MCPTool<MyToolInput> {
  name = "my_tool";
  description = "Describes what your tool does";

  schema = {
    message: {
      type: z.string(),
      description: "Description of this input parameter",
    },
  };

  async execute(input: MyToolInput) {
    // Your tool logic here
    return `Processed: ${input.message}`;
  }
}

export default MyTool;
```

## Publishing to npm

1. Update your package.json:
   - Ensure `name` is unique and follows npm naming conventions
   - Set appropriate `version`
   - Add `description`, `author`, `license`, etc.
   - Check `bin` points to the correct entry file

2. Build and test locally:
   ```bash
   npm run build
   npm link
   mcp-framework-server  # Test your CLI locally
   ```

3. Login to npm (create account if necessary):
   ```bash
   npm login
   ```

4. Publish your package:
   ```bash
   npm publish
   ```

After publishing, users can add it to their claude desktop client (read below) or run it with npx
```

## Using with Claude Desktop

### Local Development

Add this configuration to your Claude Desktop config file:

**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mcp-framework-server": {
      "command": "node",
      "args":["/absolute/path/to/mcp-framework-server/dist/index.js"]
    }
  }
}
```

### After Publishing

Add this configuration to your Claude Desktop config file:

**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mcp-framework-server": {
      "command": "npx",
      "args": ["mcp-framework-server"]
    }
  }
}
```

## Building and Testing

1. Make changes to your tools
2. Run `npm run build` to compile
3. The server will automatically load your tools on startup

## Learn More

- [MCP Framework Github](https://github.com/QuantGeekDev/mcp-framework)
- [MCP Framework Docs](https://mcp-framework.com)



---

## FastMCP 2.0 — Research & Migration Notes

This section captures our evaluation of FastMCP 2.0 as an alternative to the current Node/TypeScript `mcp-framework` implementation.

- Docs: https://gofastmcp.com/
- Tools (schemas, annotations, output): https://gofastmcp.com/servers/tools
- PyPI: https://pypi.org/project/fastmcp/

### Why FastMCP

- Pythonic decorator model: `@mcp.tool` turns functions into MCP tools.
- Automatic JSON Schema generation from type hints (helps avoid draft 2020-12 schema issues).
- Built-in HTTP transport; simpler to run without custom session plumbing.
- Structured outputs per MCP 2025-06-18: dicts/dataclasses become machine-readable JSON automatically.
- Async-first with good ergonomics; supports sync tools too.

### Installation (docs reference)

You can install FastMCP in a Python environment (venv/uv/conda). Example with pip:

```bash
pip install fastmcp
fastmcp --version
```

### Minimal Server (HTTP)

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

### Minimal Client (HTTP)

```python
import asyncio
from fastmcp import Client

async def main():
    async with Client("http://localhost:8000/mcp") as client:
        res = await client.call_tool("ping", {"name": "world"})
        print(res)

asyncio.run(main())
```

### Tools: Schemas and Output

- Parameters are derived from function signature + Python type hints (supports `Annotated` and `pydantic.Field` constraints).
- Return values:
  - `dict`/dataclass/Pydantic → structured content automatically (plus traditional text content).
  - Primitive returns (e.g., `int`, `str`) → structured output is generated when a return type is provided (wrapped under `result`) or when `output_schema` is specified.
- Optional annotations for clients (`title`, `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`).

### BookStack Example: List Books Tool

```python
from fastmcp import FastMCP
import os, requests

mcp = FastMCP("BookStack MCP")

@mcp.tool
def bookstack_list_books(offset: int = 0, count: int = 50) -> dict:
    """List books from BookStack"""
    base = os.environ["BS_URL"].rstrip("/")
    url = f"{base}/api/books?offset={offset}&count={count}"
    headers = {
        "Authorization": f"Token {os.environ['BS_TOKEN_ID']}:{os.environ['BS_TOKEN_SECRET']}"
    }
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()
```

### Suggested Migration Plan

1) Create a new Python FastMCP server (e.g., `fastmcp_server/my_server.py`).
2) Implement one BookStack tool first (`bookstack_list_books`) and verify over HTTP via FastMCP client.
3) Port remaining BookStack tools iteratively (list/read/create/update/delete/search/images).
4) Optionally define dataclasses or Pydantic models for structured outputs to get predictable schemas.
5) When ready, update downstream clients (Claude Desktop etc.) to point to the new HTTP endpoint.

### Considerations

- Pin versions for stability in production (e.g., `fastmcp==2.11.x`).
- Choose an HTTP client (`requests` or `httpx`); the example uses `requests`.
- You can run Node and Python servers in parallel during the transition and cut over tool-by-tool.
