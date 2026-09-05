"""
FastAPI Routes for Meeting Intelligent System API.
"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from typing import Optional

from .schemas import HealthResponse, ProcessMeetingResponse
from .service import process_meeting_input

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        member4_active=True,
        message="Meeting Intelligent System API is operational.",
    )


@router.post("/meetings/process", response_model=ProcessMeetingResponse)
async def process_meeting(
    meeting_id: str = Form(...),
    audio: Optional[UploadFile] = File(None),
    transcript_file: Optional[UploadFile] = File(None),
    transcript_text: Optional[str] = Form(None),
    force_reprocess: bool = Form(False),
):
    """
    Process an incoming meeting via audio upload, transcript file, or pasted transcript text.
    Returns complete Member 4 dashboard payload.
    """
    audio_bytes = None
    audio_filename = None
    if audio is not None and audio.filename:
        audio_bytes = await audio.read()
        audio_filename = audio.filename

    transcript_bytes = None
    transcript_filename = None
    if transcript_file is not None and transcript_file.filename:
        transcript_bytes = await transcript_file.read()
        transcript_filename = transcript_file.filename

    try:
        payload = process_meeting_input(
            meeting_id=meeting_id,
            audio_bytes=audio_bytes,
            audio_filename=audio_filename,
            transcript_bytes=transcript_bytes,
            transcript_filename=transcript_filename,
            transcript_text=transcript_text,
            force_reprocess=force_reprocess,
        )
        return ProcessMeetingResponse(**payload)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal processing failure: {str(e)}")
