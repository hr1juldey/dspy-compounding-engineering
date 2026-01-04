"""
FastMCP resources for exposing data to clients.

Resources provide read-only access to server data via URI patterns.
"""

from fastmcp import FastMCP

from server.application.services.repo_service import RepoService
from server.config.settings import get_settings

# Resources don't need background tasks - use separate server
resources_server = FastMCP("Resources")


@resources_server.resource("knowledge://{repo_root}/entries")
def get_kb_entries(repo_root: str) -> dict:
    """
    List all knowledge base entries for a repository.

    Args:
        repo_root: Root directory of repository (URL-encoded path)

    Returns:
        Dictionary with entries list and count
    """
    from utils.knowledge import KnowledgeBase
    from utils.paths import CompoundingPaths

    paths = CompoundingPaths(repo_root)
    kb = KnowledgeBase(knowledge_dir=str(paths.knowledge_dir))
    entries = kb.get_all_learnings()

    return {"entries": entries, "count": len(entries), "repo_root": repo_root}


@resources_server.resource("repo://{repo_root}/status")
def get_repo_status_resource(repo_root: str) -> dict:
    """
    Get repository configuration and status.

    Args:
        repo_root: Root directory of repository (URL-encoded path)

    Returns:
        Repository status information
    """
    service = RepoService()
    return service.get_repo_status(repo_root)


@resources_server.resource("system://config")
def get_system_config() -> dict:
    """
    Get current system configuration.

    Returns:
        Dictionary of all server settings (sensitive values excluded)
    """
    settings = get_settings()
    config = settings.model_dump()

    # Exclude potentially sensitive values
    safe_config = {k: v for k, v in config.items() if "key" not in k.lower()}
    return safe_config


@resources_server.resource("system://status")
def get_system_status_resource() -> dict:
    """
    Get current system health status.

    Returns:
        Dictionary with service availability status
    """
    from utils.io import get_system_status

    return get_system_status()


__all__ = [
    "resources_server",
    "get_kb_entries",
    "get_repo_status_resource",
    "get_system_config",
    "get_system_status_resource",
]
