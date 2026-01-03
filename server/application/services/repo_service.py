"""
Application service for repository operations.
"""

from pathlib import Path

from utils.knowledge import KnowledgeBase
from utils.paths import CompoundingPaths


class RepoService:
    """Service for repository management and status."""

    def _get_dir_name_from_env(self, repo_root: str) -> str | None:
        """Read COMPOUNDING_DIR_NAME from target repo's .env file."""
        env_file = Path(repo_root) / ".env"
        if not env_file.exists():
            return None
        try:
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line.startswith("COMPOUNDING_DIR_NAME="):
                    return line.split("=", 1)[1].strip().strip("'\"")
        except Exception:
            pass
        return None

    def initialize_repo(self, repo_root: str, dir_name: str | None = None) -> dict:
        """
        Initialize compounding directory for a repository.

        Args:
            repo_root: Root directory of repository
            dir_name: Name of base directory (e.g., '.claude', '.ce', '.qwen').
                      If None, reads from target repo's .env or defaults to '.claude'.

        Returns:
            Initialization status
        """
        # Priority: explicit param > target repo's .env > default
        if dir_name is None:
            dir_name = self._get_dir_name_from_env(repo_root)

        paths = CompoundingPaths(repo_root, base_dir_name=dir_name)

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
            "compounding_dir": str(paths.base_dir),
            "dir_name": paths.base_dir.name,
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
