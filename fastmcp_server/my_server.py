"""FastMCP entrypoint for the BookStack MCP server."""

from fastmcp import FastMCP

from fastmcp_server.bookstack import register_bookstack_tools


mcp = FastMCP("BookStack MCP (FastMCP)")

register_bookstack_tools(mcp)


if __name__ == "__main__":
    # Default to the existing MCP HTTP endpoint so clients do not need reconfiguration.
    mcp.run(transport="http", port=3054)
