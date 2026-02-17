"""Agent creation functions for MergeGuard.

Each function creates one agent via the Mistral Agents API using
`client.beta.agents.create()`. Agents are configured with their
system prompt (loaded from agents/*.md), tools, model, and
completion_args where needed.

NOTE: This is scaffold code. No actual API calls are made.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from mergeguard.schemas import ReviewReport
from mergeguard.tools import PLANNER_TOOLS, REVIEWER_TOOLS

if TYPE_CHECKING:
    from mistralai import Mistral

# Path to agent prompt files (relative to project root)
PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "agents"

MODEL = "devstral-small-latest"


def _load_prompt(agent_name: str) -> str:
    """Load a system prompt from agents/<name>.md."""
    prompt_path = PROMPTS_DIR / f"{agent_name}.md"
    return prompt_path.read_text(encoding="utf-8")


def create_planner_agent(client: Mistral) -> str:
    """Create the Planner agent.

    The Planner receives the PR input, fetches the diff, analyzes changes,
    and creates a prioritized review task list.

    Tools: fetch_pr_diff, list_changed_files
    Handoffs: → Reviewer (configured separately in handoffs.py)

    Returns:
        The agent ID.
    """
    instructions = _load_prompt("planner")

    agent = client.beta.agents.create(
        model=MODEL,
        name="MergeGuard Planner",
        description="Analyzes PR diffs and creates prioritized review task lists",
        instructions=instructions,
        tools=PLANNER_TOOLS,
    )
    return agent.id


def create_reviewer_agent(client: Mistral) -> str:
    """Create the Reviewer agent.

    The Reviewer performs detailed code review on each changed file,
    checking for correctness, security, performance, maintainability,
    and style issues.

    Tools: read_file, check_style
    Handoffs: → Verifier (configured separately in handoffs.py)

    Returns:
        The agent ID.
    """
    instructions = _load_prompt("reviewer")

    agent = client.beta.agents.create(
        model=MODEL,
        name="MergeGuard Reviewer",
        description="Performs detailed code review and produces structured comments",
        instructions=instructions,
        tools=REVIEWER_TOOLS,
    )
    return agent.id


def create_verifier_agent(client: Mistral) -> str:
    """Create the Verifier agent.

    The Verifier validates review suggestions by executing code in the
    code interpreter — running linters, test snippets, and benchmarks.

    Tools: code_interpreter (Mistral built-in)
    Handoffs: → Reporter (configured separately in handoffs.py)

    Returns:
        The agent ID.
    """
    instructions = _load_prompt("verifier")

    agent = client.beta.agents.create(
        model=MODEL,
        name="MergeGuard Verifier",
        description="Validates review suggestions via code execution",
        instructions=instructions,
        tools=[{"type": "code_interpreter"}],
    )
    return agent.id


def create_reporter_agent(client: Mistral) -> str:
    """Create the Reporter agent.

    The Reporter aggregates verified findings into a structured JSON
    review report. Uses response_format to guarantee schema conformance.

    Tools: none (output-only)
    Handoffs: none (final agent in the chain)
    Completion args: response_format with ReviewReport JSON schema

    Returns:
        The agent ID.
    """
    instructions = _load_prompt("reporter")

    agent = client.beta.agents.create(
        model=MODEL,
        name="MergeGuard Reporter",
        description="Aggregates findings into a structured JSON review report",
        instructions=instructions,
        tools=[],
        completion_args={
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "ReviewReport",
                    "schema": ReviewReport.model_json_schema(),
                },
            },
        },
    )
    return agent.id
