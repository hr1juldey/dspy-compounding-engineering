"""Async GraphRAG entity extraction with concurrency control."""

import asyncio
import time
from pathlib import Path
from typing import Callable, Optional

from utils.io.logger import logger


class GraphRAGAsync:
    """Extract entities from Python files asynchronously."""

    def __init__(self, entity_extractor, graph_store, timing_cache, max_concurrent: int = 10):
        self.entity_extractor = entity_extractor
        self.graph_store = graph_store
        self.timing_cache = timing_cache
        self.max_concurrent = max_concurrent

    async def index_files(
        self,
        python_files: list[Path],
        progress_callback: Optional[Callable] = None,
    ) -> dict:
        """Index Python files in parallel with concurrency control."""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        total_entities = 0
        indexed_files = 0

        async def index_one_file(idx: int, file_path: Path) -> None:
            nonlocal total_entities, indexed_files

            async with semaphore:
                file_start = time.time()
                loop = asyncio.get_event_loop()

                try:
                    # Read file in thread pool
                    code = await loop.run_in_executor(None, file_path.read_text)

                    # Extract entities in thread pool
                    entities = await loop.run_in_executor(
                        None,
                        self.entity_extractor.extract_from_python,
                        code,
                        str(file_path),
                    )

                    if entities:
                        # Store entities in thread pool
                        stored = await loop.run_in_executor(
                            None,
                            self.graph_store.store_entities,
                            entities,
                        )
                        total_entities += stored

                        file_time_ms = (time.time() - file_start) * 1000
                        self.timing_cache.record_indexing(
                            str(file_path), len(entities), file_time_ms
                        )
                        indexed_files += 1

                        if progress_callback:
                            progress_callback(str(file_path), idx + 1, len(python_files))

                except Exception as e:
                    logger.error(f"Failed to index {file_path}: {e}")

        # Process all files concurrently
        tasks = [index_one_file(idx, fp) for idx, fp in enumerate(python_files)]
        await asyncio.gather(*tasks)

        return {"files": indexed_files, "entities": total_entities}
