"""Event collection service (Domain Service)."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from infrastructure.events.event import OperationEvent


class EventCollector:
    """Singleton: Collects operation events across all tools."""

    _instance = None

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.events: List[OperationEvent] = []
        return cls._instance

    def emit(
        self,
        operation: str,
        subject: str,
        status: str,
        details: Dict[str, Any],
        duration_ms: int,
        error: Optional[str] = None,
    ) -> None:
        """Record an operation event."""
        event = OperationEvent(
            timestamp=datetime.now().isoformat(),
            operation=operation,
            subject=subject,
            status=status,
            duration_ms=duration_ms,
            details=details,
            error=error,
        )
        self.events.append(event)

    def get_events(self) -> List[OperationEvent]:
        """Get all collected events."""
        return self.events.copy()

    def clear(self) -> None:
        """Clear all events (reset for new operation)."""
        self.events = []


# Global singleton instance
event_collector = EventCollector()
