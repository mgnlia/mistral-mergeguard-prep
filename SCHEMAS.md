# MergeGuard — Schema Designs

> **Pre-hackathon design only — not production code**

---

## 1. Function Calling Schemas

### `get_file_context`

Fetches file content from the PR's head branch via GitHub API.

```json
{
  "type": "function",
  "function": {
    "name": "get_file_context",
    "description": "Fetch the full content of a file or a specific line range from the PR's head branch. Use this to get surrounding context for code changes.",
    "parameters": {
      "type": "object",
      "properties": {
        "file_path": {
          "type": "string",
          "description": "Path to the file in the repository (e.g., 'src/auth/login.py')"
        },
        "start_line": {
          "type": "integer",
          "description": "Start line number (1-indexed). If omitted, returns full file."
        },
        "end_line": {
          "type": "integer",
          "description": "End line number (1-indexed). If omitted, returns from start_line to EOF."
        }
      },
      "required": ["file_path"]
    }
  }
}
```

**Return format:**
```json
{
  "file_path": "src/auth/login.py",
  "language": "python",
  "start_line": 10,
  "end_line": 30,
  "content": "def login(username, password):\n    ...",
  "total_lines": 150
}
```

---

### `get_blame`

Gets git blame info to understand who changed what and when.

```json
{
  "type": "function",
  "function": {
    "name": "get_blame",
    "description": "Get git blame information for a file to understand recent change history and authorship.",
    "parameters": {
      "type": "object",
      "properties": {
        "file_path": {
          "type": "string",
          "description": "Path to the file in the repository"
        },
        "start_line": {
          "type": "integer",
          "description": "Start line for blame range (1-indexed)"
        },
        "end_line": {
          "type": "integer",
          "description": "End line for blame range (1-indexed)"
        }
      },
      "required": ["file_path"]
    }
  }
}
```

**Return format:**
```json
{
  "file_path": "src/auth/login.py",
  "blame_entries": [
    {
      "line": 15,
      "commit_sha": "abc1234",
      "author": "dev@example.com",
      "date": "2026-02-20T10:30:00Z",
      "content": "    query = f\"SELECT * FROM users WHERE name='{username}'\""
    }
  ]
}
```

---

### `get_pr_comments`

Gets existing review comments to avoid duplicate feedback.

```json
{
  "type": "function",
  "function": {
    "name": "get_pr_comments",
    "description": "Get existing review comments on the PR to avoid giving duplicate feedback.",
    "parameters": {
      "type": "object",
      "properties": {
        "file_path": {
          "type": "string",
          "description": "Filter comments by file path (optional)"
        }
      },
      "required": []
    }
  }
}
```

**Return format:**
```json
{
  "comments": [
    {
      "id": 1,
      "file_path": "src/auth/login.py",
      "line": 15,
      "body": "This looks like a SQL injection risk",
      "author": "reviewer1",
      "created_at": "2026-02-28T12:00:00Z"
    }
  ]
}
```

---

## 2. Reporter Structured Output Schema (ReviewVerdict)

This is the JSON schema for the Reporter's structured output using `completion_args.response_format`.

### Pydantic Model (for SDK)

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class Category(str, Enum):
    SECURITY = "security"
    BUG = "bug"
    PERFORMANCE = "performance"
    STYLE = "style"
    TEST_COVERAGE = "test_coverage"
    DOCUMENTATION = "documentation"

class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    SKIPPED = "skipped"

class Verdict(str, Enum):
    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    COMMENT = "COMMENT"

class Finding(BaseModel):
    id: str = Field(description="Unique finding identifier, e.g., F001")
    severity: Severity
    category: Category
    file_path: str
    start_line: int
    end_line: int
    title: str = Field(description="Short title of the finding")
    description: str = Field(description="Detailed description of the issue")
    code_snippet: Optional[str] = Field(default=None, description="Relevant code snippet")
    suggested_fix: Optional[str] = Field(default=None, description="Suggested code fix")
    verification: VerificationStatus
    verification_evidence: Optional[str] = Field(default=None, description="Output from code interpreter verification")

class CategorySummary(BaseModel):
    category: Category
    count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int

class ReviewVerdict(BaseModel):
    verdict: Verdict = Field(description="Overall review verdict")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    summary: str = Field(description="Human-readable summary, 2-3 sentences")
    total_findings: int
    findings: List[Finding]
    category_summary: List[CategorySummary]
    files_reviewed: List[str]
    review_duration_seconds: Optional[float] = None
    agents_used: List[str] = Field(default=["planner", "reviewer", "verifier", "reporter"])
```

### JSON Schema (for API)

```json
{
  "name": "review_verdict",
  "schema": {
    "type": "object",
    "properties": {
      "verdict": {
        "type": "string",
        "enum": ["APPROVE", "REQUEST_CHANGES", "COMMENT"]
      },
      "confidence": {
        "type": "number",
        "minimum": 0.0,
        "maximum": 1.0
      },
      "summary": {
        "type": "string"
      },
      "total_findings": {
        "type": "integer"
      },
      "findings": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": { "type": "string" },
            "severity": {
              "type": "string",
              "enum": ["critical", "high", "medium", "low", "info"]
            },
            "category": {
              "type": "string",
              "enum": ["security", "bug", "performance", "style", "test_coverage", "documentation"]
            },
            "file_path": { "type": "string" },
            "start_line": { "type": "integer" },
            "end_line": { "type": "integer" },
            "title": { "type": "string" },
            "description": { "type": "string" },
            "code_snippet": { "type": "string" },
            "suggested_fix": { "type": "string" },
            "verification": {
              "type": "string",
              "enum": ["verified", "unverified", "skipped"]
            },
            "verification_evidence": { "type": "string" }
          },
          "required": ["id", "severity", "category", "file_path", "start_line", "end_line", "title", "description", "verification"]
        }
      },
      "category_summary": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "category": { "type": "string" },
            "count": { "type": "integer" },
            "critical_count": { "type": "integer" },
            "high_count": { "type": "integer" },
            "medium_count": { "type": "integer" },
            "low_count": { "type": "integer" },
            "info_count": { "type": "integer" }
          },
          "required": ["category", "count", "critical_count", "high_count", "medium_count", "low_count", "info_count"]
        }
      },
      "files_reviewed": {
        "type": "array",
        "items": { "type": "string" }
      },
      "review_duration_seconds": { "type": "number" },
      "agents_used": {
        "type": "array",
        "items": { "type": "string" }
      }
    },
    "required": ["verdict", "confidence", "summary", "total_findings", "findings", "category_summary", "files_reviewed", "agents_used"]
  }
}
```

---

## 3. Backend API Schemas

### POST /api/review — Request

```json
{
  "pr_url": "https://github.com/owner/repo/pull/123",
  "options": {
    "focus_areas": ["security", "bugs"],
    "skip_style": false,
    "max_files": 20
  }
}
```

### POST /api/review — Response

```json
{
  "review_id": "rev_abc123",
  "status": "in_progress",
  "stream_url": "/api/review/rev_abc123/stream"
}
```

### GET /api/review/:id/stream — SSE Events

```
event: agent_start
data: {"agent": "planner", "timestamp": "2026-02-28T12:00:00Z"}

event: agent_progress
data: {"agent": "planner", "message": "Analyzing 5 changed files..."}

event: handoff
data: {"from": "planner", "to": "reviewer", "timestamp": "2026-02-28T12:00:15Z"}

event: function_call
data: {"agent": "reviewer", "function": "get_file_context", "args": {"file_path": "src/auth/login.py"}}

event: finding
data: {"id": "F001", "severity": "critical", "category": "security", "title": "SQL Injection in login()"}

event: agent_start
data: {"agent": "verifier", "timestamp": "2026-02-28T12:01:00Z"}

event: verification
data: {"finding_id": "F001", "status": "verified", "evidence": "..."}

event: complete
data: <full ReviewVerdict JSON>
```

### GET /api/review/:id — Response

```json
{
  "review_id": "rev_abc123",
  "status": "complete",
  "verdict": { ... },  // Full ReviewVerdict
  "pipeline": {
    "started_at": "2026-02-28T12:00:00Z",
    "completed_at": "2026-02-28T12:02:30Z",
    "agents": [
      {"name": "planner", "duration_ms": 15000, "status": "complete"},
      {"name": "reviewer", "duration_ms": 45000, "status": "complete", "function_calls": 3},
      {"name": "verifier", "duration_ms": 60000, "status": "complete", "code_executions": 4},
      {"name": "reporter", "duration_ms": 10000, "status": "complete"}
    ]
  }
}
```
