"""Client-side function implementations for MergeGuard tools.

These functions are registered with RunContext so the Mistral Conversations
API can invoke them when agents make function calls.  Each function hits
the GitHub REST API using httpx and returns a plain string result that
gets sent back to the agent as a FunctionResultEntry.

Requires GITHUB_TOKEN environment variable for authenticated requests
(higher rate limits and access to private repos).
"""

from __future__ import annotations

import json
import os
import textwrap

import httpx

# ── GitHub HTTP client ─────────────────────────────────────────────────

_GITHUB_API = "https://api.github.com"


def _gh_headers() -> dict[str, str]:
    """Build GitHub API request headers with optional auth."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MergeGuard/0.1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _gh_diff_headers() -> dict[str, str]:
    """Headers for fetching diffs (Accept: diff media type)."""
    headers = _gh_headers()
    headers["Accept"] = "application/vnd.github.v3.diff"
    return headers


# ── Tool implementations ───────────────────────────────────────────────
#
# Signature conventions:
#   - Parameter names and types match the JSON schema in tools.py
#   - Docstrings follow Google format so RunContext.register_func()
#     can auto-parse descriptions and parameter docs
#   - Return type is always str (serialised for the agent)


def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch the unified diff for a GitHub Pull Request.

    Args:
        owner: Repository owner (user or org)
        repo: Repository name
        pr_number: Pull request number
    """
    url = f"{_GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
    with httpx.Client(timeout=30) as http:
        resp = http.get(url, headers=_gh_diff_headers())
        resp.raise_for_status()
    diff = resp.text
    # Truncate very large diffs to avoid blowing context windows
    max_chars = 120_000
    if len(diff) > max_chars:
        diff = diff[:max_chars] + f"\n\n... [diff truncated at {max_chars} chars]"
    return diff


def list_changed_files(owner: str, repo: str, pr_number: int) -> str:
    """List all files changed in a GitHub Pull Request with addition/deletion counts.

    Args:
        owner: Repository owner (user or org)
        repo: Repository name
        pr_number: Pull request number
    """
    url = f"{_GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/files"
    with httpx.Client(timeout=30) as http:
        resp = http.get(url, headers=_gh_headers(), params={"per_page": 100})
        resp.raise_for_status()
    files = resp.json()
    result = []
    for f in files:
        result.append(
            {
                "filename": f["filename"],
                "status": f["status"],
                "additions": f["additions"],
                "deletions": f["deletions"],
                "changes": f["changes"],
            }
        )
    return json.dumps(result, indent=2)


def read_file(owner: str, repo: str, path: str, ref: str) -> str:
    """Read the full content of a file from the PR's head branch.

    Args:
        owner: Repository owner (user or org)
        repo: Repository name
        path: File path relative to repo root
        ref: Git ref (branch, tag, or SHA) — use PR head branch
    """
    url = f"{_GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    with httpx.Client(timeout=30) as http:
        resp = http.get(
            url,
            headers={**_gh_headers(), "Accept": "application/vnd.github.v3.raw"},
            params={"ref": ref},
        )
        resp.raise_for_status()
    content = resp.text
    max_chars = 80_000
    if len(content) > max_chars:
        content = content[:max_chars] + f"\n\n... [file truncated at {max_chars} chars]"
    return content


def check_style(code: str, language: str) -> str:
    """Run basic style checks on a code snippet. Returns a list of style issues.

    Args:
        code: Code snippet to check
        language: Programming language (python, javascript, typescript, etc.)
    """
    issues: list[dict] = []

    if language.lower() in ("python", "py"):
        # Basic Python style checks
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            # Line length
            if len(line) > 120:
                issues.append(
                    {
                        "line": i,
                        "rule": "line-too-long",
                        "message": f"Line is {len(line)} chars (max 120)",
                    }
                )
            # Trailing whitespace
            if line != line.rstrip():
                issues.append(
                    {
                        "line": i,
                        "rule": "trailing-whitespace",
                        "message": "Trailing whitespace",
                    }
                )
            # Bare except
            stripped = line.strip()
            if stripped == "except:" or stripped.startswith("except :"):
                issues.append(
                    {
                        "line": i,
                        "rule": "bare-except",
                        "message": "Bare except clause — catch specific exceptions",
                    }
                )
            # TODO/FIXME/HACK comments
            if any(tag in line.upper() for tag in ("TODO", "FIXME", "HACK", "XXX")):
                issues.append(
                    {
                        "line": i,
                        "rule": "todo-comment",
                        "message": f"Contains TODO/FIXME/HACK marker",
                    }
                )

        # Try to parse as valid Python
        try:
            import ast

            ast.parse(code)
        except SyntaxError as e:
            issues.append(
                {
                    "line": e.lineno or 0,
                    "rule": "syntax-error",
                    "message": f"Syntax error: {e.msg}",
                }
            )
    else:
        # Generic checks for other languages
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append(
                    {
                        "line": i,
                        "rule": "line-too-long",
                        "message": f"Line is {len(line)} chars (max 120)",
                    }
                )
            if line != line.rstrip():
                issues.append(
                    {
                        "line": i,
                        "rule": "trailing-whitespace",
                        "message": "Trailing whitespace",
                    }
                )

    if not issues:
        return json.dumps({"status": "clean", "issues": []})
    return json.dumps({"status": "issues_found", "count": len(issues), "issues": issues}, indent=2)
