"""GitHub API client for MergeGuard function tools.

Provides the actual HTTP implementations that back the function-calling
tools registered with the Mistral Agents API.  Uses ``httpx`` for async
HTTP and reads ``GITHUB_TOKEN`` from the environment for authenticated
access.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

_GITHUB_API = "https://api.github.com"
_TIMEOUT = 30.0


def _headers() -> dict[str, str]:
    """Build GitHub API request headers.

    Raises ``RuntimeError`` if ``GITHUB_TOKEN`` is not set.
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN environment variable is required for GitHub API access"
        )
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


# ── Tool implementations (sync — RunContext wraps them automatically) ──


def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch the unified diff for a GitHub Pull Request.

    Args:
        owner: Repository owner (user or org).
        repo: Repository name.
        pr_number: Pull request number.

    Returns:
        The unified diff as a string.
    """
    url = f"{_GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = _headers()
    headers["Accept"] = "application/vnd.github.v3.diff"
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.text


def list_changed_files(owner: str, repo: str, pr_number: int) -> str:
    """List all files changed in a GitHub Pull Request with addition/deletion counts.

    Args:
        owner: Repository owner.
        repo: Repository name.
        pr_number: Pull request number.

    Returns:
        JSON string with a list of changed files and their stats.
    """
    url = f"{_GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/files"
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.get(url, headers=_headers())
        resp.raise_for_status()
        files = resp.json()

    summary = [
        {
            "filename": f["filename"],
            "status": f["status"],
            "additions": f["additions"],
            "deletions": f["deletions"],
            "changes": f["changes"],
            "patch": f.get("patch", "")[:500],  # truncate large patches
        }
        for f in files
    ]
    return json.dumps(summary, indent=2)


def read_file(owner: str, repo: str, path: str, ref: str) -> str:
    """Read the full content of a file from a specific git ref.

    Args:
        owner: Repository owner.
        repo: Repository name.
        path: File path relative to repo root.
        ref: Git ref (branch, tag, or SHA).

    Returns:
        The file content as a string.
    """
    url = f"{_GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.get(url, headers=_headers(), params={"ref": ref})
        resp.raise_for_status()
        data = resp.json()

    if data.get("encoding") == "base64":
        import base64

        return base64.b64decode(data["content"]).decode("utf-8")
    return data.get("content", "")


def check_style(code: str, language: str) -> str:
    """Run basic style checks on a code snippet.

    Args:
        code: Code snippet to check.
        language: Programming language (python, javascript, etc.).

    Returns:
        JSON string with a list of style issues found.
    """
    issues: list[dict[str, Any]] = []

    if language.lower() == "python":
        import ast

        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append(
                {
                    "type": "syntax_error",
                    "line": e.lineno,
                    "message": str(e.msg),
                }
            )

        # Basic style heuristics
        for i, line in enumerate(code.splitlines(), 1):
            if len(line) > 120:
                issues.append(
                    {
                        "type": "line_too_long",
                        "line": i,
                        "message": f"Line exceeds 120 characters ({len(line)})",
                    }
                )
            if "\t" in line:
                issues.append(
                    {
                        "type": "tabs",
                        "line": i,
                        "message": "Use spaces instead of tabs",
                    }
                )
    else:
        # For non-Python languages, do basic length checks
        for i, line in enumerate(code.splitlines(), 1):
            if len(line) > 120:
                issues.append(
                    {
                        "type": "line_too_long",
                        "line": i,
                        "message": f"Line exceeds 120 characters ({len(line)})",
                    }
                )

    if not issues:
        return json.dumps({"status": "clean", "issues": []})
    return json.dumps({"status": "issues_found", "issues": issues}, indent=2)
