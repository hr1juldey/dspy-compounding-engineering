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
import sys
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from server.config.settings import get_settings
from server.mcp.sampling_handler import sampling_handler

# Configure Docket backend URL from settings (must be set before FastMCP init)
settings = get_settings()
os.environ.setdefault("FASTMCP_DOCKET_URL", settings.fastmcp_docket_url)


@asynccontextmanager
async def mcp_lifespan(mcp: FastMCP):
    """
    MCP server lifespan: startup and shutdown logic.

    Startup:
    - Configure logging
    - Configure DSPy (LM and settings)
    - Optionally run warmup (controlled by MCP_WARMUP_ENABLED)

    Shutdown:
    - Clean up resources if needed
    """
    from server.config import configure_dspy
    from server.config.logging import configure_logging

    # Startup
    print("Initializing MCP server...", file=sys.stderr)

    # Step 1: Configure logging
    configure_logging(level="INFO")

    # Step 2: Configure DSPy (REQUIRED - fast, ~1-2s)
    print("Configuring DSPy LM...", file=sys.stderr)
    try:
        configure_dspy()
        print("✓ DSPy LM configured", file=sys.stderr)
    except Exception as e:
        print(f"✗ Failed to configure DSPy: {e}", file=sys.stderr)
        print("Warning: Tools requiring LLM will fail", file=sys.stderr)

    # Step 3: Warmup (SLOW, 60-120s for Ollama)
    # Default: true for HTTP (long-lived), set to false for fast development restarts
    warmup_enabled = os.getenv("MCP_WARMUP_ENABLED", "true").lower() not in ("false", "0", "no")
    if warmup_enabled:
        print(
            "Starting warmup (may take 60-120s for Ollama model loading)...",
            file=sys.stderr,
        )
        try:
            from utils.knowledge.utils.warmup import WarmupTest

            warmup = WarmupTest()
            await asyncio.to_thread(warmup.run_all)
            print("✓ Warmup complete - LLM and embedder ready", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Warmup failed: {e}", file=sys.stderr)
            print("Tools will still work but first call may be slow", file=sys.stderr)
    else:
        print("Warmup disabled (set MCP_WARMUP_ENABLED=true to enable)", file=sys.stderr)
        print("Note: First tool call may take 60-120s for model loading", file=sys.stderr)

    print("MCP server ready", file=sys.stderr)

    yield

    # Shutdown
    print("Shutting down MCP server...", file=sys.stderr)


# Initialize FastMCP server with background task support, sampling fallback, and lifespan
mcp = FastMCP(
    "Compounding Engineering MCP Server",
    tasks=True,
    sampling_handler=sampling_handler,
    sampling_handler_behavior="fallback",  # Use DSPy when client lacks sampling
    lifespan=mcp_lifespan,
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
