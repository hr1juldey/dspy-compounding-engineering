"""Handle user prompts for environment selection."""

from rich.console import Console
from rich.prompt import Prompt

from server.infrastructure.execution.models import RepoEnvironment

console = Console()


class UserPrompter:
    """Prompt user to choose between multiple environments."""

    def choose_environment(self, environments: list[RepoEnvironment]) -> RepoEnvironment:
        """Ask user to pick from multiple detected environments."""
        if len(environments) == 1:
            return environments[0]

        console.print("\n[bold]Multiple environments detected:[/bold]")
        for i, env in enumerate(environments, 1):
            console.print(f"  {i}. {env.description}")

        choices = [str(i) for i in range(1, len(environments) + 1)]
        selection = Prompt.ask(
            "\n[cyan]Choose environment[/cyan]",
            choices=choices,
            default="1",
        )

        return environments[int(selection) - 1]
