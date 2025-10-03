#!/usr/bin/env python3
"""Stdio launcher for MCP Inspector.

This script runs the BookStack FastMCP server with stdio transport,
which is required for the MCP Inspector to connect and test the server.

Usage:
    npx @modelcontextprotocol/inspector python run_stdio.py
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import fastmcp_server
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment variables from {env_path}", file=sys.stderr)
else:
    print(f"⚠️  No .env file found at {env_path}", file=sys.stderr)
    print("   Make sure BS_URL, BS_TOKEN_ID, and BS_TOKEN_SECRET are set in your environment", file=sys.stderr)

from fastmcp import FastMCP
from fastmcp_server.bookstack import register_bookstack_tools


def main():
    """Run the FastMCP server with stdio transport."""
    mcp = FastMCP("BookStack MCP (FastMCP)")
    
    # Register all BookStack tools
    register_bookstack_tools(mcp)
    
    # Run with stdio transport for MCP Inspector
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

