"""
Unit tests for FastAPI endpoints.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """Create test client."""
    from server.main import app

    return TestClient(app)


def test_root_endpoint(test_client):
    """Test root endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


@patch("server.infrastructure.celery.app.check_celery_workers")
def test_health_endpoint(mock_workers, test_client):
    """Test health endpoint."""
    mock_workers.return_value = True

    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["celery_workers"] is True


@patch("server.api.v1.analyze.AnalyzeService")
def test_submit_analyze(mock_service_class, test_client):
    """Test analyze submission endpoint."""
    mock_service = MagicMock()
    mock_service.submit_analyze.return_value = "task-123"
    mock_service_class.return_value = mock_service

    response = test_client.post(
        "/api/v1/analyze",
        json={
            "repo_root": "/test/repo",
            "entity": "TestClass",
            "analysis_type": "navigate",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "task-123"


@patch("server.api.v1.analyze.AnalyzeService")
def test_get_analyze_status(mock_service_class, test_client):
    """Test analyze status endpoint."""
    mock_service = MagicMock()
    mock_service.get_status.return_value = {
        "task_id": "task-123",
        "state": "SUCCESS",
        "ready": True,
        "result": {"success": True},
    }
    mock_service_class.return_value = mock_service

    response = test_client.get("/api/v1/analyze/task-123")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "task-123"
    assert data["state"] == "SUCCESS"


@patch("server.api.v1.work.WorkService")
def test_submit_work(mock_service_class, test_client):
    """Test work submission endpoint."""
    mock_service = MagicMock()
    mock_service.submit_work.return_value = "work-123"
    mock_service_class.return_value = mock_service

    response = test_client.post(
        "/api/v1/work",
        json={"repo_root": "/test/repo", "pattern": "001"},
    )

    assert response.status_code == 200
    assert response.json()["task_id"] == "work-123"


@patch("server.api.v1.review.ReviewService")
def test_submit_review(mock_service_class, test_client):
    """Test review submission endpoint."""
    mock_service = MagicMock()
    mock_service.submit_review.return_value = "review-123"
    mock_service_class.return_value = mock_service

    response = test_client.post(
        "/api/v1/review",
        json={"repo_root": "/test/repo", "pr_url_or_id": "latest"},
    )

    assert response.status_code == 200
    assert response.json()["task_id"] == "review-123"


@patch("server.api.v1.garden.GardenService")
def test_submit_garden(mock_service_class, test_client):
    """Test garden submission endpoint."""
    mock_service = MagicMock()
    mock_service.submit_garden.return_value = "garden-123"
    mock_service_class.return_value = mock_service

    response = test_client.post(
        "/api/v1/garden",
        json={"repo_root": "/test/repo", "action": "consolidate"},
    )

    assert response.status_code == 200


@patch("server.api.v1.plan.PlanService")
def test_submit_plan(mock_service_class, test_client):
    """Test plan submission endpoint."""
    mock_service = MagicMock()
    mock_service.submit_plan.return_value = "plan-123"
    mock_service_class.return_value = mock_service

    response = test_client.post(
        "/api/v1/plan",
        json={"repo_root": "/test/repo", "feature_description": "Add X"},
    )

    assert response.status_code == 200


@patch("server.api.v1.check.CheckService")
def test_run_check(mock_service_class, test_client):
    """Test synchronous check endpoint."""
    mock_service = MagicMock()
    mock_service.check_sync.return_value = {
        "success": True,
        "exit_code": 0,
        "paths": "all",
        "auto_fix": False,
    }
    mock_service_class.return_value = mock_service

    response = test_client.post(
        "/api/v1/check",
        json={"repo_root": "/test/repo", "auto_fix": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["exit_code"] == 0


def test_openapi_docs(test_client):
    """Test OpenAPI docs are available."""
    response = test_client.get("/docs")
    assert response.status_code == 200
