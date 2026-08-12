"""Terminal output formatting for Agent-Built Demos.

Uses Rich for styled, milestone-based CLI output. All Rich markup
is encapsulated here so the rest of the codebase stays clean.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Shared console instance — force_terminal ensures color even in CI.
console = Console(highlight=False)


def print_banner(company: str) -> None:
    """Print the startup banner with company name.

    Args:
        company: The company name to display.
    """
    title = Text(f"🚀 Agent-Built Demo: {company}", style="bold")
    console.print(Panel(title, border_style="dim", expand=False))
    console.print()


def print_milestone(agent_name: str, message: str) -> None:
    """Print a milestone event from an agent.

    Args:
        agent_name: Short name of the agent (e.g., "Page Builder").
        message: The milestone message (e.g., "✓ Dataset created: ...").
    """
    label = f"[bold cyan][{agent_name:<16}][/bold cyan]"
    console.print(f"  {label} {message}")


def print_agent_start(agent_name: str) -> None:
    """Print a message indicating an agent has started.

    Args:
        agent_name: Short name of the agent.
    """
    print_milestone(agent_name, "[dim]Starting...[/dim]")


def print_agent_success(agent_name: str, message: str) -> None:
    """Print a success milestone from an agent.

    Args:
        agent_name: Short name of the agent.
        message: The success message (without the checkmark — it's added here).
    """
    print_milestone(agent_name, f"[green]✓[/green] {message}")


def print_agent_error(agent_name: str, message: str) -> None:
    """Print an error from an agent.

    Args:
        agent_name: Short name of the agent.
        message: The error description.
    """
    print_milestone(agent_name, f"[red]✗[/red] {message}")


def print_success(url: str) -> None:
    """Print the final success message with the demo URL.

    Args:
        url: The Cloud Run URL of the deployed frontend.
    """
    console.print()
    console.print(f"  [bold green]✅ Demo ready:[/bold green] [link={url}]{url}[/link]")
    console.print()


def print_error(agent_name: str, message: str) -> None:
    """Print a top-level error message.

    This is used for fatal errors that prevent the demo from completing.

    Args:
        agent_name: Name of the agent that failed (or "CLI" for orchestrator errors).
        message: Human-readable error description.
    """
    console.print()
    console.print(
        f"  [bold red]❌ [{agent_name}] Failed:[/bold red] {message}"
    )
    console.print()


def print_info(message: str) -> None:
    """Print an informational message.

    Args:
        message: The information to display.
    """
    console.print(f"  [dim]{message}[/dim]")


def print_separator() -> None:
    """Print a horizontal separator line."""
    console.print("  " + "─" * 40, style="dim")


def print_demo_prompts(prompts: list[str]) -> None:
    """Print demo prompts in a styled panel for use during the demo script.

    Args:
        prompts: List of 3 demo prompt strings.
    """
    lines = Text()
    lines.append("\n")
    for i, prompt in enumerate(prompts, 1):
        lines.append(f"  {i}. ", style="bold cyan")
        lines.append(f"{prompt}\n\n")
    console.print()
    console.print(Panel(
        lines,
        title="[bold]🎤 Demo Prompts for Conversational Analytics[/bold]",
        border_style="cyan",
        expand=False,
        padding=(0, 2),
    ))

