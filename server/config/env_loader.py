"""
Environment configuration loader.

Loads environment variables from multiple sources in priority order.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from server.config.project import get_project_root
from utils.io.logger import console


def load_configuration(env_file: str | None = None) -> None:
    """Load environment variables from multiple sources in priority order.

    Sources (in priority order):
    1. Explicit env_file parameter
    2. COMPOUNDING_ENV environment variable
    3. .env in project root
    4. .env in current working directory
    5. .env in ~/.config/compounding/
    6. .env in home directory

    Args:
        env_file: Optional explicit path to .env file

    Raises:
        SystemExit: If explicit env_file is provided but not found
    """
    root = get_project_root()
    home = Path.home()
    config_dir = home / ".config" / "compounding"

    # Define sources in priority order
    sources = [
        env_file,
        os.getenv("COMPOUNDING_ENV"),
        root / ".env",
        Path.cwd() / ".env",
        config_dir / ".env",
        home / ".env",
    ]

    seen_paths = set()
    for path_val in sources:
        if not path_val:
            continue

        path = Path(path_val).resolve()
        if path in seen_paths:
            continue

        if path.exists():
            # Override keys if primary source, otherwise fill in gaps
            is_primary = not seen_paths
            load_dotenv(dotenv_path=path, override=is_primary)
            seen_paths.add(path)
        elif path_val == env_file:
            console.print(f"[bold red]Error:[/bold red] Env file '{env_file}' not found.")
            sys.exit(1)
