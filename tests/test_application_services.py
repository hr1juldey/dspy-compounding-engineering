"""
Unit tests for application services.
"""

from unittest.mock import MagicMock, patch

from server.application.services.analyze_service import AnalyzeService
from server.application.services.check_service import CheckService
from server.application.services.garden_service import GardenService
from server.application.services.plan_service import PlanService
from server.application.services.repo_service import RepoService
from server.application.services.review_service import ReviewService
from server.application.services.work_service import WorkService


@patch("server.application.services.analyze_service.analyze_code_task")
def test_analyze_service_submit(mock_task):
    """Test analyze service submission."""
    mock_task.delay.return_value.id = "task-123"

    service = AnalyzeService()
    task_id = service.submit_analyze(repo_root="/test", entity="Foo", analysis_type="navigate")

    assert task_id == "task-123"
    mock_task.delay.assert_called_once()


@patch("server.application.services.analyze_service.AsyncResult")
def test_analyze_service_get_result_ready(mock_result):
    """Test getting ready result."""
    mock_async = MagicMock()
    mock_async.ready.return_value = True
    mock_async.get.return_value = {"success": True}
    mock_result.return_value = mock_async

    service = AnalyzeService()
    result = service.get_result("task-123")

    assert result == {"success": True}


@patch("server.application.services.analyze_service.AsyncResult")
def test_analyze_service_get_result_pending(mock_result):
    """Test getting pending result."""
    mock_async = MagicMock()
    mock_async.ready.return_value = False
    mock_result.return_value = mock_async

    service = AnalyzeService()
    result = service.get_result("task-123")

    assert result is None


@patch("server.application.services.analyze_service.AsyncResult")
def test_analyze_service_get_status_progress(mock_result):
    """Test getting status with progress."""
    mock_async = MagicMock()
    mock_async.state = "PROGRESS"
    mock_async.ready.return_value = False
    mock_async.info = {"percent": 50, "status": "Working..."}
    mock_result.return_value = mock_async

    service = AnalyzeService()
    status = service.get_status("task-123")

    assert status["state"] == "PROGRESS"
    assert status["progress"]["percent"] == 50


@patch("server.application.services.work_service.execute_work_task")
def test_work_service_submit(mock_task):
    """Test work service submission."""
    mock_task.delay.return_value.id = "work-123"

    service = WorkService()
    task_id = service.submit_work(repo_root="/test", pattern="001")

    assert task_id == "work-123"


@patch("server.application.services.review_service.review_code_task")
def test_review_service_submit(mock_task):
    """Test review service submission."""
    mock_task.delay.return_value.id = "review-123"

    service = ReviewService()
    task_id = service.submit_review(repo_root="/test")

    assert task_id == "review-123"


@patch("server.application.services.garden_service.garden_task")
def test_garden_service_submit(mock_task):
    """Test garden service submission."""
    mock_task.delay.return_value.id = "garden-123"

    service = GardenService()
    task_id = service.submit_garden(repo_root="/test", action="consolidate")

    assert task_id == "garden-123"


@patch("server.application.services.plan_service.generate_plan_task")
def test_plan_service_submit(mock_task):
    """Test plan service submission."""
    mock_task.delay.return_value.id = "plan-123"

    service = PlanService()
    task_id = service.submit_plan(repo_root="/test", feature_description="Add X")

    assert task_id == "plan-123"


@patch("server.application.services.check_service.check_policies_task")
def test_check_service_sync(mock_task):
    """Test synchronous check."""
    mock_result = MagicMock()
    mock_result.get.return_value = {"success": True, "exit_code": 0}
    mock_task.apply.return_value = mock_result

    service = CheckService()
    result = service.check_sync(repo_root="/test", auto_fix=False)

    assert result["success"] is True


@patch("server.application.services.repo_service.CompoundingPaths")
def test_repo_service_initialize(mock_paths):
    """Test repo initialization."""
    mock_instance = MagicMock()
    mock_instance.claude_dir = MagicMock()
    mock_instance.knowledge_dir = MagicMock()
    mock_instance.repo_root = "/test/repo"
    mock_paths.return_value = mock_instance

    service = RepoService()
    result = service.initialize_repo("/test/repo")

    assert result["success"] is True
    assert "/test/repo" in result["repo_root"]


@patch("server.application.services.repo_service.CompoundingPaths")
@patch("server.application.services.repo_service.KnowledgeBase")
def test_repo_service_get_status(mock_kb, mock_paths):
    """Test getting repo status."""
    mock_instance = MagicMock()
    mock_instance.claude_dir.exists.return_value = True
    mock_instance.repo_root = "/test/repo"
    mock_paths.return_value = mock_instance

    service = RepoService()
    status = service.get_repo_status("/test/repo")

    assert status["claude_dir_exists"] is True
