# MergeGuard — Multi-Agent Code Review Pipeline
## Architecture Design Document (Pre-Hackathon Prep)

> **IMPORTANT:** This is a design document only. All production code must be written during the 48h hackathon window (Feb 28–Mar 1, 2026).

---

## 1. Overview

MergeGuard is a multi-agent code review pipeline built on Mistral's Agents API with Handoffs. It automates the PR merge-quality gate with 4 specialized agents that plan, review, verify, and report on code changes.

**Target Awards:**
- "Best Use of Agent Skills" (primary)
- Online 1st Place ($1,500 + $3,000 credits)
- Global Winner ($10,000 + $15,000 credits)

---

## 2. Agent Pipeline

```
PR Submitted
    │
    ▼
┌─────────────────┐
│  PLANNER AGENT  │  mistral-large-latest
│  Tools: web_search│  Decomposes PR into reviewable chunks
│  Handoffs → Reviewer│  Assigns focus areas per file
└────────┬────────┘
         │ handoff
         ▼
┌─────────────────┐
│  REVIEWER AGENT │  mistral-large-latest
│  Tools: function_calling│  Line-by-line code analysis
│  (get_file_context, get_blame)│  Produces structured review comments
│  Handoffs → Verifier│
└────────┬────────┘
         │ handoff
         ▼
┌─────────────────┐
│  VERIFIER AGENT │  devstral-latest
│  Tools: code_interpreter│  Runs linting, type checks, tests
│  Handoffs → Reporter│  Validates reviewer findings
└────────┬────────┘
         │ handoff
         ▼
┌─────────────────┐
│  REPORTER AGENT │  mistral-large-latest
│  Structured Output│  Aggregates all findings
│  (JSON schema)  │  Produces merge/block verdict
└─────────────────┘
         │
         ▼
    Verdict JSON
    (merge / block / request-changes)
```

---

## 3. Mistral Features Used (6+)

| # | Feature | Agent | How Used |
|---|---------|-------|----------|
| 1 | **Agents API** (beta) | All | `client.beta.agents.create()` for each agent |
| 2 | **Handoffs** | All | Chain: Planner→Reviewer→Verifier→Reporter |
| 3 | **Function Calling** | Reviewer | Custom `get_file_context`, `get_blame`, `get_pr_diff` |
| 4 | **Code Interpreter** | Verifier | Built-in tool for running linting/tests |
| 5 | **Structured Output** | Reporter | JSON schema for verdict |
| 6 | **Web Search** | Planner | Built-in tool for docs/context lookup |
| 7 | **Devstral** | Verifier | Specialized coding model |

---

## 4. Agent Configurations

### 4.1 Planner Agent
```python
planner = client.beta.agents.create(
    model="mistral-large-latest",
    name="mergeguard-planner",
    description="Analyzes PR diffs and creates a structured review plan",
    instructions="""You are the Planner agent in the MergeGuard code review pipeline.

Given a PR diff, you must:
1. Identify all changed files and categorize them (source, test, config, docs)
2. Assess the risk level of each change (high/medium/low)
3. Create a review plan with specific focus areas for each file
4. Flag any files that need security review
5. Hand off to the Reviewer agent with the structured plan

Output a structured review plan before handing off.""",
    tools=[{"type": "web_search"}],
    # handoffs=[reviewer.id]  — set after all agents created
)
```

### 4.2 Reviewer Agent
```python
reviewer = client.beta.agents.create(
    model="mistral-large-latest",
    name="mergeguard-reviewer",
    description="Performs line-by-line code review with custom tools",
    instructions="""You are the Reviewer agent in the MergeGuard code review pipeline.

Given a review plan from the Planner, you must:
1. Use get_file_context to understand the full file context around changes
2. Use get_blame to understand change history
3. Review each changed file according to the plan's focus areas
4. Produce structured review comments with:
   - File path and line numbers
   - Severity (critical/warning/info)
   - Category (security/performance/style/logic/test-coverage)
   - Description and suggested fix
5. Hand off to the Verifier with your findings

Be thorough but avoid false positives. Focus on real issues.""",
    tools=[
        {
            "type": "function",
            "function": {
                "name": "get_file_context",
                "description": "Get the full content of a file in the repository",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to the file"},
                        "start_line": {"type": "integer", "description": "Start line (optional)"},
                        "end_line": {"type": "integer", "description": "End line (optional)"}
                    },
                    "required": ["file_path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_blame",
                "description": "Get git blame information for a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to the file"},
                        "line_number": {"type": "integer", "description": "Specific line to blame"}
                    },
                    "required": ["file_path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_pr_diff",
                "description": "Get the unified diff for the pull request",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Optional: specific file diff"}
                    }
                }
            }
        }
    ],
    # handoffs=[verifier.id]
)
```

### 4.3 Verifier Agent
```python
verifier = client.beta.agents.create(
    model="devstral-latest",
    name="mergeguard-verifier",
    description="Validates review findings by running code analysis",
    instructions="""You are the Verifier agent in the MergeGuard code review pipeline.

Given review findings from the Reviewer, you must:
1. Use the code interpreter to run linting checks on flagged code
2. Verify security findings with actual code analysis
3. Run type checking where applicable
4. Test edge cases mentioned in review comments
5. Mark each finding as: verified, false-positive, or needs-human-review
6. Hand off to the Reporter with verified findings

Use code_interpreter to actually execute checks, don't just reason about them.""",
    tools=[{"type": "code_interpreter"}],
    # handoffs=[reporter.id]
)
```

### 4.4 Reporter Agent
```python
from pydantic import BaseModel
from typing import List, Literal

class ReviewFinding(BaseModel):
    file_path: str
    line_start: int
    line_end: int
    severity: Literal["critical", "warning", "info"]
    category: Literal["security", "performance", "style", "logic", "test-coverage"]
    description: str
    suggested_fix: str
    verified: bool

class MergeVerdict(BaseModel):
    decision: Literal["merge", "block", "request-changes"]
    confidence: float  # 0.0 - 1.0
    summary: str
    findings: List[ReviewFinding]
    critical_count: int
    warning_count: int
    info_count: int
    review_duration_seconds: float

reporter = client.beta.agents.create(
    model="mistral-large-latest",
    name="mergeguard-reporter",
    description="Aggregates findings into a structured merge verdict",
    instructions="""You are the Reporter agent in the MergeGuard code review pipeline.

Given verified findings from the Verifier, you must:
1. Aggregate all findings into a structured report
2. Calculate the merge verdict based on:
   - BLOCK if any critical findings are verified
   - REQUEST-CHANGES if warnings > 3 or any security warnings
   - MERGE if only info-level findings
3. Assign a confidence score (0.0-1.0)
4. Write a human-readable summary
5. Output the final verdict as structured JSON

Be decisive. The verdict should be actionable.""",
    completion_args=CompletionArgs(
        response_format=ResponseFormat(
            type="json_schema",
            json_schema=JSONSchema(
                name="merge_verdict",
                schema=MergeVerdict.model_json_schema(),
            )
        )
    ),
)
```

---

## 5. Handoff Chain Setup
```python
# After all agents are created, wire up handoffs
planner = client.beta.agents.update(
    agent_id=planner.id,
    handoffs=[reviewer.id]
)
reviewer = client.beta.agents.update(
    agent_id=reviewer.id,
    handoffs=[verifier.id]
)
verifier = client.beta.agents.update(
    agent_id=verifier.id,
    handoffs=[reporter.id]
)
```

---

## 6. Frontend (Next.js)

### Pages
- `/` — Dashboard: paste PR URL, trigger review
- `/review/[id]` — Live review progress (streaming agent handoffs)
- `/history` — Past reviews

### Key Components
- `PipelineProgress` — Shows which agent is active, with live streaming
- `FindingsList` — Displays review findings with severity badges
- `VerdictCard` — Shows final merge/block decision with confidence
- `DiffViewer` — Shows annotated diff with inline review comments

### API Routes
- `POST /api/review` — Start a new review (accepts PR diff or GitHub URL)
- `GET /api/review/[id]` — Get review status/results
- `GET /api/health` — Health check

---

## 7. Demo PR (Pre-prepared)

Create a demo repository with a PR containing known issues:

1. **Security flaw** — SQL injection in a query builder (critical)
2. **Performance issue** — N+1 query in a loop (warning)
3. **Style violation** — Inconsistent naming convention (info)
4. **Missing test** — New function with no test coverage (warning)
5. **Logic bug** — Off-by-one error in pagination (critical)

This ensures the demo is reliable and showcases all severity levels.

---

## 8. Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12 + `mistralai` SDK |
| Frontend | Next.js 14 + TypeScript + Tailwind |
| API | Next.js API routes (Python subprocess or API call) |
| Deploy | Vercel (frontend) |
| CI | GitHub Actions |

---

## 9. File Structure (Planned)
```
mergeguard/
├── app/                    # Next.js app directory
│   ├── page.tsx           # Dashboard
│   ├── review/[id]/page.tsx  # Review detail
│   ├── api/
│   │   ├── review/route.ts   # Start review
│   │   ├── health/route.ts   # Health check
│   │   └── status/[id]/route.ts  # Review status
│   └── layout.tsx
├── lib/
│   ├── agents.ts          # Agent creation + handoff setup
│   ├── tools.ts           # Function calling tool implementations
│   ├── types.ts           # TypeScript types for verdict, findings
│   └── mistral.ts         # Mistral client setup
├── components/
│   ├── PipelineProgress.tsx
│   ├── FindingsList.tsx
│   ├── VerdictCard.tsx
│   └── DiffViewer.tsx
├── demo/                  # Demo PR files
│   ├── vulnerable-query.ts
│   ├── n-plus-one.ts
│   └── off-by-one.ts
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── vercel.json
└── README.md
```

---

## 10. Judging Optimization

| Criterion (25% each) | How MergeGuard Scores |
|----------------------|----------------------|
| **Impact** | Every dev team has PR review bottleneck. Measurable: review time, catch rate |
| **Technical Implementation** | 4 agents, 6+ Mistral features, handoff chain, structured output |
| **Creativity** | NOT a chatbot — structured pipeline with verification step is novel |
| **Pitch** | Live demo with real PR, before/after comparison, clear metrics |

---

## 11. Risk Mitigations

| Risk | Mitigation |
|------|-----------|
| Agents API down | Fallback: direct chat completions with manual orchestration |
| Handoffs broken | Each agent can run standalone; degrade to sequential API calls |
| Rate limits | Use ministral-8b for Planner (low-stakes), large only for Reviewer/Reporter |
| Over-scope | MVP = 4 agents + 1 demo PR + verdict JSON. No extras until MVP works |
| Demo fails | Pre-cache one successful run; show cached result if live fails |
