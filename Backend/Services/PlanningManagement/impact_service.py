"""
Services/PlanningManagement/impact_service.py
===============================================
Business logic for impact analysis.

Analyzes what happens if a ScheduleSlot is moved to a new time —
BEFORE applying the move. The admin sees the result and decides.

Functions:
  analyze_impact(slot_id, new_start, new_end, planning_group_id, db) → ImpactResponse
"""

from datetime import datetime
from sqlalchemy.orm import Session

from models.schedule      import ScheduleSlot
from Services.PlanningManagement.schemas.impact_analysis import (
    ImpactRequest, ImpactResponse, ImpactConflict, AffectedSession
)


def analyze_impact(
    slot_id:           int,
    body:              ImpactRequest,
    db:                Session,
) -> ImpactResponse:
    """
    Analyzes the impact of moving a slot to a new time without modifying the DB.

    Steps:
      1. Load the slot being moved
      2. Load all other slots in the same planning batch
      3. Check for trainer / room / group conflicts at the proposed new time
      4. Check which existing conflicts (if any) would be resolved
      5. List sessions that share a resource with the moved slot

    Args:
        slot_id: DB id of the slot to move
        body:    ImpactRequest with proposed new_start_time / new_end_time
        db:      SQLAlchemy session

    Returns:
        ImpactResponse
    """
    # ── Load the target slot ──────────────────────────────────────────────────
    slot = db.query(ScheduleSlot).filter(ScheduleSlot.id == slot_id).first()
    if not slot:
        raise ValueError(f"ScheduleSlot id={slot_id} not found.")

    # Parse proposed times
    new_start = datetime.fromisoformat(body.new_start_time)
    new_end   = datetime.fromisoformat(body.new_end_time)

    # ── Load all other slots in scope ─────────────────────────────────────────
    query = db.query(ScheduleSlot).filter(ScheduleSlot.id != slot_id)

    if body.planning_group_id:
        query = query.filter(
            ScheduleSlot.planning_group_id == body.planning_group_id,
            ScheduleSlot.status != "rejected",
        )
    else:
        query = query.filter(ScheduleSlot.status != "rejected")

    other_slots = query.all()

    # ── Helper: time overlap ──────────────────────────────────────────────────
    def overlaps(s: ScheduleSlot, start: datetime, end: datetime) -> bool:
        return s.start_time < end and start < s.end_time

    def slot_info(s: ScheduleSlot) -> dict:
        return {
            "slot_id":      s.id,
            "course_title": s.course.title     if s.course       else f"course_{s.course_id}",
            "trainer_name": s.trainer.name     if s.trainer      else f"trainer_{s.trainer_id}",
            "room_name":    s.room.name        if s.room         else f"room_{s.room_id}",
            "group_name":   s.learner_group.name if s.learner_group else f"group_{s.learner_group_id}",
            "start_time":   s.start_time.isoformat() if s.start_time else "",
            "end_time":     s.end_time.isoformat()   if s.end_time   else "",
        }

    # ── NEW conflicts after the move ──────────────────────────────────────────
    new_conflicts: list[ImpactConflict] = []

    for other in other_slots:
        if not overlaps(other, new_start, new_end):
            continue   # no time overlap → no conflict possible

        info = slot_info(other)

        if other.trainer_id == slot.trainer_id:
            new_conflicts.append(ImpactConflict(
                conflict_type = "trainer",
                slot_id       = other.id,
                course_title  = info["course_title"],
                trainer_name  = info["trainer_name"],
                room_name     = info["room_name"],
                group_name    = info["group_name"],
                start_time    = info["start_time"],
                end_time      = info["end_time"],
                description   = (
                    f"Trainer '{info['trainer_name']}' already teaches "
                    f"'{info['course_title']}' at the proposed time."
                ),
            ))

        if other.room_id == slot.room_id:
            new_conflicts.append(ImpactConflict(
                conflict_type = "room",
                slot_id       = other.id,
                course_title  = info["course_title"],
                trainer_name  = info["trainer_name"],
                room_name     = info["room_name"],
                group_name    = info["group_name"],
                start_time    = info["start_time"],
                end_time      = info["end_time"],
                description   = (
                    f"Room '{info['room_name']}' is already used by "
                    f"'{info['course_title']}' at the proposed time."
                ),
            ))

        if other.learner_group_id == slot.learner_group_id:
            new_conflicts.append(ImpactConflict(
                conflict_type = "group",
                slot_id       = other.id,
                course_title  = info["course_title"],
                trainer_name  = info["trainer_name"],
                room_name     = info["room_name"],
                group_name    = info["group_name"],
                start_time    = info["start_time"],
                end_time      = info["end_time"],
                description   = (
                    f"Group '{info['group_name']}' already has '{info['course_title']}' "
                    f"at the proposed time."
                ),
            ))

    # ── RESOLVED conflicts (existed at current time, disappear after move) ────
    resolved_conflicts: list[ImpactConflict] = []
    old_start = slot.start_time
    old_end   = slot.end_time

    for other in other_slots:
        if not overlaps(other, old_start, old_end):
            continue

        info = slot_info(other)
        if other.trainer_id == slot.trainer_id or \
           other.room_id    == slot.room_id    or \
           other.learner_group_id == slot.learner_group_id:

            resolved_conflicts.append(ImpactConflict(
                conflict_type = "resolved",
                slot_id       = other.id,
                course_title  = info["course_title"],
                trainer_name  = info["trainer_name"],
                room_name     = info["room_name"],
                group_name    = info["group_name"],
                start_time    = info["start_time"],
                end_time      = info["end_time"],
                description   = f"Conflict with '{info['course_title']}' resolved by this move.",
            ))

    # ── Affected sessions (share trainer/room/group, not necessarily in conflict) ──
    affected: list[AffectedSession] = []
    for other in other_slots:
        relations = []
        if other.trainer_id      == slot.trainer_id:      relations.append("same_trainer")
        if other.room_id         == slot.room_id:         relations.append("same_room")
        if other.learner_group_id == slot.learner_group_id: relations.append("same_group")
        if not relations:
            continue
        info = slot_info(other)
        affected.append(AffectedSession(
            slot_id      = other.id,
            course_title = info["course_title"],
            trainer_name = info["trainer_name"],
            room_name    = info["room_name"],
            start_time   = info["start_time"],
            end_time     = info["end_time"],
            relation     = " + ".join(relations),
        ))

    # ── Build response ────────────────────────────────────────────────────────
    is_safe = len(new_conflicts) == 0
    summary = (
        f"Moving '{slot.course.title if slot.course else 'session'}' "
        f"to {new_start.strftime('%A %d/%m %H:%M')} → {new_end.strftime('%H:%M')}. "
        f"{'No conflicts.' if is_safe else f'{len(new_conflicts)} conflict(s) detected.'}"
    )
    recommendation = (
        "✅ Safe to move — no conflicts detected."
        if is_safe else
        "⚠️ Conflicts detected. Resolve them or choose a different slot."
    )

    return ImpactResponse(
        slot_id            = slot_id,
        course_title       = slot.course.title if slot.course else f"course_{slot.course_id}",
        proposed_start     = new_start.isoformat(),
        proposed_end       = new_end.isoformat(),
        is_safe            = is_safe,
        new_conflicts      = new_conflicts,
        resolved_conflicts = resolved_conflicts,
        affected_sessions  = affected,
        summary            = summary,
        recommendation     = recommendation,
    )