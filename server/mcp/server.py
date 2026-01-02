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


if __name__ == "__main__":
    import sys

    # Determine transport based on environment or args
    # Primary: stdio (default) - standard MCP protocol via stdin/stdout
    # Backup: http (12001) or streamable-http - for clients that need HTTP
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 12001

    # Run MCP server
    # - stdio: Default JSON-RPC stdio (primary transport, standard MCP)
    # - http: Standard HTTP transport on port 12001 (backup/fallback)
    # - streamable-http: Production HTTP with streaming on port 12001 (recommended for production)
    if transport in ("http", "streamable-http"):
        print(
            f"Starting MCP server on HTTP :{port} (transport={transport})",
            file=sys.stderr,
        )
        mcp.run(transport=transport, host="0.0.0.0", port=port)
    else:
        print("Starting MCP server on stdio (primary transport)", file=sys.stderr)
        mcp.run()
