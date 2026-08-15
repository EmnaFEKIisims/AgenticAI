"""
Services/PlanningManagement/regeneration_service.py
=====================================================
Business logic for planning regeneration.

Generates a new planning batch, saves all slots to DB,
returns the new planning_group_id.
"""

import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from agents.planning_agent import PlanningAgent
from models.schedule import ScheduleSlot
from Services.PlanningManagement.schemas.planning_regeneration import RegenerateRequest, RegenerateResponse


def regenerate_planning(
    body: RegenerateRequest,
    db:   Session,
) -> RegenerateResponse:
    """
    Generates a new planning proposal different from the rejected one.

    Steps:
      1. Call PlanningAgent.regenerate() with shuffled data (different order)
      2. Save all new slots to DB with a fresh planning_group_id
      3. Return the new group_id + schedule

    Args:
        body: RegenerateRequest (constraints + rejected_group_id + attempt)
        db:   SQLAlchemy session

    Returns:
        RegenerateResponse with new planning_group_id and schedule
    """
    print(f"\n  [RegenerationService] Attempt #{body.attempt}...")

    agent = PlanningAgent(db=db)

    # Generate new planning (shuffled order for different result)
    result = agent.regenerate(
        constraints_dict  = body.constraints_dict,
        extra_constraints = body.user_constraints or "",
        attempt           = body.attempt,
    )

    if not result.success:
        return RegenerateResponse(
            success           = False,
            planning_group_id = "",
            total_sessions    = 0,
            attempt           = body.attempt,
            engine            = "greedy",
            final_constraints = {},
            schedule          = [],
            message           = result.error or "Regeneration failed.",
        )

    # Generate a new UUID for this planning batch
    new_group_id = str(uuid.uuid4())

    # Save all slots to DB
    saved = _save_schedule_to_db(result.schedule, new_group_id, db)
    print(f"  [RegenerationService] ✅ {saved} slot(s) saved with group_id='{new_group_id}'.")

    return RegenerateResponse(
        success           = True,
        planning_group_id = new_group_id,
        total_sessions    = result.total_sessions,
        attempt           = body.attempt,
        engine            = result.engine,
        final_constraints = result.constraints_used,
        schedule          = result.schedule,
        message           = f"✅ New proposal generated ({result.total_sessions} sessions, attempt #{body.attempt}).",
    )


def save_initial_planning(
    schedule:  list[dict],
    db:        Session,
) -> str:
    """
    Saves the initial planning (from /run or /run/full-pipeline) to DB.
    Returns the new planning_group_id.

    Called by PlanningRouter after the first successful generation.
    """
    group_id = str(uuid.uuid4())
    saved    = _save_schedule_to_db(schedule, group_id, db)
    print(f"  [RegenerationService] Initial planning saved: {saved} slots, group_id='{group_id}'.")
    return group_id


def _save_schedule_to_db(
    schedule: list[dict],
    group_id: str,
    db:       Session,
) -> int:
    """
    Inserts all sessions of a schedule into DB as ScheduleSlot rows.
    Returns the count of inserted rows.
    """
    from datetime import datetime as dt

    slots = []
    for s in schedule:
        try:
            start = dt.fromisoformat(s["start_time"])
            end   = dt.fromisoformat(s["end_time"])
        except Exception:
            continue

        slot = ScheduleSlot(
            course_id          = s["course_id"],
            trainer_id         = s["trainer_id"],
            room_id            = s["room_id"],
            learner_group_id   = s["learner_group_id"],
            start_time         = start,
            end_time           = end,
            planning_group_id  = group_id,
            session_number     = s.get("session_number"),
            quality_score      = s.get("quality_score", 0.0),
            pedagogical_audit_score = s.get("pedagogical_audit_score", 0.0),
            status             = "draft",
            is_validated       = False,
            move_history       = [],
        )
        slots.append(slot)

    db.add_all(slots)
    db.commit()
    return len(slots)