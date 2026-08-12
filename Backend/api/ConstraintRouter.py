from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.DB import SessionLocal
from agents.ConstraintAgent import ConstraintAgent
from Services.constraintAgent.Schema import ValidationStatus


router = APIRouter(prefix="/constraints", tags=["Constraint Agent"])


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

class ConstraintAnalyzeRequest(BaseModel):
    pedagogical_text: Optional[str] = Field(
        default="",
        description=(
            "Pedagogical wishes in natural language. "
            "Examples: 'Start with fundamentals before advanced topics. "
            "Avoid cognitive overload — max 2 new concepts per session.'"
        ),
        examples=["Start with fundamentals. Balance theory and practice."]
    )
    user_text: Optional[str] = Field(
        default="",
        description=(
            "Scheduling constraints in natural language (English or French). "
            "Examples: 'No sessions on Friday. Ahmed available Monday morning only. "
            "Sessions of 1h30 with 5 min breaks.'"
        ),
        examples=["No sessions on Friday. Ahmed available Monday morning only."]
    )


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
    success:           bool
    is_valid:          bool
    validation:        ValidationResultOut
    planning_dict:     dict        # ready for PlanningAgent.run()
    preprocessing:     dict        # text analysis metadata (language, days found, etc.)
    error:             str = ""


class ISOConstraintOut(BaseModel):
    constraint_type: str
    value:           object
    severity:        str
    description:     str


class ISOListResponse(BaseModel):
    total:       int
    constraints: list[ISOConstraintOut]


# =============================================================================
#  ENDPOINTS
# =============================================================================

@router.post(
    "/analyze",
    response_model=ConstraintAnalyzeResponse,
    summary="Analyze and validate constraints from all 3 sources",
)
def analyze_constraints(
    body: ConstraintAnalyzeRequest,
    db:   Session = Depends(get_db),
):

    agent = ConstraintAgent(db=db)

    result = agent.run(
        pedagogical_text = body.pedagogical_text or "",
        user_text        = body.user_text        or "",
    )

    # Serialize validation issues
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


@router.get(
    "/iso",
    response_model=ISOListResponse,
    summary="View all ISO constraints stored in the database",
)
def get_iso_constraints(db: Session = Depends(get_db)):

    from Services.constraintAgent.Loaders.Iso_loader import ISOLoader
    iso_loader = ISOLoader(db)
    iso_list   = iso_loader.load()

    return ISOListResponse(
        total = len(iso_list),
        constraints = [
            ISOConstraintOut(
                constraint_type = c.constraint_type,
                value           = c.value,
                severity        = c.severity.value,
                description     = c.description,
            )
            for c in iso_list
        ]
    )


@router.post(
    "/validate-only",
    response_model=ValidationResultOut,
    summary="Validate a planning_dict without running the full pipeline",
)
def validate_planning_dict(
    planning_dict: dict,
    db: Session = Depends(get_db),
):

    from Services.constraintAgent.Schema import ConstraintOutput
    from Services.constraintAgent.Rules.iso_rules      import run_all_iso_checks
    from Services.constraintAgent.Rules.business_rules import run_all_business_checks
    from Services.constraintAgent.Validator            import Validator

    # Rebuild ConstraintOutput from the dict
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
                severity=i.severity.value, suggestion=i.suggestion
            )
            for i in validation.issues
        ],
        warnings = validation.warnings,
    )