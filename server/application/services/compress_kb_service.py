"""
Knowledge base compression service.

Wraps compress_kb_task Celery task for MCP/API access.
"""

from server.infrastructure.celery.tasks.compress_kb import compress_kb_task


class CompressKBService:
    """Service for compressing AI.md knowledge base."""

    def submit_compression(
        self,
        repo_root: str,
        ratio: float = 0.5,
        dry_run: bool = False,
    ) -> str:
        """
        Submit KB compression task to Celery.

        Args:
            repo_root: Root directory of repository
            ratio: Target compression ratio (0.0 to 1.0)
            dry_run: Preview mode without modifying file

        Returns:
            Task ID for async tracking
        """
        result = compress_kb_task.delay(repo_root=repo_root, ratio=ratio, dry_run=dry_run)  # type: ignore[no-untyped-call]
        return result.id
