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

- **Model:** `devstral-latest` (code-specialized)
- **Tools:** `read_file` (function), `check_style` (function)
- **Input:** Review plan from Planner
- **Output:** List of review comments (file, line, severity, message, suggestion)
- **Handoff:** → Verifier Agent (passes review comments)

### 3. Verifier Agent

**Role:** Validate the Reviewer's suggestions by running code analysis.

- **Model:** `devstral-latest`
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
- **Output format:** Structured JSON via `response_format` with JSON schema
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

## Mistral API Usage

### Agent Creation
```python
agent = client.beta.agents.create(
    model="mistral-large-latest",
    name="Planner",
    instructions="...",  # loaded from agents/planner.md
    tools=[{
        "type": "function",
        "function": {
            "name": "fetch_pr_diff",
            "description": "Fetch the diff for a GitHub PR",
            "parameters": { ... }
        }
    }],
    completion_args={"temperature": 0.3}
)
```

### Handoff Setup
```python
# After creating all agents:
client.beta.agents.update(
    agent_id=planner.id,
    handoffs=[reviewer.id]
)
client.beta.agents.update(
    agent_id=reviewer.id,
    handoffs=[verifier.id]
)
client.beta.agents.update(
    agent_id=verifier.id,
    handoffs=[reporter.id]
)
```

### Structured Output (Reporter)
```python
reporter = client.beta.agents.create(
    model="mistral-large-latest",
    name="Reporter",
    instructions="...",
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "ReviewReport",
            "schema": { ... }  # from schemas.py
        }
    }
)
```

## Differentiation

What makes MergeGuard stand out from typical chatbot submissions:

1. **Real-world utility** — solves actual PR review bottleneck that every dev team faces
2. **Deep Agents API usage** — uses 6+ Mistral features (Agents, Handoffs, Function Calling, Code Interpreter, Structured Output, Devstral)
3. **Verifier agent** — unique validation step that catches false positives, demonstrating agent self-correction
4. **Structured output** — machine-readable JSON report, not just chat text
5. **Dev-tool judges love** — judges are developers who immediately understand the value
