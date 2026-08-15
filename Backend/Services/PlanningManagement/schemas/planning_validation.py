"""
schemas/planning_validation.py
================================
Pydantic schemas for HITL planning validation (validate / reject).
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ValidateRequest(BaseModel):
    """Body for POST /planning/{group_id}/validate"""
    planning_group_id: str = Field(..., description="UUID of the planning batch to validate")
    validation_notes:  Optional[str] = Field(
        None, max_length=500,
        description="Optional admin comment on the validated planning"
    )


class RejectRequest(BaseModel):
    """Body for POST /planning/{group_id}/reject"""
    planning_group_id: str   = Field(..., description="UUID of the planning batch to reject")
    reason:            Optional[str] = Field(
        None, max_length=500,
        description="Reason for rejection — shown when regenerating"
    )


class ValidationResponse(BaseModel):
    """Returned after validate or reject."""
    success:           bool
    planning_group_id: str
    status:            str            # "validated" | "rejected"
    total_slots:       int
    message:           str
    timestamp:         datetime


class PlanningStatusResponse(BaseModel):
    """Current HITL status for a planning batch."""
    planning_group_id: str
    status:            str            # "draft" | "validated" | "rejected"
    total_slots:       int
    validated_slots:   int
    rejected_slots:    int
    draft_slots:       int
    created_at:        Optional[datetime]
    validated_at:      Optional[datetime]
    rejected_at:       Optional[datetime]