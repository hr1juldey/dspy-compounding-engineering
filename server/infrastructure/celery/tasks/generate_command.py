"""
Celery task for meta-command generation.
"""

from server.infrastructure.celery.app import celery_app
from server.infrastructure.redis.pubsub import publish_progress
from utils.paths import CompoundingPaths
from workflows.generate_command import run_generate_command


@celery_app.task(bind=True)
def generate_command_task(
    self,
    repo_root: str,
    description: str,
    dry_run: bool = False,
):
    """
    Generate new CLI command from description (async task).

    Args:
        repo_root: Root directory of target repository
        description: Natural language description of command
        dry_run: Preview mode without creating files

    Returns:
        Task result dictionary
    """
    # Initialize paths
    CompoundingPaths(repo_root)

    # Publish progress
    publish_progress(self.request.id, 0, "Starting command generation...")

    try:
        # Execute generate command workflow
        result = run_generate_command(description=description, dry_run=dry_run)

        publish_progress(self.request.id, 100, "Command generation complete")

        return {
            "success": True,
            "result": result,
            "description": description,
            "dry_run": dry_run,
        }

    except Exception as e:
        publish_progress(self.request.id, 100, f"Generation failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "description": description,
        }
