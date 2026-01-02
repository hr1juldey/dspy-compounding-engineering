"""
Todo service - backward compatibility layer.

Re-exports from SOLID-compliant split modules.
This file maintains API compatibility while delegating to focused modules.
"""

# File utilities (path, ID, string operations)
# Analyzer (dependency analysis)
from utils.todo.analyzer import analyze_dependencies

# Creator (create new todos)
from utils.todo.creator import create_finding_todo
from utils.todo.file_utils import (
    get_next_issue_id,
    get_todos_dir,
    sanitize_description,
)

# Parser (read/write todo files)
from utils.todo.parser import atomic_update_todo, parse_todo, serialize_todo

# Query (filter/search todos)
from utils.todo.query import get_ready_todos

# Updater (update/complete todos)
from utils.todo.updater import add_work_log_entry, complete_todo

# Deprecated alias for backward compatibility
_get_todos_dir = get_todos_dir

__all__ = [
    # File utils
    "get_todos_dir",
    "get_next_issue_id",
    "sanitize_description",
    # Parser
    "parse_todo",
    "serialize_todo",
    "atomic_update_todo",
    # Creator
    "create_finding_todo",
    # Updater
    "add_work_log_entry",
    "complete_todo",
    # Query
    "get_ready_todos",
    # Analyzer
    "analyze_dependencies",
    # Deprecated
    "_get_todos_dir",
]
