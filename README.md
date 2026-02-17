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
| **Structured Output** | Reporter | JSON schema via `CompletionArgs(response_format=...)` |
| **Devstral** | Reviewer, Verifier | `devstral-2512` frontier code model |
| **RunContext** | Pipeline | `run_async` with registered tool functions |

## Quick Start

```bash
# Install dependencies
uv sync

# Run on a PR (requires MISTRAL_API_KEY and GITHUB_TOKEN)
uv run mergeguard https://github.com/owner/repo/pull/123
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MISTRAL_API_KEY` | ✅ | Mistral API key for agent creation |
| `GITHUB_TOKEN` | Recommended | GitHub PAT for higher rate limits on PR fetching |

## Project Structure

```
├── agents/                     # System prompts (source-of-truth)
│   ├── planner.md
│   ├── reviewer.md
│   ├── verifier.md
│   └── reporter.md
├── src/mergeguard/
│   ├── __init__.py
│   ├── main.py                 # CLI + RunContext tool loop
│   ├── agents.py               # Agent creation (CompletionArgs)
│   ├── handoffs.py             # Handoff chain setup
│   ├── tools.py                # Function tool schemas
│   ├── schemas.py              # Pydantic output models
│   └── prompts/                # Bundled prompts (package_data)
│       ├── __init__.py
│       ├── planner.md
│       ├── reviewer.md
│       ├── verifier.md
│       └── reporter.md
└── pyproject.toml
```

## License

MIT
