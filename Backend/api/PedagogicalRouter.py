"""
api/PedagogicalRouter.py
==========================
FastAPI router for the Pedagogical Agent.

Endpoints:
  POST /audit              → Audit a planning → AuditReport
  GET  /audit/rules        → View all pedagogical rules
  GET  /audit/report/{id}  → Get last report for a planning ID (in memory)
"""

import io
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from Services.PedagogicalAgent.Schemas.Planning_schema  import Planning, Session, SessionType, DifficultyLevel, RoomType, WeekDay
from Services.PedagogicalAgent.Schemas.audit_schema     import AuditReport
from agents.pedagogical_agent import PedagogicalAgent
from utils.rule_loader         import load_rules, reload_rules


router = APIRouter(prefix="/audit", tags=["Pedagogical Agent"])

# In-memory store: planning_id → AuditReport
_reports: dict[int | str, AuditReport] = {}
_agent   = PedagogicalAgent()


# =============================================================================
#  REQUEST SCHEMAS
# =============================================================================

class SessionIn(BaseModel):
    """Input session for the audit endpoint."""
    course:       str
    teacher:      str
    room:         str
    day:          WeekDay
    start:        str              = Field(..., example="08:00")
    end:          str              = Field(..., example="11:00")
    session_type: SessionType      = SessionType.THEORY
    difficulty:   DifficultyLevel  = DifficultyLevel.MEDIUM
    room_type:    RoomType         = RoomType.CLASSROOM
    prerequisites: list[str]       = []
    course_id:    Optional[int]    = None
    trainer_id:   Optional[int]    = None
    group:        str              = ""


class AuditRequest(BaseModel):
    """
    Input to POST /audit.
    Accepts either:
      - sessions[]      : list of SessionIn (direct input)
      - schedule[]      : list[dict] from PlanningAgent output
    """
    sessions:    Optional[list[SessionIn]] = None
    schedule:    Optional[list[dict]]      = None
    planning_id: Optional[int]             = None
    group_name:  str                       = ""


# =============================================================================
#  RESPONSE SCHEMAS
# =============================================================================

class CriterionOut(BaseModel):
    rule:           str
    status:         str
    passed:         bool
    score:          float
    weight:         float
    score_ratio:    float
    severity:       str
    message:        str
    recommendation: str = ""
    iso_reference:  str = ""


class AuditReportOut(BaseModel):
    score:           float
    max_score:       float
    score_label:     str
    grade:           str
    is_compliant:    bool
    compliance_rate: float
    total_criteria:  int
    passed_criteria: int
    failed_criteria: int
    high_violations: int
    planning_id:     Optional[int]
    group_name:      Optional[str]
    total_sessions:  int
    total_hours:     float
    iso_references:  list[str]
    criteria:        list[CriterionOut]
    recommendations: list[str]
    group_scores:    dict[str, float] = Field(default_factory=dict)


# =============================================================================
#  ENDPOINT 1 — POST /audit
# =============================================================================

@router.post(
    "",
    response_model=AuditReportOut,
    summary="Audit a training planning against pedagogical rules",
)
def run_audit(body: AuditRequest):
    """
    Runs the full Pedagogical Agent pipeline on a planning.

    **Option A** — from PlanningAgent output (recommended):
    ```json
    {
      "schedule": [...],
      "group_name": "Group Python Beginners",
      "planning_id": 1
    }
    ```

    **Option B** — direct session input:
    ```json
    {
      "sessions": [
        {"course": "Java", "teacher": "Ahmed", "room": "A101",
         "day": "Monday", "start": "08:00", "end": "10:00",
         "session_type": "theory", "difficulty": "medium"}
      ]
    }
    ```

    IMPORTANT (Option A): when `schedule` contains several learner groups
    running in parallel — the normal shape of a well-optimized multi-group
    plan — this delegates to `PedagogicalAgent.generate_report()`, which
    audits each group SEPARATELY and averages the scores. Building one
    merged Planning across all groups and calling `.audit()` on it directly
    (the previous behavior here) made every group's hours sum together as
    if a single learner attended all of them at once, which is what was
    tanking the score on an otherwise well-optimized schedule.
    """
    if body.schedule:
        try:
            report = _agent.generate_report(body.schedule, group_name=body.group_name)
        except ValueError as e:
            # Raised when no session in the payload could be parsed into a
            # valid Planning (bad/missing day or time fields) — see server
            # logs for the per-session reason from Planning.from_schedule().
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")

    elif body.sessions:
        sessions = [
            Session(
                course        = s.course,
                teacher       = s.teacher,
                room          = s.room,
                day           = s.day,
                start         = s.start,
                end           = s.end,
                group         = s.group or body.group_name,
                session_type  = s.session_type,
                difficulty    = s.difficulty,
                room_type     = s.room_type,
                prerequisites = s.prerequisites,
                course_id     = s.course_id,
                trainer_id    = s.trainer_id,
            )
            for s in body.sessions
        ]
        planning = Planning(
            sessions    = sessions,
            planning_id = body.planning_id,
            group_name  = body.group_name,
        )

        if not planning.sessions:
            raise HTTPException(status_code=422, detail="Planning has no sessions to audit.")

        if body.planning_id:
            planning.planning_id = body.planning_id

        try:
            report = _agent.audit(planning)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")

    else:
        raise HTTPException(
            status_code=422,
            detail="Provide either 'schedule' (from PlanningAgent) or 'sessions' (direct input)."
        )

    # Cache report
    cache_key = body.planning_id or id(report)
    _reports[cache_key] = report

    return AuditReportOut(**report.to_dict())


# =============================================================================
#  ENDPOINT 2 — GET /audit/rules
# =============================================================================

@router.get(
    "/rules",
    summary="View all pedagogical rules currently active",
)
def get_rules(refresh: bool = False):
    """
    Returns the full pedagogical_rules.json content.
    Add `?refresh=true` to reload the file from disk without restarting.
    """
    try:
        rules = reload_rules() if refresh else load_rules()
        return {
            "total_sections": len(rules),
            "rules":          rules,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
#  ENDPOINT 3 — GET /audit/report/{id}
# =============================================================================

@router.get(
    "/report/{planning_id}",
    response_model=AuditReportOut,
    summary="Get the last audit report for a planning ID",
)
def get_report(planning_id: int):
    """
    Returns the cached audit report for a given planning ID.
    Call POST /audit first to generate the report.
    """
    report = _reports.get(planning_id)
    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"No audit report found for planning_id={planning_id}. "
                   "Call POST /audit first."
        )
    return AuditReportOut(**report.to_dict())