"""Policy enforcement workflow."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from server.infrastructure.execution import RepoExecutor
from utils.policy.orchestrator import PolicyEnforcer

console = Console()


def _get_files_to_check(repo_root: Path, paths: list[str] | None, staged_only: bool) -> list[Path]:
    """Get list of Python files to check."""
    executor = RepoExecutor(repo_root)

    if staged_only:
        # Get staged files from git
        result = executor.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            files = [Path(f) for f in result.stdout.strip().split("\n") if f.endswith(".py")]
            return [f for f in files if f.exists()]
        return []

    if paths:
        # Check specified paths
        all_files = []
        for path_str in paths:
            path = Path(path_str)
            if path.is_file() and path.suffix == ".py":
                all_files.append(path)
            elif path.is_dir():
                all_files.extend(path.rglob("*.py"))
        return all_files

    # Check all Python files in repo
    try:
        result = executor.run(
            ["git", "ls-files", "*.py"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return [Path(f) for f in result.stdout.strip().split("\n") if f]
    except Exception:
        pass

    # Fallback to glob
    return list(Path(".").rglob("*.py"))


def _display_violations_table(enforcer: PolicyEnforcer, violations_by_severity: dict):
    """Display violations grouped by severity."""
    if not any(violations_by_severity.values()):
        console.print("[green]✓ No policy violations found![/green]")
        return

    for severity in ["ERROR", "WARNING", "INFO"]:
        violations = violations_by_severity.get(severity, [])
        if not violations:
            continue

        color = {"ERROR": "red", "WARNING": "yellow", "INFO": "blue"}[severity]
        title = f"{severity}S ({len(violations)})"

        table = Table(title=title, border_style=color)
        table.add_column("File", style="cyan", overflow="fold")
        table.add_column("Line", style="white", justify="right")
        table.add_column("Rule", style="magenta")
        table.add_column("Message", overflow="fold")

        for v in violations:
            file_rel = str(v.file_path.relative_to(enforcer.repo_root))
            line = str(v.line) if v.line else "-"
            table.add_row(file_rel, line, v.rule_id, v.message)

        console.print(table)


def run_check(
    repo_root: str | Path,
    paths: list[str] | None = None,
    auto_fix: bool = False,
    staged_only: bool = False,
) -> int:
    """
    Run policy enforcement checks on codebase.

    Args:
        repo_root: Root directory of target repository
        paths: Files or directories to check
        auto_fix: Auto-fix violations using ruff
        staged_only: Check only staged files

    Returns:
        Exit code (0 for success, 1 for violations found)
    """
    console.print(
        Panel.fit(
            "[bold]Policy Enforcement Check[/bold]\n"
            f"Auto-fix: {auto_fix} | Staged only: {staged_only}",
            border_style="blue",
        )
    )

    # Initialize RepoExecutor for target repo
    repo_root = Path(repo_root)
    executor = RepoExecutor(repo_root)

    # Get files to check
    files = _get_files_to_check(repo_root, paths, staged_only)
    if not files:
        console.print("[yellow]No Python files found to check.[/yellow]")
        return 0

    console.print(f"[dim]Checking {len(files)} Python files...[/dim]\n")

    # Initialize enforcer
    enforcer = PolicyEnforcer()

    # Run checks
    all_violations = []
    violations_by_severity = {"ERROR": [], "WARNING": [], "INFO": []}
    files_with_violations = 0
    cache_hits = 0

    with console.status("[cyan]Running policy checks...") as status:
        for i, file_path in enumerate(files, 1):
            status.update(f"[cyan]Checking {file_path.name} ({i}/{len(files)})...")

            # Check if cached
            if enforcer.cache.get(file_path):
                cache_hits += 1

            result = enforcer.check_file(file_path)

            if result.violations:
                files_with_violations += 1
                all_violations.extend(result.violations)

                for v in result.violations:
                    violations_by_severity[v.severity].append(v)

    # Display results
    console.rule("[bold]Results[/bold]")

    _display_violations_table(enforcer, violations_by_severity)

    # Summary
    total_violations = len(all_violations)
    error_count = len(violations_by_severity["ERROR"])
    warning_count = len(violations_by_severity["WARNING"])
    info_count = len(violations_by_severity["INFO"])

    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Files checked: {len(files)}")
    console.print(f"  Files with violations: {files_with_violations}")
    console.print(f"  Cache hits: {cache_hits}/{len(files)}")
    console.print(f"  Total violations: {total_violations}")

    if error_count:
        console.print(f"  [red]Errors: {error_count}[/red]")
    if warning_count:
        console.print(f"  [yellow]Warnings: {warning_count}[/yellow]")
    if info_count:
        console.print(f"  [blue]Info: {info_count}[/blue]")

    # Auto-fix if requested
    if auto_fix and (error_count or warning_count):
        console.print("\n[cyan]Running auto-fix with ruff...[/cyan]")
        try:
            # Run ruff check --fix
            fix_result = executor.run(
                ["ruff", "check", "--fix"] + [str(f) for f in files],
                capture_output=True,
                text=True,
            )

            # Run ruff format
            format_result = executor.run(
                ["ruff", "format"] + [str(f) for f in files],
                capture_output=True,
                text=True,
            )

            if fix_result.returncode == 0 and format_result.returncode == 0:
                console.print("[green]✓ Auto-fix completed successfully[/green]")
                console.print("[dim]Re-run check to see remaining violations[/dim]")
            else:
                console.print("[yellow]⚠ Auto-fix completed with warnings[/yellow]")

        except Exception as e:
            console.print(f"[red]Error running auto-fix: {e}[/red]")

    # Exit code
    if error_count > 0:
        console.print("\n[red]❌ Policy check failed (errors found)[/red]")
        return 1

    console.print("\n[green]✓ Policy check passed[/green]")
    return 0
