from anthropic import Anthropic
from fastapi import FastAPI
from pydantic import BaseModel

from app.config import Settings

# Load settings from .env via pydantic-settings
settings = Settings()

# Create the FastAPI application
app = FastAPI(title="AI Incident Triage Assistant", version="1.0.0")


# Define the expected shape of incoming triage requests
class TriageRequest(BaseModel):
    log_text: str
    source: str = "unknown"

@app.post("/triage")
async def triage_incident(payload: TriageRequest):
    # Create an Anthropic client for this request
    client = Anthropic(api_key=settings.anthropic_api_key)

    # Send the log to Claude with a basic analysis prompt
    message = client.messages.create(
        model=settings.model_name,
        max_tokens=settings.max_tokens,
        messages=[
            {
                "role": "user",
                "content": f"Analyze this error log and provide severity, category, summary, likely causes, and recommended actions:\n\nSource: {payload.source}\n\nLog:\n{payload.log_text}",
            }
        ],
    )

    # Return Claude's raw text response wrapped in JSON
    return {"analysis": message.content[0].text}
