"""Agent creation for MergeGuard pipeline."""

from __future__ import annotations

import importlib.resources
from typing import TYPE_CHECKING

from mistralai import CompletionArgs, ResponseFormat, JSONSchema

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


def _load_prompt(name: str) -> str:
    """Load an agent's system prompt from the prompts package data.

    Uses importlib.resources so prompts are resolved correctly whether
    running from source, an installed wheel, or a zip archive.
    Falls back to Path(__file__)-relative resolution for editable installs.
    """
    # Try importlib.resources first (works with package_data / installed)
    try:
        pkg = importlib.resources.files("mergeguard") / "prompts" / f"{name}.md"
        return pkg.read_text(encoding="utf-8")
    except (FileNotFoundError, TypeError, ModuleNotFoundError):
        pass

    # Fallback: resolve relative to this file → ../../agents/<name>.md
    from pathlib import Path

    agents_dir = Path(__file__).resolve().parent.parent.parent / "agents"
    prompt_path = agents_dir / f"{name}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Agent prompt not found. Tried importlib.resources and {prompt_path}"
        )
    return prompt_path.read_text(encoding="utf-8")


# ── Agent factories ────────────────────────────────────────────────────


def create_planner(client: Mistral) -> object:
    """Create the Planner agent — parses PR and builds review plan."""
    return client.beta.agents.create(
        model="mistral-large-latest",
        name="MergeGuard-Planner",
        description="Analyzes PR diffs and creates a structured review plan.",
        instructions=_load_prompt("planner"),
        tools=PLANNER_TOOLS,
        completion_args=CompletionArgs(temperature=0.2),
    )


def create_reviewer(client: Mistral) -> object:
    """Create the Reviewer agent — performs detailed code review.

    Uses devstral-2512 (Mistral's frontier code model).
    """
    return client.beta.agents.create(
        model="devstral-2512",
        name="MergeGuard-Reviewer",
        description="Reviews code changes and produces detailed comments.",
        instructions=_load_prompt("reviewer"),
        tools=REVIEWER_TOOLS,
        completion_args=CompletionArgs(temperature=0.3),
    )


def create_verifier(client: Mistral) -> object:
    """Create the Verifier agent — validates review suggestions.

    Uses devstral-2512 (Mistral's frontier code model).
    """
    return client.beta.agents.create(
        model="devstral-2512",
        name="MergeGuard-Verifier",
        description="Validates review comments using code execution.",
        instructions=_load_prompt("verifier"),
        tools=VERIFIER_TOOLS,
        completion_args=CompletionArgs(temperature=0.1),
    )


def create_reporter(client: Mistral) -> object:
    """Create the Reporter agent — produces structured JSON report.

    response_format is placed inside completion_args (not top-level)
    per the Mistral Agents API spec.
    """
    return client.beta.agents.create(
        model="mistral-large-latest",
        name="MergeGuard-Reporter",
        description="Aggregates findings into a structured review report.",
        instructions=_load_prompt("reporter"),
        tools=REPORTER_TOOLS,
        completion_args=CompletionArgs(
            temperature=0.1,
            response_format=ResponseFormat(
                type="json_schema",
                json_schema=JSONSchema(
                    name="ReviewReport",
                    schema=ReviewReport.model_json_schema(),
                ),
            ),
        ),
    )
