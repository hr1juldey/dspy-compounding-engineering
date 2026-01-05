"""
Codify service for knowledge base feedback integration.

Wraps codify_task Celery task for MCP/API access.
"""

from server.infrastructure.celery.tasks.codify import codify_task


class CodifyService:
    """Service for codifying feedback into knowledge base."""

    def submit_codify(
        self,
        repo_root: str,
        feedback: str,
        source: str = "manual_input",
    ) -> str:
        """
        Submit feedback codification task to Celery.

        Args:
            repo_root: Root directory of repository
            feedback: Feedback, instruction, or learning to codify
            source: Source of feedback (e.g., 'review', 'retro')

        Returns:
            Task ID for async tracking
        """
        result = codify_task.delay(repo_root=repo_root, feedback=feedback, source=source)  # type: ignore[no-untyped-call]
        return result.id
