"""Handoff chain setup for MergeGuard pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from mergeguard.agents import (
    create_planner,
    create_reporter,
    create_reviewer,
    create_verifier,
)

if TYPE_CHECKING:
    from mistralai import Mistral


@dataclass
class MergeGuardChain:
    """Holds the 4-agent chain with handoffs configured."""

    planner_id: str
    reviewer_id: str
    verifier_id: str
    reporter_id: str
    entry_agent_id: str  # alias for planner_id — where to send user input


def build_chain(client: Mistral) -> MergeGuardChain:
    """Create all 4 agents and wire up the handoff chain.

    Chain: Planner → Reviewer → Verifier → Reporter

    Returns a MergeGuardChain with all agent IDs.
    """
    # 1. Create agents
    planner = create_planner(client)
    reviewer = create_reviewer(client)
    verifier = create_verifier(client)
    reporter = create_reporter(client)

    # 2. Wire handoffs: each agent hands off to the next
    client.beta.agents.update(
        agent_id=planner.id,
        handoffs=[reviewer.id],
    )
    client.beta.agents.update(
        agent_id=reviewer.id,
        handoffs=[verifier.id],
    )
    client.beta.agents.update(
        agent_id=verifier.id,
        handoffs=[reporter.id],
    )
    # Reporter is terminal — no handoff

    return MergeGuardChain(
        planner_id=planner.id,
        reviewer_id=reviewer.id,
        verifier_id=verifier.id,
        reporter_id=reporter.id,
        entry_agent_id=planner.id,
    )


def teardown_chain(client: Mistral, chain: MergeGuardChain) -> None:
    """Delete all agents in the chain (cleanup)."""
    for agent_id in [
        chain.planner_id,
        chain.reviewer_id,
        chain.verifier_id,
        chain.reporter_id,
    ]:
        try:
            client.beta.agents.delete(agent_id=agent_id)
        except Exception:
            pass  # best-effort cleanup
