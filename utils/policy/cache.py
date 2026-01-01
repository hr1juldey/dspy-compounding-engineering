"""File-based cache for policy validation results."""

import hashlib
import json
import time
from pathlib import Path

from utils.policy.violations import PolicyResult


class PolicyCache:
    """TTL-based cache for policy validation."""

    def __init__(self, cache_dir: Path, ttl_seconds: int = 3600):
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file content."""
        return hashlib.sha256(file_path.read_bytes()).hexdigest()

    def get(self, file_path: Path) -> PolicyResult | None:
        """Get cached result if valid."""
        file_hash = self._file_hash(file_path)
        cache_file = self.cache_dir / f"{file_hash}.json"

        if not cache_file.exists():
            return None

        cache_age = time.time() - cache_file.stat().st_mtime
        if cache_age > self.ttl_seconds:
            cache_file.unlink()
            return None

        with open(cache_file) as f:
            data = json.load(f)
        return PolicyResult(**data)

    def set(self, file_path: Path, result: PolicyResult):
        """Cache validation result."""
        file_hash = self._file_hash(file_path)
        cache_file = self.cache_dir / f"{file_hash}.json"

        with open(cache_file, "w") as f:
            json.dump(result.model_dump(), f)
