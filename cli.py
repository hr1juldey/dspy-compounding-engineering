from typing import Optional

import typer

from config import configure_dspy
from workflows.triage import run_triage
from workflows.plan import run_plan
from workflows.review import run_review
from workflows.work import run_work
from workflows.resolve_todo import run_resolve_todo
from workflows.generate_command import run_generate_command
from workflows.codify import run_codify

app = typer.Typer()


@app.callback()
def main():
    """
    Compounding Engineering Plugin (DSPy Edition)
    """
    configure_dspy()


@app.command()
def triage():
    """
    Triage and categorize findings for the CLI todo system.
    """
    run_triage()


@app.command()
def plan(feature_description: str):
    """
    Transform feature descriptions into well-structured project plans.
    """
    run_plan(feature_description)


@app.command()
def work(plan_file: str):
    """
    Execute work plans systematically.
    """
    run_work(plan_file)


@app.command()
def review(
    pr_url_or_id: str = typer.Argument("latest", help="PR number, URL, branch name, or 'latest' for local changes"),
    project: bool = typer.Option(False, "--project", "-p", help="Review entire project instead of just changes"),
):
    """
    Perform exhaustive multi-agent code reviews.

    Examples:
        uv run python cli.py review              # Review local changes
        uv run python cli.py review --project    # Review entire project
        uv run python cli.py review 123          # Review PR #123
    """
    run_review(pr_url_or_id, project=project)


@app.command()
def resolve_todo(
    pattern: Optional[str] = typer.Argument(
        None,
        help="Optional pattern to filter todos (e.g., '001' or 'security')"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-n",
        help="Show what would be done without applying changes"
    ),
    sequential: bool = typer.Option(
        False,
        "--sequential", "-s",
        help="Execute todos sequentially instead of in parallel"
    ),
    max_workers: int = typer.Option(
        3,
        "--workers", "-w",
        help="Maximum number of parallel workers"
    ),
    in_place: bool = typer.Option(
        True,
        "--in-place/--worktree",
        help="Apply changes in-place to current branch (default) or use isolated worktree"
    )
):
    """
    Resolve all ready todos from code review findings.

    This command processes todos that have been triaged and marked as ready,
    using AI agents to generate and apply fixes.

    The workflow:
    1. Discovers all *-ready-*.md files in todos/
    2. Analyzes dependencies between todos
    3. Executes resolutions (in parallel where possible)
    4. Marks completed todos and offers to commit

    Examples:
        python cli.py resolve-todo              # Resolve all ready todos
        python cli.py resolve-todo 001          # Resolve only todo 001
        python cli.py resolve-todo security     # Resolve todos matching 'security'
        python cli.py resolve-todo --dry-run    # Preview without applying changes
    """
    run_resolve_todo(
        pattern=pattern,
        dry_run=dry_run,
        parallel=not sequential,
        max_workers=max_workers,
        in_place=in_place
    )


@app.command()
def generate_command(
    description: str = typer.Argument(
        ...,
        help="Natural language description of what the command should do"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-n",
        help="Show what would be created without writing files"
    )
):
    """
    Generate a new CLI command from a natural language description.

    This meta-command creates new commands for the Compounding Engineering plugin.
    It analyzes the description, designs an appropriate workflow and agents,
    and generates all necessary code.

    Examples:
        python cli.py generate-command "Create a command to format code"
        python cli.py generate-command "Add a lint command that checks Python style"
        python cli.py generate-command --dry-run "Create a deployment workflow"
    """
    run_generate_command(description=description, dry_run=dry_run)


@app.command()
def codify(
    feedback: str = typer.Argument(
        ...,
        help="The feedback, instruction, or learning to codify"
    ),
    source: str = typer.Option(
        "manual_input",
        "--source", "-s",
        help="Source of the feedback (e.g., 'review', 'retro')"
    )
):
    """
    Codify feedback into the knowledge base.
    
    This command uses the FeedbackCodifier agent to transform raw feedback
    into structured improvements (documentation, rules, patterns) and saves
    them to the persistent knowledge base.
    
    Examples:
        python cli.py codify "Always use strict typing in Python files"
        python cli.py codify "We should use factory pattern for creating agents" --source retro
    """
    run_codify(feedback=feedback, source=source)


if __name__ == "__main__":
    app()
