# MergeGuard — Architecture Design Document

> **Status:** Pre-hackathon prep (design only, no production code)
> **Event:** Mistral Worldwide Hackathon 2026 (Feb 28–Mar 1)
> **Target Awards:** Best Use of Agent Skills + Online 1st Place / Global Winner

---

## 1. Overview

MergeGuard is a **multi-agent code review pipeline** that uses the Mistral Agents API with Handoffs to automatically review Pull Requests. It chains 4 specialized agents:

```
PR Diff Input
    │
    ▼
┌──────────┐    handoff    ┌──────────┐    handoff    ┌──────────┐    handoff    ┌──────────┐
│ PLANNER  │──────────────▶│ REVIEWER  │──────────────▶│ VERIFIER │──────────────▶│ REPORTER │
│ mistral- │               │ mistral-  │               │ devstral │               │ mistral- │
│ large    │               │ large     │               │          │               │ large    │
│          │               │           │               │          │               │          │
│ Decomposes│              │ Line-by-  │               │ Runs     │               │ Structured│
│ PR into  │               │ line code │               │ linting  │               │ JSON     │
│ chunks   │               │ analysis  │               │ & tests  │               │ verdict  │
└──────────┘               └──────────┘               └──────────┘               └──────────┘
     │                          │                          │                          │
  web_search              function_calling            code_interpreter          structured_output
  (context)               (get_file_context,           (lint, test)            (ReviewVerdict)
                           get_blame)
```

## 2. Mistral Features Showcased

| # | Feature | Where Used | Notes |
|---|---------|-----------|-------|
| 1 | **Agents API** (beta) | All 4 agents | `client.beta.agents.create()` |
| 2 | **Handoffs** | Planner→Reviewer→Verifier→Reporter | Linear chain with `handoffs=[]` |
| 3 | **Function Calling** | Reviewer agent | `get_file_context`, `get_blame` custom tools |
| 4 | **Code Interpreter** | Verifier agent | Runs linting/test code in sandbox |
| 5 | **Structured Output** | Reporter agent | `CompletionArgs(response_format=...)` |
| 6 | **Web Search** | Planner agent | Looks up library docs, CVE databases |
| 7 | **Devstral model** | Verifier agent | Code-specialized model for verification |
| 8 | **Conversations API** | Pipeline orchestrator | `conversations.start()` / `conversations.append()` |

**Total: 8 distinct Mistral features** — maximizes "Best Use of Agent Skills" scoring.

## 3. Agent Configurations

### 3.1 Planner Agent

```
Model:       mistral-large-latest
Name:        mergeguard-planner
Description: Reads PR diffs and decomposes them into reviewable chunks with context
Tools:       [web_search]
Handoffs:    [reviewer_agent.id]
Instructions: (see AGENT_PROMPTS.md)
```

**Responsibilities:**
- Parse the unified diff format
- Identify changed files, functions, and logical units
- Use web_search to look up unfamiliar libraries/APIs referenced in changes
- Categorize changes: security-sensitive, logic change, style, refactor, new feature, test
- Output a structured plan of review chunks for the Reviewer
- Hand off to Reviewer with the decomposed plan

### 3.2 Reviewer Agent

```
Model:       mistral-large-latest
Name:        mergeguard-reviewer
Description: Performs line-by-line code analysis using function tools for context
Tools:       [function:get_file_context, function:get_blame]
Handoffs:    [verifier_agent.id]
Instructions: (see AGENT_PROMPTS.md)
```

**Responsibilities:**
- For each chunk from the Planner, perform detailed code review
- Call `get_file_context(file, start_line, end_line)` to see surrounding code
- Call `get_blame(file, line)` to understand change history
- Identify: bugs, security issues, performance problems, style violations, missing error handling
- Assign severity: critical, warning, info, style
- Hand off findings + original diff to Verifier

### 3.3 Verifier Agent

```
Model:       devstral-small-latest (or devstral-2512)
Name:        mergeguard-verifier
Description: Validates review findings by running linting and test code
Tools:       [code_interpreter]
Handoffs:    [reporter_agent.id]
Instructions: (see AGENT_PROMPTS.md)
```

**Responsibilities:**
- Take Reviewer findings and attempt to verify them programmatically
- Use code_interpreter to:
  - Run linting rules against code snippets
  - Execute simple test cases to verify bug claims
  - Check for common vulnerability patterns (regex-based)
  - Validate that suggested fixes compile/run
- Mark each finding as: verified, likely, unverified, false_positive
- Hand off verified findings to Reporter

### 3.4 Reporter Agent

```
Model:       mistral-large-latest
Name:        mergeguard-reporter
Description: Aggregates findings into a structured JSON review verdict
Tools:       []
Handoffs:    []
CompletionArgs: response_format=ReviewVerdict (JSON schema)
Instructions: (see AGENT_PROMPTS.md)
```

**Responsibilities:**
- Aggregate all findings from Verifier
- Produce a final structured JSON verdict (see schemas below)
- Include: overall verdict (approve/request_changes/comment), summary, per-file findings
- No handoffs — terminal agent in the chain

## 4. Pipeline Orchestration Flow

```python
# Pseudocode — NOT production code

# 1. Create all 4 agents
planner = client.beta.agents.create(...)
reviewer = client.beta.agents.create(...)
verifier = client.beta.agents.create(...)
reporter = client.beta.agents.create(...)

# 2. Set up handoff chain
client.beta.agents.update(agent_id=planner.id, handoffs=[reviewer.id])
client.beta.agents.update(agent_id=reviewer.id, handoffs=[verifier.id])
client.beta.agents.update(agent_id=verifier.id, handoffs=[reporter.id])

# 3. Start conversation with Planner
response = client.beta.conversations.start(
    agent_id=planner.id,
    inputs=[{"role": "user", "content": f"Review this PR diff:\n\n{diff_text}"}]
)

# 4. Handle function calls in a loop
while not is_terminal(response):
    if has_function_call(response):
        result = execute_function(response)
        response = client.beta.conversations.append(
            conversation_id=response.conversation_id,
            inputs=[FunctionResultEntry(tool_call_id=..., result=result)]
        )
    else:
        # Agent handoff or final response — continue
        break

# 5. Extract final structured JSON from Reporter
verdict = parse_verdict(response)
```

**Key insight:** The Mistral Agents API handles handoffs automatically. When the Planner decides it's done, it hands off to the Reviewer within the same conversation. We only need to handle function calls (step 4) since built-in tools (web_search, code_interpreter) execute server-side.

## 5. Tech Stack

### Backend (Python)
- **Runtime:** Python 3.12+ with `uv`
- **SDK:** `mistralai` (latest, for beta agents API)
- **Framework:** FastAPI for the API server
- **Key endpoints:**
  - `POST /api/review` — Submit a PR diff for review
  - `GET /api/review/{id}` — Get review status/results
  - `GET /api/review/{id}/stream` — SSE stream of pipeline progress
  - `GET /api/health` — Health check

### Frontend (Next.js)
- **Framework:** Next.js 14+ (App Router)
- **UI:** Tailwind CSS + shadcn/ui
- **Features:**
  - PR diff input (paste or GitHub URL)
  - Real-time pipeline progress visualization (SSE)
  - Agent activity feed (which agent is active, what tools are being called)
  - Final verdict display with severity badges
  - File-level findings with inline diff annotations

### Deployment
- **Vercel:** Frontend (Next.js) + Backend (Python serverless functions or API routes)
- Alternative: Frontend on Vercel, Backend on Railway if needed

## 6. Data Flow

```
User Input (PR diff text or GitHub PR URL)
    │
    ▼
FastAPI Backend
    │
    ├─── Parse diff / Fetch from GitHub API
    │
    ├─── Create Mistral Agents (if not cached)
    │
    ├─── Start Conversation with Planner
    │         │
    │         ├─── [web_search] Planner looks up context
    │         │
    │         ├─── [handoff] → Reviewer
    │         │         │
    │         │         ├─── [function_call] get_file_context()
    │         │         ├─── [function_call] get_blame()
    │         │         │
    │         │         ├─── [handoff] → Verifier
    │         │         │         │
    │         │         │         ├─── [code_interpreter] lint checks
    │         │         │         ├─── [code_interpreter] test execution
    │         │         │         │
    │         │         │         ├─── [handoff] → Reporter
    │         │         │         │         │
    │         │         │         │         └─── Structured JSON output
    │         │         │         │
    │         │         │
    │         │
    │
    ├─── Stream progress events via SSE
    │
    └─── Return final ReviewVerdict JSON
              │
              ▼
         Next.js Frontend (displays results)
```

## 7. Directory Structure (Planned)

```
mergeguard/
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── factory.py       # Agent creation & handoff setup
│   │   │   ├── planner.py       # Planner agent config & prompts
│   │   │   ├── reviewer.py      # Reviewer agent config & prompts
│   │   │   ├── verifier.py      # Verifier agent config & prompts
│   │   │   └── reporter.py      # Reporter agent config & prompts
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── get_file_context.py
│   │   │   └── get_blame.py
│   │   ├── pipeline/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py  # Main pipeline loop
│   │   │   └── events.py        # SSE event types
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── review.py        # ReviewVerdict, Finding, etc.
│   │   │   └── diff.py          # DiffChunk, FileChange, etc.
│   │   └── github_client.py     # GitHub API integration
│   └── tests/
│       └── ...
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx             # Main dashboard
│   │   └── review/
│   │       └── [id]/
│   │           └── page.tsx     # Review results page
│   ├── components/
│   │   ├── DiffInput.tsx
│   │   ├── PipelineProgress.tsx
│   │   ├── AgentActivity.tsx
│   │   ├── VerdictDisplay.tsx
│   │   └── FindingCard.tsx
│   └── lib/
│       ├── api.ts
│       └── types.ts
├── demo/
│   ├── sample-pr-diff.patch     # Demo PR with known issues
│   └── expected-output.json     # Expected review verdict
├── README.md
├── vercel.json
└── .env.example
```

## 8. Demo Strategy

The demo PR should contain intentional issues across categories:

1. **Security flaw:** SQL injection via string concatenation in a query builder
2. **Bug:** Off-by-one error in pagination logic
3. **Performance:** N+1 query in a loop
4. **Style violation:** Inconsistent naming, missing docstrings
5. **Missing test:** New function with no corresponding test file
6. **Good code:** Some clean changes that should be approved (to show the system isn't just negative)

This demonstrates the pipeline catches diverse issue types and produces a nuanced verdict.

## 9. Judging Criteria Alignment

| Criteria | How MergeGuard Scores |
|----------|----------------------|
| **Agent Skills usage** | 8 Mistral features, 4-agent handoff chain |
| **Technical complexity** | Multi-agent orchestration with function calling loop |
| **Practical utility** | Solves real PR review bottleneck every dev faces |
| **Demo quality** | Real-time pipeline visualization, clear before/after |
| **Code quality** | Clean architecture, typed schemas, error handling |
| **Originality** | Not a chatbot — a structured pipeline with verification |
