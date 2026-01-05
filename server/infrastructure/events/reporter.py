"""Event reporting and formatting service."""

from typing import Any, Dict, List

from infrastructure.events.event import OperationEvent


class EventReporter:
    """Formats events for agents and human consumption."""

    def __init__(self, events: List[OperationEvent]):
        """Initialize with list of events."""
        self.events = events

    def get_summary(self) -> Dict[str, Any]:
        """Get structured summary for agents to parse."""
        return {
            "total": len(self.events),
            "successful": sum(1 for e in self.events if e.status == "success"),
            "failed": sum(1 for e in self.events if e.status in ["failed", "timeout"]),
            "operations": [
                {
                    "operation": e.operation,
                    "subject": e.subject,
                    "status": e.status,
                    "duration_ms": e.duration_ms,
                    "details": e.details,
                    "error": e.error,
                }
                for e in self.events
            ],
        }

    def get_report(self) -> str:
        """Get human-readable formatted report."""
        if not self.events:
            return "No operations performed."

        lines = ["Operation Report", "=" * 60]

        for i, e in enumerate(self.events, 1):
            symbol = "✓" if e.status == "success" else "✗"
            lines.append(f"\n[{i}] {symbol} {e.operation.upper()}")
            lines.append(f"    Subject: {e.subject}")
            lines.append(f"    Status: {e.status}")
            lines.append(f"    Duration: {e.duration_ms}ms")

            if e.details:
                for k, v in e.details.items():
                    lines.append(f"    {k}: {v}")

            if e.error:
                lines.append(f"    Error: {e.error}")

        total_ms = sum(e.duration_ms for e in self.events)
        lines.append(f"\nTotal Time: {total_ms}ms")

        return "\n".join(lines)
