import json
import logging
import sys
import uuid
from datetime import datetime, timezone

import anthropic
from fastapi import FastAPI, HTTPException, Request
from pydantic import ValidationError

from app.config import Settings
from app.models import TriageRequest, TriageResponse
from app.triage import analyze_log

settings = Settings()

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        for key in ("response_length", "source", "severity"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)
        return json.dumps(log_entry)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logging.root.handlers = [handler]
logging.root.setLevel(settings.log_level)

logger = logging.getLogger("app")

app = FastAPI(
    title="AI Incident Triage Assistant",
    version="1.0.0",
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    logger.info(
        f"Incoming {request.method} {request.url.path}",
        extra={"request_id": request_id},
    )
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.post("/triage", response_model=TriageResponse)
async def triage_incident(request: Request, payload: TriageRequest):
    request_id = request.state.request_id
    # Call the structured triage function
    analysis = analyze_log(
        log_text=payload.log_text,
        source=payload.source,
        settings=settings,
    )
    return TriageResponse(
        request_id=request_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        analysis=analysis,
    )
