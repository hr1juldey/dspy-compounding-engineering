"""Sequential (synchronous) GraphRAG entity extraction."""

import time
from pathlib import Path
from typing import Callable, Optional

from utils.io.logger import logger


class GraphRAGSequential:
    """Extract entities from Python files sequentially."""

    def __init__(self, entity_extractor, graph_store, timing_cache):
        self.entity_extractor = entity_extractor
        self.graph_store = graph_store
        self.timing_cache = timing_cache

    def index_files(
        self,
        python_files: list[Path],
        progress_callback: Optional[Callable] = None,
    ) -> dict:
        """Index Python files sequentially."""
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
                    # Store entities
                    stored = self.graph_store.store_entities(entities)
                    total_entities += stored

                    file_time_ms = (time.time() - file_start) * 1000
                    self.timing_cache.record_indexing(str(file_path), len(entities), file_time_ms)
                    indexed_files += 1

                    # Progress callback
                    if progress_callback:
                        progress_callback(str(file_path), idx + 1, len(python_files))

                    # Log progress every 50 files
                    if indexed_files % 50 == 0:
                        logger.info(
                            f"Progress: {indexed_files}/{len(python_files)} "
                            f"files, {total_entities} entities"
                        )

            except Exception as e:
                logger.error(f"Failed to index {file_path}: {e}")
                continue

        return {"files": indexed_files, "entities": total_entities}
