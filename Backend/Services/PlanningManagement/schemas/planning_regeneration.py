"""
schemas/planning_regeneration.py
==================================
Pydantic schemas for planning regeneration.
"""

from pydantic import BaseModel, Field
from typing import Optional


class RegenerateRequest(BaseModel):
    """Body for POST /planning/regenerate"""
    constraints_dict:  Optional[dict] = Field(
        None,
        description="Pre-validated planning_dict from ConstraintAgent. If provided, skips LLM extraction."
    )
    user_constraints:  Optional[str]  = Field(
        None,
        description="Free-text scheduling constraints (English or French)."
    )
    rejected_group_id: Optional[str]  = Field(
        None,
        description="UUID of the rejected planning batch. Used to generate a genuinely different schedule."
    )
    attempt:           int = Field(
        default=2, ge=2,
        description="Attempt number. Higher = more different from previous attempts."
    )


class RegenerateResponse(BaseModel):
    """Returned after successful regeneration."""
    success:           bool
    planning_group_id: str           # UUID of the new planning batch
    total_sessions:    int
    attempt:           int
    engine:            str           # "ortools" | "greedy"
    final_constraints: dict
    schedule:          list[dict]
    message:           str