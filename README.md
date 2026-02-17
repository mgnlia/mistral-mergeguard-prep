# MergeGuard — Pre-Hackathon Prep

> **⚠️ This repo contains DESIGN DOCUMENTS ONLY — no production code.**
> All code will be written during the 48h hackathon window (Feb 28–Mar 1, 2026).

## What is MergeGuard?

A multi-agent code review pipeline using the **Mistral Agents API** with **Handoffs**.

4 agents in a chain:
1. **Planner** (mistral-large) — Reads PR diff, decomposes into reviewable chunks
2. **Reviewer** (mistral-large) — Line-by-line code analysis with function calling
3. **Verifier** (devstral) — Runs linting/tests via code_interpreter
4. **Reporter** (mistral-large) — Aggregates findings into structured JSON verdict

## Prep Documents

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System overview, data flow, tech stack |
| [AGENT_CONFIGS.md](./AGENT_CONFIGS.md) | Draft agent configurations (model, tools, instructions) |
| [SCHEMAS.md](./SCHEMAS.md) | Function calling schemas + Reporter JSON verdict schema |
| [FRONTEND_PLAN.md](./FRONTEND_PLAN.md) | Next.js dashboard wireframes and component plan |
| [DEMO_PR_PLAN.md](./DEMO_PR_PLAN.md) | Demo PR with planted issues for the live demo |
| [SPRINT_PLAN.md](./SPRINT_PLAN.md) | 48h sprint timeline with phases and risk mitigation |
| [API_NOTES.md](./API_NOTES.md) | Study notes from Mistral Agents API documentation |

## Mistral Features Showcased (7)

1. Agents API (beta)
2. Handoffs (4-agent chain)
3. Function Calling (get_file_context, get_blame, get_pr_comments)
4. Code Interpreter (Verifier runs linting/tests)
5. Structured Output (Reporter JSON verdict)
6. Web Search (Reviewer checks CVE databases)
7. Devstral model (Verifier agent)

## Target Awards

- 🏆 **Best Use of Agent Skills** — Special award
- 🥇 **Online 1st Place** — $1.5K + $3K credits
- 🌍 **Global Winner** — $10K + $15K credits

## Hackathon

- **Event:** Mistral AI Worldwide Hackathon 2026
- **Dates:** Feb 28–Mar 1, 2026
- **Format:** Online track
