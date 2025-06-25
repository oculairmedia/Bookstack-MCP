import { MCPServer } from "mcp-framework";
import { config } from "dotenv";

// Load environment variables from .env file
config();

// Import tools - the framework should auto-discover these
import "./tools/ExampleToolTool.js";

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

// Force SSE transport if not set
if (!process.env.TRANSPORT) {
  process.env.TRANSPORT = "sse";
}

// Log environment and arguments for debugging
console.log("Command line arguments:", process.argv);
console.log(`Environment PORT: ${process.env.PORT}`);
console.log(`Environment TRANSPORT: ${process.env.TRANSPORT}`);

// Create the MCP server
const server = new MCPServer({
  transport: {
    type: "sse",
    options: {
      port: process.env.PORT ? parseInt(process.env.PORT) : 8080,
      endpoint: "/sse",
      messageEndpoint: "/messages"
    }
  }
});

// Log the server configuration
console.log("Starting MCP server with SSE transport");
console.log(`Port: ${process.env.PORT || 8080}`);
console.log(`SSE endpoint: /sse`);
console.log(`Messages endpoint: /messages`);

// Start the server with the transport
server.start().catch((err: Error) => {
  console.error("Failed to start MCP server:", err);
});