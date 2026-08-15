"""
Services/PlanningManagement/validation_service.py
===================================================
Business logic for HITL planning validation.

Functions:
  validate_planning(planning_group_id, notes, db)  → mark all slots as "validated"
  reject_planning(planning_group_id, reason, db)   → mark all slots as "rejected"
  get_planning_status(planning_group_id, db)       → current HITL status summary
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from models.schedule import ScheduleSlot
from Services.PlanningManagement.schemas.planning_validation import ValidationResponse, PlanningStatusResponse


# =============================================================================
#  VALIDATE
# =============================================================================

def validate_planning(
    planning_group_id: str,
    db:                Session,
    validation_notes:  str | None = None,
) -> ValidationResponse:
    """
    Marks all draft slots of a planning batch as 'validated'.

    Args:
        planning_group_id: UUID of the planning batch
        db:                SQLAlchemy session
        validation_notes:  Optional admin comment

    Returns:
        ValidationResponse with the count of updated slots.
    """
    slots = (
        db.query(ScheduleSlot)
        .filter(
            ScheduleSlot.planning_group_id == planning_group_id,
            ScheduleSlot.status.in_(["draft", "pending"]),
        )
        .all()
    )

    if not slots:
        return ValidationResponse(
            success           = False,
            planning_group_id = planning_group_id,
            status            = "unknown",
            total_slots       = 0,
            message           = f"No draft slots found for planning group '{planning_group_id}'.",
            timestamp         = datetime.now(timezone.utc),
        )

    now = datetime.now(timezone.utc)
    for slot in slots:
        slot.status           = "validated"
        slot.is_validated     = True
        slot.validated_at     = now
        slot.validation_notes = validation_notes
        slot.rejected_at      = None   # clear any previous rejection

    db.commit()
    print(f"  [ValidationService] ✅ {len(slots)} slot(s) validated for group '{planning_group_id}'.")

    return ValidationResponse(
        success           = True,
        planning_group_id = planning_group_id,
        status            = "validated",
        total_slots       = len(slots),
        message           = f"✅ {len(slots)} session(s) validated successfully.",
        timestamp         = now,
    )


# =============================================================================
#  REJECT
# =============================================================================

def reject_planning(
    planning_group_id: str,
    db:                Session,
    reason:            str | None = None,
) -> ValidationResponse:
    """
    Marks all slots of a planning batch as 'rejected'.

    Args:
        planning_group_id: UUID of the planning batch
        db:                SQLAlchemy session
        reason:            Optional reason for rejection

    Returns:
        ValidationResponse
    """
    slots = (
        db.query(ScheduleSlot)
        .filter(ScheduleSlot.planning_group_id == planning_group_id)
        .all()
    )

    if not slots:
        return ValidationResponse(
            success           = False,
            planning_group_id = planning_group_id,
            status            = "unknown",
            total_slots       = 0,
            message           = f"No slots found for planning group '{planning_group_id}'.",
            timestamp         = datetime.now(timezone.utc),
        )

    now = datetime.now(timezone.utc)
    for slot in slots:
        slot.status           = "rejected"
        slot.is_validated     = False
        slot.rejected_at      = now
        slot.validation_notes = reason
        slot.validated_at     = None

    db.commit()
    print(f"  [ValidationService] ❌ {len(slots)} slot(s) rejected for group '{planning_group_id}'.")

    return ValidationResponse(
        success           = True,
        planning_group_id = planning_group_id,
        status            = "rejected",
        total_slots       = len(slots),
        message           = f"❌ {len(slots)} session(s) rejected. Use /regenerate for a new proposal.",
        timestamp         = now,
    )


# =============================================================================
#  STATUS
# =============================================================================

def get_planning_status(
    planning_group_id: str,
    db:                Session,
) -> PlanningStatusResponse:
    """Returns the current HITL status of a planning batch."""
    slots = (
        db.query(ScheduleSlot)
        .filter(ScheduleSlot.planning_group_id == planning_group_id)
        .all()
    )

    if not slots:
        return PlanningStatusResponse(
            planning_group_id = planning_group_id,
            status            = "not_found",
            total_slots       = 0,
            validated_slots   = 0,
            rejected_slots    = 0,
            draft_slots       = 0,
            created_at        = None,
            validated_at      = None,
            rejected_at       = None,
        )

    validated = [s for s in slots if s.status == "validated"]
    rejected  = [s for s in slots if s.status == "rejected"]
    drafts    = [s for s in slots if s.status == "draft"]

    # Determine overall status
    if len(validated) == len(slots):
        overall = "validated"
    elif len(rejected) == len(slots):
        overall = "rejected"
    elif validated or rejected:
        overall = "partial"
    else:
        overall = "draft"

    return PlanningStatusResponse(
        planning_group_id = planning_group_id,
        status            = overall,
        total_slots       = len(slots),
        validated_slots   = len(validated),
        rejected_slots    = len(rejected),
        draft_slots       = len(drafts),
        created_at        = min((s.created_at for s in slots if s.created_at), default=None),
        validated_at      = max((s.validated_at for s in validated if s.validated_at), default=None),
        rejected_at       = max((s.rejected_at  for s in rejected  if s.rejected_at),  default=None),
    )