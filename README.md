# MergeGuard

**Multi-agent code review pipeline** built with the [Mistral Agents API](https://docs.mistral.ai/capabilities/agents/).

> Built for the [Mistral Worldwide Hackathon 2026](https://worldwide-hackathon.mistral.ai/) — targeting **Best Use of Agent Skills**.

## Architecture

```
┌─────────────┐    handoff    ┌──────────────┐    handoff    ┌──────────────┐    handoff    ┌──────────────┐
│   Planner   │ ──────────▶  │   Reviewer   │ ──────────▶  │   Verifier   │ ──────────▶  │   Reporter   │
│             │              │              │              │              │              │              │
│ • Parse PR  │              │ • Review code│              │ • Validate   │              │ • Aggregate  │
│ • Identify  │              │ • Find bugs  │              │   suggestions│              │ • Score      │
│   changes   │              │ • Style check│              │ • Run linter │              │ • JSON report│
│ • Plan tasks│              │ • Suggest fix│              │ • Test code  │              │ • Recommend  │
└─────────────┘              └──────────────┘              └──────────────┘              └──────────────┘
  Function tools               Function tools               code_interpreter              structured output
  (fetch_pr_diff,              (read_file,                   (validation)                  (response_format)
   list_changed_files)          check_style)
```

## Mistral Features Used

| Feature | Agent | Usage |
|---------|-------|-------|
| **Agents API** | All | `client.beta.agents.create()` |
| **Handoffs** | All | Sequential agent chain via `handoffs=[agent_id]` |
| **Function Calling** | Planner, Reviewer | Custom tools for GitHub PR interaction |
| **Code Interpreter** | Verifier | Run linting/validation on code snippets |
| **Structured Output** | Reporter | JSON schema for review report |
| **Devstral** | Reviewer, Verifier | Code-specialized model |

## Quick Start

```bash
# Install dependencies
uv sync

# Run on a PR (requires MISTRAL_API_KEY and GITHUB_TOKEN)
uv run mergeguard https://github.com/owner/repo/pull/123
```

## Project Structure

```
├── agents/              # System prompts for each agent
│   ├── planner.md
│   ├── reviewer.md
│   ├── verifier.md
│   └── reporter.md
├── docs/
│   └── architecture.md  # Detailed architecture doc
├── src/mergeguard/
│   ├── __init__.py
│   ├── main.py          # CLI entry point
│   ├── agents.py        # Agent creation
│   ├── handoffs.py      # Handoff chain setup
│   ├── tools.py         # Function tool definitions
│   └── schemas.py       # Pydantic output models
└── pyproject.toml
```

## License

MIT
