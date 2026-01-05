"""Decorator for MCP tool integration with event tracking."""

from functools import wraps
from typing import Any, Callable

from server.infrastructure.events.collector import event_collector
from server.infrastructure.events.reporter import EventReporter


def track_tool_execution(total_stages: int = 4):
    """Decorator: Automatically handles event collection for MCP tools.

    Eliminates repetitive code in tool functions by:
    1. Clearing events at start
    2. Adding events/report to response automatically
    3. Handling exceptions with partial event reporting

    Args:
        total_stages: Number of progress stages (default 4)

    Usage:
        @analysis_server.tool(task=True)
        @track_tool_execution(total_stages=4)
        async def generate_plan(repo_root: str, feature: str, ctx=None) -> dict:
            await ctx.report_progress(progress=2, total=4, message="Stage 2...")
            return {"success": True, "plan": result}
            # Decorator automatically adds "events" and "report"
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, ctx: Any | None = None, **kwargs: Any) -> dict:
            # Clear previous events
            event_collector.clear()

            try:
                # Initial progress
                if ctx:
                    await ctx.report_progress(
                        progress=1,
                        total=total_stages,
                        message=f"Starting {func.__name__}...",
                    )

                # Call actual tool function
                result = await func(*args, ctx=ctx, **kwargs)

                # Ensure result is dict
                if not isinstance(result, dict):
                    result = {"success": True, "result": result}

                # Add events and report to response
                reporter = EventReporter(event_collector.get_events())
                result["events"] = reporter.get_summary()
                result["report"] = reporter.get_report()

                return result

            except Exception as e:
                # Return error response with partial events
                reporter = EventReporter(event_collector.get_events())
                return {
                    "success": False,
                    "error": str(e),
                    "events": reporter.get_summary(),
                    "report": reporter.get_report(),
                }

        return wrapper

    return decorator
