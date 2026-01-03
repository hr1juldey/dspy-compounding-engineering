"""Unit tests for RepoExecutor and environment detection."""

import platform
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from server.infrastructure.execution.environment_detector import EnvironmentDetector
from server.infrastructure.execution.executable_resolver import ExecutableResolver
from server.infrastructure.execution.models import (
    CEnvironment,
    GoEnvironment,
    NodeEnvironment,
    PythonEnvironment,
    RustEnvironment,
)
from server.infrastructure.execution.repo_executor import RepoExecutor
from server.infrastructure.execution.user_prompter import UserPrompter


@pytest.fixture
def temp_repo():
    """Create temporary repository directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_detect_python_venv_dotenv(temp_repo):
    """Test detection of .venv directory."""
    (temp_repo / ".venv").mkdir()
    (temp_repo / ".venv" / "bin").mkdir()

    detector = EnvironmentDetector(temp_repo)
    python_envs = detector._detect_python()

    assert len(python_envs) == 1
    assert python_envs[0].venv_name == ".venv"


def test_detect_python_venv_multiple(temp_repo):
    """Test detection when multiple .venv directories exist."""
    (temp_repo / ".venv").mkdir()
    (temp_repo / "venv").mkdir()
    (temp_repo / "env").mkdir()

    mock_prompter = MagicMock(spec=UserPrompter)
    mock_prompter.choose_environment.return_value = PythonEnvironment(temp_repo, ".venv")

    detector = EnvironmentDetector(temp_repo, user_prompter=mock_prompter)
    env = detector.get_environment()

    assert isinstance(env, PythonEnvironment)
    assert env.venv_name == ".venv"
    mock_prompter.choose_environment.assert_called_once()


def test_detect_node_environment(temp_repo):
    """Test detection of Node.js environment."""
    (temp_repo / "node_modules").mkdir()
    (temp_repo / "package.json").write_text("{}")

    detector = EnvironmentDetector(temp_repo)
    env = detector.get_environment()

    assert isinstance(env, NodeEnvironment)


def test_detect_rust_environment(temp_repo):
    """Test detection of Rust environment."""
    (temp_repo / "Cargo.toml").write_text("[package]")

    detector = EnvironmentDetector(temp_repo)
    env = detector.get_environment()

    assert isinstance(env, RustEnvironment)


def test_detect_go_environment(temp_repo):
    """Test detection of Go environment."""
    (temp_repo / "go.mod").write_text("module test")

    detector = EnvironmentDetector(temp_repo)
    env = detector.get_environment()

    assert isinstance(env, GoEnvironment)


def test_detect_c_environment(temp_repo):
    """Test detection of C/C++ environment."""
    (temp_repo / "Makefile").write_text("all:")

    detector = EnvironmentDetector(temp_repo)
    env = detector.get_environment()

    assert isinstance(env, CEnvironment)


def test_python_executable_resolution_unix(temp_repo):
    """Test Python executable resolution on Unix systems."""
    if platform.system() == "Windows":
        pytest.skip("Unix-only test")

    venv_path = temp_repo / ".venv"
    bin_path = venv_path / "bin"
    bin_path.mkdir(parents=True)
    (bin_path / "python").touch(mode=0o755)

    env = PythonEnvironment(temp_repo, ".venv")
    exe_path = env.get_executable("python")

    assert exe_path == bin_path / "python"
    assert exe_path.exists()


def test_executable_resolver_fallback(temp_repo):
    """Test executable resolver falls back to command name."""
    env = PythonEnvironment(temp_repo, ".venv")
    resolver = ExecutableResolver(env)

    result = resolver.resolve("nonexistent_command")

    assert result == "nonexistent_command"


@patch("subprocess.run")
def test_repo_executor_run(mock_run, temp_repo):
    """Test RepoExecutor.run() executes with correct cwd."""
    (temp_repo / ".venv").mkdir()
    (temp_repo / ".venv" / "bin").mkdir()

    executor = RepoExecutor(temp_repo)
    executor.run(["python", "--version"], capture_output=True)

    mock_run.assert_called_once()
    assert mock_run.call_args.kwargs["cwd"] == temp_repo


def test_repo_executor_get_env_vars(temp_repo):
    """Test RepoExecutor.get_env_vars() returns environment variables."""
    (temp_repo / ".venv").mkdir()

    executor = RepoExecutor(temp_repo)
    env_vars = executor.get_env_vars()

    assert "VIRTUAL_ENV" in env_vars
    assert str(temp_repo / ".venv") in env_vars["VIRTUAL_ENV"]
