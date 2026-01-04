"""
FastMCP server for Model Context Protocol.

Exposes CLI functionality via stdio transport with:
- Background tasks via Docket (Redis-backed)
- Prompts for structured LLM interactions
- Resources for data exposure
- Sampling fallback using CE's LM configuration
"""

import asyncio
import os

from fastmcp import FastMCP

from server.config.settings import get_settings
from server.mcp.sampling_handler import sampling_handler

# Configure Docket backend URL from settings (must be set before FastMCP init)
settings = get_settings()
os.environ.setdefault("FASTMCP_DOCKET_URL", settings.fastmcp_docket_url)

# Initialize FastMCP server with background task support and sampling fallback
mcp = FastMCP(
    "Compounding Engineering MCP Server",
    tasks=True,
    sampling_handler=sampling_handler,
    sampling_handler_behavior="fallback",  # Use DSPy when client lacks sampling
)

# Import subservers for composition
from server.mcp.prompts import prompts_server  # noqa: E402
from server.mcp.resources import resources_server  # noqa: E402
from server.mcp.servers import (  # noqa: E402
    analysis_server,
    execution_server,
    knowledge_server,
    system_server,
)
from server.mcp.tools import repository_server  # noqa: E402


async def setup_server():
    """Compose subservers into main server (called at startup)."""
    # Import prompts and resources (no tasks)
    await mcp.import_server(prompts_server)
    await mcp.import_server(resources_server)

    # Import repository tools (sync, fast operations)
    await mcp.import_server(repository_server)

    # Import subservers WITHOUT prefix to keep original tool names
    await mcp.import_server(analysis_server)  # analyze_code, generate_plan
    await mcp.import_server(knowledge_server)  # index_codebase, garden_knowledge, etc.
    await mcp.import_server(execution_server)  # execute_work, review_code, check_policies
    await mcp.import_server(system_server)  # triage_issues, generate_command, etc.


# Run setup when module loads
asyncio.run(setup_server())

__all__ = ["mcp"]


def get_mcp_server() -> FastMCP:
    """
    Get the configured MCP server instance.

    Returns:
        FastMCP server instance with all tools registered
    """
    return mcp
