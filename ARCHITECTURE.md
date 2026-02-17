# MergeGuard — Architecture Design Document

> **Status:** Pre-hackathon prep (design only, no production code)
> **Hackathon:** Mistral Worldwide Hackathon 2026 (Feb 28–Mar 1)
> **Target Awards:** Best Use of Agent Skills + Online 1st Place / Global Winner

---

## 1. System Overview

MergeGuard is a multi-agent code review pipeline that uses the **Mistral Agents API** with **Handoffs** to orchestrate 4 specialized agents in a chain. Given a GitHub PR diff, the pipeline produces a structured review verdict.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   PLANNER   │────▶│  REVIEWER    │────▶│  VERIFIER    │────▶│  REPORTER   │
│ mistral-large│     │ mistral-large│     │  devstral    │     │ mistral-large│
│              │     │              │     │              │     │              │
│ Reads diff,  │     │ Line-by-line │     │ Runs linting │     │ Aggregates   │
│ decomposes   │     │ code analysis│     │ & tests via  │     │ into JSON    │
│ into chunks  │     │ w/ fn calling│     │ code_interp  │     │ verdict      │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                    │                    │                    │
   Handoff →           Handoff →            Handoff →          Final Output
```

## 2. Mistral Features Showcased (6+)

| # | Feature | Where Used |
|---|---------|------------|
| 1 | **Agents API** (beta) | All 4 agents created via `client.beta.agents.create()` |
| 2 | **Handoffs** | Planner → Reviewer → Verifier → Reporter chain |
| 3 | **Function Calling** | Reviewer uses `get_file_context`, `get_blame`, `get_pr_comments` |
| 4 | **Code Interpreter** | Verifier runs linting/test commands in sandbox |
| 5 | **Structured Output** | Reporter outputs JSON verdict via `completion_args.response_format` |
| 6 | **Web Search** | Reviewer can search for best practices / CVE databases |
| 7 | **Devstral Model** | Verifier agent uses `devstral-latest` for code-focused tasks |

## 3. Data Flow

```
User Input (PR URL or diff text)
        │
        ▼
   ┌─────────┐
   │ Backend  │  Python (FastAPI)
   │ /review  │
   └────┬────┘
        │ 1. Fetch PR diff from GitHub API
        │ 2. Start conversation with Planner agent
        ▼
   ┌─────────────────────────────────────────────┐
   │         Mistral Agents API (Cloud)           │
   │                                               │
   │  Planner ──handoff──▶ Reviewer               │
   │                          │                    │
   │                    function.call              │
   │                    (get_file_context)          │
   │                          │                    │
   │                    ◀── tool result ──         │
   │                          │                    │
   │              ──handoff──▶ Verifier            │
   │                          │                    │
   │                    code_interpreter            │
   │                    (run linter/tests)          │
   │                          │                    │
   │              ──handoff──▶ Reporter            │
   │                          │                    │
   │                    structured output           │
   │                    (JSON verdict)              │
   └──────────────────────┬──────────────────────┘
                          │
                          ▼
                   ┌────────────┐
                   │  Frontend   │  Next.js on Vercel
                   │  Dashboard  │
                   └────────────┘
```

## 4. Tech Stack

### Backend (Python)
- **Runtime:** Python 3.12+ via `uv`
- **Framework:** FastAPI with SSE (Server-Sent Events) for streaming progress
- **SDK:** `mistralai` Python SDK (latest)
- **GitHub Integration:** `httpx` for GitHub REST API calls
- **Deployment:** Vercel Serverless Functions (Python runtime) OR Railway

### Frontend (Next.js)
- **Framework:** Next.js 14+ (App Router)
- **UI:** Tailwind CSS + shadcn/ui components
- **State:** React hooks + SSE for real-time pipeline updates
- **Deployment:** Vercel

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/review` | Start a review pipeline for a PR |
| GET | `/api/review/:id/stream` | SSE stream of pipeline progress |
| GET | `/api/review/:id` | Get final review result |
| GET | `/api/health` | Health check |

## 5. Handoff Execution Mode

We use **`handoff_execution="server"`** (default) so the Mistral cloud handles the handoff chain automatically. The conversation flows:

1. Start conversation with Planner agent
2. Planner analyzes diff, produces chunk plan, triggers handoff to Reviewer
3. Reviewer performs line-by-line analysis, may call functions, triggers handoff to Verifier
4. Verifier runs code_interpreter for linting/tests, triggers handoff to Reporter
5. Reporter produces structured JSON verdict

For function calls (Reviewer's tools), we use **`handoff_execution="client"`** so we can intercept `function.call` outputs, execute them locally, and return results via `FunctionResultEntry`.

**Key insight:** We may need a hybrid approach — use client-side execution to handle function calls in the Reviewer step, then let the chain continue.

## 6. Error Handling Strategy

- **Timeout:** 120s max per agent step, 5min total pipeline
- **Retry:** Up to 2 retries per agent on transient errors
- **Fallback:** If handoff chain breaks, fall back to sequential conversation.append()
- **Rate limits:** Queue reviews, max 3 concurrent pipelines

## 7. Demo Strategy

Prepare a demo PR repository with intentional issues:
1. **Security flaw:** SQL injection in a Python endpoint
2. **Style violation:** Inconsistent naming, missing docstrings
3. **Missing test:** New function without corresponding test
4. **Performance issue:** N+1 query pattern
5. **Bug:** Off-by-one error in loop

This gives the pipeline rich material to demonstrate all 4 agents working together.
