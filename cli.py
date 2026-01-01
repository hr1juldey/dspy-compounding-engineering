import math
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from config import configure_dspy
from utils.io import get_system_status
from utils.knowledge import KnowledgeBase
from workflows.analyze import run_analyze
from workflows.check import run_check
from workflows.codify import run_codify
from workflows.garden import run_garden
from workflows.generate_command import run_generate_command
from workflows.plan import run_plan
from workflows.review import run_review
from workflows.triage import run_triage
from workflows.work import run_unified_work

console = Console()
app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})


@app.callback()
def main(
    env_file: Annotated[
        Optional[Path],
        typer.Option(
            "--env-file",
            "-e",
            help="Explicit path to a .env file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
):
    """
    Compounding Engineering (DSPy Edition)

    Available Commands:
    - triage          - Categorize findings for todo system
    - plan            - Generate project plans from descriptions
    - work            - Execute todos and plans with ReAct agents
    - review          - Multi-agent exhaustive code review
    - analyze         - GraphRAG code analysis (NEW)
    - garden          - Knowledge base maintenance (NEW)
    - check           - Policy enforcement checks (NEW)
    - migrate         - Migrate to .compounding/ structure (NEW)
    - generate-command - Meta-command generator
    - codify          - Codify feedback into knowledge base
    - compress-kb     - Compress AI.md knowledge base
    - index           - Index codebase for semantic search
    - status          - System diagnostics
    """
    configure_dspy(env_file=str(env_file) if env_file else None)


@app.command()
def triage():
    """
    Triage and categorize findings for the CLI todo system.
    """
    run_triage()


@app.command()
def analyze(
    entity: str = typer.Argument(..., help="Entity to analyze (function, class, or module name)"),
    analysis_type: str = typer.Option(
        "navigate", "--type", "-t", help="Analysis type: navigate|impact|deps|arch|search"
    ),
    max_depth: int = typer.Option(2, "--depth", "-d", help="Max relationship depth (1-3)"),
    change_type: str = typer.Option("Modify", "--change", help="Change type for impact analysis"),
    no_save: bool = typer.Option(False, "--no-save", help="Don't save results to file"),
):
    """
    Analyze code using GraphRAG agents.

    Examples:
        compounding analyze CodeNavigatorModule --type navigate
        compounding analyze process_request --type impact --change Delete
        compounding analyze src.utils:target.function --type deps
        compounding analyze . --type arch
        compounding analyze start_query:end_query --type search
    """
    run_analyze(
        entity=entity,
        analysis_type=analysis_type,
        max_depth=max_depth,
        change_type=change_type,
        save=not no_save,
    )


@app.command()
def plan(feature_description: str):
    """
    Transform feature descriptions into well-structured project plans.
    """
    run_plan(feature_description)


@app.command()
def work(
    pattern: Optional[str] = typer.Argument(None, help="Todo ID, plan file, or pattern"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Dry run mode"),
    sequential: bool = typer.Option(
        False,
        "--sequential",
        "-s",
        help="Execute todos sequentially instead of in parallel",
    ),
    max_workers: int = typer.Option(
        3, "--workers", "-w", help="Maximum number of parallel workers"
    ),
    in_place: bool = typer.Option(
        True,
        "--in-place/--worktree",
        help="Apply changes in-place to current branch (default) or use isolated worktree",
    ),
):
    """
    Unified work command using DSPy ReAct.

    Automatically detects input type:
    - Todo ID: "001"
    - Plan file: "plans/feature.md"
    - Pattern: "p1", "security"

    **Migration Note**: This command replaces the old `resolve-todo` command.
    All todo resolution and plan execution now go through this unified interface.
    """
    # Validate pattern input for security
    if pattern:
        if len(pattern) > 256:
            raise typer.BadParameter("Pattern too long (max 256 characters)")
        if "\0" in pattern:
            raise typer.BadParameter("Null bytes not allowed in pattern")
        if ".." in pattern or pattern.startswith("/"):
            raise typer.BadParameter("Path traversal sequences not allowed")

    run_unified_work(
        pattern=pattern,
        dry_run=dry_run,
        parallel=not sequential,
        max_workers=max_workers,
        in_place=in_place,
    )


@app.command()
def review(
    pr_url_or_id: str = typer.Argument(
        "latest", help="PR number, URL, branch name, or 'latest' for local changes"
    ),
    project: bool = typer.Option(
        False, "--project", "-p", help="Review entire project instead of just changes"
    ),
):
    """
    Perform exhaustive multi-agent code reviews.

    Examples:
        compounding review              # Review local changes
        compounding review --project    # Review entire project
        compounding review 123          # Review PR #123
    """
    run_review(pr_url_or_id, project=project)


@app.command()
def generate_command(
    description: str = typer.Argument(
        ..., help="Natural language description of what the command should do"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Show what would be created without writing files",
    ),
):
    """
    Generate a new CLI command from a natural language description.

    This meta-command creates new commands for the Compounding Engineering plugin.
    It analyzes the description, designs an appropriate workflow and agents,
    and generates all necessary code.

    Examples:
        compounding generate-command "Create a command to format code"
        compounding generate-command "Add a lint command that checks Python style"
        compounding generate-command --dry-run "Create a deployment workflow"
    """
    run_generate_command(description=description, dry_run=dry_run)


@app.command()
def codify(
    feedback: str = typer.Argument(..., help="The feedback, instruction, or learning to codify"),
    source: str = typer.Option(
        "manual_input",
        "--source",
        "-s",
        help="Source of the feedback (e.g., 'review', 'retro')",
    ),
):
    """
    Codify feedback into the knowledge base.

    This command uses the FeedbackCodifier agent to transform raw feedback
    into structured improvements (documentation, rules, patterns) and saves
    them to the persistent knowledge base.

    Examples:
        compounding codify "Always use strict typing in Python files"
        compounding codify "We should use factory pattern for creating agents" --source retro
    """
    run_codify(feedback=feedback, source=source)


@app.command()
def check(
    paths: Annotated[list[str], typer.Argument(help="Files or directories to check")] = None,
    auto_fix: Annotated[
        bool, typer.Option("--fix", help="Auto-fix violations (runs ruff --fix)")
    ] = False,
    staged_only: Annotated[bool, typer.Option("--staged", help="Check only staged files")] = False,
):
    """
    Run policy enforcement checks on codebase.

    Validates:
    - Import rules (no relative imports)
    - File size limits (100 lines max)
    - Ruff linting and formatting

    Examples:
        compounding check                    # Check all Python files
        compounding check --staged           # Check staged files only
        compounding check src/ --fix         # Check and auto-fix src/
        compounding check utils/policy/      # Check specific directory
    """
    exit_code = run_check(paths=paths, auto_fix=auto_fix, staged_only=staged_only)
    raise typer.Exit(code=exit_code)


@app.command()
def garden(
    action: str = typer.Argument(
        "consolidate", help="Action: consolidate|compress-memory|index-commits|all"
    ),
    limit: int = typer.Option(100, "--limit", "-l", help="Max commits to index"),
):
    """
    Maintain and optimize the knowledge base.

    Examples:
        compounding garden consolidate       # Clean up KB duplicates
        compounding garden index-commits     # Index recent git commits
        compounding garden compress-memory   # Compress agent memories
        compounding garden all               # Run full maintenance
    """
    run_garden(action=action, limit=limit)


@app.command()
def compress_kb(
    ratio: float = typer.Option(0.5, "--ratio", "-r", help="Target compression ratio (0.0 to 1.0)"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show stats without modifying the file"
    ),
):
    """
    Compress the AI knowledge base (AI.md) using LLM.

    This command semantically compresses the knowledge base to reduce token usage
    while preserving key learnings and structure.
    """
    # Input validation for ratio parameter
    if not isinstance(ratio, (int, float)):
        raise ValueError("Ratio must be a number")
    if not (0.0 <= ratio <= 1.0):
        raise ValueError("Ratio must be between 0.0 and 1.0")
    if not math.isfinite(ratio):
        raise ValueError("Ratio must be a finite number (not NaN or infinity)")

    kb = KnowledgeBase()
    kb.compress_ai_md(ratio=ratio, dry_run=dry_run)


@app.command()
def index(
    root_dir: Annotated[str, typer.Option("--dir", "-d", help="Root directory to index")] = ".",
    recreate: Annotated[
        bool, typer.Option("--recreate", "-r", help="Force recreation of the vector collection")
    ] = False,
):
    """
    Index the codebase for semantic search using Vector Embeddings.
    Use this to enable agents to find relevant code snippets.
    Performs smart incremental indexing (skips unchanged files).
    """
    kb = KnowledgeBase()
    kb.index_codebase(root_dir=root_dir, force_recreate=recreate)


@app.command()
def migrate():
    """
    Migrate from old directory structure to new .compounding/ structure.

    Moves:
    - .knowledge/ → .compounding/knowledge/
    - plans/ → .compounding/plans/
    - todos/ → .compounding/todos/
    - analysis/ → .compounding/analysis/
    """
    from rich.panel import Panel

    from utils.paths import get_paths

    console.print(
        Panel.fit(
            "[bold]Migrating to .compounding/ Directory Structure[/bold]",
            border_style="blue",
        )
    )

    paths = get_paths()
    migrated = paths.migrate_legacy_structure()

    if migrated:
        console.print("\n[green]✓ Migration complete![/green]\n")
        console.print("[bold]Migrated directories:[/bold]")
        for item in migrated:
            console.print(f"  {item}")
        console.print("\n[dim]Old directories have been moved to .compounding/[/dim]")
        console.print("[dim]The system is now portable to any repository![/dim]")
    else:
        console.print("\n[yellow]No migration needed - already using .compounding/[/yellow]")


@app.command()
def status():
    """
    Check the current status of external services (Qdrant, API keys).
    """
    from rich.panel import Panel

    status_text = get_system_status()
    console.print(Panel(status_text, title="System Diagnostics", border_style="cyan"))


if __name__ == "__main__":
    app()
