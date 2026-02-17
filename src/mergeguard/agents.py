"""Agent creation for MergeGuard pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from mergeguard.schemas import ReviewReport
from mergeguard.tools import (
    PLANNER_TOOLS,
    REPORTER_TOOLS,
    REVIEWER_TOOLS,
    VERIFIER_TOOLS,
)

if TYPE_CHECKING:
    from mistralai import Mistral

# ── Prompt loading ─────────────────────────────────────────────────────

AGENTS_DIR = Path(__file__).resolve().parent.parent.parent / "agents"


def _load_prompt(name: str) -> str:
    """Load an agent's system prompt from agents/<name>.md."""
    prompt_path = AGENTS_DIR / f"{name}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Agent prompt not found: {prompt_path}")
    return prompt_path.read_text()


# ── Agent factories ────────────────────────────────────────────────────


def create_planner(client: Mistral) -> object:
    """Create the Planner agent — parses PR and builds review plan."""
    return client.beta.agents.create(
        model="mistral-large-latest",
        name="MergeGuard-Planner",
        description="Analyzes PR diffs and creates a structured review plan.",
        instructions=_load_prompt("planner"),
        tools=PLANNER_TOOLS,
        completion_args={"temperature": 0.2},
    )


def create_reviewer(client: Mistral) -> object:
    """Create the Reviewer agent — performs detailed code review."""
    return client.beta.agents.create(
        model="devstral-latest",
        name="MergeGuard-Reviewer",
        description="Reviews code changes and produces detailed comments.",
        instructions=_load_prompt("reviewer"),
        tools=REVIEWER_TOOLS,
        completion_args={"temperature": 0.3},
    )


def create_verifier(client: Mistral) -> object:
    """Create the Verifier agent — validates review suggestions."""
    return client.beta.agents.create(
        model="devstral-latest",
        name="MergeGuard-Verifier",
        description="Validates review comments using code execution.",
        instructions=_load_prompt("verifier"),
        tools=VERIFIER_TOOLS,
        completion_args={"temperature": 0.1},
    )


def create_reporter(client: Mistral) -> object:
    """Create the Reporter agent — produces structured JSON report."""
    report_schema = ReviewReport.model_json_schema()

    return client.beta.agents.create(
        model="mistral-large-latest",
        name="MergeGuard-Reporter",
        description="Aggregates findings into a structured review report.",
        instructions=_load_prompt("reporter"),
        tools=REPORTER_TOOLS,
        completion_args={"temperature": 0.1},
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "ReviewReport",
                "schema": report_schema,
            },
        },
    )
