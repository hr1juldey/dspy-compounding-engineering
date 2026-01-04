"""
System subserver - system operations and meta-commands.

Contains tools for system status, configuration, triage, and command generation.
"""

import asyncio
import os

from fastmcp import FastMCP

from utils.paths import CompoundingPaths
from workflows.generate_command import run_generate_command
from workflows.triage import run_triage

system_server = FastMCP("System")


@system_server.tool(task=True)  # SLOW: background if client supports (optional mode)
async def triage_issues(
    repo_root: str,
    pattern: str | None = None,
    dry_run: bool = False,
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
    CompoundingPaths(repo_root)

    try:
        result = await asyncio.to_thread(run_triage, pattern=pattern, dry_run=dry_run)

        return {"success": True, "result": result, "pattern": pattern, "dry_run": dry_run}

    except Exception as e:
        return {"success": False, "error": str(e), "pattern": pattern}


@system_server.tool(task=True)  # SLOW: background if client supports (optional mode)
async def generate_command(
    repo_root: str,
    description: str,
    dry_run: bool = False,
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
    CompoundingPaths(repo_root)

    try:
        result = await asyncio.to_thread(
            run_generate_command, description=description, dry_run=dry_run
        )

        return {"success": True, "result": result, "description": description, "dry_run": dry_run}

    except Exception as e:
        return {"success": False, "error": str(e), "description": description}


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
