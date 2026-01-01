"""GraphRAG code analysis workflow."""

import json
import os
from datetime import datetime

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from agents.graphrag.architecture_mapper import ArchitectureMapperModule
from agents.graphrag.code_navigator import CodeNavigatorModule
from agents.graphrag.dependency_tracer import DependencyTracerModule
from agents.graphrag.impact_analyzer import ImpactAnalyzerModule
from agents.graphrag.multi_hop_searcher import MultiHopSearcher

console = Console()


def _display_navigation_report(result):
    """Display CodeNavigator results."""
    console.print(Panel(f"[bold]Entity:[/bold] {result.entity_name}", border_style="cyan"))

    if result.entity_details:
        details = result.entity_details
        console.print("\n[bold cyan]Details:[/bold cyan]")
        console.print(f"  Type: {details.get('type', 'Unknown')}")
        console.print(f"  File: {details.get('file_path', 'Unknown')}")
        if details.get("line_start"):
            console.print(f"  Lines: {details['line_start']}-{details.get('line_end', '?')}")
        if details.get("docstring"):
            console.print(f"  Docstring: {details['docstring'][:100]}...")

    if result.relationships:
        console.print("\n[bold cyan]Relationships:[/bold cyan]")
        for rel_type, entities in result.relationships.items():
            if entities:
                console.print(f"\n  {rel_type.upper()}:")
                for entity in entities[:10]:  # Limit to 10
                    name = entity.get("name", "Unknown")
                    file = entity.get("file_path", "")
                    console.print(f"    - {name} ({file})")

    console.print(f"\n[bold]Impact Scope:[/bold] {result.impact_scope}")

    if result.next_actions:
        console.print("\n[bold cyan]Suggested Actions:[/bold cyan]")
        for action in result.next_actions:
            console.print(f"  - {action}")


def _display_impact_report(result):
    """Display ImpactAnalyzer results."""
    console.print(
        Panel(
            f"[bold]Analyzing impact of {result.change_type} on:[/bold] {result.target_entity}",
            border_style="yellow",
        )
    )

    if result.direct_dependents:
        table = Table(title="Direct Dependents", border_style="yellow")
        table.add_column("Entity", style="cyan")
        table.add_column("Type", style="white")
        table.add_column("File", style="dim", overflow="fold")

        for dep in result.direct_dependents[:20]:
            table.add_row(
                dep.get("name", "Unknown"),
                dep.get("type", "Unknown"),
                dep.get("file_path", ""),
            )

        console.print(table)
        console.print(f"[dim]Showing 20 of {len(result.direct_dependents)} dependents[/dim]\n")

    if result.blast_radius:
        console.print("[bold]Blast Radius:[/bold]")
        for category, count in result.blast_radius.items():
            console.print(f"  {category}: {count}")

    console.print(f"\n[bold]Risk Assessment:[/bold] {result.risk_assessment}")

    if result.recommended_approach:
        console.print(
            Panel(
                result.recommended_approach,
                title="Recommended Approach",
                border_style="green",
            )
        )


def _display_architecture_report(result):
    """Display ArchitectureMapper results."""
    console.print(Panel("[bold]Architecture Analysis[/bold]", border_style="blue"))

    if result.hubs:
        table = Table(title="Key Hubs (PageRank)", border_style="blue")
        table.add_column("Entity", style="cyan")
        table.add_column("Type", style="white")
        table.add_column("Score", justify="right", style="yellow")
        table.add_column("File", style="dim", overflow="fold")

        for hub in result.hubs[:15]:
            table.add_row(
                hub.get("entity_name", "Unknown"),
                hub.get("entity_type", "Unknown"),
                f"{hub.get('pagerank_score', 0):.4f}",
                hub.get("file_path", ""),
            )

        console.print(table)

    if result.clusters:
        console.print("\n[bold]Clusters (Communities):[/bold]")
        for cluster in result.clusters[:5]:
            console.print(f"\n  Cluster {cluster.get('cluster_id', '?')}:")
            members = cluster.get("members", [])
            for member in members[:10]:
                console.print(f"    - {member}")
            if len(members) > 10:
                console.print(f"    [dim]... and {len(members) - 10} more[/dim]")

    if result.bottlenecks:
        console.print("\n[bold red]Bottlenecks:[/bold red]")
        for bottleneck in result.bottlenecks:
            console.print(f"  - {bottleneck}")


def _display_dependency_report(result):
    """Display DependencyTracer results."""
    console.print(
        Panel(
            f"[bold]Dependency Path:[/bold] {result.source_entity} → {result.target_entity}",
            border_style="magenta",
        )
    )

    if result.found and result.shortest_path:
        console.print(f"\n[bold green]Path Found ({len(result.shortest_path)} hops):[/bold green]")
        for i, entity in enumerate(result.shortest_path, 1):
            name = entity.get("name", "Unknown")
            file = entity.get("file_path", "")
            console.print(f"  {i}. {name} ({file})")

    if result.circular_dependencies:
        console.print("\n[bold red]⚠ Circular Dependency Detected![/bold red]")
        cycle_path = result.circular_dependencies.get("cycle_path", [])
        console.print(f"Cycle: {' → '.join(cycle_path)}")

    if result.coupling_metrics:
        console.print("\n[bold]Coupling Metrics:[/bold]")
        for metric, value in result.coupling_metrics.items():
            console.print(f"  {metric}: {value}")

    if result.recommendations:
        console.print(
            Panel(
                "\n".join(f"- {rec}" for rec in result.recommendations),
                title="Recommendations",
                border_style="green",
            )
        )


def _save_analysis_result(analysis_type: str, entity: str, result: dict):
    """Save analysis result to file."""
    analysis_dir = "analysis"
    os.makedirs(analysis_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_entity = "".join(c if c.isalnum() else "_" for c in entity)
    filename = f"{timestamp}_{analysis_type}_{safe_entity}.json"
    filepath = os.path.join(analysis_dir, filename)

    with open(filepath, "w") as f:
        json.dump(result, f, indent=2, default=str)

    console.print(f"\n[dim]Saved to: {filepath}[/dim]")
    return filepath


def run_analyze(
    entity: str,
    analysis_type: str = "navigate",
    max_depth: int = 2,
    change_type: str = "Modify",
    save: bool = True,
):
    """
    Analyze code using GraphRAG agents.

    Args:
        entity: Entity to analyze (function, class, or module name)
        analysis_type: Analysis type (navigate|impact|deps|arch|search)
        max_depth: Maximum relationship depth (1-3)
        change_type: Change type for impact analysis
        save: Whether to save results to file
    """
    console.print(
        Panel.fit(
            f"[bold]GraphRAG Code Analysis[/bold]\nType: {analysis_type} | Entity: {entity}",
            border_style="blue",
        )
    )

    try:
        if analysis_type == "navigate":
            with console.status("[cyan]Navigating entity relationships..."):
                agent = CodeNavigatorModule()
                result = agent(query=entity, max_depth=max_depth)

            _display_navigation_report(result)

            if save and hasattr(result, "model_dump"):
                _save_analysis_result("navigate", entity, result.model_dump())

        elif analysis_type == "impact":
            with console.status("[cyan]Analyzing blast radius..."):
                agent = ImpactAnalyzerModule()
                result = agent(target_entity=entity, change_type=change_type)

            _display_impact_report(result)

            if save and hasattr(result, "model_dump"):
                _save_analysis_result("impact", entity, result.model_dump())

        elif analysis_type == "arch":
            with console.status("[cyan]Mapping architecture..."):
                agent = ArchitectureMapperModule()
                scope = "Module" if entity != "." else "Global"
                result = agent(analysis_scope=scope, focus_area=entity if entity != "." else None)

            _display_architecture_report(result)

            if save and hasattr(result, "model_dump"):
                _save_analysis_result("arch", entity, result.model_dump())

        elif analysis_type == "deps":
            # For deps, entity should be "source:target" or just "source" for cycle detection
            if ":" in entity:
                source, target = entity.split(":", 1)
            else:
                source = entity
                target = "detect_cycles"

            with console.status("[cyan]Tracing dependencies..."):
                agent = DependencyTracerModule()
                result = agent(source_entity=source, target_entity=target)

            _display_dependency_report(result)

            if save and hasattr(result, "model_dump"):
                _save_analysis_result("deps", entity, result.model_dump())

        elif analysis_type == "search":
            # For search, entity should be "start:target"
            if ":" in entity:
                start, target = entity.split(":", 1)
            else:
                console.print("[red]Error: Search requires format 'start:target'[/red]")
                return

            with console.status("[cyan]Searching multi-hop path..."):
                agent = MultiHopSearcher()
                result = agent(start_query=start, target_query=target, max_hops=max_depth)

            if result.found:
                console.print(f"\n[green]✓ Path found ({result.hops} hops)![/green]")
                console.print(Markdown(result.reasoning))

                if result.path:
                    table = Table(title="Path", border_style="green")
                    table.add_column("Step", justify="right")
                    table.add_column("Entity", style="cyan")
                    table.add_column("Type", style="white")

                    for i, step in enumerate(result.path, 1):
                        table.add_row(str(i), step.get("name", "?"), step.get("type", "?"))

                    console.print(table)
            else:
                console.print("\n[yellow]✗ No path found[/yellow]")
                console.print(Markdown(result.reasoning))

            if save and hasattr(result, "model_dump"):
                _save_analysis_result("search", entity, result.model_dump())

        else:
            console.print(f"[red]Unknown analysis type: {analysis_type}[/red]")
            console.print("Valid types: navigate, impact, arch, deps, search")

    except Exception as e:
        console.print(f"[red]Analysis failed: {e}[/red]")
        import traceback

        console.print(f"[dim]{traceback.format_exc()}[/dim]")
