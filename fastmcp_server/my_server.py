"""FastMCP entrypoint for the BookStack MCP server."""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from fastmcp import FastMCP

from fastmcp_server.bookstack import register_production_tools

logger = logging.getLogger("bookstack.mcp")

# Load environment variables from .env file
# Look for .env in the parent directory (Bookstack-MCP/)
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"✅ Loaded environment variables from {env_path}")
else:
    logger.info(f"⚠️  No .env file found at {env_path}")
    logger.info("   Make sure BS_URL, BS_TOKEN_ID, and BS_TOKEN_SECRET are set in your environment")


mcp = FastMCP("BookStack MCP (FastMCP)")

logger.info("Registering BookStack production tool stack...")
register_production_tools(mcp)
logger.info(
    "✅ Registered production tools: selective full-featured tools (search, list, "
    "images, observability), simplified content_crud/batch_operations, direct page "
    "tools, and PDF/attachment tools."
)


if __name__ == "__main__":
    # Default to the existing MCP HTTP endpoint so clients do not need reconfiguration.
    mcp.run(transport="http", port=int(os.environ.get("PORT", "3054")))
