"""
Async file indexing with concurrency control.

Provides parallel file processing while respecting memory constraints.
DSPy handles embedding batching internally via batch_size config.
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple


class AsyncFileIndexer:
    """
    Parallel file indexer with concurrency control.

    Processes multiple files concurrently while limiting concurrent files
    to manage memory usage. Does NOT rate limit embeddings - DSPy handles
    that via its centralized batch_size configuration.

    Provider-agnostic: works with OpenAI, Anthropic, Ollama, etc.
    """

    def __init__(self, indexer: Any, max_concurrency: int = 20):
        """
        Initialize async indexer.

        Args:
            indexer: CodebaseIndexer instance (sync methods)
            max_concurrency: Max concurrent files (prevents memory exhaustion)
        """
        self.indexer = indexer
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def index_file_async(
        self,
        filepath: str,
        full_path: str,
        indexed_files: Dict[str, float],
    ) -> Tuple[str, bool, Optional[str]]:
        """
        Index single file with concurrency control.

        Runs sync indexing in thread pool to avoid blocking event loop.

        Returns:
            (filepath, success, error_message)
        """
        async with self.semaphore:
            # Run sync indexing in thread pool (doesn't block event loop)
            loop = asyncio.get_event_loop()
            try:
                result = await loop.run_in_executor(
                    None,
                    self.indexer.file_indexer.index_file,
                    filepath,
                    full_path,
                    indexed_files,
                )
                return (filepath, result, None)
            except Exception as e:
                return (filepath, False, str(e))

    async def index_files_parallel(
        self,
        files: List[Tuple[str, str]],
        indexed_files: Dict[str, float],
        progress_callback: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Index multiple files in parallel.

        DSPy handles embedding batching internally - we just parallelize
        file I/O and processing.

        Args:
            files: List of (filepath, full_path) tuples
            indexed_files: Current index state
            progress_callback: Optional callback(current, total, filepath)

        Returns:
            Stats dict: {updated: int, skipped: int, failed: int, errors: List}
        """
        tasks = [
            self.index_file_async(filepath, full_path, indexed_files)
            for filepath, full_path in files
        ]

        updated, skipped, failed = 0, 0, 0
        errors = []

        # Process tasks with progress updates
        for i, coro in enumerate(asyncio.as_completed(tasks)):
            filepath, success, error = await coro

            if error:
                failed += 1
                errors.append(f"{filepath}: {error}")
            elif success:
                updated += 1
            else:
                skipped += 1

            if progress_callback:
                progress_callback(i + 1, len(tasks), filepath)

        return {
            "updated": updated,
            "skipped": skipped,
            "failed": failed,
            "errors": errors,
        }
