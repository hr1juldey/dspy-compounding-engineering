"""
FastMCP server for Model Context Protocol.
Exposes CLI functionality via stdio transport.
"""

from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Compounding Engineering MCP Server")

# Import all tool functions to register them
# (tools are registered via @mcp.tool() decorator in tools.py)
__all__ = ["mcp"]


def get_mcp_server() -> FastMCP:
    """
    Get the configured MCP server instance.

    Returns:
        FastMCP server instance
    """
    return mcp


if __name__ == "__main__":
    # Run MCP server via stdio transport
    mcp.run()
