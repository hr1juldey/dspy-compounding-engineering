"""Policy violation data structures."""

from enum import Enum

from pydantic import BaseModel


class Severity(str, Enum):
    """Violation severity levels."""

    ERROR = "ERROR"  # Blocks commits
    WARNING = "WARNING"  # Shows message
    INFO = "INFO"  # Informational


class Violation(BaseModel):
    """Single policy violation."""

    file_path: str
    line_number: int | None = None
    rule_id: str
    severity: Severity
    message: str
    suggestion: str | None = None
    auto_fixable: bool = False


class PolicyResult(BaseModel):
    """Aggregated policy check result."""

    violations: list[Violation]
    files_checked: int
    files_with_violations: int
    errors: int
    warnings: int
    infos: int

    @property
    def passed(self) -> bool:
        """True if no ERROR-level violations."""
        return self.errors == 0

    @property
    def should_block_commit(self) -> bool:
        """True if commit should be blocked."""
        return self.errors > 0
