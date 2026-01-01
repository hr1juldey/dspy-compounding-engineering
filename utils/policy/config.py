"""Policy configuration loader."""

from pathlib import Path

import yaml
from pydantic import BaseModel


class PolicyConfig(BaseModel):
    """Policy configuration schema."""

    max_file_lines: int = 100
    block_threshold_lines: int = 600
    allow_relative_imports: bool = False
    enforce_ruff: bool = True
    naming_patterns: dict[str, str] = {}
    enforce_solid: bool = True
    enforce_dry: bool = True
    enforce_ddd: bool = True
    cache_ttl_seconds: int = 3600
    parallel_validation: bool = True
    relative_import_severity: str = "ERROR"
    file_size_severity: str = "WARNING"
    solid_severity: str = "WARNING"
    dry_severity: str = "WARNING"
    ddd_severity: str = "WARNING"


def load_policy_config(repo_root: Path) -> PolicyConfig:
    """Load policy config with inheritance."""
    config_path = repo_root / ".compounding-policy.yaml"

    if config_path.exists():
        with open(config_path) as f:
            user_config = yaml.safe_load(f)
        return PolicyConfig(**user_config)

    return PolicyConfig()
