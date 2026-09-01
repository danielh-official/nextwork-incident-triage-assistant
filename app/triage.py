import logging

from anthropic import Anthropic

from app.config import Settings
from app.models import Severity, TriageAnalysis

logger = logging.getLogger("triage")

# Tell Claude exactly what JSON shape to return
SYSTEM_PROMPT = """You are an expert incident response engineer. Analyze the provided application log or error message and return a JSON object with exactly these fields:

{
  "severity": "<critical|high|medium|low|info>",
  "category": "<short category like 'memory', 'network', 'authentication', 'database', 'configuration', 'application'>",
  "summary": "<one-sentence summary of the incident>",
  "likely_causes": ["<cause 1>", "<cause 2>"],
  "recommended_actions": ["<action 1>", "<action 2>"]
}

Rules:
- severity must be one of: critical, high, medium, low, info
- Return ONLY the JSON object, no markdown, no code fences, no explanation
- likely_causes and recommended_actions should each have 1-3 items"""

# Deterministic rules that override AI severity for known critical patterns
ESCALATION_RULES = [
    {
        "patterns": ["OOM", "OutOfMemoryError", "out of memory", "Cannot allocate memory"],
        "severity": "critical",
        "reason": "Memory exhaustion detected",
    },
    {
        "patterns": ["segfault", "SIGSEGV", "segmentation fault", "core dumped"],
        "severity": "critical",
        "reason": "Process crash detected",
    },
    {
        "patterns": ["FATAL", "panic", "unrecoverable"],
        "severity": "critical",
        "reason": "Fatal error keyword detected",
    },
    {
        "patterns": ["unauthorized", "403 Forbidden", "401 Unauthorized", "authentication failed"],
        "severity": "high",
        "reason": "Authentication or authorization failure detected",
    },
]

# Ordered lowest to highest for severity comparison
SEVERITY_ORDER = ["info", "low", "medium", "high", "critical"]

def check_escalation_rules(log_text: str) -> dict | None:
    # Convert log to lowercase for case-insensitive matching
    log_lower = log_text.lower()
    for rule in ESCALATION_RULES:
        for pattern in rule["patterns"]:
            if pattern.lower() in log_lower:
                return {"severity": rule["severity"], "reason": rule["reason"]}
    return None

def _strip_fences(text: str) -> str:
    # ponytail: Claude sometimes wraps the JSON in ```json fences despite the prompt.
    # Swap for a tool/structured-output call if the shape drifts further.
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1].removeprefix("json").strip()
    return text


def analyze_log(log_text: str, source: str, settings: Settings) -> TriageAnalysis:
    # Create an Anthropic client with the API key and timeout
    client = Anthropic(
        api_key=settings.anthropic_api_key,
        timeout=settings.claude_timeout,
    )

    # Send the log to Claude with the structured system prompt
    message = client.messages.create(
        model=settings.model_name,
        max_tokens=settings.max_tokens,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Source: {source}\n\nLog:\n{log_text}",
            }
        ],
    )

    response_text = message.content[0].text
    logger.info(
        "Claude response received", extra={"response_length": len(response_text)}
    )

    # Validate Claude's JSON against our Pydantic model
    analysis = TriageAnalysis.model_validate_json(response_text)

    # Check if deterministic rules should override the AI severity
    escalation = check_escalation_rules(log_text)
    if escalation:
        escalation_severity = Severity(escalation["severity"])
        # Only escalate UP, never lower the AI's rating
        if SEVERITY_ORDER.index(escalation_severity.value) > SEVERITY_ORDER.index(
            analysis.severity.value
        ):
            original = analysis.severity.value
            analysis.severity = escalation_severity
            analysis.escalated = True
            analysis.escalation_reason = escalation["reason"]
            logger.info(
                f"Escalation applied: {original} -> {escalation_severity.value}",
                extra={
                    "original_severity": original,
                    "escalated_severity": escalation_severity.value,
                },
            )

    return analysis


if __name__ == "__main__":
    assert _strip_fences('{"a": 1}') == '{"a": 1}'
    assert _strip_fences('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert _strip_fences('```\n{"a": 1}\n```') == '{"a": 1}'
    print("ok")
