"""
Integration tests for the server stack.
Tests with real services where possible.
"""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def integration_client():
    """Create test client for integration tests."""
    from server.main import app

    return TestClient(app)


def test_full_server_startup(integration_client):
    """Test server starts up successfully."""
    response = integration_client.get("/")
    assert response.status_code == 200


def test_health_check_integration(integration_client):
    """Test health check with real celery check."""
    response = integration_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "celery_workers" in data


def test_openapi_schema_generation(integration_client):
    """Test OpenAPI schema is generated correctly."""
    response = integration_client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "paths" in schema
    assert "/api/v1/analyze" in schema["paths"]
    assert "/health" in schema["paths"]


def test_analyze_endpoint_validation(integration_client):
    """Test analyze endpoint validates input."""
    # Missing required field
    response = integration_client.post(
        "/api/v1/analyze",
        json={"entity": "TestClass"},
    )
    assert response.status_code == 422

    # Invalid analysis_type
    response = integration_client.post(
        "/api/v1/analyze",
        json={
            "repo_root": "/test",
            "entity": "TestClass",
            "max_depth": 5,  # Invalid, should be 1-3
        },
    )
    assert response.status_code == 422


def test_work_endpoint_validation(integration_client):
    """Test work endpoint validates input."""
    # Missing repo_root
    response = integration_client.post(
        "/api/v1/work",
        json={"pattern": "001"},
    )
    assert response.status_code == 422


def test_check_endpoint_synchronous(integration_client):
    """Test check endpoint returns synchronously."""
    response = integration_client.post(
        "/api/v1/check",
        json={
            "repo_root": str(Path.cwd()),
            "paths": None,
            "auto_fix": False,
        },
    )
    assert response.status_code == 200
    # Should return immediately, not a task_id


def test_config_endpoint_get(integration_client):
    """Test config UI endpoint."""
    response = integration_client.get("/api/v1/config")
    assert response.status_code == 200
    # Should return HTML


def test_cors_headers(integration_client):
    """Test CORS middleware is configured."""
    # TestClient doesn't trigger CORS headers (simulates internal requests)
    # Instead, verify CORS middleware is present in the app
    from fastapi.middleware.cors import CORSMiddleware

    from server.main import app

    # Check that CORSMiddleware is in the middleware stack
    # Middleware is wrapped, so we need to check the cls attribute
    middleware_classes = [m.cls for m in app.user_middleware]
    assert CORSMiddleware in middleware_classes


@pytest.mark.skipif(not os.path.exists("/.dockerenv"), reason="Only run in Docker environment")
def test_static_files_accessible(integration_client):
    """Test static files are served."""
    response = integration_client.get("/static/style.css")
    assert response.status_code == 200
    assert "text/css" in response.headers.get("content-type", "")
