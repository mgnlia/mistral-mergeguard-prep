"""Function tool definitions for MergeGuard agents."""

from __future__ import annotations

# ── Tool schemas for Mistral function calling ──────────────────────────

FETCH_PR_DIFF = {
    "type": "function",
    "function": {
        "name": "fetch_pr_diff",
        "description": "Fetch the unified diff for a GitHub Pull Request.",
        "parameters": {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Repository owner (user or org)",
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name",
                },
                "pr_number": {
                    "type": "integer",
                    "description": "Pull request number",
                },
            },
            "required": ["owner", "repo", "pr_number"],
        },
    },
}

LIST_CHANGED_FILES = {
    "type": "function",
    "function": {
        "name": "list_changed_files",
        "description": "List all files changed in a GitHub Pull Request with addition/deletion counts.",
        "parameters": {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Repository owner",
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name",
                },
                "pr_number": {
                    "type": "integer",
                    "description": "Pull request number",
                },
            },
            "required": ["owner", "repo", "pr_number"],
        },
    },
}

READ_FILE = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the full content of a file from the PR's head branch.",
        "parameters": {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Repository owner",
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name",
                },
                "path": {
                    "type": "string",
                    "description": "File path relative to repo root",
                },
                "ref": {
                    "type": "string",
                    "description": "Git ref (branch, tag, or SHA) — use PR head branch",
                },
            },
            "required": ["owner", "repo", "path", "ref"],
        },
    },
}

CHECK_STYLE = {
    "type": "function",
    "function": {
        "name": "check_style",
        "description": "Run basic style checks on a code snippet. Returns a list of style issues.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Code snippet to check",
                },
                "language": {
                    "type": "string",
                    "description": "Programming language (python, javascript, typescript, etc.)",
                },
            },
            "required": ["code", "language"],
        },
    },
}


# ── Convenience groupings ──────────────────────────────────────────────

PLANNER_TOOLS = [FETCH_PR_DIFF, LIST_CHANGED_FILES]
REVIEWER_TOOLS = [READ_FILE, CHECK_STYLE]
VERIFIER_TOOLS = [{"type": "code_interpreter"}]
REPORTER_TOOLS: list = []  # Reporter uses structured output only
