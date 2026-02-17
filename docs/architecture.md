# MergeGuard Architecture

## Overview

MergeGuard is a 4-agent pipeline that performs automated code review on GitHub Pull Requests. Each agent specializes in one phase of the review process and hands off to the next via Mistral's Handoffs API.

## Agent Chain

### 1. Planner Agent

**Role:** Receive a PR URL, fetch the diff, and produce a structured review plan.

- **Model:** `mistral-large-latest`
- **Tools:** `fetch_pr_diff` (function), `list_changed_files` (function)
- **Input:** PR URL from user
- **Output:** Review plan — list of files to review, priority order, areas of concern
- **Handoff:** → Reviewer Agent (passes review plan + diff context)

### 2. Reviewer Agent

**Role:** Perform detailed code review on each changed file.

- **Model:** `devstral-2512` (code-specialized frontier model)
- **Tools:** `read_file` (function), `check_style` (function)
- **Input:** Review plan from Planner
- **Output:** List of review comments (file, line, severity, message, suggestion)
- **Handoff:** → Verifier Agent (passes review comments)

### 3. Verifier Agent

**Role:** Validate the Reviewer's suggestions by running code analysis.

- **Model:** `devstral-2512`
- **Tools:** `code_interpreter` (built-in)
- **Input:** Review comments from Reviewer
- **Output:** Verified comments — each marked as confirmed/rejected with evidence
- **Handoff:** → Reporter Agent (passes verified comments)

The Verifier uses code_interpreter to:
- Run linting on suggested fixes
- Test that code snippets compile/parse correctly
- Verify style suggestions match project conventions
- Check for false positives in the Reviewer's output

### 4. Reporter Agent

**Role:** Aggregate all findings into a final structured review report.

- **Model:** `mistral-large-latest`
- **Tools:** None (output only)
- **Output format:** Structured JSON via `CompletionArgs(response_format=...)` with JSON schema
- **Input:** Verified comments from Verifier
- **Output:** `ReviewReport` JSON — summary, scored comments, overall score, recommendation

## Handoff Flow

```
User Input (PR URL)
       │
       ▼
   ┌─────────┐
   │ Planner │──── fetch_pr_diff(), list_changed_files()
   └────┬────┘
        │ handoff (review plan + diff)
        ▼
   ┌──────────┐
   │ Reviewer │──── read_file(), check_style()
   └────┬─────┘
        │ handoff (review comments)
        ▼
   ┌──────────┐
   │ Verifier │──── code_interpreter
   └────┬─────┘
        │ handoff (verified comments)
        ▼
   ┌──────────┐
   │ Reporter │──── structured output (JSON schema)
   └────┬─────┘
        │
        ▼
   ReviewReport JSON
```

## Conversation Execution (RunContext)

The pipeline uses Mistral's `RunContext` + `run_async` pattern for automatic
function-call execution and multi-agent handoffs:

```python
from mistralai.extra.run.context import RunContext

async with RunContext(agent_id=chain.entry_agent_id) as run_ctx:
    @run_ctx.register_func
    def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> str:
        """Fetch PR diff from GitHub."""
        # Real implementation using httpx + GitHub API
        ...

    run_result = await client.beta.conversations.run_async(
        run_ctx=run_ctx, inputs=user_message
    )
```

The SDK automatically:
1. Sends the user message to the entry agent (Planner)
2. Intercepts function call requests and executes registered functions
3. Returns function results to the agent
4. Follows handoff instructions to the next agent in the chain
5. Repeats until the terminal agent (Reporter) produces final output

## Mistral API Usage

### Agent Creation
```python
from mistralai import CompletionArgs, ResponseFormat, JSONSchema

agent = client.beta.agents.create(
    model="devstral-2512",
    name="Reviewer",
    instructions="...",
    tools=[...],
    completion_args=CompletionArgs(temperature=0.3)
)
```

### Structured Output (Reporter)
```python
reporter = client.beta.agents.create(
    model="mistral-large-latest",
    name="Reporter",
    instructions="...",
    completion_args=CompletionArgs(
        temperature=0.1,
        response_format=ResponseFormat(
            type="json_schema",
            json_schema=JSONSchema(
                name="ReviewReport",
                schema=ReviewReport.model_json_schema(),
            )
        )
    )
)
```

### Handoff Setup
```python
client.beta.agents.update(agent_id=planner.id, handoffs=[reviewer.id])
client.beta.agents.update(agent_id=reviewer.id, handoffs=[verifier.id])
client.beta.agents.update(agent_id=verifier.id, handoffs=[reporter.id])
```

## Differentiation

What makes MergeGuard stand out from typical chatbot submissions:

1. **Real-world utility** — solves actual PR review bottleneck that every dev team faces
2. **Deep Agents API usage** — uses 7+ Mistral features (Agents, Handoffs, Function Calling, Code Interpreter, Structured Output, Devstral, RunContext)
3. **Verifier agent** — unique validation step that catches false positives, demonstrating agent self-correction
4. **Structured output** — machine-readable JSON report, not just chat text
5. **Dev-tool judges love** — judges are developers who immediately understand the value
