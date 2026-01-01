"""
Celery task for GraphRAG code analysis.
"""

from server.infrastructure.celery.app import celery_app
from server.infrastructure.redis.pubsub import publish_progress
from utils.paths import CompoundingPaths
from workflows.analyze import run_analyze


@celery_app.task(bind=True)
def analyze_code_task(
    self,
    repo_root: str,
    entity: str,
    analysis_type: str = "navigate",
    max_depth: int = 2,
    change_type: str = "Modify",
    save: bool = True,
):
    """
    Analyze code using GraphRAG agents (async Celery task).

    Args:
        repo_root: Root directory of target repository
        entity: Entity to analyze (function, class, module name)
        analysis_type: Type of analysis (navigate|impact|deps|arch|search)
        max_depth: Maximum relationship depth (1-3)
        change_type: Type of change for impact analysis
        save: Whether to save results to file

    Returns:
        Analysis result dictionary
    """
    task_id = self.request.id

    # Initialize paths for target repo (ensures .compounding exists)
    CompoundingPaths(repo_root)

    # Emit initial progress
    publish_progress(task_id, 0, "Initializing GraphRAG analysis...")
    self.update_state(state="PROGRESS", meta={"percent": 0, "status": "Initializing..."})

    # Run analysis workflow
    publish_progress(task_id, 25, f"Running {analysis_type} analysis...")
    self.update_state(state="PROGRESS", meta={"percent": 25, "status": "Analyzing..."})

    try:
        result = run_analyze(
            entity=entity,
            analysis_type=analysis_type,
            max_depth=max_depth,
            change_type=change_type,
            save=save,
        )

        publish_progress(task_id, 100, "Analysis complete")
        self.update_state(state="PROGRESS", meta={"percent": 100, "status": "Complete"})

        return {"success": True, "result": result, "entity": entity, "type": analysis_type}

    except Exception as e:
        publish_progress(task_id, 100, f"Analysis failed: {str(e)}")
        return {"success": False, "error": str(e), "entity": entity, "type": analysis_type}
