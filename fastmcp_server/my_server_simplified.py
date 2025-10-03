"""FastMCP server with simplified BookStack tools to avoid MCP schema size limits."""

import os
from pathlib import Path
from dotenv import load_dotenv
from fastmcp import FastMCP

from fastmcp_server.bookstack import register_simplified_bookstack_tools

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment variables from {env_path}")
else:
    print(f"⚠️  No .env file found at {env_path}")
    print("   Make sure BS_URL, BS_TOKEN_ID, and BS_TOKEN_SECRET are set in your environment")

mcp = FastMCP("BookStack MCP (Simplified)")

# Register simplified tools that avoid deep schema nesting
register_simplified_bookstack_tools(mcp)


if __name__ == "__main__":
    # Default to the existing MCP HTTP endpoint so clients do not need reconfiguration.
    mcp.run(transport="http", port=3055)  # Use different port to avoid conflict

