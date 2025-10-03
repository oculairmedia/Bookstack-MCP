/**
 * ⚠️ DEPRECATED: This TypeScript/mcp-framework server is deprecated and no longer maintained.
 *
 * Please use the Python FastMCP server instead:
 *   cd fastmcp_server
 *   python3 -m fastmcp_server
 *
 * See src/DEPRECATED.md for migration instructions.
 */

import { MCPServer, HttpStreamTransport } from "mcp-framework";
import { config } from "dotenv";
import type { IncomingMessage, ServerResponse } from "http";

// Load environment variables from .env file
config();

console.warn("⚠️  WARNING: This TypeScript server is DEPRECATED!");
console.warn("⚠️  Please migrate to the Python FastMCP server in fastmcp_server/");
console.warn("⚠️  See src/DEPRECATED.md for migration instructions.\n");

// Import tools - the framework should auto-discover these

// Import Bookstack list tools
import "./tools/BookstackListBooksTool.js";
import "./tools/BookstackListBookshelvesTool.js";
import "./tools/BookstackListChaptersTool.js";
import "./tools/BookstackListPagesTool.js";

// Import Bookstack create tools
import "./tools/BookstackCreateBookTool.js";
import "./tools/BookstackCreateBookshelfTool.js";
import "./tools/BookstackCreateChapterTool.js";
import "./tools/BookstackCreatePageTool.js";

// Import Bookstack read tools
import "./tools/BookstackReadBookTool.js";
import "./tools/BookstackReadBookshelfTool.js";
import "./tools/BookstackReadChapterTool.js";
import "./tools/BookstackReadPageTool.js";

// Import Bookstack update tools
import "./tools/BookstackUpdateBookTool.js";
import "./tools/BookstackUpdateBookshelfTool.js";
import "./tools/BookstackUpdateChapterTool.js";
import "./tools/BookstackUpdatePageTool.js";

// Import Bookstack delete tools
import "./tools/BookstackDeleteBookTool.js";
import "./tools/BookstackDeleteBookshelfTool.js";
import "./tools/BookstackDeleteChapterTool.js";
import "./tools/BookstackDeletePageTool.js";

// Import Bookstack search tools
import "./tools/BookstackSearchTool.js";
import "./tools/BookstackManageImagesTool.js";
import "./tools/BookstackSearchImagesTool.js";

type TransportMode = "http" | "sse";

interface StreamHealthPayload {
  status: string;
  transport: string;
  endpoint: string;
  sessions: number;
  uptime: number;
  timestamp: string;
}

const HTTP_RESPONSE_MODES = new Set(["stream", "batch"]);

let configuredHealthEndpoint = "/health";
let httpTransportPatched = false;

function configureHttpTransportHealth(healthEndpoint: string) {
  configuredHealthEndpoint = healthEndpoint;

  if (httpTransportPatched) {
    return;
  }

  const prototype = (HttpStreamTransport.prototype as unknown) as Record<string, any>;
  const originalStart = prototype.start;

  if (typeof originalStart !== "function") {
    console.warn("HttpStreamTransport.start is not available; health endpoint will not be exposed");
    return;
  }

  prototype.start = async function patchedStart(...args: unknown[]) {
    // Ensure the transport remembers which health endpoint to expose
    if (!this.__healthEndpoint) {
      this.__healthEndpoint = configuredHealthEndpoint;
    }

    await originalStart.apply(this, args);

    const server = this._server as unknown as {
      listeners(event: string): Array<(req: IncomingMessage, res: ServerResponse) => void>;
      removeAllListeners(event: string): void;
      on(event: string, listener: (req: IncomingMessage, res: ServerResponse) => void): void;
    } | undefined;

    if (!server) {
      console.warn("HTTP transport started without an HTTP server; health endpoint unavailable");
      return;
    }

    const existingHandlers = server.listeners("request");
    if (!existingHandlers.length) {
      return;
    }

    const primaryHandler = existingHandlers[0];
    const additionalHandlers = existingHandlers.slice(1);

    server.removeAllListeners("request");

    server.on("request", (req: IncomingMessage, res: ServerResponse) => {
      if (!req.url) {
        primaryHandler.call(server, req, res);
        return;
      }

      const pathname = extractPathname(req.url, req.headers.host ?? "localhost");
      const healthPath = this.__healthEndpoint as string;

      if ((req.method === "GET" || req.method === "HEAD") && pathname === healthPath) {
        const payload: StreamHealthPayload = {
          status: "ok",
          transport: this.type,
          endpoint: this._endpoint,
          sessions: Object.keys(this._transports ?? {}).length,
          uptime: process.uptime(),
          timestamp: new Date().toISOString()
        };

        const headers = {
          "Content-Type": "application/json",
          "Cache-Control": "no-cache"
        } as Record<string, string>;

        if (req.method === "HEAD") {
          res.writeHead(200, headers).end();
        } else {
          res.writeHead(200, headers).end(JSON.stringify(payload));
        }
        return;
      }

      if (req.method === "OPTIONS" && pathname === healthPath) {
        res.writeHead(204, {
          "Access-Control-Allow-Methods": "GET,HEAD,OPTIONS",
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Max-Age": "600"
        }).end();
        return;
      }

      primaryHandler.call(server, req, res);
    });

    for (const handler of additionalHandlers) {
      server.on("request", handler);
    }
  };

  httpTransportPatched = true;
}

function extractPathname(url: string, host: string): string {
  try {
    return new URL(url, `http://${host}`).pathname;
  } catch (error) {
    const [path] = url.split("?");
    return path ?? "/";
  }
}

function parseTransportMode(): TransportMode {
  const args = process.argv.slice(2);
  const hasFlag = (flag: string) => args.includes(flag);

  if (hasFlag("--http")) {
    return "http";
  }

  if (hasFlag("--sse")) {
    return "sse";
  }

  const envTransport = (process.env.TRANSPORT ?? "sse").toLowerCase();
  return envTransport === "http" ? "http" : "sse";
}

function resolveHttpResponseMode(): "stream" | "batch" {
  const envMode = (process.env.HTTP_RESPONSE_MODE ?? "stream").toLowerCase();
  return HTTP_RESPONSE_MODES.has(envMode) ? (envMode as "stream" | "batch") : "stream";
}

function resolveInteger(value: string | undefined, fallback: number): number {
  if (!value) {
    return fallback;
  }

  const parsed = parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

const transportMode = parseTransportMode();
process.env.TRANSPORT = transportMode;

const httpEndpoint = process.env.HTTP_ENDPOINT ?? "/mcp";
const httpHealthEndpoint = process.env.HEALTH_ENDPOINT ?? "/health";
const httpPort = resolveInteger(process.env.PORT, 3001);
const httpResponseMode = resolveHttpResponseMode();

const sseEndpoint = process.env.SSE_ENDPOINT ?? "/sse";
const sseMessageEndpoint = process.env.SSE_MESSAGE_ENDPOINT ?? "/messages";
const ssePort = resolveInteger(process.env.PORT, 8080);

if (transportMode === "http") {
  configureHttpTransportHealth(httpHealthEndpoint);
}

const transportConfig = transportMode === "http"
  ? {
      type: "http-stream" as const,
      options: {
        port: httpPort,
        endpoint: httpEndpoint,
        responseMode: httpResponseMode,
        healthEndpoint: httpHealthEndpoint,

        // Session configuration for proper HTTP transport
        session: {
          enabled: true,
          headerName: "Mcp-Session-Id",
          allowClientTermination: true,
        },

        // Stream resumability for missed messages
        resumability: {
          enabled: false,
          historyDuration: 300000, // 5 minutes
        },

        // CORS configuration
        cors: {
          allowOrigin: "*"
        }
      }
    }
  : {
      type: "sse" as const,
      options: {
        port: ssePort,
        endpoint: sseEndpoint,
        messageEndpoint: sseMessageEndpoint
      }
    };

const activePort = transportMode === "http" ? httpPort : ssePort;
process.env.PORT = String(activePort);

// Log environment and arguments for debugging
console.log("Command line arguments:", process.argv);
console.log(`Environment TRANSPORT: ${process.env.TRANSPORT}`);

if (transportMode === "http") {
  console.log("Starting MCP server with HTTP Stream transport");
  console.log(`Port: ${httpPort}`);
  console.log(`HTTP endpoint: ${httpEndpoint}`);
  console.log(`Health endpoint: ${httpHealthEndpoint}`);
  console.log(`Response mode: ${httpResponseMode}`);
} else {
  console.log("Starting MCP server with SSE transport");
  console.log(`Port: ${ssePort}`);
  console.log(`SSE endpoint: ${sseEndpoint}`);
  console.log(`Messages endpoint: ${sseMessageEndpoint}`);
}

// Create the MCP server with the resolved transport configuration
const server = new MCPServer({
  transport: transportConfig
});

// Start the server with the selected transport
server.start().catch((err: Error) => {
  console.error("Failed to start MCP server:", err);
  process.exitCode = 1;
});
