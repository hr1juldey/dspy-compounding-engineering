"""
Application service for repository operations.
"""

from utils.knowledge import KnowledgeBase
from utils.paths import CompoundingPaths


class RepoService:
    """Service for repository management and status."""

    def initialize_repo(self, repo_root: str) -> dict:
        """
        Initialize .compounding directory for a repository.

        Args:
            repo_root: Root directory of repository

        Returns:
            Initialization status
        """
        paths = CompoundingPaths(repo_root)

        # Create all required directories
        paths.claude_dir.mkdir(parents=True, exist_ok=True)
        paths.knowledge_dir.mkdir(exist_ok=True)
        paths.plans_dir.mkdir(exist_ok=True)
        paths.todos_dir.mkdir(exist_ok=True)
        paths.cache_dir.mkdir(exist_ok=True)
        paths.analysis_dir.mkdir(exist_ok=True)
        paths.memory_dir.mkdir(exist_ok=True)

        return {
            "success": True,
            "repo_root": str(paths.repo_root),
            "claude_dir": str(paths.claude_dir),
            "initialized": True,
        }

    def get_repo_status(self, repo_root: str) -> dict:
        """
        Get status of repository knowledge base and configuration.

        Args:
            repo_root: Root directory of repository

        Returns:
            Status dictionary
        """
        paths = CompoundingPaths(repo_root)

        # Check if .compounding exists
        exists = paths.claude_dir.exists()

        status = {
            "repo_root": str(paths.repo_root),
            "claude_dir_exists": exists,
            "paths": {
                "knowledge": str(paths.knowledge_dir),
                "plans": str(paths.plans_dir),
                "todos": str(paths.todos_dir),
                "analysis": str(paths.analysis_dir),
            },
        }

        if exists:
            # Get knowledge base stats
            try:
                kb = KnowledgeBase()
                status["knowledge_base"] = {
                    "available": True,
                    "entries": kb.get_entry_count() if hasattr(kb, "get_entry_count") else 0,
                }
            except Exception as e:
                status["knowledge_base"] = {"available": False, "error": str(e)}

        return status
