"""
api/ConstraintRouter.py
========================
Endpoints:
  POST /constraints/analyze       → Run ConstraintAgent (async + timeout)
  GET  /constraints/iso           → View ISO constraints in DB
  POST /constraints/validate-only → Validate a planning_dict
"""

import asyncio
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.DB import SessionLocal
from agents.ConstraintAgent import ConstraintAgent

router = APIRouter(prefix="/constraints", tags=["Constraint Agent"])

_executor = ThreadPoolExecutor(max_workers=4)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================================================================
#  Schemas
# =============================================================================

class ConstraintAnalyzeRequest(BaseModel):
    pedagogical_text: Optional[str] = Field(default="")
    user_text:        Optional[str] = Field(default="")


class ValidationIssueOut(BaseModel):
    field:      str
    message:    str
    severity:   str
    suggestion: str = ""


class ValidationResultOut(BaseModel):
    status:   str
    is_valid: bool
    issues:   list[ValidationIssueOut]
    warnings: list[str]


class ConstraintAnalyzeResponse(BaseModel):
    success:       bool
    is_valid:      bool
    validation:    ValidationResultOut
    planning_dict: dict
    preprocessing: dict
    error:         str = ""


class ISOConstraintOut(BaseModel):
    constraint_type: str
    value:           object
    severity:        str
    description:     str


class ISOListResponse(BaseModel):
    total:       int
    constraints: list[ISOConstraintOut]


# =============================================================================
#  Helper — runs in thread (LLM calls are blocking)
# =============================================================================

def _run_agent(db: Session, pedagogical_text: str, user_text: str):
    agent = ConstraintAgent(db=db)
    return agent.run(
        pedagogical_text=pedagogical_text,
        user_text=user_text,
    )


# =============================================================================
#  POST /constraints/analyze
# =============================================================================

@router.post(
    "/analyze",
    response_model=ConstraintAnalyzeResponse,
    summary="Analyze and validate constraints from all 3 sources",
)
async def analyze_constraints(
    body: ConstraintAnalyzeRequest,
    db:   Session = Depends(get_db),
):
    loop = asyncio.get_event_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(
                _executor,
                lambda: _run_agent(
                    db               = db,
                    pedagogical_text = body.pedagogical_text or "",
                    user_text        = body.user_text        or "",
                )
            ),
            timeout=120.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout — check Ollama or switch to Groq in .env")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    issues_out = [
        ValidationIssueOut(
            field      = i.field,
            message    = i.message,
            severity   = i.severity.value,
            suggestion = i.suggestion,
        )
        for i in result.validation.issues
    ]

    return ConstraintAnalyzeResponse(
        success       = result.success,
        is_valid      = result.validation.is_valid,
        validation    = ValidationResultOut(
            status   = result.validation.status.value,
            is_valid = result.validation.is_valid,
            issues   = issues_out,
            warnings = result.validation.warnings,
        ),
        planning_dict = result.planning_dict,
        preprocessing = result.preprocessing,
        error         = result.error,
    )


# =============================================================================
#  GET /constraints/iso
# =============================================================================

@router.get(
    "/iso",
    response_model=ISOListResponse,
    summary="View all ISO constraints stored in the database",
)
def get_iso_constraints(db: Session = Depends(get_db)):
    from Services.constraintAgent.Loaders.Iso_loader import ISOLoader
    iso_list = ISOLoader(db).load()
    return ISOListResponse(
        total=len(iso_list),
        constraints=[
            ISOConstraintOut(
                constraint_type=c.constraint_type,
                value=c.value,
                severity=c.severity.value,
                description=c.description,
            )
            for c in iso_list
        ],
    )


# =============================================================================
#  POST /constraints/validate-only
# =============================================================================

@router.post(
    "/validate-only",
    response_model=ValidationResultOut,
    summary="Validate a planning_dict without running the full pipeline",
)
def validate_planning_dict(planning_dict: dict, db: Session = Depends(get_db)):
    try:
        from Services.constraintAgent.Schema           import ConstraintOutput
        from Services.constraintAgent.Rules.iso_rules      import run_all_iso_checks
        from Services.constraintAgent.Rules.business_rules import run_all_business_checks
        from Services.constraintAgent.Validator            import Validator

        output = ConstraintOutput(
            forbidden_days                  = planning_dict.get("forbidden_days", []),
            trainer_availability            = planning_dict.get("trainer_availability", {}),
            session_duration_override       = planning_dict.get("session_duration_override"),
            sessions_per_day                = planning_dict.get("sessions_per_day"),
            break_between_sessions_minutes  = planning_dict.get("break_between_sessions_minutes"),
            lunch_break_after_n_sessions    = planning_dict.get("lunch_break_after_n_sessions"),
            lunch_break_duration_minutes    = planning_dict.get("lunch_break_duration_minutes"),
            day_start_time                  = planning_dict.get("day_start_time"),
            min_room_capacity               = planning_dict.get("min_room_capacity"),
            room_type_required              = planning_dict.get("room_type_required"),
            group_priority                  = planning_dict.get("group_priority"),
            no_parallel_sessions_same_group = planning_dict.get("no_parallel_sessions_same_group", False),
            prefer_matching_specialization  = planning_dict.get("prefer_matching_specialization", True),
        )

        validator       = Validator()
        validation      = validator.validate(output)
        iso_issues      = run_all_iso_checks(output)
        business_issues = run_all_business_checks(output)

        existing_msgs = {i.message for i in validation.issues}
        for issue in iso_issues + business_issues:
            if issue.message not in existing_msgs:
                validation.issues.append(issue)

        return ValidationResultOut(
            status   = validation.status.value,
            is_valid = validation.is_valid,
            issues   = [
                ValidationIssueOut(
                    field=i.field, message=i.message,
                    severity=i.severity.value, suggestion=i.suggestion,
                )
                for i in validation.issues
            ],
            warnings = validation.warnings,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))