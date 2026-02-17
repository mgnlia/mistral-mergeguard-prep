"""MergeGuard — CLI entry point.

Parses command-line arguments, initializes the Mistral client, creates the
agent pipeline, runs the handoff chain, and prints the final review report.

Usage:
    uv run python -m mergeguard --pr https://github.com/owner/repo/pull/123
    uv run python -m mergeguard --diff path/to/changes.diff

NOTE: This is scaffold code. No actual API calls are made.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from mergeguard.handoffs import PipelineAgents, create_pipeline, delete_pipeline
from mergeguard.schemas import ReviewReport

console = Console()


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL into (owner, repo, pr_number).

    Args:
        url: GitHub PR URL like https://github.com/owner/repo/pull/123

    Returns:
        Tuple of (owner, repo, pr_number).

    Raises:
        ValueError: If the URL format is invalid.
    """
    pattern = r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.match(pattern, url)
    if not match:
        raise ValueError(
            f"Invalid PR URL: {url}\n"
            "Expected format: https://github.com/owner/repo/pull/123"
        )
    return match.group(1), match.group(2), int(match.group(3))


def read_diff_file(path: str) -> str:
    """Read a local diff file.

    Args:
        path: Path to the diff file.

    Returns:
        The diff content as a string.

    Raises:
        FileNotFoundError: If the file doesn't exist.
    """
    diff_path = Path(path)
    if not diff_path.exists():
        raise FileNotFoundError(f"Diff file not found: {path}")
    return diff_path.read_text(encoding="utf-8")


def run_pipeline(client, agents: PipelineAgents, user_message: str) -> ReviewReport:
    """Run the MergeGuard review pipeline.

    Starts a conversation with the Planner agent, which triggers the
    handoff chain: Planner → Reviewer → Verifier → Reporter.

    Args:
        client: Authenticated Mistral client.
        agents: The pipeline agent IDs.
        user_message: The initial message (PR URL or diff content).

    Returns:
        The final ReviewReport from the Reporter agent.
    """
    # Start a conversation with the Planner agent
    response = client.beta.conversations.start(
        agent_id=agents.planner_id,
        inputs=user_message,
    )

    # The conversation runs through all handoffs automatically.
    # The final response comes from the Reporter agent as structured JSON.
    report_data = json.loads(response.output)
    return ReviewReport.model_validate(report_data)


def print_report(report: ReviewReport) -> None:
    """Pretty-print the review report to the console."""
    # Header
    emoji = "✅" if report.recommendation.value == "approve" else "❌"
    console.print()
    console.print(
        Panel(
            f"[bold]{emoji} {report.recommendation.value.upper()}[/bold]  —  "
            f"Score: [bold]{report.overall_score}/100[/bold]  |  "
            f"Files: {report.files_reviewed}  |  Issues: {report.total_issues}",
            title="[bold blue]MergeGuard Review Report[/bold blue]",
            border_style="blue",
        )
    )

    # Summary
    console.print(f"\n[bold]Summary:[/bold] {report.summary}\n")

    # Comments
    if report.comments:
        console.print("[bold]Issues Found:[/bold]\n")
        for i, comment in enumerate(report.comments, 1):
            severity_colors = {
                "critical": "red",
                "warning": "yellow",
                "suggestion": "cyan",
                "nitpick": "dim",
            }
            color = severity_colors.get(comment.severity.value, "white")
            verified_mark = " ✓" if comment.verified else ""

            console.print(
                f"  [{color}]{i}. [{comment.severity.value.upper()}][/{color}]"
                f"{verified_mark}  {comment.file}"
                f"{f':{comment.line}' if comment.line else ''}"
            )
            console.print(f"     {comment.message}")
            if comment.suggestion:
                console.print(f"     [dim]→ {comment.suggestion}[/dim]")
            console.print()
    else:
        console.print("[green]No issues found! 🎉[/green]\n")

    # JSON output
    console.print("[bold]Raw JSON Report:[/bold]")
    json_str = report.model_dump_json(indent=2)
    console.print(Syntax(json_str, "json", theme="monokai"))


def main() -> None:
    """Main entry point for MergeGuard CLI."""
    parser = argparse.ArgumentParser(
        prog="mergeguard",
        description="MergeGuard — Multi-agent code review pipeline using Mistral Agents API",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--pr",
        type=str,
        help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)",
    )
    group.add_argument(
        "--diff",
        type=str,
        help="Path to a local diff file",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Mistral API key (defaults to MISTRAL_API_KEY env var)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON only (no pretty printing)",
    )

    args = parser.parse_args()

    # Resolve API key
    api_key = args.api_key or os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        console.print(
            "[red]Error: No API key provided. Set MISTRAL_API_KEY or use --api-key.[/red]"
        )
        sys.exit(1)

    # Build user message
    if args.pr:
        owner, repo, pr_number = parse_pr_url(args.pr)
        user_message = (
            f"Please review this pull request:\n"
            f"Repository: {owner}/{repo}\n"
            f"PR Number: {pr_number}\n"
            f"URL: {args.pr}"
        )
        console.print(f"[blue]Reviewing PR: {args.pr}[/blue]")
    else:
        diff_content = read_diff_file(args.diff)
        user_message = (
            f"Please review this diff:\n\n```diff\n{diff_content}\n```"
        )
        console.print(f"[blue]Reviewing diff: {args.diff}[/blue]")

    # Initialize Mistral client
    # NOTE: Scaffold only — this import would fail without the mistralai package installed
    console.print("[yellow]⚠ SCAFFOLD MODE — no actual API calls will be made[/yellow]")
    console.print("[dim]To run for real, install dependencies with: uv sync[/dim]\n")

    try:
        from mistralai import Mistral

        client = Mistral(api_key=api_key)
    except ImportError:
        console.print("[red]mistralai package not installed. Run: uv sync[/red]")
        sys.exit(1)

    # Create pipeline and run
    console.print("[blue]Creating agent pipeline...[/blue]")
    agents = create_pipeline(client)

    console.print("[blue]Running review pipeline (Planner → Reviewer → Verifier → Reporter)...[/blue]")
    try:
        report = run_pipeline(client, agents, user_message)

        if args.json:
            print(report.model_dump_json(indent=2))
        else:
            print_report(report)
    finally:
        # Clean up agents
        console.print("[dim]Cleaning up agents...[/dim]")
        delete_pipeline(client, agents)

    console.print("[green]Done![/green]")


if __name__ == "__main__":
    main()
