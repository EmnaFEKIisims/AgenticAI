"""
api/planning_router.py
======================
FastAPI router for the Planning Agent.

Endpoints:
  POST /planning/run          -> Run the full planning agent
  GET  /planning/constraints  -> View all constraints stored in DB
  GET  /planning/schedule     -> Get the last generated schedule (in memory)
  POST /planning/validate     -> Validate the current schedule
  GET  /planning/export/csv   -> Download the schedule as CSV
"""

import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.DB import SessionLocal
from agents.planning_agent import PlanningAgent, schedule_to_csv_bytes


router = APIRouter(prefix="/planning", tags=["Planning Agent"])

# In-memory store for the last generated schedule
_last_schedule:  list[dict] = []
_last_validated: bool       = False


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
#  Schemas
# =============================================================================

class PlanningRunRequest(BaseModel):
    user_constraints: Optional[str] = Field(
        default=None,
        description="Optional extra constraints in free text (English or French).",
        examples=["No sessions on Friday. Ahmed available Monday morning only."]
    )


class SessionSlot(BaseModel):
    # ── Display fields ──────────────────────────────────────────────────────
    session_number: int
    course_id:      int
    course_title:   str
    trainer_id:     int
    trainer_name:   str
    room_id:        int
    room_name:      str
    group_name:     str
    suggested_day:  str
    suggested_time: str
    reasoning:      str

    # ── DB fields (match ScheduleSlot model exactly) ────────────────────────
    learner_group_id:        int     # was "group_id" — FIXED
    start_time:              str     # ISO 8601 datetime
    end_time:                str     # ISO 8601 datetime
    status:                  str     # "draft"
    is_validated:            bool
    quality_score:           float
    pedagogical_audit_score: float

    class Config:
        extra = "ignore"             # silently ignore any extra keys


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
    """
    Generates the optimal training schedule.

    - DB constraints are **always loaded automatically**.
    - `user_constraints`: optional natural language (English or French).

    Minimal call:
    ```json
    {}
    ```
    With constraints:
    ```json
    { "user_constraints": "No sessions on Friday. Ahmed available Monday morning only." }
    ```
    """
    global _last_schedule, _last_validated

    agent  = PlanningAgent(db=db)
    result = agent.run(
        extra_constraints=body.user_constraints or ""
    )

    if not result.success:
        raise HTTPException(status_code=422, detail=result.error)

    _last_schedule  = result.schedule
    _last_validated = False

    db_constraints, _ = agent.get_constraints()

    return PlanningRunResponse(
        success           = result.success,
        total_sessions    = result.total_sessions,
        db_constraints    = db_constraints,
        user_constraints  = {},
        final_constraints = result.constraints_used,
        schedule          = [SessionSlot(**s) for s in result.schedule],
    )


@router.get(
    "/constraints",
    response_model=ConstraintsResponse,
    summary="View all constraints currently stored in DB",
)
def get_constraints(db: Session = Depends(get_db)):
    constraints, nb = PlanningAgent(db=db).get_constraints()
    return ConstraintsResponse(total=nb, constraints=constraints)


@router.get(
    "/schedule",
    response_model=list[SessionSlot],
    summary="Get the last generated schedule",
)
def get_last_schedule():
    if not _last_schedule:
        raise HTTPException(
            status_code=404,
            detail="No schedule generated yet. Call POST /planning/run first."
        )
    return [SessionSlot(**s) for s in _last_schedule]


@router.post(
    "/validate",
    response_model=ValidateResponse,
    summary="Validate the current schedule (HITL)",
)
def validate_schedule():
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
    if not _last_schedule:
        raise HTTPException(
            status_code=404,
            detail="No schedule to export. Call POST /planning/run first."
        )
    return StreamingResponse(
        io.BytesIO(schedule_to_csv_bytes(_last_schedule)),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=schedule.csv"},
    )