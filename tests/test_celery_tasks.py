"""
Unit tests for Celery tasks with mocks.
"""

from unittest.mock import patch


@patch("server.infrastructure.celery.tasks.analyze.run_analyze")
@patch("server.infrastructure.celery.tasks.analyze.CompoundingPaths")
@patch("server.infrastructure.celery.tasks.analyze.publish_progress")
def test_analyze_code_task_success(mock_progress, mock_paths, mock_run):
    """Test analyze task with successful execution."""
    from server.infrastructure.celery.tasks.analyze import analyze_code_task

    mock_run.return_value = {"result": "analysis complete"}

    # Call task using .apply() to simulate execution
    result = analyze_code_task.apply(
        kwargs={
            "repo_root": "/test/repo",
            "entity": "TestClass",
            "analysis_type": "navigate",
        }
    )

    task_result = result.get()
    assert task_result["success"] is True
    assert "result" in task_result
    mock_run.assert_called_once()
    mock_paths.assert_called_once_with("/test/repo")


@patch("server.infrastructure.celery.tasks.analyze.run_analyze")
@patch("server.infrastructure.celery.tasks.analyze.CompoundingPaths")
@patch("server.infrastructure.celery.tasks.analyze.publish_progress")
def test_analyze_code_task_failure(mock_progress, mock_paths, mock_run):
    """Test analyze task with failure."""
    from server.infrastructure.celery.tasks.analyze import analyze_code_task

    mock_run.side_effect = Exception("Analysis failed")

    result = analyze_code_task.apply(
        kwargs={
            "repo_root": "/test/repo",
            "entity": "TestClass",
        }
    )

    task_result = result.get()
    assert task_result["success"] is False
    assert "error" in task_result


@patch("server.infrastructure.celery.tasks.work.run_unified_work")
@patch("server.infrastructure.celery.tasks.work.CompoundingPaths")
@patch("server.infrastructure.celery.tasks.work.publish_progress")
def test_execute_work_task(mock_progress, mock_paths, mock_run):
    """Test work execution task."""
    from server.infrastructure.celery.tasks.work import execute_work_task

    mock_run.return_value = {"status": "completed"}

    result = execute_work_task.apply(kwargs={"repo_root": "/test/repo", "pattern": "001"})

    task_result = result.get()
    assert task_result["success"] is True
    mock_run.assert_called_once()


@patch("server.infrastructure.celery.tasks.review.run_review")
@patch("server.infrastructure.celery.tasks.review.CompoundingPaths")
@patch("server.infrastructure.celery.tasks.review.publish_progress")
def test_review_code_task(mock_progress, mock_paths, mock_run):
    """Test code review task."""
    from server.infrastructure.celery.tasks.review import review_code_task

    mock_run.return_value = {"findings": []}

    result = review_code_task.apply(kwargs={"repo_root": "/test/repo", "pr_url_or_id": "latest"})

    task_result = result.get()
    assert task_result["success"] is True


@patch("server.infrastructure.celery.tasks.garden.run_garden")
@patch("server.infrastructure.celery.tasks.garden.CompoundingPaths")
@patch("server.infrastructure.celery.tasks.garden.publish_progress")
def test_garden_task(mock_progress, mock_paths, mock_run):
    """Test garden task."""
    from server.infrastructure.celery.tasks.garden import garden_task

    mock_run.return_value = {"cleaned": 10}

    result = garden_task.apply(kwargs={"repo_root": "/test/repo", "action": "consolidate"})

    task_result = result.get()
    assert task_result["success"] is True


@patch("server.infrastructure.celery.tasks.plan.run_plan")
@patch("server.infrastructure.celery.tasks.plan.CompoundingPaths")
@patch("server.infrastructure.celery.tasks.plan.publish_progress")
def test_generate_plan_task(mock_progress, mock_paths, mock_run):
    """Test plan generation task."""
    from server.infrastructure.celery.tasks.plan import generate_plan_task

    mock_run.return_value = {"plan": "created"}

    result = generate_plan_task.apply(
        kwargs={
            "repo_root": "/test/repo",
            "feature_description": "Add feature X",
        }
    )

    task_result = result.get()
    assert task_result["success"] is True


@patch("server.infrastructure.celery.tasks.check.run_check")
@patch("server.infrastructure.celery.tasks.check.CompoundingPaths")
def test_check_policies_task(mock_paths, mock_run):
    """Test policy check task."""
    from server.infrastructure.celery.tasks.check import check_policies_task

    mock_run.return_value = 0

    result = check_policies_task.apply(
        kwargs={"repo_root": "/test/repo", "paths": None, "auto_fix": False}
    )

    task_result = result.get()
    assert task_result["success"] is True
    assert task_result["exit_code"] == 0
