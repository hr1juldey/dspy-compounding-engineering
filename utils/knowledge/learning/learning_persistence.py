"""
Learning persistence to disk with atomic writes.

Handles safe, atomic storage of learning JSON files using FileLock and temp files.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from filelock import FileLock


class LearningPersistence:
    """
    Handles atomic persistence of learnings to JSON files.

    Single Responsibility: Ensure learnings are safely written to disk
    using atomic operations (temp file + rename) and file locks.
    """

    def __init__(self, knowledge_dir: str):
        """
        Initialize persistence manager.

        Args:
            knowledge_dir: Directory where learnings are stored
        """
        self.knowledge_dir = knowledge_dir
        Path(knowledge_dir).mkdir(parents=True, exist_ok=True)

    def save_to_disk(self, learning: Dict[str, Any]) -> str:
        """
        Save learning to disk atomically using FileLock.

        Args:
            learning: Learning dictionary with 'id', 'category', etc.

        Returns:
            Path to saved learning file

        Raises:
            Exception: If save fails
        """
        learning_id = learning.get("id") or self.generate_learning_id()
        category = learning.get("category", "general").lower().replace(" ", "-")
        filename = f"{learning_id}-{category}.json"
        filepath = os.path.join(self.knowledge_dir, filename)

        # Add metadata
        learning["id"] = learning_id
        if "created_at" not in learning:
            learning["created_at"] = datetime.now().isoformat()

        # Atomic write with lock
        lock_path = os.path.join(self.knowledge_dir, "kb.lock")
        lock = FileLock(lock_path, timeout=10)

        try:
            with lock:
                # Atomic: write to temp, then rename
                tmp_path = filepath + ".tmp"
                with open(tmp_path, "w") as f:
                    json.dump(learning, f, indent=2)
                os.replace(tmp_path, filepath)

            return filepath
        except Exception as e:
            # Clean up temp file if write failed
            tmp_path = filepath + ".tmp"
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise e

    def generate_learning_id(self) -> str:
        """Generate unique learning ID with timestamp + random bytes."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        random_suffix = os.urandom(4).hex()
        return f"{timestamp}-{random_suffix}"

    def get_filename(self, learning_id: str, category: str) -> str:
        """Generate filename from ID and category."""
        safe_category = category.lower().replace(" ", "-")
        return f"{learning_id}-{safe_category}.json"
