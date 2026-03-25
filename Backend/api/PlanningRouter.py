"""
api/planning_router.py
======================
FastAPI router for the Planning Agent.

Endpoints:
  POST /planning/run          -> Run the full planning agent (constraints from DB + optional user text)
  GET  /planning/constraints  -> View all constraints stored in DB
  GET  /planning/schedule     -> Get the last generated schedule (stored in memory)
  POST /planning/validate     -> Validate the current schedule
  GET  /planning/export/csv   -> Download the schedule as CSV
"""


import csv
import io
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.DB import SessionLocal
from agents.planning_agent import (
    PlanningAgent,
    _load_constraints_from_db,
    _extract_constraints_from_text,
    _merge_constraints,
    _load_data_from_db,
    _generate_schedule,
)


router = APIRouter(prefix="/planning", tags=["Planning Agent"])

# In-memory store for the last generated schedule (per session)
_last_schedule: list[dict] = []
_last_validated: bool = False


# =============================================================================
#  DB Dependency
# =============================================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================================================================
#  Request / Response Schemas
# =============================================================================

class PlanningRunRequest(BaseModel):
    user_constraints: Optional[str] = Field(
        default=None,
        description="Optional extra constraints in free text (English or French).",
        examples=["No sessions on Friday. Ahmed available Monday morning only."]
    )


class SessionSlot(BaseModel):
    session_number: int
    course_id:      int
    course_title:   str
    trainer_id:     int
    trainer_name:   str
    room_id:        int
    room_name:      str
    group_id:       int
    group_name:     str
    suggested_day:  str
    suggested_time: str
    reasoning:      str


class PlanningRunResponse(BaseModel):
    success:           bool
    total_sessions:    int
    db_constraints:    dict
    user_constraints:  dict
    final_constraints: dict
    schedule:          list[SessionSlot]


class ValidateResponse(BaseModel):
    success:   bool
    validated: bool
    message:   str


class ConstraintsResponse(BaseModel):
    total:       int
    constraints: dict


# =============================================================================
#  ENDPOINTS
# =============================================================================

@router.post(
    "/run",
    response_model=PlanningRunResponse,
    summary="Run the planning agent and generate a schedule",
)
def run_planning(
    body: PlanningRunRequest,
    db:   Session = Depends(get_db),
):

    global _last_schedule, _last_validated

    # 1. Load constraints from DB
    db_constraints, nb_rows = _load_constraints_from_db(db)

    # 2. Extract user constraints via LLM (if provided)
    user_constraints = {}
    if body.user_constraints and body.user_constraints.strip():
        user_constraints = _extract_constraints_from_text(body.user_constraints.strip())

    # 3. Merge
    final_constraints = _merge_constraints(db_constraints, user_constraints)

    # 4. Load data from DB
    data = _load_data_from_db(db)
    if not data:
        raise HTTPException(
            status_code=404,
            detail="No data found in DB (Courses, Trainers, Rooms, Groups are all empty). "
                   "Please import data first."
        )

    # 5. Generate schedule
    schedule = _generate_schedule(data, final_constraints)
    if not schedule:
        raise HTTPException(
            status_code=422,
            detail="No sessions could be scheduled with the current data and constraints."
        )

    # Store in memory for validation + export
    _last_schedule  = schedule
    _last_validated = False

    return PlanningRunResponse(
        success           = True,
        total_sessions    = len(schedule),
        db_constraints    = db_constraints,
        user_constraints  = user_constraints,
        final_constraints = final_constraints,
        schedule          = [SessionSlot(**s) for s in schedule],
    )


@router.get(
    "/constraints",
    response_model=ConstraintsResponse,
    summary="View all constraints currently stored in DB",
)
def get_constraints(db: Session = Depends(get_db)):
    """Returns all constraints loaded from the Constraints table."""
    constraints, nb_rows = _load_constraints_from_db(db)
    return ConstraintsResponse(total=nb_rows, constraints=constraints)


@router.get(
    "/schedule",
    response_model=list[SessionSlot],
    summary="Get the last generated schedule",
)
def get_last_schedule():
    """Returns the last schedule generated by the agent (stored in memory)."""
    if not _last_schedule:
        raise HTTPException(
            status_code=404,
            detail="No schedule generated yet. Call POST /planning/run first."
        )
    return [SessionSlot(**s) for s in _last_schedule]


@router.post(
    "/validate",
    response_model=ValidateResponse,
    summary="Validate the current schedule",
)
def validate_schedule():
    """
    Marks the last generated schedule as validated.
    Must call POST /planning/run before validating.
    """
    global _last_validated

    if not _last_schedule:
        raise HTTPException(
            status_code=404,
            detail="No schedule to validate. Call POST /planning/run first."
        )

    _last_validated = True
    return ValidateResponse(
        success   = True,
        validated = True,
        message   = f"Schedule validated. {len(_last_schedule)} session(s) confirmed.",
    )


@router.get(
    "/export/csv",
    summary="Download the last generated schedule as CSV",
)
def export_csv():
    """
    Downloads the last generated schedule as a CSV file.
    Call POST /planning/run first to generate a schedule.
    """
    if not _last_schedule:
        raise HTTPException(
            status_code=404,
            detail="No schedule to export. Call POST /planning/run first."
        )

    fieldnames = [
        "session_number", "course_id", "course_title",
        "trainer_id", "trainer_name", "room_id", "room_name",
        "group_id", "group_name", "suggested_day", "suggested_time", "reasoning",
    ]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(_last_schedule)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=schedule.csv"},
    )