# MergeGuard

**Multi-agent code review pipeline using Mistral Agents API**

Built for the [Mistral Worldwide Hackathon 2026](https://mistral.ai) — targeting the **"Best Use of Agent Skills"** award.

MergeGuard orchestrates 4 specialized AI agents that review pull requests end-to-end: from analyzing the diff, to reviewing each change, verifying suggestions with real code execution, and producing a structured final report. The agents communicate through Mistral's native **Handoffs** mechanism — no external orchestrator needed.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MergeGuard Pipeline                         │
│                                                                     │
│   PR URL / Diff                                                     │
│        │                                                            │
│        ▼                                                            │
│  ┌───────────┐   handoff   ┌────────────┐   handoff   ┌──────────┐│
│  │  PLANNER  │ ──────────► │  REVIEWER   │ ──────────► │ VERIFIER ││
│  │   Agent   │             │   Agent     │             │  Agent   ││
│  └───────────┘             └────────────┘             └──────────┘│
│        │                         │                          │      │
│   Uses:                     Uses:                      Uses:      │
│   • fetch_pr_diff           • read_file                • code_    │
│   • list_changed_files      • check_style                interpreter│
│                                                             │      │
│                                                    handoff  │      │
│                                                             ▼      │
│                                                      ┌──────────┐ │
│                                                      │ REPORTER │ │
│                                                      │  Agent   │ │
│                                                      └──────────┘ │
│                                                             │      │
│                                                        Uses:      │
│                                                   • structured    │
│                                                     JSON output   │
│                                                             │      │
│                                                             ▼      │
│                                                    ┌──────────────┐│
│                                                    │ ReviewReport ││
│                                                    │    (JSON)    ││
│                                                    └──────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### Handoff Flow

```
Planner ──► Reviewer ──► Verifier ──► Reporter ──► Structured JSON Report
   │            │             │             │
   │            │             │             └─ response_format (JSON schema)
   │            │             └─ code_interpreter (lint, test snippets)
   │            └─ function tools (read_file, check_style)
   └─ function tools (fetch_pr_diff, list_changed_files)
```

## Mistral Features Used

| Feature | Where |
|---|---|
| **Agents API** | All 4 agents created via `client.beta.agents.create()` |
| **Handoffs** | Chain: Planner → Reviewer → Verifier → Reporter |
| **Function Calling** | `fetch_pr_diff`, `read_file`, `list_changed_files`, `check_style` |
| **Code Interpreter** | Verifier agent runs linting & test snippets |
| **Structured Output** | Reporter agent uses `response_format` with JSON schema |
| **Devstral Model** | Code-optimized model for all agents |

## Quick Start

```bash
# Install dependencies
uv sync

# Run a review (scaffold — no actual API calls yet)
uv run python -m mergeguard --pr https://github.com/owner/repo/pull/123

# Or with a local diff
uv run python -m mergeguard --diff path/to/changes.diff
```

## Project Structure

```
├── agents/                # Agent system prompts
│   ├── planner.md
│   ├── reviewer.md
│   ├── verifier.md
│   └── reporter.md
├── docs/
│   └── architecture.md   # Detailed architecture doc
├── src/mergeguard/
│   ├── __init__.py
│   ├── main.py            # CLI entry point
│   ├── agents.py          # Agent creation functions
│   ├── handoffs.py        # Handoff chain setup
│   ├── tools.py           # Function tool definitions
│   └── schemas.py         # Pydantic models for structured output
├── pyproject.toml
└── README.md
```

## License

MIT
