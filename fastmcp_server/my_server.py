"""FastMCP entrypoint for the BookStack MCP server."""

import logging
import os
from fastmcp_server.bookstack.tools_direct_pages import register_direct_page_tools
from pathlib import Path
from dotenv import load_dotenv
from fastmcp import FastMCP

logger = logging.getLogger("bookstack.mcp")

from fastmcp_server.bookstack import (
    register_simplified_bookstack_tools,
    register_selective_bookstack_tools,
)

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

# Register additional full-featured tools first (search, list, images)
# This will also register the complex manage_content and batch_operations
logger.info("Registering full-featured tools...")
register_selective_bookstack_tools(mcp)

# Then register simplified tools (now named as primary tools without _simple suffix)
# These will replace the complex versions: bookstack_manage_content, bookstack_batch_operations
logger.info("Registering simplified tools (replacing complex versions)...")
register_simplified_bookstack_tools(mcp)

register_direct_page_tools(mcp)
logger.info("✅ Registered direct page tools: bookstack_create_page_direct, bookstack_update_page_direct, bookstack_create_page_from_file, bookstack_update_page_from_file")
logger.info("✅ Registered 7 tools: manage_content, batch_operations, list, search, semantic_search, manage_images, search_images")


if __name__ == "__main__":
    # Default to the existing MCP HTTP endpoint so clients do not need reconfiguration.
    mcp.run(transport="http", port=3054)
