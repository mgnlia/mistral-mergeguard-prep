"""Configuration and constants for MergeGuard."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "mistral-large-latest"
DEFAULT_HANDOFF_MODE = "server"  # "server" | "client"

AGENT_NAMES = {
    "planner": "mergeguard-planner",
    "reviewer": "mergeguard-reviewer",
    "verifier": "mergeguard-verifier",
    "reporter": "mergeguard-reporter",
}


# ---------------------------------------------------------------------------
# Runtime config (populated from env / CLI)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MergeGuardConfig:
    """Immutable runtime configuration."""

    mistral_api_key: str = field(repr=False)
    github_token: str = field(repr=False)
    model: str = DEFAULT_MODEL
    handoff_mode: str = DEFAULT_HANDOFF_MODE

    @classmethod
    def from_env(cls) -> "MergeGuardConfig":
        """Build config from environment variables.

        Required:
            MISTRAL_API_KEY
            GITHUB_TOKEN

        Optional:
            MERGEGUARD_MODEL        (default: mistral-large-latest)
            MERGEGUARD_HANDOFF_MODE (default: server)
        """
        mistral_key = os.environ.get("MISTRAL_API_KEY", "")
        github_token = os.environ.get("GITHUB_TOKEN", "")

        if not mistral_key:
            raise EnvironmentError("MISTRAL_API_KEY environment variable is required")
        if not github_token:
            raise EnvironmentError("GITHUB_TOKEN environment variable is required")

        return cls(
            mistral_api_key=mistral_key,
            github_token=github_token,
            model=os.environ.get("MERGEGUARD_MODEL", DEFAULT_MODEL),
            handoff_mode=os.environ.get("MERGEGUARD_HANDOFF_MODE", DEFAULT_HANDOFF_MODE),
        )
