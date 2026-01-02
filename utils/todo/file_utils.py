"""
File utilities for todo system.

Single Responsibility: Path management, ID generation, string sanitization.
"""

import glob
import os
import re
from typing import Optional


def get_todos_dir(todos_dir: Optional[str] = None) -> str:
    """Get todos directory path using centralized path management."""
    if todos_dir is not None:
        return todos_dir

    from utils.paths import get_paths

    return str(get_paths().todos_dir)


def get_next_issue_id(todos_dir: Optional[str] = None) -> int:
    """Get next available issue ID by scanning existing todos."""
    todos_dir = get_todos_dir(todos_dir)

    if not os.path.exists(todos_dir):
        os.makedirs(todos_dir, exist_ok=True)
        return 1

    existing_files = glob.glob(os.path.join(todos_dir, "*.md"))
    if not existing_files:
        return 1

    max_id = 0
    for filepath in existing_files:
        filename = os.path.basename(filepath)
        match = re.match(r"^(\d+)-", filename)
        if match:
            max_id = max(max_id, int(match.group(1)))

    return max_id + 1


def sanitize_description(description: str) -> str:
    """Convert description to kebab-case for filename."""
    slug = description.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug[:50]
