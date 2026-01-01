"""File size validator."""

from pathlib import Path

from utils.policy.protocols.base import StaticProtocol
from utils.policy.protocols.questions import PolicyQuestion
from utils.policy.violations import Severity, Violation


class FileSizeProtocol(StaticProtocol):
    """Validates file size limits."""

    def get_rule_id(self) -> str:
        return "SIZE001"

    def get_questions(self) -> list[PolicyQuestion]:
        return [
            PolicyQuestion(
                question="What should be the maximum lines per file?",
                header="File Size",
                config_key="max_file_lines",
                options=[
                    {"label": "50 lines", "description": "Very strict", "value": 50},
                    {"label": "100 lines", "description": "Recommended", "value": 100},
                    {"label": "200 lines", "description": "Lenient", "value": 200},
                ],
                default_index=1,
            )
        ]

    def check(self, file_path: Path) -> list[Violation]:
        """Check file line count."""
        config = self.context.config or {}
        source = file_path.read_text()
        total_lines = len(source.splitlines())

        exec_lines = sum(
            1 for line in source.splitlines() if line.strip() and not line.strip().startswith("#")
        )

        violations = []
        block_threshold = config.get("block_threshold_lines", 600)
        max_lines = config.get("max_file_lines", 100)

        if total_lines > block_threshold:
            violations.append(
                Violation(
                    file_path=str(file_path),
                    line_number=None,
                    rule_id="SIZE001",
                    severity=Severity.ERROR,
                    message=f"File exceeds {block_threshold} lines ({total_lines} lines)",
                    suggestion="Split into multiple files following SRP",
                    auto_fixable=False,
                )
            )
        elif exec_lines > max_lines:
            violations.append(
                Violation(
                    file_path=str(file_path),
                    line_number=None,
                    rule_id="SIZE002",
                    severity=Severity(config.get("file_size_severity", "WARNING")),
                    message=f"File exceeds {max_lines} executable lines ({exec_lines} lines)",
                    suggestion="Consider refactoring into smaller modules",
                    auto_fixable=False,
                )
            )

        return violations
