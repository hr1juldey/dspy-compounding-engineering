"""Policy state management with persistence."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from utils.policy.violations import Violation


class PolicyState(str, Enum):
    """State machine for policy enforcement."""

    INIT = "init"
    CONFIGURE = "configure"
    VALIDATE = "validate"
    ACTIVE = "active"
    VIOLATION_REVIEW = "violation_review"
    FIX_MODE = "fix_mode"


@dataclass
class PolicyContext:
    """Persistent state across policy enforcement sessions."""

    state: PolicyState = PolicyState.INIT
    config: dict | None = None
    recent_violations: list[Violation] = field(default_factory=list)
    fixed_violations: list[Violation] = field(default_factory=list)
    violation_patterns: dict[str, int] = field(default_factory=dict)
    files_checked: int = 0
    last_check_time: datetime | None = None
    session_id: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Serialize for JSON persistence."""
        return {
            "state": self.state.value,
            "config": self.config,
            "recent_violations": [v.model_dump() for v in self.recent_violations],
            "fixed_violations": [v.model_dump() for v in self.fixed_violations],
            "violation_patterns": self.violation_patterns,
            "files_checked": self.files_checked,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PolicyContext":
        """Deserialize from JSON."""
        return cls(
            state=PolicyState(data["state"]),
            config=data.get("config"),
            recent_violations=[Violation(**v) for v in data.get("recent_violations", [])],
            fixed_violations=[Violation(**v) for v in data.get("fixed_violations", [])],
            violation_patterns=data.get("violation_patterns", {}),
            files_checked=data.get("files_checked", 0),
            last_check_time=(
                datetime.fromisoformat(data["last_check_time"])
                if data.get("last_check_time")
                else None
            ),
            session_id=data.get("session_id", datetime.now().isoformat()),
        )

    def save(self, path: Path = Path(".compounding-policy-state.json")):
        """Save to disk."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_disk(cls, path: Path = Path(".compounding-policy-state.json")) -> "PolicyContext":
        """Load from disk or create new."""
        if path.exists():
            with open(path) as f:
                return cls.from_dict(json.load(f))
        return cls()
