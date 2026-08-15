"""
schemas/schedule_move.py
=========================
Pydantic schemas for drag-and-drop session moves.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MoveRequest(BaseModel):
    """Body for PATCH /planning/session/{slot_id}/move"""
    new_start_time: str = Field(
        ...,
        description="New session start time in ISO 8601 format: 2025-09-01T08:00:00",
        examples=["2025-09-01T08:00:00"]
    )
    new_end_time: str = Field(
        ...,
        description="New session end time in ISO 8601 format: 2025-09-01T11:00:00",
        examples=["2025-09-01T11:00:00"]
    )
    admin_note: Optional[str] = Field(
        None, max_length=255,
        description="Optional admin note explaining why this session was moved"
    )


class MoveHistoryEntry(BaseModel):
    """One entry in the slot's move_history JSON column."""
    from_start: str
    from_end:   str
    to_start:   str
    to_end:     str
    admin_note: Optional[str]
    moved_at:   str   # ISO 8601 datetime


class MoveResponse(BaseModel):
    """Returned after a successful move."""
    success:       bool
    slot_id:       int
    from_start:    str
    from_end:      str
    to_start:      str
    to_end:        str
    move_count:    int    # total moves applied to this slot so far
    message:       str