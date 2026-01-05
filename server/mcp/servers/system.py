"""
System subserver - system operations and meta-commands.

Contains tools for system status, configuration, triage, and command generation.
"""

import asyncio
import os

from fastmcp import FastMCP
from infrastructure.events.decorators import track_tool_execution

from utils.paths import get_paths, reset_paths
from workflows.generate_command import run_generate_command
from workflows.triage import run_triage

system_server = FastMCP("System")


@system_server.tool(task=True)  # SLOW: background if client supports (optional mode)
@track_tool_execution(total_stages=2)
async def triage_issues(
    repo_root: str,
    pattern: str | None = None,
    dry_run: bool = False,
    ctx=None,
) -> dict:
    """
    Triage and categorize codebase issues.

    Args:
        repo_root: Root directory of repository
        pattern: Optional pattern to filter issues (e.g., 'security', 'performance')
        dry_run: Preview mode without creating todos

    Returns:
        Triage result dictionary
    """
    reset_paths()
    get_paths(repo_root)

    try:
        if ctx:
            await ctx.report_progress(progress=2, total=2, message="Triaging issues...")

        result = await asyncio.wait_for(
            asyncio.to_thread(run_triage, pattern=pattern, dry_run=dry_run),
            timeout=600,  # 10 minutes
        )

        return {"success": True, "result": result, "pattern": pattern, "dry_run": dry_run}

    except asyncio.TimeoutError:
        if ctx:
            ctx.logger.error("Issue triage timed out after 10 minutes")
        raise
    except Exception as e:
        if ctx:
            ctx.logger.error(f"Issue triage failed: {e}")
        raise


@system_server.tool(task=True)  # SLOW: background if client supports (optional mode)
@track_tool_execution(total_stages=2)
async def generate_command(
    repo_root: str,
    description: str,
    dry_run: bool = False,
    ctx=None,
) -> dict:
    """
    Generate new CLI command from natural language description.

    Args:
        repo_root: Root directory of repository
        description: Natural language description of command to create
        dry_run: Preview mode without creating files

    Returns:
        Command generation result dictionary
    """
    reset_paths()
    get_paths(repo_root)

    try:
        if ctx:
            await ctx.report_progress(progress=2, total=2, message="Generating command...")

        result = await asyncio.wait_for(
            asyncio.to_thread(run_generate_command, description=description, dry_run=dry_run),
            timeout=600,  # 10 minutes
        )

        return {"success": True, "result": result, "description": description, "dry_run": dry_run}

    except asyncio.TimeoutError:
        if ctx:
            ctx.logger.error("Command generation timed out after 10 minutes")
        raise
    except Exception as e:
        if ctx:
            ctx.logger.error(f"Command generation failed: {e}")
        raise


@system_server.tool()
def get_system_status(repo_root: str) -> dict:
    """
    Get system diagnostics (synchronous - returns immediately).

    Checks status of Qdrant, Redis, Ollama, and repository configuration.

    Args:
        repo_root: Root directory of repository

    Returns:
        System status information
    """
    from utils.io import get_system_status as get_status

    status_text = get_status()
    return {"success": True, "status_text": status_text, "repo_root": repo_root}


@system_server.tool()
def configure_llm(provider: str, model: str) -> dict:
    """
    Configure LLM provider and model for autonomous agent (synchronous).

    Args:
        provider: LLM provider (ollama, openai, anthropic)
        model: Model name (e.g., qwen2.5:7b, gpt-4, claude-3.5-sonnet)

    Returns:
        Configuration confirmation
    """
    os.environ["DSPY_LM_PROVIDER"] = provider
    os.environ["DSPY_LM_MODEL"] = model

    from server.api.v1.config import update_env_file

    update_env_file({"DSPY_LM_PROVIDER": provider, "DSPY_LM_MODEL": model})

    return {
        "success": True,
        "provider": provider,
        "model": model,
        "message": "LLM configuration updated (restart may be required)",
    }
