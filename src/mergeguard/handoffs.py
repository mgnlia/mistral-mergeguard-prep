"""Handoff chain setup for MergeGuard.

Creates all 4 agents, then wires them together using Mistral's handoff mechanism:
  Planner → Reviewer → Verifier → Reporter

Each agent's `handoffs` field is updated to point to the next agent in the chain.
When an agent finishes its work, it automatically hands off control (and the full
conversation context) to the next agent.

NOTE: This is scaffold code. No actual API calls are made.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from mergeguard.agents import (
    create_planner_agent,
    create_reporter_agent,
    create_reviewer_agent,
    create_verifier_agent,
)

if TYPE_CHECKING:
    from mistralai import Mistral


@dataclass
class PipelineAgents:
    """Container for the 4 agent IDs in the MergeGuard pipeline."""

    planner_id: str
    reviewer_id: str
    verifier_id: str
    reporter_id: str


def create_pipeline(client: Mistral) -> PipelineAgents:
    """Create all 4 agents and wire up the handoff chain.

    Steps:
        1. Create each agent via the Agents API
        2. Update each agent (except Reporter) to set its handoff target

    The handoff chain is:
        Planner → Reviewer → Verifier → Reporter

    Args:
        client: Authenticated Mistral client.

    Returns:
        PipelineAgents with all 4 agent IDs.
    """
    # Step 1: Create all agents
    planner_id = create_planner_agent(client)
    reviewer_id = create_reviewer_agent(client)
    verifier_id = create_verifier_agent(client)
    reporter_id = create_reporter_agent(client)

    # Step 2: Wire up handoffs
    # Planner hands off to Reviewer
    client.beta.agents.update(
        agent_id=planner_id,
        handoffs=[reviewer_id],
    )

    # Reviewer hands off to Verifier
    client.beta.agents.update(
        agent_id=reviewer_id,
        handoffs=[verifier_id],
    )

    # Verifier hands off to Reporter
    client.beta.agents.update(
        agent_id=verifier_id,
        handoffs=[reporter_id],
    )

    # Reporter is the final agent — no handoffs

    return PipelineAgents(
        planner_id=planner_id,
        reviewer_id=reviewer_id,
        verifier_id=verifier_id,
        reporter_id=reporter_id,
    )


def delete_pipeline(client: Mistral, agents: PipelineAgents) -> None:
    """Clean up all agents in the pipeline.

    Call this after the review is complete to avoid leaving orphaned agents
    on the Mistral platform.

    Args:
        client: Authenticated Mistral client.
        agents: The PipelineAgents to delete.
    """
    for agent_id in [
        agents.planner_id,
        agents.reviewer_id,
        agents.verifier_id,
        agents.reporter_id,
    ]:
        client.beta.agents.delete(agent_id=agent_id)
