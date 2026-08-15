"""
Services/PlanningManagement/move_service.py
============================================
Business logic for drag-and-drop session moves.

Functions:
  move_session(slot_id, new_start, new_end, admin_note, db) → MoveResponse
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from models.schedule   import ScheduleSlot
from Services.PlanningManagement.schemas.schedule_move import MoveRequest, MoveResponse, MoveHistoryEntry


def move_session(
    slot_id:    int,
    body:       MoveRequest,
    db:         Session,
) -> MoveResponse:
    """
    Applies a drag-and-drop move to a single ScheduleSlot.

    Updates start_time + end_time in the DB.
    Appends an entry to move_history for audit trail.

    Args:
        slot_id: DB id of the ScheduleSlot to move
        body:    MoveRequest with new_start_time, new_end_time, admin_note
        db:      SQLAlchemy session

    Returns:
        MoveResponse
    """
    slot = db.query(ScheduleSlot).filter(ScheduleSlot.id == slot_id).first()
    if not slot:
        raise ValueError(f"ScheduleSlot id={slot_id} not found.")

    if slot.status == "validated":
        raise ValueError(
            f"Cannot move a validated slot (id={slot_id}). "
            "Reject or re-draft the planning first."
        )

    # Parse new times
    try:
        new_start = datetime.fromisoformat(body.new_start_time)
        new_end   = datetime.fromisoformat(body.new_end_time)
    except ValueError as e:
        raise ValueError(f"Invalid datetime format: {e}")

    if new_end <= new_start:
        raise ValueError("new_end_time must be after new_start_time.")

    # Save old times for the history entry
    old_start = slot.start_time.isoformat() if slot.start_time else ""
    old_end   = slot.end_time.isoformat()   if slot.end_time   else ""

    # Build history entry
    history_entry = {
        "from_start": old_start,
        "from_end":   old_end,
        "to_start":   new_start.isoformat(),
        "to_end":     new_end.isoformat(),
        "admin_note": body.admin_note,
        "moved_at":   datetime.now(timezone.utc).isoformat(),
    }

    # Apply move
    slot.start_time   = new_start
    slot.end_time     = new_end
    slot.move_history = list(slot.move_history or []) + [history_entry]
    slot.status       = "draft"      # move resets validation status

    db.commit()
    db.refresh(slot)

    move_count = len(slot.move_history)
    print(
        f"  [MoveService] Slot #{slot_id} moved: "
        f"{old_start} → {new_start.isoformat()} (move #{move_count})"
    )

    return MoveResponse(
        success    = True,
        slot_id    = slot_id,
        from_start = old_start,
        from_end   = old_end,
        to_start   = new_start.isoformat(),
        to_end     = new_end.isoformat(),
        move_count = move_count,
        message    = f"Session moved to {new_start.strftime('%A %H:%M')} (move #{move_count}).",
    )


def get_move_history(slot_id: int, db: Session) -> list[dict]:
    """Returns the full move history for a given slot."""
    slot = db.query(ScheduleSlot).filter(ScheduleSlot.id == slot_id).first()
    if not slot:
        raise ValueError(f"ScheduleSlot id={slot_id} not found.")
    return slot.move_history or []
"""
Services/PlanningManagement/move_service.py
============================================
Business logic for drag-and-drop session moves.

Functions:
  move_session(slot_id, new_start, new_end, admin_note, db) → MoveResponse
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from models.schedule   import ScheduleSlot
from Services.PlanningManagement.schemas.schedule_move import MoveRequest, MoveResponse, MoveHistoryEntry


def move_session(
    slot_id:    int,
    body:       MoveRequest,
    db:         Session,
) -> MoveResponse:
    """
    Applies a drag-and-drop move to a single ScheduleSlot.

    Updates start_time + end_time in the DB.
    Appends an entry to move_history for audit trail.

    Args:
        slot_id: DB id of the ScheduleSlot to move
        body:    MoveRequest with new_start_time, new_end_time, admin_note
        db:      SQLAlchemy session

    Returns:
        MoveResponse
    """
    slot = db.query(ScheduleSlot).filter(ScheduleSlot.id == slot_id).first()
    if not slot:
        raise ValueError(f"ScheduleSlot id={slot_id} not found.")

    if slot.status == "validated":
        raise ValueError(
            f"Cannot move a validated slot (id={slot_id}). "
            "Reject or re-draft the planning first."
        )

    # Parse new times
    try:
        new_start = datetime.fromisoformat(body.new_start_time)
        new_end   = datetime.fromisoformat(body.new_end_time)
    except ValueError as e:
        raise ValueError(f"Invalid datetime format: {e}")

    if new_end <= new_start:
        raise ValueError("new_end_time must be after new_start_time.")

    # Save old times for the history entry
    old_start = slot.start_time.isoformat() if slot.start_time else ""
    old_end   = slot.end_time.isoformat()   if slot.end_time   else ""

    # Build history entry
    history_entry = {
        "from_start": old_start,
        "from_end":   old_end,
        "to_start":   new_start.isoformat(),
        "to_end":     new_end.isoformat(),
        "admin_note": body.admin_note,
        "moved_at":   datetime.now(timezone.utc).isoformat(),
    }

    # Apply move
    slot.start_time   = new_start
    slot.end_time     = new_end
    slot.move_history = list(slot.move_history or []) + [history_entry]
    slot.status       = "draft"      # move resets validation status

    db.commit()
    db.refresh(slot)

    move_count = len(slot.move_history)
    print(
        f"  [MoveService] Slot #{slot_id} moved: "
        f"{old_start} → {new_start.isoformat()} (move #{move_count})"
    )

    return MoveResponse(
        success    = True,
        slot_id    = slot_id,
        from_start = old_start,
        from_end   = old_end,
        to_start   = new_start.isoformat(),
        to_end     = new_end.isoformat(),
        move_count = move_count,
        message    = f"Session moved to {new_start.strftime('%A %H:%M')} (move #{move_count}).",
    )


def get_move_history(slot_id: int, db: Session) -> list[dict]:
    """Returns the full move history for a given slot."""
    slot = db.query(ScheduleSlot).filter(ScheduleSlot.id == slot_id).first()
    if not slot:
        raise ValueError(f"ScheduleSlot id={slot_id} not found.")
    return slot.move_history or []