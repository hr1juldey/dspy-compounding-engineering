"""
GraphRAG time estimation and warnings.

Shows Rich-formatted warnings before long-running indexing operations.
"""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from utils.knowledge.graphrag_timing import GraphRAGTimingCache


class GraphRAGTimeEstimator:
    """
    Estimates GraphRAG indexing time and shows warnings.

    Uses timing cache to predict duration and warn users.
    """

    def __init__(self):
        """Initialize time estimator with timing cache."""
        self.timing_cache = GraphRAGTimingCache()

    def estimate_and_warn(
        self, root_dir: str | Path, console: Console, threshold_sec: int = 300
    ) -> tuple[float, int]:
        """
        Estimate indexing time and show warning if exceeds threshold.

        Args:
            root_dir: Root directory to index
            console: Rich console for output
            threshold_sec: Warning threshold in seconds (default: 5 minutes)

        Returns:
            Tuple of (estimated_seconds, file_count)
        """
        # Count Python files
        root_path = Path(root_dir)
        python_files = list(root_path.rglob("*.py"))
        file_count = len(python_files)

        if file_count == 0:
            console.print("[yellow]No Python files found to index[/yellow]")
            return 0.0, 0

        # Estimate time
        estimated_sec = self.timing_cache.estimate_time(file_count)
        estimated_min = estimated_sec / 60.0

        # Show estimation
        heuristics = self.timing_cache.get_heuristics()

        # Build timing table
        table = Table(title="GraphRAG Indexing Estimation", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Python files", str(file_count))
        table.add_row("Estimated time", f"{estimated_min:.1f} minutes")
        table.add_row("Per-file avg", f"{heuristics['per_file_ms']:.0f}ms")

        if heuristics["total_runs"] > 0:
            table.add_row("Based on", f"{heuristics['total_files_indexed']} previous files")
        else:
            table.add_row("Note", "First run (conservative estimate)")

        console.print(table)
        console.print()

        # Show warning if exceeds threshold
        if estimated_sec > threshold_sec:
            self._show_warning(console, estimated_min)

        return estimated_sec, file_count

    def _show_warning(self, console: Console, estimated_min: float):
        """Show warning panel for long indexing times."""
        warning_text = (
            f"[yellow]⚠️  GraphRAG indexing will take approximately "
            f"[bold]{estimated_min:.1f} minutes[/bold][/yellow]\n\n"
            "[dim]This is significantly longer than standard indexing because:[/dim]\n"
            "  • AST parsing for entity extraction\n"
            "  • Relation graph construction\n"
            "  • Embedding generation for all entities\n"
            "  • NetworkX graph building\n\n"
            "[cyan]💡 Tip:[/cyan] GraphRAG provides deep code understanding but "
            "isn't always needed.\n"
            "   Consider using standard indexing for quick iterations."
        )

        console.print(
            Panel(
                warning_text,
                title="[bold red]Long Indexing Time Expected[/bold red]",
                border_style="yellow",
            )
        )
        console.print()
