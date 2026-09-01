from enum import Enum

from pydantic import BaseModel, Field


# Constrain severity to exactly five levels
class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


# Input model for the triage request
class TriageRequest(BaseModel):
    log_text: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="The error log or incident text to analyze",
    )
    source: str = Field(
        default="unknown", description="Source system or application name"
    )

# Structured output from Claude's analysis
class TriageAnalysis(BaseModel):
    severity: Severity
    category: str
    summary: str
    likely_causes: list[str]
    recommended_actions: list[str]
    escalated: bool = False
    escalation_reason: str | None = None


# Full API response wrapping the analysis
class TriageResponse(BaseModel):
    request_id: str
    timestamp: str
    analysis: TriageAnalysis
