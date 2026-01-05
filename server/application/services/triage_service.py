"""
Triage service for issue categorization.

Wraps triage_task Celery task for MCP/API access.
"""

from server.infrastructure.celery.tasks.triage import triage_task


class TriageService:
    """Service for triaging and categorizing codebase issues."""

    def submit_triage(
        self,
        repo_root: str,
        pattern: str | None = None,
        dry_run: bool = False,
    ) -> str:
        """
        Submit triage task to Celery.

        Args:
            repo_root: Root directory of repository
            pattern: Optional pattern to filter issues
            dry_run: Preview mode without creating todos

        Returns:
            Task ID for async tracking
        """
        result = triage_task.delay(repo_root=repo_root, pattern=pattern, dry_run=dry_run)  # type: ignore[no-untyped-call]
        return result.id
