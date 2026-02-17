"""Pydantic models for MergeGuard structured output."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Severity(str, Enum):
    critical = "critical"
    warning = "warning"
    suggestion = "suggestion"
    nitpick = "nitpick"


class VerificationStatus(str, Enum):
    confirmed = "confirmed"
    modified = "modified"
    rejected = "rejected"
    unverified = "unverified"


class ReviewComment(BaseModel):
    """A single review comment on a specific file and line."""

    file: str = Field(description="File path relative to repo root")
    line: int = Field(description="Line number in the file")
    severity: Severity = Field(description="Issue severity level")
    message: str = Field(description="Description of the issue")
    suggestion: str = Field(default="", description="Recommended fix or improvement")
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.unverified,
        description="Whether the Verifier confirmed this comment",
    )


class ReviewStats(BaseModel):
    """Aggregate statistics for the review."""

    files_reviewed: int = 0
    total_comments: int = 0
    critical: int = 0
    warnings: int = 0
    suggestions: int = 0
    nitpicks: int = 0


class ReviewReport(BaseModel):
    """Final structured review report produced by the Reporter agent."""

    summary: str = Field(description="2-3 sentence overview of the review")
    comments: list[ReviewComment] = Field(default_factory=list)
    overall_score: int = Field(
        ge=0, le=100, description="Quality score from 0 (worst) to 100 (best)"
    )
    recommendation: Literal["approve", "request_changes"] = Field(
        description="Final recommendation"
    )
    stats: ReviewStats = Field(default_factory=ReviewStats)

    def to_json_schema(self) -> dict:
        """Return JSON schema for use with Mistral response_format."""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "ReviewReport",
                "schema": self.model_json_schema(),
            },
        }
