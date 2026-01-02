"""
GraphRAG Indexer - Entity extraction and graph construction.

Orchestrates entity extraction from codebase and stores in Qdrant.
"""

import time
from pathlib import Path

from utils.io.logger import logger
from utils.knowledge.entities import EntityExtractor
from utils.knowledge.graph_store import GraphStore
from utils.knowledge.graphrag_timing import GraphRAGTimingCache


class GraphRAGIndexer:
    """
    Indexes codebase for GraphRAG.

    Extracts entities, builds graph, stores in Qdrant.
    """

    def __init__(self, graph_store: GraphStore):
        """
        Initialize GraphRAG indexer.

        Args:
            graph_store: GraphStore for entity storage
        """
        self.graph_store = graph_store
        self.entity_extractor = EntityExtractor()
        self.timing_cache = GraphRAGTimingCache()

    def index_codebase(
        self, root_dir: str | Path, force_recreate: bool = False, progress_callback=None
    ) -> dict:
        """
        Index entire codebase for GraphRAG.

        Args:
            root_dir: Root directory to index
            force_recreate: Recreate collection from scratch
            progress_callback: Optional callback(file_path, progress, total)

        Returns:
            Dict with statistics: {files: int, entities: int, time_sec: float}
        """
        start_time = time.time()
        root_path = Path(root_dir)

        # Find all Python files
        python_files = list(root_path.rglob("*.py"))

        if not python_files:
            logger.warning(f"No Python files found in {root_dir}")
            return {"files": 0, "entities": 0, "time_sec": 0.0}

        # Recreate collection if needed
        if force_recreate:
            logger.info("Force recreating GraphRAG collection")
            self.graph_store._ensure_collection(force_recreate=True)

        logger.info(f"Indexing {len(python_files)} Python files for GraphRAG")

        total_entities = 0
        indexed_files = 0

        for idx, file_path in enumerate(python_files):
            file_start = time.time()

            try:
                # Read file
                code = file_path.read_text()

                # Extract entities
                entities = self.entity_extractor.extract_from_python(code, str(file_path))

                if entities:
                    # Store entities in Qdrant
                    stored = self.graph_store.store_entities(entities)
                    total_entities += stored

                    file_time_ms = (time.time() - file_start) * 1000

                    # Record timing
                    self.timing_cache.record_indexing(str(file_path), len(entities), file_time_ms)

                    indexed_files += 1

                    # Progress callback
                    if progress_callback:
                        progress_callback(str(file_path), idx + 1, len(python_files))

                    # Log progress every 50 files
                    if indexed_files % 50 == 0:
                        logger.info(
                            f"Progress: {indexed_files}/{len(python_files)} files, "
                            f"{total_entities} entities"
                        )

            except Exception as e:
                logger.error(f"Failed to index {file_path}: {e}")
                continue

        # Complete timing cache
        self.timing_cache.complete_run()

        elapsed_time = time.time() - start_time

        stats = {"files": indexed_files, "entities": total_entities, "time_sec": elapsed_time}

        logger.success(
            f"GraphRAG indexing complete: {indexed_files} files, "
            f"{total_entities} entities in {elapsed_time:.1f}s"
        )

        return stats

    def index_file(self, file_path: str | Path) -> int:
        """
        Index a single file for GraphRAG.

        Args:
            file_path: Path to Python file

        Returns:
            Number of entities extracted
        """
        path = Path(file_path)

        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return 0

        try:
            # Read file
            code = path.read_text()

            # Extract entities
            entities = self.entity_extractor.extract_from_python(code, str(path))

            if entities:
                # Store entities
                stored = self.graph_store.store_entities(entities)
                logger.info(f"Indexed {path.name}: {stored} entities")
                return stored

            return 0

        except Exception as e:
            logger.error(f"Failed to index {file_path}: {e}")
            return 0

    def update_file(self, file_path: str | Path) -> int:
        """
        Update entities for a single file (incremental indexing).

        Args:
            file_path: Path to Python file

        Returns:
            Number of entities updated
        """
        path = Path(file_path)

        # Delete old entities for this file
        deleted = self.graph_store.delete_entities_by_file(str(path))

        if deleted > 0:
            logger.debug(f"Deleted {deleted} old entities for {path.name}")

        # Re-index file
        return self.index_file(path)
