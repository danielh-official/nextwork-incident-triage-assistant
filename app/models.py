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
    log_text: str
    source: str = "unknown"


# Structured output from Claude's analysis
class TriageAnalysis(BaseModel):
    severity: Severity
    category: str
    summary: str
    likely_causes: list[str]
    recommended_actions: list[str]


# Full API response wrapping the analysis
class TriageResponse(BaseModel):
    request_id: str
    timestamp: str
    analysis: TriageAnalysis
