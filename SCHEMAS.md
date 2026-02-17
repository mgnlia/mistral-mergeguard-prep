# MergeGuard — Schema Designs

> **Status:** Pre-hackathon prep (schema design, not production code)

---

## 1. Function Calling Schemas

### 1.1 `get_file_context` — Used by Reviewer Agent

**Purpose:** Retrieve surrounding lines of code from a file to understand the context of a change.

```json
{
  "type": "function",
  "function": {
    "name": "get_file_context",
    "description": "Retrieve lines of code from a file in the repository to understand the context surrounding a change. Returns the specified line range with line numbers.",
    "parameters": {
      "type": "object",
      "properties": {
        "file_path": {
          "type": "string",
          "description": "The relative path to the file in the repository (e.g., 'src/auth/login.py')"
        },
        "start_line": {
          "type": "integer",
          "description": "The starting line number (1-indexed, inclusive)"
        },
        "end_line": {
          "type": "integer",
          "description": "The ending line number (1-indexed, inclusive)"
        },
        "branch": {
          "type": "string",
          "description": "The branch to read from. Use 'head' for the PR branch (new code) or 'base' for the target branch (old code). Defaults to 'head'."
        }
      },
      "required": ["file_path", "start_line", "end_line"]
    }
  }
}
```

**Return format:**
```json
{
  "file_path": "src/auth/login.py",
  "start_line": 10,
  "end_line": 25,
  "branch": "head",
  "content": "10: def authenticate(username, password):\n11:     ...",
  "language": "python",
  "total_lines": 150
}
```

### 1.2 `get_blame` — Used by Reviewer Agent

**Purpose:** Get git blame information for a specific line to understand its history.

```json
{
  "type": "function",
  "function": {
    "name": "get_blame",
    "description": "Get git blame information for a specific line in a file. Returns the author, date, and commit message of the last change to that line.",
    "parameters": {
      "type": "object",
      "properties": {
        "file_path": {
          "type": "string",
          "description": "The relative path to the file in the repository"
        },
        "line_number": {
          "type": "integer",
          "description": "The line number to get blame for (1-indexed)"
        }
      },
      "required": ["file_path", "line_number"]
    }
  }
}
```

**Return format:**
```json
{
  "file_path": "src/auth/login.py",
  "line_number": 15,
  "author": "jane.doe",
  "date": "2026-02-10T14:30:00Z",
  "commit_sha": "abc123f",
  "commit_message": "feat: add login endpoint",
  "original_line": "    query = f\"SELECT * FROM users WHERE name='{username}'\""
}
```

---

## 2. Structured Output Schema — ReviewVerdict

**Purpose:** The Reporter agent's output format. Enforced via `CompletionArgs(response_format=...)`.

### Pydantic Models (for `client.beta.agents.create` with `completion_args`)

```python
# Design reference — will be implemented as Pydantic models during hackathon

class Finding:
    file_path: str                    # e.g., "src/auth/login.py"
    line_start: int                   # Starting line number
    line_end: int | None              # Ending line (None if single line)
    severity: str                     # "critical" | "warning" | "info" | "style"
    category: str                     # "security" | "bug" | "performance" | "quality"
    title: str                        # One-line summary, e.g., "SQL Injection vulnerability"
    description: str                  # Detailed explanation
    suggestion: str | None            # Recommended fix
    verification_status: str          # "verified" | "likely" | "unverified" | "false_positive"
    confidence: float                 # 0.0 to 1.0
    code_snippet: str | None          # The problematic code

class FileReview:
    file_path: str                    # File path
    language: str                     # Detected language
    change_type: str                  # "added" | "modified" | "deleted"
    findings: list[Finding]           # Findings for this file
    positive_notes: list[str]         # Good things about the code

class ReviewStats:
    total_files_reviewed: int
    total_findings: int
    critical_count: int
    warning_count: int
    info_count: int
    style_count: int
    verified_count: int
    false_positive_count: int

class ReviewVerdict:
    verdict: str                      # "approve" | "request_changes" | "comment"
    summary: str                      # 2-3 sentence summary of the review
    confidence: float                 # Overall confidence in the verdict (0.0-1.0)
    files: list[FileReview]           # Per-file reviews
    stats: ReviewStats                # Aggregate statistics
    false_positives: list[Finding]    # Findings marked as false positives
    recommendations: list[str]        # High-level recommendations
    review_duration_ms: int | None    # How long the pipeline took
```

### JSON Schema (equivalent, for reference)

```json
{
  "name": "ReviewVerdict",
  "schema": {
    "type": "object",
    "properties": {
      "verdict": {
        "type": "string",
        "enum": ["approve", "request_changes", "comment"],
        "description": "Overall review decision"
      },
      "summary": {
        "type": "string",
        "description": "2-3 sentence summary of the review findings"
      },
      "confidence": {
        "type": "number",
        "minimum": 0.0,
        "maximum": 1.0,
        "description": "Overall confidence in the verdict"
      },
      "files": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "file_path": { "type": "string" },
            "language": { "type": "string" },
            "change_type": {
              "type": "string",
              "enum": ["added", "modified", "deleted"]
            },
            "findings": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "file_path": { "type": "string" },
                  "line_start": { "type": "integer" },
                  "line_end": { "type": ["integer", "null"] },
                  "severity": {
                    "type": "string",
                    "enum": ["critical", "warning", "info", "style"]
                  },
                  "category": {
                    "type": "string",
                    "enum": ["security", "bug", "performance", "quality"]
                  },
                  "title": { "type": "string" },
                  "description": { "type": "string" },
                  "suggestion": { "type": ["string", "null"] },
                  "verification_status": {
                    "type": "string",
                    "enum": ["verified", "likely", "unverified", "false_positive"]
                  },
                  "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0
                  },
                  "code_snippet": { "type": ["string", "null"] }
                },
                "required": ["file_path", "line_start", "severity", "category", "title", "description", "verification_status", "confidence"]
              }
            },
            "positive_notes": {
              "type": "array",
              "items": { "type": "string" }
            }
          },
          "required": ["file_path", "language", "change_type", "findings", "positive_notes"]
        }
      },
      "stats": {
        "type": "object",
        "properties": {
          "total_files_reviewed": { "type": "integer" },
          "total_findings": { "type": "integer" },
          "critical_count": { "type": "integer" },
          "warning_count": { "type": "integer" },
          "info_count": { "type": "integer" },
          "style_count": { "type": "integer" },
          "verified_count": { "type": "integer" },
          "false_positive_count": { "type": "integer" }
        },
        "required": ["total_files_reviewed", "total_findings", "critical_count", "warning_count", "info_count", "style_count", "verified_count", "false_positive_count"]
      },
      "false_positives": {
        "type": "array",
        "items": { "$ref": "#/properties/files/items/properties/findings/items" }
      },
      "recommendations": {
        "type": "array",
        "items": { "type": "string" }
      },
      "review_duration_ms": { "type": ["integer", "null"] }
    },
    "required": ["verdict", "summary", "confidence", "files", "stats", "false_positives", "recommendations"]
  }
}
```

---

## 3. API Endpoint Schemas

### POST /api/review — Submit PR for review

**Request:**
```json
{
  "diff_text": "unified diff string (optional if github_url provided)",
  "github_url": "https://github.com/owner/repo/pull/123 (optional if diff_text provided)",
  "options": {
    "focus_areas": ["security", "bugs"],
    "severity_threshold": "info",
    "include_style": true
  }
}
```

**Response:**
```json
{
  "review_id": "uuid",
  "status": "queued",
  "created_at": "2026-02-28T10:00:00Z",
  "stream_url": "/api/review/{review_id}/stream"
}
```

### GET /api/review/{id}/stream — SSE Pipeline Progress

**Event types:**
```
event: pipeline.started
data: {"review_id": "uuid", "agent": "planner", "timestamp": "..."}

event: agent.started
data: {"agent": "planner", "model": "mistral-large-latest", "timestamp": "..."}

event: tool.called
data: {"agent": "planner", "tool": "web_search", "query": "...", "timestamp": "..."}

event: agent.handoff
data: {"from": "planner", "to": "reviewer", "chunks_count": 5, "timestamp": "..."}

event: tool.called
data: {"agent": "reviewer", "tool": "get_file_context", "args": {...}, "timestamp": "..."}

event: finding.detected
data: {"agent": "reviewer", "severity": "critical", "title": "SQL Injection", "timestamp": "..."}

event: agent.handoff
data: {"from": "reviewer", "to": "verifier", "findings_count": 7, "timestamp": "..."}

event: tool.called
data: {"agent": "verifier", "tool": "code_interpreter", "action": "lint_check", "timestamp": "..."}

event: finding.verified
data: {"title": "SQL Injection", "status": "verified", "confidence": 0.95, "timestamp": "..."}

event: agent.handoff
data: {"from": "verifier", "to": "reporter", "verified_count": 5, "timestamp": "..."}

event: pipeline.completed
data: {"review_id": "uuid", "verdict": "request_changes", "duration_ms": 45000, "timestamp": "..."}
```

### GET /api/review/{id} — Get Final Results

**Response:** Full `ReviewVerdict` JSON (see above).

---

## 4. Frontend State Types

```typescript
// Design reference — TypeScript types for frontend

type PipelineStage = 'idle' | 'planner' | 'reviewer' | 'verifier' | 'reporter' | 'complete' | 'error';

interface PipelineEvent {
  type: string;
  data: Record<string, unknown>;
  timestamp: string;
}

interface ReviewState {
  reviewId: string | null;
  stage: PipelineStage;
  events: PipelineEvent[];
  activeAgent: string | null;
  activeTool: string | null;
  findingsPreview: FindingPreview[];
  verdict: ReviewVerdict | null;
  error: string | null;
}

interface FindingPreview {
  title: string;
  severity: 'critical' | 'warning' | 'info' | 'style';
  verified: boolean;
}
```
