"""Environment models for cross-repo execution."""

import platform
from abc import ABC, abstractmethod
from pathlib import Path


class RepoEnvironment(ABC):
    """Base class for repository environments."""

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root).resolve()

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of environment."""

    @abstractmethod
    def get_executable(self, command: str) -> Path | None:
        """Resolve executable path for command."""

    def get_env_vars(self) -> dict[str, str]:
        """Get environment variables for execution."""
        return {}


class PythonEnvironment(RepoEnvironment):
    """Python virtual environment (.venv, venv, env)."""

    def __init__(self, repo_root: Path, venv_name: str = ".venv"):
        super().__init__(repo_root)
        self.venv_name = venv_name
        self.venv_path = repo_root / venv_name

    @property
    def description(self) -> str:
        return f"Python ({self.venv_name})"

    def get_executable(self, command: str) -> Path | None:
        """Resolve executable from .venv/bin (Unix) or .venv/Scripts (Windows)."""
        bin_dir = "Scripts" if platform.system() == "Windows" else "bin"
        exe_path = self.venv_path / bin_dir / command

        if platform.system() == "Windows" and not exe_path.exists():
            exe_path = exe_path.with_suffix(".exe")

        return exe_path if exe_path.exists() else None

    def get_env_vars(self) -> dict[str, str]:
        bin_dir = "Scripts" if platform.system() == "Windows" else "bin"
        return {
            "VIRTUAL_ENV": str(self.venv_path),
            "PATH": f"{self.venv_path / bin_dir}:{Path.cwd()}",
        }


class NodeEnvironment(RepoEnvironment):
    """Node.js environment (node_modules)."""

    @property
    def description(self) -> str:
        return "Node.js (node_modules)"

    def get_executable(self, command: str) -> Path | None:
        exe_path = self.repo_root / "node_modules" / ".bin" / command
        return exe_path if exe_path.exists() else None


class RustEnvironment(RepoEnvironment):
    """Rust environment (Cargo)."""

    @property
    def description(self) -> str:
        return "Rust (Cargo)"

    def get_executable(self, command: str) -> Path | None:
        cargo_home = Path.home() / ".cargo" / "bin" / command
        return cargo_home if cargo_home.exists() else None


class GoEnvironment(RepoEnvironment):
    """Go environment (go.mod)."""

    @property
    def description(self) -> str:
        return "Go (go.mod)"

    def get_executable(self, command: str) -> Path | None:
        return None


class CEnvironment(RepoEnvironment):
    """C/C++ environment (Makefile)."""

    @property
    def description(self) -> str:
        return "C/C++ (Makefile)"

    def get_executable(self, command: str) -> Path | None:
        return None
