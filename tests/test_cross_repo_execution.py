"""Integration tests for cross-repository execution."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from server.infrastructure.execution import RepoExecutor
from workflows.check import run_check


@pytest.fixture
def temp_python_repo():
    """Create temporary Python repository with .venv."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Create .venv structure
        venv_path = repo_path / ".venv"
        bin_path = venv_path / "bin"
        bin_path.mkdir(parents=True)

        # Create fake ruff executable
        ruff_path = bin_path / "ruff"
        ruff_path.write_text("#!/bin/bash\necho 'fake ruff'")
        ruff_path.chmod(0o755)

        # Create test Python file
        (repo_path / "test.py").write_text("print('hello')")

        yield repo_path


@pytest.fixture
def temp_node_repo():
    """Create temporary Node.js repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Create node_modules structure
        (repo_path / "node_modules" / ".bin").mkdir(parents=True)
        (repo_path / "package.json").write_text('{"name": "test"}')

        yield repo_path


def test_environment_detection_python(temp_python_repo):
    """Test that Python environment is correctly detected."""
    executor = RepoExecutor(temp_python_repo)
    assert "Python" in executor.environment.description
    assert executor.environment.venv_name == ".venv"


def test_environment_detection_node(temp_node_repo):
    """Test that Node.js environment is correctly detected."""
    executor = RepoExecutor(temp_node_repo)
    assert "Node.js" in executor.environment.description


def test_executable_resolution_from_venv(temp_python_repo):
    """Test that executables are resolved from target repo's .venv."""
    executor = RepoExecutor(temp_python_repo)
    ruff_path = executor.resolver.resolve("ruff")

    assert str(temp_python_repo / ".venv" / "bin" / "ruff") == ruff_path


def test_multiple_repos_isolation(temp_python_repo, temp_node_repo):
    """Test that multiple repos maintain environment isolation."""
    python_executor = RepoExecutor(temp_python_repo)
    node_executor = RepoExecutor(temp_node_repo)

    assert "Python" in python_executor.environment.description
    assert "Node.js" in node_executor.environment.description
    assert python_executor.repo_root != node_executor.repo_root


@patch("subprocess.run")
def test_check_workflow_uses_target_venv(mock_run, temp_python_repo):
    """Test that check workflow uses target repo's .venv."""
    # Create a test file
    test_file = temp_python_repo / "test.py"
    test_file.write_text("print('test')")

    # Mock subprocess to verify correct executable is called
    from unittest.mock import MagicMock

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_run.return_value = mock_result

    # Run check workflow
    run_check(repo_root=temp_python_repo, paths=[str(test_file)])

    # Verify that subprocess was called with correct cwd
    calls = mock_run.call_args_list
    for call in calls:
        assert call.kwargs.get("cwd") == temp_python_repo


def test_repo_executor_cwd_isolation(temp_python_repo):
    """Test that RepoExecutor executes commands in correct cwd."""
    executor = RepoExecutor(temp_python_repo)

    with patch("subprocess.run") as mock_run:
        executor.run(["ls", "-la"])
        mock_run.assert_called_once()
        assert mock_run.call_args.kwargs["cwd"] == temp_python_repo
