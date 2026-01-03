"""Centralized path management for compounding engineering system.

This module provides a unified interface for managing all system directories
and files, ensuring the system is portable across different repositories.
"""

import os
from pathlib import Path


class CompoundingPaths:
    """Manages all paths for the compounding engineering system."""

    def __init__(self, repo_root: Path | str | None = None, base_dir_name: str | None = None):
        """
        Initialize path manager.

        Args:
            repo_root: Root of the repository. If None, auto-detect.
            base_dir_name: Name of base directory (e.g., '.ce', '.claude', '.qwen').
                          If None, reads from COMPOUNDING_DIR_NAME env var or defaults to '.ce'.
        """
        if repo_root is None:
            self.repo_root = self._find_repo_root()
        else:
            self.repo_root = Path(repo_root).resolve()

        # Determine base directory name
        dir_name = base_dir_name or os.getenv("COMPOUNDING_DIR_NAME", ".ce")
        self.base_dir = self.repo_root / dir_name
        # Keep claude_dir as alias for backward compatibility
        self.claude_dir = self.base_dir

        # Subdirectories
        self.knowledge_dir = self.base_dir / "knowledge"
        self.plans_dir = self.base_dir / "plans"
        self.todos_dir = self.base_dir / "todos"
        self.cache_dir = self.base_dir / "cache"
        self.analysis_dir = self.base_dir / "analysis"
        self.memory_dir = self.base_dir / "memory"

    def _find_repo_root(self) -> Path:
        """
        Find repository root by looking for .git directory.

        Returns:
            Path to repository root

        Raises:
            ValueError: If no git repository found
        """
        current = Path.cwd()

        # Walk up the directory tree looking for .git
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent

        # If no .git found, use current directory
        # (allows usage in non-git projects)
        return Path.cwd()

    def ensure_directories(self):
        """Create all necessary directories if they don't exist."""
        for directory in [
            self.base_dir,
            self.knowledge_dir,
            self.plans_dir,
            self.todos_dir,
            self.cache_dir,
            self.analysis_dir,
            self.memory_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def get_knowledge_file(self, filename: str) -> Path:
        """Get path to a knowledge file."""
        return self.knowledge_dir / filename

    def get_plan_file(self, filename: str) -> Path:
        """Get path to a plan file."""
        return self.plans_dir / filename

    def get_todo_file(self, filename: str) -> Path:
        """Get path to a todo file."""
        return self.todos_dir / filename

    def get_cache_file(self, filename: str) -> Path:
        """Get path to a cache file."""
        return self.cache_dir / filename

    def get_analysis_file(self, filename: str) -> Path:
        """Get path to an analysis file."""
        return self.analysis_dir / filename

    def migrate_legacy_structure(self):
        """
        Migrate from old structure to configured base directory structure.

        Moves:
        - .knowledge/ → {base_dir}/knowledge/
        - plans/ → {base_dir}/plans/
        - todos/ → {base_dir}/todos/
        - analysis/ → {base_dir}/analysis/
        """
        import shutil

        migrations = [
            (self.repo_root / ".knowledge", self.knowledge_dir),
            (self.repo_root / ".compounding", self.base_dir),
            (self.repo_root / "plans", self.plans_dir),
            (self.repo_root / "todos", self.todos_dir),
            (self.repo_root / "analysis", self.analysis_dir),
        ]

        migrated = []

        for old_path, new_path in migrations:
            if old_path.exists() and not new_path.exists():
                # Ensure parent exists
                new_path.parent.mkdir(parents=True, exist_ok=True)

                # Move directory
                shutil.move(str(old_path), str(new_path))
                migrated.append(f"{old_path.name} → {self.base_dir.name}/{new_path.name}")

        return migrated


# Global singleton instance
_paths_instance = None


def get_paths(repo_root: Path | str | None = None) -> CompoundingPaths:
    """
    Get the global CompoundingPaths instance.

    Args:
        repo_root: Optional repository root. Only used on first call.

    Returns:
        CompoundingPaths instance
    """
    global _paths_instance

    if _paths_instance is None:
        _paths_instance = CompoundingPaths(repo_root)
        _paths_instance.ensure_directories()

    return _paths_instance


def reset_paths():
    """Reset the global paths instance (useful for testing)."""
    global _paths_instance
    _paths_instance = None
