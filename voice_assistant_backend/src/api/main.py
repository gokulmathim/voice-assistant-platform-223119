import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware


def _csv_env(name: str, default: str) -> List[str]:
    raw = os.getenv(name, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


def _build_database_url_from_env() -> Optional[str]:
    """
    Builds a SQLAlchemy-style DATABASE_URL from the database container env vars if present.

    Expected env vars (from workspace DB container):
    - POSTGRES_URL (may already be a full URL)
    - POSTGRES_USER
    - POSTGRES_PASSWORD
    - POSTGRES_DB
    - POSTGRES_PORT

    We also support DATABASE_URL if already provided.
    """
    direct = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if direct:
        # Allow either:
        # - postgresql://user:pass@host:port/db
        # - postgresql://host:port/db (credentials could be separate)
        return direct

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    port = os.getenv("POSTGRES_PORT")
    host = os.getenv("POSTGRES_HOST", "localhost")

    if not all([user, password, db, port]):
        return None

    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


app = FastAPI(
    title="Voice Assistant Backend",
    description=(
        "FastAPI backend for the Voice Assistant preview. "
        "Provides health check, assist pipeline, and history endpoints."
    ),
    version="0.1.0",
    openapi_tags=[
        {"name": "health", "description": "Health and diagnostics endpoints."},
        {"name": "assistant", "description": "Voice assistant pipeline endpoints."},
        {"name": "history", "description": "Conversation history endpoints."},
    ],
)

# CORS: allow preview frontend (3000) to call backend (3001).
# Keep permissive defaults for local dev, but prefer explicit origins.
allow_origins = _csv_env(
    "CORS_ALLOW_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"], summary="Health Check")
def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns:
        JSON object indicating the service is up, and basic configuration signals useful for preview debugging.
    """
    db_url = _build_database_url_from_env()
    return {
        "message": "Healthy",
        "cors_allow_origins": allow_origins,
        "db_configured": bool(db_url),
    }


@app.get("/history", tags=["history"], summary="Get chat history")
def get_history() -> List[Dict[str, Any]]:
    """
    Returns chat history.

    Note:
        The workspace includes a Postgres schema container, but this preview endpoint returns an empty history
        until the full persistence layer is connected in this repo.

    Returns:
        A list of chat messages, newest-last (chronological).
    """
    return []


@app.post("/assist", tags=["assistant"], summary="Assist from audio (STT→LLM→TTS)")
async def assist(
    audio: UploadFile = File(..., description="Audio recorded in the browser (webm/opus typically)."),
    language: str = Form("en", description="STT language/locale hint (e.g., en, en-US)."),
    voice: str = Form("default", description="TTS voice preset identifier."),
) -> Dict[str, Any]:
    """
    Accepts an audio blob and returns a simple assistant response payload.

    This is a preview-friendly stub that matches the frontend contract:
      - transcript: string
      - replyText: string
      - ttsAudioUrl?: string

    Args:
        audio: Uploaded audio file.
        language: Language hint.
        voice: Voice preset.

    Returns:
        JSON payload with transcript and reply text.
    """
    # Read bytes so the endpoint exercises multipart upload end-to-end.
    _ = await audio.read()

    # Stub behavior: demonstrate successful roundtrip without external providers.
    transcript = f"(stub transcript; received {audio.filename or 'audio'}; lang={language})"
    reply_text = (
        "Stub reply from backend. "
        "Wire STT/LLM/TTS providers and DB persistence in the next step."
    )

    return {"transcript": transcript, "replyText": reply_text, "ttsAudioUrl": None}
