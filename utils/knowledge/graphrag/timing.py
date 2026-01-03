"""
GraphRAG timing cache for indexing time estimation.

Stores historical timing data to predict future indexing duration.
"""

import json

from utils.io.logger import logger
from utils.paths import get_paths


class GraphRAGTimingCache:
    """
    Caches GraphRAG indexing timing data for accurate estimates.

    Stores:
    - Per-file average extraction time
    - Entity count per file
    - Total indexing time
    """

    def __init__(self):
        """Initialize timing cache."""
        paths = get_paths()
        self.cache_file = paths.cache_dir / "graphrag_timing.json"
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_cache()

    def _load_cache(self):
        """Load timing cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load timing cache: {e}")
                self.data = self._get_default_data()
        else:
            self.data = self._get_default_data()

    def _get_default_data(self) -> dict:
        """Get default timing data with conservative estimates."""
        return {
            "per_file_ms": 1200.0,  # Realistic default for GraphRAG:
            # 1200ms per file
            # (AST + entities + embeddings + storage)
            "total_runs": 0,
            "total_files_indexed": 0,
            "total_time_ms": 0,
            "last_updated": None,
        }

    def _save_cache(self):
        """Save timing cache to disk."""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save timing cache: {e}")

    def record_indexing(self, file_path: str, entities_count: int, time_ms: float):
        """
        Record timing data for a single file.

        Args:
            file_path: Path of indexed file
            entities_count: Number of entities extracted
            time_ms: Time taken in milliseconds
        """
        # Update running averages
        self.data["total_files_indexed"] += 1
        self.data["total_time_ms"] += time_ms

        # Recalculate per-file average
        self.data["per_file_ms"] = self.data["total_time_ms"] / self.data["total_files_indexed"]

        # Save periodically (every 10 files)
        if self.data["total_files_indexed"] % 10 == 0:
            self._save_cache()

    def complete_run(self):
        """Mark indexing run as complete and save cache."""
        import datetime

        self.data["total_runs"] += 1
        self.data["last_updated"] = datetime.datetime.now().isoformat()
        self._save_cache()

        logger.info(
            f"Timing cache updated: {self.data['per_file_ms']:.1f}ms per file "
            f"(from {self.data['total_files_indexed']} files)"
        )

    def get_heuristics(self) -> dict:
        """
        Get timing heuristics.

        Returns:
            Dict with per_file_ms and total_runs
        """
        return {
            "per_file_ms": self.data["per_file_ms"],
            "total_runs": self.data["total_runs"],
            "total_files_indexed": self.data["total_files_indexed"],
        }

    def estimate_time(self, file_count: int, estimated_entities: int | None = None) -> float:
        """
        Estimate indexing time for given file count.

        Args:
            file_count: Number of files to index
            estimated_entities: Estimated total entities (optional)

        Returns:
            Estimated time in seconds
        """
        per_file_ms = self.data["per_file_ms"]

        # Simple estimation: file_count * per_file_ms
        total_ms = file_count * per_file_ms

        # Convert to seconds
        return total_ms / 1000.0

    def reset(self):
        """Reset timing cache to defaults."""
        self.data = self._get_default_data()
        self._save_cache()
        logger.info("Timing cache reset to defaults")
