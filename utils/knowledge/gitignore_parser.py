"""
Parse .gitignore patterns and filter files accordingly.

Provides unified filtering logic across all indexers to avoid DRY violations.
"""

from pathlib import Path
from typing import Set


class GitignoreParser:
    """Parse and apply .gitignore patterns with override support."""

    def __init__(self, root_dir: str | Path, force_include: Set[str] | None = None):
        """
        Initialize gitignore parser.

        Args:
            root_dir: Root directory to search for .gitignore
            force_include: Directories to index even if in .gitignore
        """
        self.root_dir = Path(root_dir)
        self.force_include = force_include or {".ce", ".claude", ".qwen"}
        self.ignore_patterns = self._load_gitignore()

    def _load_gitignore(self) -> Set[str]:
        """Load patterns from .gitignore at root."""
        patterns = set()
        gitignore_path = self.root_dir / ".gitignore"

        if not gitignore_path.exists():
            return patterns

        try:
            with open(gitignore_path) as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue
                    # Normalize pattern (remove trailing slash)
                    pattern = line.rstrip("/")
                    patterns.add(pattern)
        except Exception as e:
            from utils.io.logger import logger

            logger.warning(f"Failed to load .gitignore: {e}")

        return patterns

    def should_ignore(self, file_path: Path) -> bool:
        """
        Check if file should be ignored.

        Args:
            file_path: Path to check (relative to root)

        Returns:
            True if should be ignored, False if should be included
        """
        # Check force_include first
        for part in file_path.parts:
            if part in self.force_include:
                return False

        # Check against ignore patterns
        for pattern in self.ignore_patterns:
            # Pattern matches if any path component matches
            for part in file_path.parts:
                if part == pattern or part.startswith(pattern + "/"):
                    return True
            # Also check if pattern matches the full path
            if str(file_path).startswith(pattern):
                return True

        return False

    def filter_files(self, files: list[Path] | list[str]) -> list[Path]:
        """
        Filter files based on .gitignore patterns.

        Args:
            files: List of file paths (str or Path)

        Returns:
            Filtered list of paths that should be indexed
        """
        result = []
        for f in files:
            path = Path(f) if isinstance(f, str) else f
            # Make relative to root for consistent checking
            try:
                rel_path = path.relative_to(self.root_dir)
            except ValueError:
                rel_path = path

            if not self.should_ignore(rel_path):
                result.append(path)

        return result
