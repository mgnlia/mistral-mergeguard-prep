# MergeGuard — Architecture

## Overview

MergeGuard is a **multi-agent code review pipeline** built on the Mistral Agents API. Four specialized agents collaborate through Mistral's native Handoff mechanism to produce a comprehensive, structured code review for any pull request.

The pipeline is fully autonomous once triggered: no external orchestrator, no polling loops, no manual intervention. Mistral's Agents API manages the entire conversation flow through handoffs.

---

## Agent Pipeline

### 1. Planner Agent

**Role:** Receives the PR input and creates a structured review plan.

**Inputs:**
- PR URL (via CLI) or local diff path

**Function Tools:**
- `fetch_pr_diff` — Calls the GitHub API to retrieve the unified diff for a pull request
- `list_changed_files` — Extracts the list of changed files with change types (added, modified, deleted) and line counts

**Behavior:**
1. Receives the PR URL or diff content from the user message
2. Calls `fetch_pr_diff` to retrieve the raw diff (if PR URL provided)
3. Calls `list_changed_files` to get a structured file list
4. Analyzes the scope of changes: which files, what kind of changes, estimated complexity
5. Creates a prioritized review task list — ordering files by risk (e.g., core logic > tests > config)
6. Hands off to the **Reviewer Agent** with the diff content and task list

**Model:** `devstral-small-latest`

---

### 2. Reviewer Agent

**Role:** Performs detailed code review on each changed file.

**Inputs (from Planner handoff):**
- PR diff content
- Prioritized review task list

**Function Tools:**
- `read_file` — Reads the full content of a file from the repository (for context beyond the diff)
- `check_style` — Runs basic style/lint checks on a code snippet and returns violations

**Behavior:**
1. Iterates through the task list from the Planner
2. For each file/change:
   - Reads the full file content via `read_file` for surrounding context
   - Analyzes the diff hunks for correctness, style, security, performance
   - Calls `check_style` on modified code sections
   - Produces review comments with file path, line number, severity, message, and suggested fix
3. Compiles all review comments into a structured list
4. Hands off to the **Verifier Agent** with the review comments and relevant code snippets

**Model:** `devstral-small-latest`

---

### 3. Verifier Agent

**Role:** Validates the Reviewer's suggestions by executing code.

**Inputs (from Reviewer handoff):**
- Review comments with suggested fixes
- Relevant code snippets

**Tools:**
- `code_interpreter` (Mistral built-in) — Executes Python code in a sandboxed environment

**Behavior:**
1. Receives the review comments and code snippets from the Reviewer
2. For each actionable suggestion:
   - Writes a small test or lint check in the code interpreter
   - Runs the original code snippet to reproduce the issue (if applicable)
   - Runs the suggested fix to verify it resolves the issue
   - Marks the suggestion as `verified`, `unverified`, or `invalid`
3. Filters out invalid suggestions to reduce noise
4. Hands off to the **Reporter Agent** with verified review comments

**Model:** `devstral-small-latest`

---

### 4. Reporter Agent

**Role:** Aggregates all findings into the final structured review report.

**Inputs (from Verifier handoff):**
- Verified review comments

**Output Format:**
- Uses `response_format` with a JSON schema (see `schemas.py`) to guarantee structured output

**Behavior:**
1. Receives the verified review comments from the Verifier
2. Aggregates comments by file and severity
3. Computes an overall quality score (0–100) based on severity distribution
4. Determines a recommendation: `approve` or `request_changes`
5. Writes a human-readable summary paragraph
6. Returns the final `ReviewReport` as structured JSON

**Model:** `devstral-small-latest`

**Completion Args:**
```python
response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "ReviewReport",
        "schema": ReviewReport.model_json_schema()
    }
}
```

---

## Handoff Chain

```
User Message (PR URL)
        │
        ▼
   ┌─────────┐
   │ Planner  │──── fetch_pr_diff(), list_changed_files()
   └────┬────┘
        │ handoff (diff + task list)
        ▼
   ┌──────────┐
   │ Reviewer  │──── read_file(), check_style()
   └────┬─────┘
        │ handoff (review comments + code)
        ▼
   ┌──────────┐
   │ Verifier  │──── code_interpreter
   └────┬─────┘
        │ handoff (verified comments)
        ▼
   ┌──────────┐
   │ Reporter  │──── response_format (JSON schema)
   └────┬─────┘
        │
        ▼
   ReviewReport (JSON)
```

Handoffs are configured via `client.beta.agents.update()` after all agents are created:

```python
client.beta.agents.update(planner_id,   handoffs=[reviewer_id])
client.beta.agents.update(reviewer_id,  handoffs=[verifier_id])
client.beta.agents.update(verifier_id,  handoffs=[reporter_id])
# Reporter has no handoffs — it produces the final output
```

---

## Mistral Features Used

### Agents API
All four agents are created via `client.beta.agents.create()` with distinct system prompts, tools, and configurations. Each agent is a persistent, stateful entity on the Mistral platform.

### Handoffs
The core orchestration mechanism. Each agent's `handoffs` field points to the next agent in the chain. When an agent finishes its work, it hands off control (and conversation context) to the next agent automatically.

### Function Calling
Custom function tools with JSON Schema definitions:
- `fetch_pr_diff` — GitHub API integration
- `read_file` — Repository file access
- `list_changed_files` — PR file enumeration
- `check_style` — Code style validation

### Code Interpreter
The Verifier agent uses Mistral's built-in `code_interpreter` tool to execute Python code in a sandboxed environment — validating suggestions, running linters, and testing code snippets.

### Structured Output
The Reporter agent uses `response_format` with a JSON schema derived from Pydantic models to guarantee the final output conforms to the `ReviewReport` schema.

### Devstral Model
All agents use `devstral-small-latest` — Mistral's code-optimized model — for superior performance on code understanding, review, and generation tasks.

---

## Data Flow

| Stage | Input | Output | Tools |
|---|---|---|---|
| **Planner** | PR URL or diff path | Diff content + prioritized task list | `fetch_pr_diff`, `list_changed_files` |
| **Reviewer** | Diff + task list | Review comments (file, line, severity, message, suggestion) | `read_file`, `check_style` |
| **Verifier** | Review comments + code | Verified review comments (with verification status) | `code_interpreter` |
| **Reporter** | Verified comments | `ReviewReport` JSON (summary, comments, score, recommendation) | `response_format` |
