"""Ruff compliance validator."""

import subprocess
from pathlib import Path

from server.infrastructure.execution import RepoExecutor
from utils.policy.protocols.base import StaticProtocol
from utils.policy.protocols.questions import PolicyQuestion
from utils.policy.violations import Severity, Violation


class RuffProtocol(StaticProtocol):
    """Validates ruff compliance."""

    def get_rule_id(self) -> str:
        return "RUFF001"

    def get_questions(self) -> list[PolicyQuestion]:
        return [
            PolicyQuestion(
                question="Should ruff checks be enforced?",
                header="Ruff Enforcement",
                config_key="enforce_ruff",
                options=[
                    {
                        "label": "Yes",
                        "description": "Enforce ruff check and format",
                        "value": True,
                    },
                    {"label": "No", "description": "Skip ruff checks", "value": False},
                ],
            )
        ]

    def check(self, file_path: Path) -> list[Violation]:
        """Check ruff compliance."""
        config = self.context.config or {}
        if not config.get("enforce_ruff", True):
            return []

        violations = []

        # Find repo root from file path (use file's parent as fallback)
        repo_root = file_path.parent
        executor = RepoExecutor(repo_root)

        try:
            result = executor.run(
                ["ruff", "check", str(file_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                violations.append(
                    Violation(
                        file_path=str(file_path),
                        line_number=None,
                        rule_id=self.get_rule_id(),
                        severity=Severity.WARNING,
                        message=f"Ruff check failed: {result.stdout[:200]}",
                        suggestion="Run 'ruff check --fix' to auto-fix",
                        auto_fixable=True,
                    )
                )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return violations
