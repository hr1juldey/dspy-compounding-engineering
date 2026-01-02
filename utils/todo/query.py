"""
Todo query module.

Single Responsibility: Query and filter todo files.
"""

import glob
import os
import re
from typing import List, Optional

from utils.todo.file_utils import get_todos_dir
from utils.todo.parser import parse_todo


def get_ready_todos(todos_dir: Optional[str] = None, pattern: Optional[str] = None) -> List[str]:
    """
    Find all ready todos, optionally filtered by pattern.

    Args:
        todos_dir: Directory containing todos
        pattern: Optional regex pattern to filter filenames

    Returns:
        List of absolute file paths
    """
    todos_dir = get_todos_dir(todos_dir)

    if not os.path.exists(todos_dir):
        return []

    files = glob.glob(os.path.join(todos_dir, "*.md"))
    ready_todos = []

    for f in files:
        if pattern and not re.search(pattern, os.path.basename(f)):
            continue

        try:
            parsed = parse_todo(f)
            fm = parsed["frontmatter"]
            if fm.get("status") == "ready":
                ready_todos.append(os.path.abspath(f))
        except Exception:
            continue

    return sorted(ready_todos)
