"""Main executor for cross-repo command execution."""

import subprocess
from pathlib import Path

from server.infrastructure.execution.environment_detector import EnvironmentDetector
from server.infrastructure.execution.executable_resolver import ExecutableResolver
from server.infrastructure.execution.user_prompter import UserPrompter


class RepoExecutor:
    """Execute commands in target repository context with environment isolation."""

    def __init__(self, repo_root: str | Path, user_prompter: UserPrompter | None = None):
        self.repo_root = Path(repo_root).resolve()
        self.detector = EnvironmentDetector(self.repo_root, user_prompter)
        self.environment = self.detector.get_environment()
        self.resolver = ExecutableResolver(self.environment)

    def run(
        self, cmd: list[str], cwd: str | Path | None = None, **kwargs
    ) -> subprocess.CompletedProcess:
        """Execute command with resolved executable and correct cwd.

        Args:
            cmd: Command as list (e.g., ["ruff", "check", "."])
            cwd: Working directory (defaults to repo_root)
            **kwargs: Additional arguments for subprocess.run()

        Returns:
            CompletedProcess instance
        """
        resolved_cmd = cmd.copy()
        resolved_cmd[0] = self.resolver.resolve(cmd[0])

        return subprocess.run(
            resolved_cmd,
            cwd=cwd or self.repo_root,
            **kwargs,
        )

    def run_python(
        self, args: list[str], cwd: str | Path | None = None, **kwargs
    ) -> subprocess.CompletedProcess:
        """Execute Python with target repo's interpreter.

        Args:
            args: Python arguments (e.g., ["-m", "pytest", "tests/"])
            cwd: Working directory (defaults to repo_root)
            **kwargs: Additional arguments for subprocess.run()

        Returns:
            CompletedProcess instance
        """
        python_cmd = self.resolver.resolve("python")
        return subprocess.run(
            [python_cmd] + args,
            cwd=cwd or self.repo_root,
            **kwargs,
        )

    def get_env_vars(self) -> dict[str, str]:
        """Get environment variables for execution context.

        Returns:
            Dictionary of environment variables (VIRTUAL_ENV, PATH, etc.)
        """
        return self.environment.get_env_vars()
