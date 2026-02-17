"""MergeGuard CLI entry point."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

# ── GitHub API helper ──────────────────────────────────────────────────

_github_client: httpx.Client | None = None


def _gh_client() -> httpx.Client:
    """Lazy-init an httpx client with GITHUB_TOKEN auth (if available)."""
    global _github_client
    if _github_client is None:
        headers = {"Accept": "application/vnd.github.v3+json"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        _github_client = httpx.Client(
            base_url="https://api.github.com",
            headers=headers,
            timeout=30.0,
        )
    return _github_client


# ── PR URL parsing ─────────────────────────────────────────────────────


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Extract owner, repo, and PR number from a GitHub PR URL.

    Supports: https://github.com/owner/repo/pull/123
    """
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {url}")
    return match.group(1), match.group(2), int(match.group(3))


# ── Tool implementations ──────────────────────────────────────────────


def _fetch_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch the unified diff for a GitHub Pull Request."""
    gh = _gh_client()
    resp = gh.get(
        f"/repos/{owner}/{repo}/pulls/{pr_number}",
        headers={"Accept": "application/vnd.github.v3.diff"},
    )
    if resp.status_code == 200:
        return resp.text
    return json.dumps({"error": f"GitHub API returned {resp.status_code}", "body": resp.text[:500]})


def _list_changed_files(owner: str, repo: str, pr_number: int) -> str:
    """List all files changed in a GitHub Pull Request."""
    gh = _gh_client()
    resp = gh.get(f"/repos/{owner}/{repo}/pulls/{pr_number}/files")
    if resp.status_code == 200:
        files = [
            {
                "filename": f["filename"],
                "status": f["status"],
                "additions": f["additions"],
                "deletions": f["deletions"],
                "changes": f["changes"],
            }
            for f in resp.json()
        ]
        return json.dumps(files)
    return json.dumps({"error": f"GitHub API returned {resp.status_code}"})


def _read_file(owner: str, repo: str, path: str, ref: str) -> str:
    """Read the full content of a file from a specific ref."""
    gh = _gh_client()
    resp = gh.get(
        f"/repos/{owner}/{repo}/contents/{path}",
        params={"ref": ref},
        headers={"Accept": "application/vnd.github.v3.raw"},
    )
    if resp.status_code == 200:
        return resp.text
    return json.dumps({"error": f"GitHub API returned {resp.status_code}"})


def _check_style(code: str, language: str) -> str:
    """Run basic style checks on a code snippet."""
    issues: list[dict] = []
    if language == "python":
        import ast

        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append({"type": "syntax_error", "message": str(e), "line": e.lineno})
        # Basic checks
        for i, line in enumerate(code.splitlines(), 1):
            if len(line) > 120:
                issues.append({"type": "line_too_long", "line": i, "length": len(line)})
    return json.dumps({"language": language, "issues": issues, "count": len(issues)})


# ── Review pipeline (async with RunContext) ────────────────────────────


async def run_review_async(pr_url: str) -> dict:
    """Run the full MergeGuard review pipeline on a PR.

    Uses the Mistral RunContext + run_async pattern for function-call
    execution and multi-agent handoffs.

    Returns the ReviewReport as a dict.
    """
    from mistralai import Mistral
    from mistralai.extra.run.context import RunContext

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
        # Start conversation with the Planner (entry agent) using RunContext
        console.print("[bold]Starting review...[/]\n")

        user_message = (
            f"Please review this Pull Request: "
            f"https://github.com/{owner}/{repo}/pull/{pr_number}"
        )

        async with RunContext(agent_id=chain.entry_agent_id) as run_ctx:
            # Register all function tools so the SDK can execute them
            # when agents invoke tool calls during the conversation.

            @run_ctx.register_func
            def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> str:
                """Fetch the unified diff for a GitHub Pull Request.

                Args:
                    owner: Repository owner (user or org).
                    repo: Repository name.
                    pr_number: Pull request number.
                """
                console.print(f"  [dim]→ fetch_pr_diff({owner}/{repo}#{pr_number})[/]")
                return _fetch_pr_diff(owner, repo, pr_number)

            @run_ctx.register_func
            def list_changed_files(owner: str, repo: str, pr_number: int) -> str:
                """List all files changed in a GitHub Pull Request.

                Args:
                    owner: Repository owner (user or org).
                    repo: Repository name.
                    pr_number: Pull request number.
                """
                console.print(f"  [dim]→ list_changed_files({owner}/{repo}#{pr_number})[/]")
                return _list_changed_files(owner, repo, pr_number)

            @run_ctx.register_func
            def read_file(owner: str, repo: str, path: str, ref: str) -> str:
                """Read the full content of a file from the PR's head branch.

                Args:
                    owner: Repository owner.
                    repo: Repository name.
                    path: File path relative to repo root.
                    ref: Git ref (branch, tag, or SHA).
                """
                console.print(f"  [dim]→ read_file({owner}/{repo}/{path}@{ref})[/]")
                return _read_file(owner, repo, path, ref)

            @run_ctx.register_func
            def check_style(code: str, language: str) -> str:
                """Run basic style checks on a code snippet.

                Args:
                    code: Code snippet to check.
                    language: Programming language (python, javascript, etc.).
                """
                console.print(f"  [dim]→ check_style(lang={language}, {len(code)} chars)[/]")
                return _check_style(code, language)

            # Run the conversation — the SDK handles function call loops
            # and handoffs between agents automatically.
            run_result = await client.beta.conversations.run_async(
                run_ctx=run_ctx,
                inputs=user_message,
            )

        # Parse the final JSON report from the Reporter
        report = json.loads(run_result.outputs[-1].content)
        return report

    finally:
        # Cleanup agents
        console.print("\n[dim]Cleaning up agents...[/]")
        teardown_chain(client, chain)


def run_review(pr_url: str) -> dict:
    """Synchronous wrapper around the async review pipeline."""
    return asyncio.run(run_review_async(pr_url))


# ── Display ────────────────────────────────────────────────────────────


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


# ── CLI ────────────────────────────────────────────────────────────────


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
