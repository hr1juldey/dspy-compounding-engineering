"""Policy enforcement orchestrator."""

from pathlib import Path

from utils.policy.cache import PolicyCache
from utils.policy.config import load_policy_config
from utils.policy.state import PolicyContext
from utils.policy.static.file_size_protocol import FileSizeProtocol
from utils.policy.static.import_protocol import ImportProtocol
from utils.policy.static.ruff_protocol import RuffProtocol
from utils.policy.violations import PolicyResult


class PolicyEnforcer:
    """Main policy enforcement coordinator."""

    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or Path.cwd()
        self.config = load_policy_config(self.repo_root)
        self.cache = PolicyCache(
            self.repo_root / ".compounding-cache", ttl_seconds=self.config.cache_ttl_seconds
        )
        self.context = PolicyContext.load_from_disk()
        self.context.config = self.config.model_dump()

        self.static_validators = [
            ImportProtocol(self.context),
            FileSizeProtocol(self.context),
            RuffProtocol(self.context),
        ]

    def check_file(self, file_path: Path) -> PolicyResult:
        """Check single file against all policies."""
        cached = self.cache.get(file_path)
        if cached:
            return cached

        violations = []

        for validator in self.static_validators:
            violations.extend(validator.check(file_path))

        result = PolicyResult(
            violations=violations,
            files_checked=1,
            files_with_violations=1 if violations else 0,
            errors=sum(1 for v in violations if v.severity == "ERROR"),
            warnings=sum(1 for v in violations if v.severity == "WARNING"),
            infos=sum(1 for v in violations if v.severity == "INFO"),
        )

        self.cache.set(file_path, result)
        return result

    def check_repo(self, paths: list[Path] | None = None) -> PolicyResult:
        """Check multiple files or entire repo."""
        if paths is None:
            paths = list(self.repo_root.rglob("*.py"))

        all_violations = []
        for path in paths:
            result = self.check_file(path)
            all_violations.extend(result.violations)

        return PolicyResult(
            violations=all_violations,
            files_checked=len(paths),
            files_with_violations=len([p for p in paths if self.check_file(p).violations]),
            errors=sum(1 for v in all_violations if v.severity == "ERROR"),
            warnings=sum(1 for v in all_violations if v.severity == "WARNING"),
            infos=sum(1 for v in all_violations if v.severity == "INFO"),
        )
