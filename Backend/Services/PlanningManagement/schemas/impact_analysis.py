"""
schemas/impact_analysis.py
============================
Pydantic schemas for impact analysis — what happens if session X is moved?
"""

from pydantic import BaseModel, Field
from typing import Optional


class ImpactRequest(BaseModel):
    """Body for POST /planning/session/{slot_id}/impact"""
    new_start_time: str = Field(
        ...,
        description="Proposed new start time (ISO 8601)",
        examples=["2025-09-01T14:00:00"]
    )
    new_end_time: str = Field(
        ...,
        description="Proposed new end time (ISO 8601)",
        examples=["2025-09-01T17:00:00"]
    )
    planning_group_id: Optional[str] = Field(
        None,
        description="UUID of the planning batch to search for conflicts in. "
                    "If omitted, searches all non-rejected slots."
    )


class ImpactConflict(BaseModel):
    """One detected conflict in the impact analysis."""
    conflict_type:    str           # "trainer" | "room" | "group"
    slot_id:          int           # the conflicting slot's DB id
    course_title:     str
    trainer_name:     str
    room_name:        str
    group_name:       str
    start_time:       str
    end_time:         str
    description:      str           # human-readable explanation


class AffectedSession(BaseModel):
    """A session that shares a resource with the moved session."""
    slot_id:      int
    course_title: str
    trainer_name: str
    room_name:    str
    start_time:   str
    end_time:     str
    relation:     str   # "same_trainer" | "same_room" | "same_group"


class ImpactResponse(BaseModel):
    """Full impact analysis result."""
    slot_id:            int
    course_title:       str
    proposed_start:     str
    proposed_end:       str

    is_safe:            bool          # True if zero conflicts
    new_conflicts:      list[ImpactConflict]
    resolved_conflicts: list[ImpactConflict]   # conflicts that disappear after the move
    affected_sessions:  list[AffectedSession]   # sessions sharing a resource

    summary:            str           # human-readable summary
    recommendation:     str           # suggested action