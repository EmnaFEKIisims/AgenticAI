"""
api/PlanningRouter.py
======================
FastAPI router for the Planning Agent.

Updated to support the 3 run modes of PlanningAgent:

  Mode 1 — /planning/run/with-constraints
    Body includes pre-validated constraints_dict from ConstraintAgent.
    → PlanningAgent skips all extraction, uses the dict directly.

  Mode 2 — /planning/run  (existing, updated)
    Body includes optional user_constraints text.
    → LLM extracts from text, merges with DB.

  Mode 3 — /planning/run/full-pipeline  (NEW)
    Runs ConstraintAgent first, then PlanningAgent.
    Single endpoint that does everything end-to-end.

Endpoints:
  POST /planning/run                    -> Mode 2: text constraints
  POST /planning/run/with-constraints   -> Mode 1: pre-validated dict
  POST /planning/run/full-pipeline      -> Mode 3: ConstraintAgent + PlanningAgent
  GET  /planning/constraints            -> All DB constraints
  GET  /planning/schedule               -> Last generated schedule
  POST /planning/validate               -> HITL validation
  GET  /planning/export/csv             -> CSV download
"""

import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.DB import SessionLocal
from agents.planning_agent import PlanningAgent, schedule_to_csv_bytes
from agents.ConstraintAgent import ConstraintAgent


router = APIRouter(prefix="/planning", tags=["Planning Agent"])

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
    """Mode 2 — text constraints only."""
    user_constraints: Optional[str] = Field(
        default=None,
        description="Optional scheduling constraints in free text (English or French).",
        examples=["No sessions on Friday. Ahmed available Monday morning only."]
    )


class PlanningRunWithConstraintsRequest(BaseModel):
    """Mode 1 — pre-validated constraints_dict from ConstraintAgent."""
    constraints_dict: dict = Field(
        ...,
        description=(
            "Pre-validated constraint dict from ConstraintAgent. "
            "Pass result.planning_dict from POST /constraints/analyze."
        )
    )


class FullPipelineRequest(BaseModel):
    """Mode 3 — runs ConstraintAgent then PlanningAgent end-to-end."""
    pedagogical_text: Optional[str] = Field(
        default="",
        description="Pedagogical preferences in free text.",
        examples=["Start with fundamentals. Avoid cognitive overload."]
    )
    user_text: Optional[str] = Field(
        default="",
        description="Scheduling constraints in free text (English or French).",
        examples=["No sessions on Friday. Ahmed available Monday morning only."]
    )


class SessionSlot(BaseModel):
    # Display fields
    session_number:  int
    course_id:       int
    course_title:    str
    trainer_id:      int
    trainer_name:    str
    room_id:         int
    room_name:       str
    group_name:      str
    suggested_day:   str
    suggested_time:  str
    reasoning:       str

    # DB fields (match ScheduleSlot model)
    learner_group_id:        int
    start_time:              str
    end_time:                str
    status:                  str
    is_validated:            bool
    quality_score:           float
    pedagogical_audit_score: float

    class Config:
        extra = "ignore"


class PlanningRunResponse(BaseModel):
    success:           bool
    total_sessions:    int
    final_constraints: dict
    schedule:          list[SessionSlot]


class FullPipelineResponse(BaseModel):
    success:              bool
    total_sessions:       int
    constraint_valid:     bool
    constraint_issues:    list[dict]
    constraint_warnings:  list[str]
    final_constraints:    dict
    schedule:             list[SessionSlot]


class ValidateResponse(BaseModel):
    success:   bool
    validated: bool
    message:   str


class ConstraintsResponse(BaseModel):
    total:       int
    constraints: dict


# =============================================================================
#  HELPER
# =============================================================================

def _store_and_respond(result, agent, db) -> PlanningRunResponse:
    """Stores schedule in memory and builds the response."""
    global _last_schedule, _last_validated
    _last_schedule  = result.schedule
    _last_validated = False
    return PlanningRunResponse(
        success           = result.success,
        total_sessions    = result.total_sessions,
        final_constraints = result.constraints_used,
        schedule          = [SessionSlot(**s) for s in result.schedule],
    )


# =============================================================================
#  ENDPOINT 1 — POST /planning/run  (Mode 2: text constraints)
# =============================================================================

@router.post(
    "/run",
    response_model=PlanningRunResponse,
    summary="[Mode 2] Generate schedule with optional text constraints",
)
def run_planning(
    body: PlanningRunRequest,
    db:   Session = Depends(get_db),
):
    """
    Generates the optimal schedule.
    DB constraints are always loaded automatically.
    `user_constraints` is optional free text (English or French) — the LLM extracts it.

    For best results with validated constraints, use **POST /planning/run/full-pipeline**.

    Minimal call (DB constraints only):
    ```json
    {}
    ```
    With text constraints:
    ```json
    { "user_constraints": "No sessions on Friday." }
    ```
    """
    global _last_schedule, _last_validated

    agent  = PlanningAgent(db=db)
    # Pass "" for API mode (no input() called), None would trigger terminal mode
    result = agent.run(extra_constraints=body.user_constraints or "")

    if not result.success:
        raise HTTPException(status_code=422, detail=result.error)

    return _store_and_respond(result, agent, db)


# =============================================================================
#  ENDPOINT 2 — POST /planning/run/with-constraints  (Mode 1: pre-validated dict)
# =============================================================================

@router.post(
    "/run/with-constraints",
    response_model=PlanningRunResponse,
    summary="[Mode 1] Generate schedule from pre-validated ConstraintAgent output",
)
def run_with_constraints(
    body: PlanningRunWithConstraintsRequest,
    db:   Session = Depends(get_db),
):
    """
    Generates schedule using a pre-validated constraint dict from the ConstraintAgent.

    **Recommended workflow:**
    1. Call `POST /constraints/analyze` → get `planning_dict`
    2. Pass `planning_dict` here as `constraints_dict`

    This mode skips LLM extraction entirely — constraints are already validated
    against ISO rules and business rules.

    ```json
    {
      "constraints_dict": { ...planning_dict from /constraints/analyze... }
    }
    ```
    """
    global _last_schedule, _last_validated

    agent  = PlanningAgent(db=db)
    result = agent.run(constraints_dict=body.constraints_dict)

    if not result.success:
        raise HTTPException(status_code=422, detail=result.error)

    return _store_and_respond(result, agent, db)


# =============================================================================
#  ENDPOINT 3 — POST /planning/run/full-pipeline  (Mode 3: end-to-end)
# =============================================================================

@router.post(
    "/run/full-pipeline",
    response_model=FullPipelineResponse,
    summary="[Mode 3] Run ConstraintAgent + PlanningAgent in one call",
)
def run_full_pipeline(
    body: FullPipelineRequest,
    db:   Session = Depends(get_db),
):
    """
    Full end-to-end pipeline in a single call:

    1. **ConstraintAgent** — loads ISO constraints from DB,
       extracts pedagogical + scheduling constraints via LLM,
       merges and validates everything (ISO rules + business rules).

    2. **PlanningAgent** — receives the validated constraint dict,
       generates the optimal schedule.

    The response includes constraint validation details so you can
    see what was applied and any warnings raised.

    ```json
    {
      "pedagogical_text": "Start with fundamentals. Avoid cognitive overload.",
      "user_text": "No sessions on Friday. Ahmed available Monday morning only."
    }
    ```
    """
    global _last_schedule, _last_validated

    # Step 1: ConstraintAgent
    constraint_agent  = ConstraintAgent(db=db)
    constraint_result = constraint_agent.run(
        pedagogical_text = body.pedagogical_text or "",
        user_text        = body.user_text        or "",
    )

    # Step 2: PlanningAgent — uses pre-validated dict
    planning_agent  = PlanningAgent(db=db)
    planning_result = planning_agent.run(
        constraints_dict=constraint_result.planning_dict
    )

    if not planning_result.success:
        raise HTTPException(status_code=422, detail=planning_result.error)

    _last_schedule  = planning_result.schedule
    _last_validated = False

    # Serialize constraint issues for response
    issues_out = [
        {
            "field":      i.field,
            "message":    i.message,
            "severity":   i.severity.value,
            "suggestion": i.suggestion,
        }
        for i in constraint_result.validation.issues
    ]

    return FullPipelineResponse(
        success             = planning_result.success,
        total_sessions      = planning_result.total_sessions,
        constraint_valid    = constraint_result.validation.is_valid,
        constraint_issues   = issues_out,
        constraint_warnings = constraint_result.validation.warnings,
        final_constraints   = planning_result.constraints_used,
        schedule            = [SessionSlot(**s) for s in planning_result.schedule],
    )


# =============================================================================
#  ENDPOINT 4 — GET /planning/constraints
# =============================================================================

@router.get(
    "/constraints",
    response_model=ConstraintsResponse,
    summary="View all constraints currently stored in DB",
)
def get_constraints(db: Session = Depends(get_db)):
    """Returns all constraints from the Constraints table."""
    constraints, nb = PlanningAgent(db=db).get_constraints()
    return ConstraintsResponse(total=nb, constraints=constraints)


# =============================================================================
#  ENDPOINT 5 — GET /planning/schedule
# =============================================================================

@router.get(
    "/schedule",
    response_model=list[SessionSlot],
    summary="Get the last generated schedule (in memory)",
)
def get_last_schedule():
    """Returns the last schedule generated by any /run endpoint."""
    if not _last_schedule:
        raise HTTPException(
            status_code=404,
            detail="No schedule generated yet. Call POST /planning/run first."
        )
    return [SessionSlot(**s) for s in _last_schedule]


# =============================================================================
#  ENDPOINT 6 — POST /planning/validate
# =============================================================================

@router.post(
    "/validate",
    response_model=ValidateResponse,
    summary="HITL — validate the current schedule",
)
def validate_schedule():
    """Marks the last generated schedule as validated."""
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


# =============================================================================
#  ENDPOINT 7 — GET /planning/export/csv
# =============================================================================

@router.get(
    "/export/csv",
    summary="Download the last generated schedule as CSV",
)
def export_csv():
    """Downloads the last generated schedule as a CSV file."""
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