"""Resolve executables from repository environment (cross-platform)."""

from server.infrastructure.execution.models import RepoEnvironment


class ExecutableResolver:
    """Resolve executable paths from environment (Mac/Linux/Windows)."""

    def __init__(self, environment: RepoEnvironment):
        self.environment = environment

    def resolve(self, command: str) -> str:
        """Resolve executable path for command.

        Args:
            command: Command name to resolve (e.g., "ruff", "pytest", "node")

        Returns:
            Absolute path to executable if found in environment,
            otherwise returns command name for system PATH fallback
        """
        exe_path = self.environment.get_executable(command)

        if exe_path and exe_path.exists():
            return str(exe_path)

        return command
