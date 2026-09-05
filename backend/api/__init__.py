"""
Backend API Package for Meeting Intelligent System.
Provides FastAPI service connecting frontend inputs to the Member 1-4 pipeline.
"""

from .app import app
from .service import process_meeting_input

__all__ = ["app", "process_meeting_input"]
