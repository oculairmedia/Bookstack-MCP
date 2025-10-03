# HTTP Transport for Bookstack MCP Server

> **⚠️ DEPRECATED**: This document describes the deprecated TypeScript/mcp-framework server. The Python FastMCP server uses HTTP transport by default. See the main [README.md](README.md) for current documentation.

This document describes the HTTP transport implementation for the **deprecated** TypeScript Bookstack MCP server, based on the MCP Streamable HTTP protocol (version 2025-06-18).

## Features

- **Streamable HTTP transport**: Supports the MCP 2025-06-18 protocol with streaming capabilities
- **Session management**: Maintains persistent sessions across requests
- **Security**: Origin validation and DNS rebinding protection
- **Health checks**: Built-in health endpoint for monitoring
- **Recovery support**: In-memory event store for session recovery
- **CORS support**: Configured for local development and production use

## Running with HTTP Transport

### Using npm scripts

```bash
# Production mode (after building)
npm run start:http
```

### Using Docker

```bash
# Build and run with HTTP transport
docker-compose -f docker-compose.http.yml up --build

# Or set environment variable
TRANSPORT=http docker-compose up --build
```

### Direct command

```bash
# From the everything directory
node src/index.js --http

# Or from dist after building
node dist/index.js --http
```

## Endpoints

- **POST /mcp**: Main MCP endpoint for JSON-RPC requests
- **GET /mcp**: SSE streaming endpoint for responses
- **DELETE /mcp**: Session termination endpoint
- **GET /health**: Health check endpoint

## Configuration

Environment variables:
- `PORT`: Server port (default: 3001 when `TRANSPORT=http`)
- `HTTP_ENDPOINT`: Override the MCP endpoint path (default: `/mcp`)
- `HEALTH_ENDPOINT`: Override the health endpoint path (default: `/health`)
- `HTTP_RESPONSE_MODE`: `stream` (default) or `batch`
- `BS_URL`: Bookstack API URL
- `BS_TOKEN_ID`: Bookstack API token ID
- `BS_TOKEN_SECRET`: Bookstack API token secret

## Client Configuration

To connect to the HTTP transport, configure your MCP client:

```json
{
  "mcpServers": {
    "bookstack": {
      "url": "http://localhost:3001/mcp",
      "transport": {
        "type": "http",
        "config": {
          "url": "http://localhost:3001/mcp"
        }
      }
    }
  }
}
```

## Security Features

1. **Origin Validation**: Only allows requests from configured origins
2. **DNS Rebinding Protection**: Validates Host headers
3. **Protocol Version Check**: Ensures compatible MCP protocol versions
4. **Session Isolation**: Each client gets a unique session ID

## Differences from SSE Transport

- HTTP transport supports request/response streaming
- Better suited for cloud deployments and proxies
- Supports session recovery through event store
- More robust error handling and reconnection logic
