"""GraphRAG Indexer - orchestrates entity extraction via service layer."""

import asyncio
import os
import time
from pathlib import Path
from typing import Callable, Optional

from utils.io.logger import logger
from utils.knowledge.graphrag.async_indexer import GraphRAGAsync
from utils.knowledge.graphrag.entities import EntityExtractor
from utils.knowledge.graphrag.graph_store import GraphStore
from utils.knowledge.graphrag.sequential import GraphRAGSequential
from utils.knowledge.graphrag.timing import GraphRAGTimingCache


class GraphRAGIndexer:
    """Orchestrates entity extraction via async/sequential strategies."""

    def __init__(self, graph_store: GraphStore):
        """Initialize with graph store."""
        self.graph_store = graph_store
        self.entity_extractor = EntityExtractor()
        self.timing_cache = GraphRAGTimingCache()

    def index_codebase(
        self,
        root_dir: str | Path,
        force_recreate: bool = False,
        progress_callback: Optional[Callable] = None,
    ) -> dict:
        """Index codebase for GraphRAG (async or sequential)."""
        start_time = time.time()
        root_path = Path(root_dir)
        all_files = list(root_path.rglob("*.py"))

        if not all_files:
            logger.warning(f"No Python files in {root_dir}")
            return {"files": 0, "entities": 0, "time_sec": 0.0}

        if force_recreate:
            logger.info("Force recreating GraphRAG collection")
            self.graph_store._ensure_collection(force_recreate=True)

        # Filter files using .gitignore patterns
        from utils.knowledge.utils.gitignore_parser import GitignoreParser

        gitignore = GitignoreParser(root_dir)
        python_files = gitignore.filter_files(all_files)

        logger.info(f"Indexing {len(python_files)} Python files for GraphRAG")

        # Choose async or sequential mode
        use_async = os.getenv("USE_ASYNC_GRAPHRAG", "true").lower() == "true"

        if use_async:
            # Use async indexing for 5-20x speedup
            async_indexer = GraphRAGAsync(
                self.entity_extractor, self.graph_store, self.timing_cache, max_concurrent=10
            )
            stats = asyncio.run(async_indexer.index_files(python_files, progress_callback))
        else:
            # Use sequential fallback (debugging/rollback)
            sequential_indexer = GraphRAGSequential(
                self.entity_extractor, self.graph_store, self.timing_cache
            )
            stats = sequential_indexer.index_files(python_files, progress_callback)

        # Complete timing cache
        self.timing_cache.complete_run()

        elapsed_time = time.time() - start_time
        stats["time_sec"] = elapsed_time

        logger.success(
            f"GraphRAG indexing complete: {stats['files']} files, "
            f"{stats['entities']} entities in {elapsed_time:.1f}s"
        )

        return stats

    def index_file(self, file_path: str | Path) -> int:
        """Index single file for GraphRAG."""
        path = Path(file_path)

        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return 0

        try:
            code = path.read_text()
            entities = self.entity_extractor.extract_from_python(code, str(path))

            if entities:
                stored = self.graph_store.store_entities(entities)
                logger.info(f"Indexed {path.name}: {stored} entities")
                return stored

            return 0

        except Exception as e:
            logger.error(f"Failed to index {file_path}: {e}")
            return 0

    def update_file(self, file_path: str | Path) -> int:
        """Update entities for single file (incremental)."""
        path = Path(file_path)

        # Delete old entities for this file
        deleted = self.graph_store.delete_entities_by_file(str(path))

        if deleted > 0:
            logger.debug(f"Deleted {deleted} old entities for {path.name}")

        # Re-index file
        return self.index_file(path)
