"""Prompt loading for MergeGuard agents.

Uses importlib.resources when installed as a package, falls back to
__file__-relative path for editable / source-tree runs.
"""

from __future__ import annotations

import importlib.resources
from pathlib import Path

# ── Prompt resolution ──────────────────────────────────────────────────

# Strategy 1: package data (installed via `uv sync` / pip)
_PKG_AGENTS: Path | None = None
try:
    _ref = importlib.resources.files("mergeguard") / "agents"
    # Materialise to a real path (works for both regular and editable installs)
    _candidate = Path(str(_ref))
    if _candidate.is_dir():
        _PKG_AGENTS = _candidate
except Exception:
    pass

# Strategy 2: source tree (running from repo root)
_SRC_AGENTS = Path(__file__).resolve().parent.parent.parent / "agents"


def _agents_dir() -> Path:
    """Return the agents prompt directory, preferring package data."""
    if _PKG_AGENTS is not None and _PKG_AGENTS.is_dir():
        return _PKG_AGENTS
    if _SRC_AGENTS.is_dir():
        return _SRC_AGENTS
    raise FileNotFoundError(
        "Cannot locate agent prompts directory. Tried:\n"
        f"  package data: {_PKG_AGENTS}\n"
        f"  source tree:  {_SRC_AGENTS}\n"
        "Make sure the 'agents/' directory exists at the project root "
        "or is bundled as package data."
    )


def load_prompt(name: str) -> str:
    """Load an agent's system prompt from agents/<name>.md."""
    prompt_path = _agents_dir() / f"{name}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Agent prompt not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")
