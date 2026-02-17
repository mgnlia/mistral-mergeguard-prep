"""MergeGuard CLI entry point."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Extract owner, repo, and PR number from a GitHub PR URL.

    Supports: https://github.com/owner/repo/pull/123
    """
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {url}")
    return match.group(1), match.group(2), int(match.group(3))


def run_review(pr_url: str) -> dict:
    """Run the full MergeGuard review pipeline on a PR.

    Returns the ReviewReport as a dict.
    """
    from mistralai import Mistral

    from mergeguard.handoffs import build_chain, teardown_chain

    # Parse PR URL
    owner, repo, pr_number = parse_pr_url(pr_url)
    console.print(
        f"[bold blue]MergeGuard[/] reviewing "
        f"[green]{owner}/{repo}[/] PR [yellow]#{pr_number}[/]"
    )

    # Initialize Mistral client
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        console.print("[red]Error:[/] MISTRAL_API_KEY environment variable not set")
        sys.exit(1)

    client = Mistral(api_key=api_key)

    # Build the agent chain
    console.print("[dim]Creating agent chain...[/]")
    chain = build_chain(client)
    console.print(
        f"[dim]Chain ready: Planner({chain.planner_id[:8]}) → "
        f"Reviewer({chain.reviewer_id[:8]}) → "
        f"Verifier({chain.verifier_id[:8]}) → "
        f"Reporter({chain.reporter_id[:8]})[/]"
    )

    try:
        # Start conversation with the Planner (entry agent)
        console.print("[bold]Starting review...[/]\n")

        # TODO: During hackathon sprint, implement:
        # 1. Create a conversation with the entry agent
        # 2. Send the PR URL as user message
        # 3. Handle function call responses (fetch_pr_diff, etc.)
        # 4. Follow handoffs through the chain
        # 5. Collect final structured output from Reporter

        # Placeholder — will be implemented during the hackathon
        response = client.beta.conversations.create(
            agent_id=chain.entry_agent_id,
            inputs=f"Please review this Pull Request: https://github.com/{owner}/{repo}/pull/{pr_number}",
        )

        # Parse the final JSON report from the Reporter
        report = json.loads(response.outputs[-1].content)
        return report

    finally:
        # Cleanup agents
        console.print("\n[dim]Cleaning up agents...[/]")
        teardown_chain(client, chain)


def display_report(report: dict) -> None:
    """Pretty-print the review report."""
    console.print()
    console.print(
        Panel(
            report.get("summary", "No summary"),
            title="[bold]Review Summary[/]",
            border_style="blue",
        )
    )

    score = report.get("overall_score", 0)
    rec = report.get("recommendation", "unknown")
    score_color = "green" if score >= 80 else "yellow" if score >= 50 else "red"
    rec_color = "green" if rec == "approve" else "red"

    console.print(
        f"\n  Score: [{score_color}]{score}/100[/]  |  "
        f"Recommendation: [{rec_color}]{rec}[/]\n"
    )

    comments = report.get("comments", [])
    if comments:
        console.print(f"[bold]Comments ({len(comments)}):[/]\n")
        for c in comments:
            sev = c.get("severity", "info")
            sev_colors = {
                "critical": "red bold",
                "warning": "yellow",
                "suggestion": "cyan",
                "nitpick": "dim",
            }
            color = sev_colors.get(sev, "white")
            console.print(
                f"  [{color}][{sev.upper()}][/] "
                f"{c.get('file', '?')}:{c.get('line', '?')} — "
                f"{c.get('message', '')}"
            )
            if c.get("suggestion"):
                console.print(f"    [dim]→ {c['suggestion']}[/]")
    else:
        console.print("[green]No issues found — clean PR! 🎉[/]")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="mergeguard",
        description="MergeGuard — AI-powered multi-agent code review",
    )
    parser.add_argument(
        "pr_url",
        help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON report instead of formatted display",
    )

    args = parser.parse_args()

    try:
        report = run_review(args.pr_url)

        if args.json:
            console.print_json(json.dumps(report, indent=2))
        else:
            display_report(report)

    except ValueError as e:
        console.print(f"[red]Error:[/] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Review cancelled.[/]")
        sys.exit(130)


if __name__ == "__main__":
    main()
