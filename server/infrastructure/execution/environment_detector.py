"""Detect repository environment type (Python/Node/Rust/Go/C)."""

from pathlib import Path

from server.infrastructure.execution.models import (
    CEnvironment,
    GoEnvironment,
    NodeEnvironment,
    PythonEnvironment,
    RepoEnvironment,
    RustEnvironment,
)
from server.infrastructure.execution.user_prompter import UserPrompter


class EnvironmentDetector:
    """Detect environment type in target repository."""

    def __init__(self, repo_root: Path, user_prompter: UserPrompter | None = None):
        self.repo_root = Path(repo_root).resolve()
        self.user_prompter = user_prompter or UserPrompter()

    def _detect_python(self) -> list[PythonEnvironment]:
        """Detect Python virtual environments (.venv, venv, env)."""
        python_envs = []
        for venv_name in [".venv", "venv", "env"]:
            venv_path = self.repo_root / venv_name
            if venv_path.exists() and venv_path.is_dir():
                python_envs.append(PythonEnvironment(self.repo_root, venv_name))
        return python_envs

    def get_environment(self) -> RepoEnvironment:  # noqa: C901
        """Detect and return repository environment."""
        environments = []

        python_envs = self._detect_python()
        if len(python_envs) > 1:
            selected = self.user_prompter.choose_environment(python_envs)  # type: ignore[arg-type]
            environments.append(selected)
        elif python_envs:
            environments.extend(python_envs)

        if (self.repo_root / "node_modules").exists():
            environments.append(NodeEnvironment(self.repo_root))

        if (self.repo_root / "Cargo.toml").exists():
            environments.append(RustEnvironment(self.repo_root))

        if (self.repo_root / "go.mod").exists():
            environments.append(GoEnvironment(self.repo_root))

        if (self.repo_root / "Makefile").exists():
            environments.append(CEnvironment(self.repo_root))

        if len(environments) > 1:
            return self.user_prompter.choose_environment(environments)

        if len(environments) == 1:
            return environments[0]

        from server.infrastructure.execution.models import RepoEnvironment

        class SystemEnvironment(RepoEnvironment):
            @property
            def description(self) -> str:
                return "System (no environment detected)"

            def get_executable(self, command: str) -> Path | None:
                return None

        return SystemEnvironment(self.repo_root)
