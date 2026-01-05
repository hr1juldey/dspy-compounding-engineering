import math
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from server.config import configure_dspy
from utils.io import get_system_status
from utils.io.logger import configure_logging
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
    skip_warmup: Annotated[
        bool,
        typer.Option(
            "--skip-warmup",
            help="Skip LLM/embedder warmup test on startup",
        ),
    ] = False,
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
    - warmup          - Test LLM and embedder initialization
    - status          - System diagnostics
    """
    configure_logging()
    configure_dspy(env_file=str(env_file) if env_file else None)

    # Auto-warmup on first invocation (can be skipped with --skip-warmup)
    if not skip_warmup:
        try:
            from utils.knowledge.utils.warmup import WarmupTest

            tester = WarmupTest()
            tester.run_all()
        except Exception as e:
            console.print(
                f"\n[bold red]System warmup failed:[/bold red] {e}\n"
                f"[dim]Use --skip-warmup to bypass this check[/dim]"
            )
            raise typer.Exit(code=1) from e


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
        ce analyze CodeNavigatorModule --type navigate
        ce analyze process_request --type impact --change Delete
        ce analyze src.utils:target.function --type deps
        ce analyze . --type arch
        ce analyze start_query:end_query --type search
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
        ce review              # Review local changes
        ce review --project    # Review entire project
        ce review 123          # Review PR #123
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
        ce generate-command "Create a command to format code"
        ce generate-command "Add a lint command that checks Python style"
        ce generate-command --dry-run "Create a deployment workflow"
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
        ce codify "Always use strict typing in Python files"
        ce codify "We should use factory pattern for creating agents" --source retro
    """
    run_codify(feedback=feedback, source=source)


@app.command()
def check(
    paths: Annotated[list[str] | None, typer.Argument(help="Files or directories to check")] = None,
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
        ce check                    # Check all Python files
        ce check --staged           # Check staged files only
        ce check src/ --fix         # Check and auto-fix src/
        ce check utils/policy/      # Check specific directory
    """
    exit_code = run_check(".", paths=paths, auto_fix=auto_fix, staged_only=staged_only)
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
        ce garden consolidate       # Clean up KB duplicates
        ce garden index-commits     # Index recent git commits
        ce garden compress-memory   # Compress agent memories
        ce garden all               # Run full maintenance
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
    with_graphrag: Annotated[
        bool,
        typer.Option(
            "--with-graphrag",
            "-g",
            help="Enable GraphRAG entity extraction (slower but deeper code understanding)",
        ),
    ] = False,
):
    """
    Index the codebase for semantic search using Vector Embeddings.
    Use this to enable agents to find relevant code snippets.
    Performs smart incremental indexing (skips unchanged files).

    GraphRAG Mode (--with-graphrag):
    - Extracts code entities (functions, classes, methods)
    - Builds knowledge graph with relationships
    - Enables advanced code navigation and impact analysis
    - WARNING: Significantly slower than standard indexing
    """
    from rich.console import Console

    from utils.knowledge.utils.time_estimator import GraphRAGTimeEstimator

    console = Console()

    # Show time estimation if GraphRAG enabled
    if with_graphrag:
        estimator = GraphRAGTimeEstimator()
        estimated_sec, file_count = estimator.estimate_and_warn(
            root_dir, console, threshold_sec=300
        )

        if estimated_sec > 60:
            # Ask for confirmation for long-running operations
            confirm = typer.confirm(
                f"\nGraphRAG indexing will take ~{estimated_sec / 60:.1f} minutes. Continue?"
            )
            if not confirm:
                console.print("[yellow]GraphRAG indexing cancelled[/yellow]")
                raise typer.Exit(0)

    # Perform indexing
    kb = KnowledgeBase()
    kb.index_codebase(root_dir=root_dir, force_recreate=recreate, with_graphrag=with_graphrag)

    if with_graphrag:
        console.print("\n[green]✓ GraphRAG indexing complete![/green]")
        console.print(
            "[dim]Code entities and relationships are now available for advanced navigation.[/dim]"
        )


@app.command()
def init(
    dir_name: Annotated[
        str | None,
        typer.Option("--dir", "-d", help="Base directory name (.claude, .ce, .qwen, .compounding)"),
    ] = None,
    interactive: Annotated[
        bool, typer.Option("--interactive", "-i", help="Interactive mode")
    ] = True,
):
    """
    Initialize compounding directory structure.

    Creates base directory and subdirectories for:
    - Knowledge base
    - Plans and todos
    - Analysis and memory
    - Cache

    Examples:
        ce init                    # Interactive mode (prompts for directory)
        ce init --dir .claude      # Use .claude directory
        ce init --dir .ce          # Use .ce directory (AI agent default)
    """
    import os
    import re

    from rich.panel import Panel
    from rich.prompt import Prompt

    from utils.paths import CompoundingPaths

    # Determine directory name
    if dir_name is None and interactive:
        # Interactive prompt
        console.print(
            Panel(
                "[bold]Choose base directory name[/bold]\n\n"
                "This directory will contain all compounding engineering data:\n"
                "• Knowledge base and learnings\n"
                "• Plans and todos\n"
                "• Analysis results and memory\n\n"
                "[dim]Common choices:[/dim]\n"
                "  .claude      - For Claude AI users\n"
                "  .qwen        - For Qwen AI users\n"
                "  .ce          - Generic (compounding engineering)\n"
                "  .compounding - Full name\n",
                border_style="cyan",
            )
        )

        dir_name = Prompt.ask("[cyan]Directory name[/cyan]", default=".claude")
    elif dir_name is None:
        # Non-interactive default
        dir_name = os.getenv("COMPOUNDING_DIR_NAME", ".ce")

    # Validate directory name
    if not dir_name.startswith("."):  # type: ignore[union-attr]
        dir_name = f".{dir_name}"

    # Create paths instance with chosen directory
    paths = CompoundingPaths(base_dir_name=dir_name)
    paths.ensure_directories()

    # Write to .env for persistence
    env_file = Path.cwd() / ".env"
    env_content = ""

    if env_file.exists():
        env_content = env_file.read_text()

    # Update or add COMPOUNDING_DIR_NAME
    if "COMPOUNDING_DIR_NAME=" in env_content:
        env_content = re.sub(
            r"COMPOUNDING_DIR_NAME=.*", f"COMPOUNDING_DIR_NAME={dir_name}", env_content
        )
    else:
        env_content += f"\n# Compounding Directory\nCOMPOUNDING_DIR_NAME={dir_name}\n"

    env_file.write_text(env_content)

    console.print(f"\n[green]✓ Initialized {dir_name}/ structure[/green]")
    console.print(f"[dim]Created: {paths.base_dir}[/dim]\n")
    console.print("[bold]Subdirectories:[/bold]")
    for subdir in [
        paths.knowledge_dir,
        paths.plans_dir,
        paths.todos_dir,
        paths.memory_dir,
        paths.cache_dir,
        paths.analysis_dir,
    ]:
        console.print(f"  {subdir.relative_to(paths.repo_root)}")


@app.command()
def migrate():
    """
    Migrate from old directory structure to current structure.

    Moves:
    - .knowledge/ → {base_dir}/knowledge/
    - .compounding/ → {base_dir}/ (if different)
    - plans/ → {base_dir}/plans/
    - todos/ → {base_dir}/todos/
    - analysis/ → {base_dir}/analysis/
    """
    import shutil

    from rich.panel import Panel

    from utils.paths import get_paths

    paths = get_paths()

    console.print(
        Panel.fit(
            f"[bold]Migrating to {paths.base_dir.name}/ Structure[/bold]",
            border_style="blue",
        )
    )

    # Migration logic
    migrations = [
        (paths.repo_root / ".knowledge", paths.knowledge_dir),
        (paths.repo_root / ".compounding", paths.base_dir),
        (paths.repo_root / "plans", paths.plans_dir),
        (paths.repo_root / "todos", paths.todos_dir),
        (paths.repo_root / "analysis", paths.analysis_dir),
    ]

    migrated = []
    for old_path, new_path in migrations:
        if old_path.exists() and not new_path.exists():
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old_path), str(new_path))
            migrated.append(f"{old_path.name} → {paths.base_dir.name}/{new_path.name}")

    if migrated:
        console.print("\n[green]✓ Migration complete![/green]\n")
        console.print("[bold]Migrated directories:[/bold]")
        for item in migrated:
            console.print(f"  {item}")
    else:
        msg = f"No migration needed - already using {paths.base_dir.name}/"
        console.print(f"\n[yellow]{msg}[/yellow]")


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
