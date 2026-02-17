"""Function tool definitions for MergeGuard agents.

Each tool is defined as a JSON Schema dict compatible with Mistral's function calling API.
These are passed to `client.beta.agents.create()` in the `tools` parameter.

NOTE: This is scaffold code. The actual tool implementations (the functions that execute
when the agent calls a tool) would be registered as handlers in the conversation loop.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Tool: fetch_pr_diff
# Used by: Planner Agent
# ---------------------------------------------------------------------------
FETCH_PR_DIFF = {
    "type": "function",
    "function": {
        "name": "fetch_pr_diff",
        "description": (
            "Fetch the unified diff for a GitHub pull request. "
            "Returns the raw diff text including all file changes, hunks, and context lines."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "GitHub repository owner (user or organization)",
                },
                "repo": {
                    "type": "string",
                    "description": "GitHub repository name",
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

# ---------------------------------------------------------------------------
# Tool: read_file
# Used by: Reviewer Agent
# ---------------------------------------------------------------------------
READ_FILE = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": (
            "Read the full content of a file from the repository at the PR's head ref. "
            "Use this to get surrounding context beyond what the diff shows."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "GitHub repository owner",
                },
                "repo": {
                    "type": "string",
                    "description": "GitHub repository name",
                },
                "path": {
                    "type": "string",
                    "description": "File path relative to repository root",
                },
                "ref": {
                    "type": "string",
                    "description": "Git ref (branch, tag, or SHA) to read from. Defaults to the PR head branch.",
                },
            },
            "required": ["owner", "repo", "path"],
        },
    },
}

# ---------------------------------------------------------------------------
# Tool: list_changed_files
# Used by: Planner Agent
# ---------------------------------------------------------------------------
LIST_CHANGED_FILES = {
    "type": "function",
    "function": {
        "name": "list_changed_files",
        "description": (
            "List all files changed in a pull request with metadata. "
            "Returns an array of objects with file path, change type "
            "(added, modified, deleted, renamed), additions count, and deletions count."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "GitHub repository owner",
                },
                "repo": {
                    "type": "string",
                    "description": "GitHub repository name",
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

# ---------------------------------------------------------------------------
# Tool: check_style
# Used by: Reviewer Agent
# ---------------------------------------------------------------------------
CHECK_STYLE = {
    "type": "function",
    "function": {
        "name": "check_style",
        "description": (
            "Run basic style and lint checks on a code snippet. "
            "Returns a list of style violations with line numbers and descriptions. "
            "Supports Python (via ruff/flake8 rules), JavaScript/TypeScript (basic checks), "
            "and generic whitespace/formatting checks."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The code snippet to check",
                },
                "language": {
                    "type": "string",
                    "description": "Programming language of the snippet (e.g., 'python', 'javascript', 'typescript')",
                },
                "filename": {
                    "type": "string",
                    "description": "Original filename (used to infer language if not specified)",
                },
            },
            "required": ["code"],
        },
    },
}


# ---------------------------------------------------------------------------
# Convenience: all tools grouped by agent
# ---------------------------------------------------------------------------
PLANNER_TOOLS = [FETCH_PR_DIFF, LIST_CHANGED_FILES]
REVIEWER_TOOLS = [READ_FILE, CHECK_STYLE]
# Verifier uses code_interpreter (built-in, not a function tool)
# Reporter uses response_format (not a tool)
