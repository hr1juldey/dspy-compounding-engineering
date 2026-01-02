"""
MCP tool definitions.
Each tool delegates to application services.
"""

# Import all tool modules to register tools with MCP server
import server.mcp.tools.analysis  # noqa: F401
import server.mcp.tools.execution  # noqa: F401
import server.mcp.tools.knowledge  # noqa: F401
import server.mcp.tools.repository  # noqa: F401
import server.mcp.tools.system  # noqa: F401

__all__ = [
    "analysis",
    "execution",
    "knowledge",
    "repository",
    "system",
]
