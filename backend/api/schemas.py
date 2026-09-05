"""
Pydantic Schemas for Meeting Intelligent System API.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    member4_active: bool = True
    message: str = "Meeting Intelligent System API is operational."


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class ProcessMeetingResponse(BaseModel):
    meeting_id: str
    processing_stage: str
    total_canonical_items: int
    views: Dict[str, Any]
    key_decisions: List[Dict[str, Any]]
    diagnostics: List[str] = Field(default_factory=list)
