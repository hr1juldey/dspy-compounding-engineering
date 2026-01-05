"""Event value objects and constants."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class OperationEvent:
    """Value object: Single operation event."""

    timestamp: str
    operation: str
    subject: str
    status: str
    duration_ms: int
    details: Dict[str, Any]
    error: Optional[str] = None


class EventStatus:
    """Event status constants."""

    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class OperationType:
    """Event operation type constants."""

    WEB_SEARCH = "web_search"
    CODE_ANALYSIS = "code_analysis"
    FILE_OPERATION = "file_operation"
    TOOL_EXECUTION = "tool_execution"
