"""
FastMCP server for Model Context Protocol.
Exposes CLI functionality via stdio transport.
"""

from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Compounding Engineering MCP Server")

# Import all tool functions to register them with the mcp instance
# (tools are registered via @mcp.tool() decorator when modules are imported)
# NOTE: Must be after mcp instance creation to avoid circular imports
import server.mcp.tools  # noqa: F401, E402

__all__ = ["mcp"]


def get_mcp_server() -> FastMCP:
    """
    Get the configured MCP server instance.

    Returns:
        FastMCP server instance with all tools registered
    """
    return mcp
