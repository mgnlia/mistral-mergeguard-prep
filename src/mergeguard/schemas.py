"""Pydantic models for MergeGuard structured output.

These schemas define the structured JSON output format used by the Reporter agent
via Mistral's response_format feature.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Review comment severity levels."""

    CRITICAL = "critical"
    WARNING = "warning"
    SUGGESTION = "suggestion"
    NITPICK = "nitpick"


class Category(str, Enum):
    """Review comment categories."""

    CORRECTNESS = "correctness"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    STYLE = "style"


class Recommendation(str, Enum):
    """Final review recommendation."""

    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"


class ReviewComment(BaseModel):
    """A single review comment on a specific file/line."""

    file: str = Field(description="File path relative to repo root")
    line: Optional[int] = Field(
        default=None, description="Line number in the file (null if file-level comment)"
    )
    severity: Severity = Field(description="Issue severity level")
    category: Category = Field(description="Issue category")
    message: str = Field(description="Clear description of the issue found")
    suggestion: Optional[str] = Field(
        default=None, description="Concrete code fix or improvement suggestion"
    )
    verified: bool = Field(
        default=False,
        description="Whether the Verifier agent confirmed this issue via code execution",
    )


class ReviewReport(BaseModel):
    """Final structured review report produced by the Reporter agent."""

    summary: str = Field(
        description="Human-readable 2-4 sentence summary of the review"
    )
    comments: list[ReviewComment] = Field(
        default_factory=list, description="All review comments, ordered by severity"
    )
    overall_score: int = Field(
        ge=0,
        le=100,
        description="Overall quality score from 0 (worst) to 100 (best)",
    )
    recommendation: Recommendation = Field(
        description="Final recommendation: approve or request_changes"
    )
    files_reviewed: int = Field(
        ge=0, description="Total number of files reviewed"
    )
    total_issues: int = Field(
        ge=0, description="Total number of issues found across all files"
    )
