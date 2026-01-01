"""Knowledge base maintenance workflow."""

import json
import os

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

from agents.knowledge_gardener.orchestrator import KnowledgeGardenerOrchestrator
from utils.knowledge import KnowledgeBase
from utils.memory.maintainer import AgentMemoryMaintainer

console = Console()


def _get_kb_stats(kb: KnowledgeBase) -> dict:
    """Get current knowledge base statistics."""
    try:
        kb_dir = kb.knowledge_dir
        if not os.path.exists(kb_dir):
            return {"entries": 0, "size_kb": 0}

        # Count entries
        entries = 0
        total_size = 0

        for file in os.listdir(kb_dir):
            if file.endswith(".json"):
                file_path = os.path.join(kb_dir, file)
                try:
                    with open(file_path) as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            entries += len(data)
                        else:
                            entries += 1
                    total_size += os.path.getsize(file_path)
                except Exception:
                    pass

        return {"entries": entries, "size_kb": total_size / 1024}
    except Exception:
        return {"entries": 0, "size_kb": 0}


def _consolidate_knowledge(kb: KnowledgeBase):
    """Consolidate knowledge base using KnowledgeGardener."""
    console.print("\n[bold cyan]Consolidating Knowledge Base[/bold cyan]")

    # Get current KB entries
    current_entries = []
    try:
        kb_dir = kb.knowledge_dir
        for file in os.listdir(kb_dir):
            if file.endswith(".json"):
                file_path = os.path.join(kb_dir, file)
                with open(file_path) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        current_entries.extend(data)
                    else:
                        current_entries.append(data)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not load KB entries: {e}[/yellow]")
        return

    if not current_entries:
        console.print("[yellow]No KB entries found to consolidate[/yellow]")
        return

    console.print(f"[dim]Found {len(current_entries)} KB entries[/dim]")

    # Run KnowledgeGardener orchestrator
    with console.status("[cyan]Running Knowledge Gardener..."):
        orchestrator = KnowledgeGardenerOrchestrator()

        result = orchestrator(
            current_knowledge_json=json.dumps(current_entries, indent=2),
            agent_memories_json="[]",  # Will be filled by compress-memory action
            recent_commits_json="[]",  # Will be filled by index-commits action
        )

    # Display results
    console.print("\n[green]✓ Consolidation complete[/green]")

    if result.pattern_summary:
        console.print(
            Panel(
                result.pattern_summary,
                title="Identified Patterns",
                border_style="cyan",
            )
        )

    console.print("\n[dim]Compressed knowledge available in result[/dim]")


def _compress_agent_memories():
    """Compress agent memories across all agents."""
    console.print("\n[bold cyan]Compressing Agent Memories[/bold cyan]")

    # Known agent names from the codebase
    agent_names = [
        "code_navigator",
        "impact_analyzer",
        "architecture_mapper",
        "dependency_tracer",
        "multi_hop_searcher",
        "knowledge_gardener",
        "repo_research_analyst",
        "best_practices_researcher",
        "framework_docs_researcher",
    ]

    compressed_count = 0

    with Progress() as progress:
        task = progress.add_task("[cyan]Compressing memories...", total=len(agent_names))

        for agent_name in agent_names:
            progress.update(task, description=f"[cyan]Compressing {agent_name}...")

            try:
                maintainer = AgentMemoryMaintainer()
                maintainer.compress_agent_memories(agent_name)
                compressed_count += 1
            except Exception as e:
                console.print(f"[yellow]Warning: Could not compress {agent_name}: {e}[/yellow]")

            progress.advance(task)

    console.print(
        f"[green]✓ Compressed {compressed_count}/{len(agent_names)} agent memories[/green]"
    )


def _index_git_commits(limit: int):
    """Index recent git commits as shared memory."""
    console.print(f"\n[bold cyan]Indexing Git Commits (last {limit})[/bold cyan]")

    with console.status("[cyan]Indexing commits..."):
        maintainer = AgentMemoryMaintainer()
        indexed_count = maintainer.index_git_commits(limit=limit)

    console.print(f"[green]✓ Indexed {indexed_count} commits to shared memory[/green]")


def run_garden(action: str = "consolidate", limit: int = 100):
    """
    Maintain and optimize the knowledge base.

    Args:
        action: Action to perform (consolidate|compress-memory|index-commits|all)
        limit: Maximum commits to index (for index-commits action)
    """
    console.print(
        Panel.fit(
            f"[bold]Knowledge Base Maintenance[/bold]\nAction: {action}",
            border_style="blue",
        )
    )

    kb = KnowledgeBase()

    # Get before stats
    console.rule("[bold]Before[/bold]")
    before_stats = _get_kb_stats(kb)
    console.print(f"  KB Entries: {before_stats['entries']}")
    console.print(f"  KB Size: {before_stats['size_kb']:.2f} KB")

    # Execute action
    if action == "consolidate":
        _consolidate_knowledge(kb)

    elif action == "compress-memory":
        _compress_agent_memories()

    elif action == "index-commits":
        _index_git_commits(limit)

    elif action == "all":
        console.print("\n[bold]Running full maintenance cycle...[/bold]")
        _index_git_commits(limit)
        _compress_agent_memories()
        _consolidate_knowledge(kb)

    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Valid actions: consolidate, compress-memory, index-commits, all")
        return

    # Get after stats
    console.rule("[bold]After[/bold]")
    after_stats = _get_kb_stats(kb)
    console.print(f"  KB Entries: {after_stats['entries']}")
    console.print(f"  KB Size: {after_stats['size_kb']:.2f} KB")

    # Show improvement
    if before_stats["entries"] != after_stats["entries"]:
        diff = after_stats["entries"] - before_stats["entries"]
        sign = "+" if diff > 0 else ""
        console.print(f"  [dim]Change: {sign}{diff} entries[/dim]")

    console.print("\n[bold green]✓ Garden maintenance complete[/bold green]")
