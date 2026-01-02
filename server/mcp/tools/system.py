"""
MCP tools for system operations and meta-commands.
"""

from server.application.services.generate_command_service import GenerateCommandService
from server.application.services.triage_service import TriageService
from server.mcp.server import mcp


@mcp.tool()
def triage_issues(repo_root: str, pattern: str | None = None, dry_run: bool = False) -> dict:
    """
    Triage and categorize codebase issues (async - returns task_id).

    Args:
        repo_root: Root directory of repository
        pattern: Optional pattern to filter issues (e.g., 'security', 'performance')
        dry_run: Preview mode without creating todos

    Returns:
        Task submission info with task_id
    """
    service = TriageService()
    task_id = service.submit_triage(repo_root=repo_root, pattern=pattern, dry_run=dry_run)
    return {"task_id": task_id, "status": "submitted"}


@mcp.tool()
def generate_command(repo_root: str, description: str, dry_run: bool = False) -> dict:
    """
    Generate new CLI command from natural language (async - returns task_id).

    Args:
        repo_root: Root directory of repository
        description: Natural language description of command to create
        dry_run: Preview mode without creating files

    Returns:
        Task submission info with task_id
    """
    service = GenerateCommandService()
    task_id = service.submit_generation(
        repo_root=repo_root, description=description, dry_run=dry_run
    )
    return {"task_id": task_id, "status": "submitted"}


@mcp.tool()
def get_system_status(repo_root: str) -> dict:
    """
    Get system diagnostics (synchronous - returns immediately).

    Checks status of:
    - Qdrant vector database
    - Redis (Celery broker)
    - Ollama LLM
    - Repository configuration

    Args:
        repo_root: Root directory of repository

    Returns:
        System status information
    """
    from utils.io import get_system_status as get_status

    status_text = get_status()

    return {"success": True, "status_text": status_text, "repo_root": repo_root}


@mcp.tool()
def configure_llm(provider: str, model: str) -> dict:
    """
    Configure LLM provider and model for autonomous agent (synchronous).

    Allows MCP users to choose their LLM (e.g., Ollama instead of Claude).

    Args:
        provider: LLM provider (ollama, openai, anthropic)
        model: Model name (e.g., qwen2.5:7b, gpt-4, claude-3.5-sonnet)

    Returns:
        Configuration confirmation
    """
    import os

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
