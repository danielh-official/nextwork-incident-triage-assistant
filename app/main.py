from datetime import datetime, timezone

from fastapi import FastAPI, Request

from app.config import Settings
from app.models import TriageRequest, TriageResponse
from app.triage import analyze_log

settings = Settings()

app = FastAPI(title="AI Incident Triage Assistant", version="1.0.0")


@app.post("/triage", response_model=TriageResponse)
async def triage_incident(payload: TriageRequest):
    # Call the structured triage function
    analysis = analyze_log(
        log_text=payload.log_text,
        source=payload.source,
        settings=settings,
    )
    return TriageResponse(
        request_id="placeholder",
        timestamp=datetime.now(timezone.utc).isoformat(),
        analysis=analysis,
    )
