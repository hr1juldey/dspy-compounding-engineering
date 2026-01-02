"""
Project-level utilities and constants.

Provides project root detection, project hashing, and context configuration.
"""

import hashlib
import os
import subprocess
from pathlib import Path

# Constants for context management
CONTEXT_WINDOW_LIMIT = int(os.getenv("CONTEXT_WINDOW_LIMIT", "128000"))
CONTEXT_OUTPUT_RESERVE = int(os.getenv("CONTEXT_OUTPUT_RESERVE", "4096"))
DEFAULT_MAX_TOKENS = int(os.getenv("DSPY_MAX_TOKENS", "16384"))

# Tier 1 files - important for quick context inclusion
TIER_1_FILES = [
    "pyproject.toml",
    "README.md",
    "Dockerfile",
    "docker-compose.yml",
    "requirements.txt",
    "package.json",
]

# Vector search configuration
SPARSE_MODEL_NAME = "Qdrant/bm25"
DENSE_FALLBACK_MODEL_NAME = "jinaai/jina-embeddings-v2-small-en"


def get_project_root() -> Path:
    """Get the project root directory, preferably the Git root."""
    try:
        from utils.io.safe import run_safe_command

        result = run_safe_command(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.STDOUT,
            text=True,
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return Path(os.getcwd())


def get_project_hash() -> str:
    """Generate a stable hash for the current project based on its root path."""
    root_path = str(get_project_root().absolute())
    return hashlib.sha256(root_path.encode()).hexdigest()[:16]
