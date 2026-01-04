"""
FastMCP subservers for tool composition.

Each subserver groups related tools by domain:
- analysis: GraphRAG code analysis and planning
- knowledge: Knowledge base management
- execution: Code execution, review, and policy checking
- system: System operations and meta-commands
"""

from server.mcp.servers.analysis import analysis_server
from server.mcp.servers.execution import execution_server
from server.mcp.servers.knowledge import knowledge_server
from server.mcp.servers.system import system_server

__all__ = [
    "analysis_server",
    "execution_server",
    "knowledge_server",
    "system_server",
]
