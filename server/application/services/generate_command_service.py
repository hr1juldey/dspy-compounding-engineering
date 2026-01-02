"""
Generate command service for meta-command generation.

Wraps generate_command_task Celery task for MCP/API access.
"""

from server.infrastructure.celery.tasks.generate_command import generate_command_task


class GenerateCommandService:
    """Service for generating new CLI commands from descriptions."""

    def submit_generation(
        self,
        repo_root: str,
        description: str,
        dry_run: bool = False,
    ) -> str:
        """
        Submit command generation task to Celery.

        Args:
            repo_root: Root directory of repository
            description: Natural language description of command
            dry_run: Preview mode without creating files

        Returns:
            Task ID for async tracking
        """
        result = generate_command_task.delay(
            repo_root=repo_root, description=description, dry_run=dry_run
        )
        return result.id
