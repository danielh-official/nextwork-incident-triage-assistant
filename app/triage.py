import logging

from anthropic import Anthropic

from app.config import Settings
from app.models import TriageAnalysis

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
    return analysis
