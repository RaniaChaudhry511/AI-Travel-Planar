import asyncio
import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from openai import OpenAIError, RateLimitError
from pydantic import BaseModel, Field

from agents import Runner, SQLiteSession
from agents.exceptions import AgentsException
from export_pdf import export_itinerary_pdf


logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
DATA_DIR = Path("/tmp") if os.getenv("VERCEL") == "1" else BASE_DIR
MOCK_MODE = os.getenv("MOCK_MODE", "").strip().lower()
MAX_ATTEMPTS = 3
RETRY_WAIT_SECONDS = 5
RUN_TIMEOUT_SECONDS = 60
QUOTA_REPLY = "Gemini ki aaj ki quota khatam ho gayi hai. Meherbani karke kal dobara try karein."
BUSY_REPLY = "Gemini abhi busy hai, thodi der baad dobara try karein."

app = FastAPI(title="AI Travel Planner")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)
    session_id: str = Field(min_length=1, max_length=128)


class ExportRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000)


def _error_details(exc: Exception) -> str:
    response = getattr(exc, "response", None)
    return " ".join(
        str(value)
        for value in (exc, getattr(response, "text", None), getattr(exc, "body", None))
        if value is not None
    ).lower()


def _status_code(exc: Exception) -> int | None:
    response = getattr(exc, "response", None)
    status_code = getattr(exc, "status_code", None)
    if status_code is None and response is not None:
        status_code = getattr(response, "status_code", None)
    return status_code


def _is_quota_error(exc: Exception) -> bool:
    details = _error_details(exc)
    return (
        isinstance(exc, RateLimitError)
        or _status_code(exc) == 429
        or "resource_exhausted" in details
        or "quota" in details
    )


def _is_retryable(exc: Exception) -> bool:
    if _is_quota_error(exc):
        return False
    return isinstance(exc, TimeoutError) or _status_code(exc) in (500, 503)


def _log_exception(exc: Exception, attempt: int) -> None:
    logger.exception(
        "Travel planning request failed (attempt %s/%s): %s: %s",
        attempt,
        MAX_ATTEMPTS,
        type(exc).__name__,
        exc,
    )
    response = getattr(exc, "response", None)
    if response is not None:
        response_text = getattr(response, "text", None)
        if response_text is not None:
            logger.error("Gemini response text: %s", response_text)

    body = getattr(exc, "body", None)
    if body is not None:
        logger.error("Gemini exception body: %s", body)


def _error_response(error: str, reply: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": error, "reply": reply},
    )


def _mock_itinerary(message: str) -> str:
    return f"""## Your sample travel plan

*This is a mock response for testing; no AI request was made.*

### Trip idea
You said: **{message}**

| Day | Morning | Afternoon | Evening |
|---|---|---|---|
| 1 | Arrive and settle in | Explore a nearby landmark | Local dinner and rest |
| 2 | Scenic walk and breakfast | Visit a museum or beach | Sunset viewpoint |
| 3 | Slow morning | Pick up souvenirs | Head home |

### Budget guide
- Stay: choose a comfortable option near transit
- Food: mix local favorites with casual cafes
- Transport: use public transit where practical
- Keep a small emergency fund for unexpected costs

### Before you go
Check current opening hours, transport schedules, weather, and travel documents.
"""


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/favicon.ico")
async def favicon() -> FileResponse:
    return FileResponse(WEB_DIR / "favicon.svg", media_type="image/svg+xml")


@app.post("/chat")
async def chat(request: ChatRequest) -> JSONResponse:
    if MOCK_MODE == "quota":
        return _error_response("quota", QUOTA_REPLY, 429)
    if MOCK_MODE == "busy":
        return _error_response("busy", BUSY_REPLY, 503)
    if MOCK_MODE in {"1", "true", "yes"}:
        return JSONResponse(content={"reply": _mock_itinerary(request.message)})

    from agent import agent

    session = SQLiteSession(request.session_id, str(DATA_DIR / "travel_history.db"))
    for attempt in range(MAX_ATTEMPTS):
        try:
            result = await asyncio.wait_for(
                Runner.run(agent, request.message, session=session),
                timeout=RUN_TIMEOUT_SECONDS,
            )
            return JSONResponse(content={"reply": result.final_output})
        except (AgentsException, OpenAIError, TimeoutError) as exc:
            _log_exception(exc, attempt + 1)
            if _is_quota_error(exc):
                return _error_response("quota", QUOTA_REPLY, 429)
            if _is_retryable(exc):
                if attempt < MAX_ATTEMPTS - 1:
                    await asyncio.sleep(RETRY_WAIT_SECONDS)
                    continue
                return _error_response("busy", BUSY_REPLY, 503)
            return _error_response(
                "unavailable",
                "I couldn't complete that plan right now. Please try again.",
                503,
            )

    return _error_response("busy", BUSY_REPLY, 503)


@app.post("/export-pdf")
async def export_pdf(request: ExportRequest) -> Response:
    try:
        pdf = export_itinerary_pdf(request.text)
    except Exception as exc:
        logger.exception("Could not export itinerary PDF")
        raise HTTPException(status_code=500, detail="Could not create the PDF.") from exc

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="travel-plan.pdf"'},
    )
