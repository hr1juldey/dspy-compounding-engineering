"""
MCP tool definitions.

Legacy tools moved to subservers:
- analysis → server/mcp/servers/analysis.py
- execution → server/mcp/servers/execution.py
- knowledge → server/mcp/servers/knowledge.py
- system → server/mcp/servers/system.py

Only repository tools remain here (fast, sync operations).
"""

from server.mcp.tools.repository import repository_server

__all__ = ["repository_server"]
