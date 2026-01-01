"""
Unit tests for MCP tools.
Tests the underlying service calls, not the MCP decorators.
"""

from unittest.mock import MagicMock, patch


@patch("server.application.services.analyze_service.analyze_code_task")
def test_mcp_analyze_code_service(mock_task):
    """Test MCP analyze_code service call."""
    from server.application.services.analyze_service import AnalyzeService

    mock_task.delay.return_value.id = "task-123"

    service = AnalyzeService()
    task_id = service.submit_analyze(
        repo_root="/test/repo",
        entity="TestClass",
        analysis_type="navigate",
    )

    assert task_id == "task-123"
    mock_task.delay.assert_called_once()


@patch("server.application.services.work_service.execute_work_task")
def test_mcp_execute_work_service(mock_task):
    """Test MCP execute_work service call."""
    from server.application.services.work_service import WorkService

    mock_task.delay.return_value.id = "work-123"

    service = WorkService()
    task_id = service.submit_work(repo_root="/test/repo", pattern="001")

    assert task_id == "work-123"


@patch("server.application.services.review_service.review_code_task")
def test_mcp_review_code_service(mock_task):
    """Test MCP review_code service call."""
    from server.application.services.review_service import ReviewService

    mock_task.delay.return_value.id = "review-123"

    service = ReviewService()
    task_id = service.submit_review(repo_root="/test/repo")

    assert task_id == "review-123"


@patch("server.application.services.garden_service.garden_task")
def test_mcp_garden_knowledge_service(mock_task):
    """Test MCP garden_knowledge service call."""
    from server.application.services.garden_service import GardenService

    mock_task.delay.return_value.id = "garden-123"

    service = GardenService()
    task_id = service.submit_garden(repo_root="/test/repo", action="consolidate")

    assert task_id == "garden-123"


@patch("server.application.services.plan_service.generate_plan_task")
def test_mcp_generate_plan_service(mock_task):
    """Test MCP generate_plan service call."""
    from server.application.services.plan_service import PlanService

    mock_task.delay.return_value.id = "plan-123"

    service = PlanService()
    task_id = service.submit_plan(repo_root="/test/repo", feature_description="Add X")

    assert task_id == "plan-123"


@patch("server.application.services.check_service.check_policies_task")
def test_mcp_check_policies_service(mock_task):
    """Test MCP check_policies service call (synchronous)."""
    from server.application.services.check_service import CheckService

    mock_result = MagicMock()
    mock_result.get.return_value = {"success": True, "exit_code": 0}
    mock_task.apply.return_value = mock_result

    service = CheckService()
    result = service.check_sync(repo_root="/test/repo", auto_fix=False)

    assert result["success"] is True


def test_mcp_get_task_status_service():
    """Test get_task_status via AsyncResult."""
    from celery.result import AsyncResult

    # This is testing the pattern, not mocking AsyncResult itself
    # since it's a core Celery class
    task_id = "test-task-123"
    result = AsyncResult(task_id)

    # Verify we can create AsyncResult objects
    assert result.id == task_id


@patch("server.application.services.repo_service.CompoundingPaths")
def test_mcp_get_repo_status_service(mock_paths):
    """Test MCP get_repo_status service call."""
    from server.application.services.repo_service import RepoService

    mock_instance = MagicMock()
    mock_instance.claude_dir.exists.return_value = True
    mock_instance.repo_root = "/test/repo"
    mock_paths.return_value = mock_instance

    service = RepoService()
    status = service.get_repo_status("/test/repo")

    assert status["claude_dir_exists"] is True


@patch("server.application.services.repo_service.CompoundingPaths")
def test_mcp_initialize_repo_service(mock_paths):
    """Test MCP initialize_repo service call."""
    from server.application.services.repo_service import RepoService

    mock_instance = MagicMock()
    mock_instance.claude_dir = MagicMock()
    mock_instance.repo_root = "/test/repo"
    mock_paths.return_value = mock_instance

    service = RepoService()
    result = service.initialize_repo("/test/repo")

    assert result["success"] is True
