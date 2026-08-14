"""
Services/AnomalyAgent/resolver.py
===================================
Proposes concrete solutions for each detected anomaly.

⚠️  IMPORTANT: The resolver NEVER modifies the planning automatically.
It only returns a list of suggested solutions.
The admin must review and apply them via HITL.

Input:  anomaly dict + current schedule
Output: list of Resolution proposals

Example:
  Anomaly: trainer_overload (Ahmed, Monday 8h)
  →  [
       Resolution("Move S10 to Tuesday 14:00"),
       Resolution("Move S10 to Wednesday 10:00"),
       Resolution("Assign session to trainer Sara"),
     ]
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict


# =============================================================================
#  RESOLUTION TYPE
# =============================================================================

@dataclass
class Resolution:
    action:         str            # "move_session" | "change_trainer" | "change_room" | "split_session"
    description:    str            # Human-readable suggestion
    priority:       int = 1        # 1 = best, 2 = good, 3 = possible
    details:        dict = field(default_factory=dict)
    estimated_impact: str = ""     # e.g. "Resolves overload on Monday"
    requires_hitl:  bool = True    # Always True — no automatic changes


# =============================================================================
#  HELPERS
# =============================================================================

def _parse_dt(iso_str: str) -> datetime:
    try:
        return datetime.fromisoformat(iso_str)
    except Exception:
        return datetime(2000, 1, 1)

def _fmt_slot(dt: datetime) -> str:
    return dt.strftime("%A %H:%M")

def _trainer_busy_slots(schedule: list[dict], trainer_id: int) -> set[str]:
    """Returns set of 'YYYY-MM-DD HH:MM' strings when trainer is busy."""
    busy = set()
    for s in schedule:
        if s.get("trainer_id") == trainer_id:
            busy.add(s.get("start_time", "")[:16])
    return busy

def _room_busy_slots(schedule: list[dict], room_id: int) -> set[str]:
    busy = set()
    for s in schedule:
        if s.get("room_id") == room_id:
            busy.add(s.get("start_time", "")[:16])
    return busy

def _available_trainers(schedule: list[dict], exclude_id: int) -> list[dict]:
    """Returns unique trainers in the schedule excluding the given trainer."""
    seen = set()
    trainers = []
    for s in schedule:
        tid = s.get("trainer_id")
        if tid and tid != exclude_id and tid not in seen:
            seen.add(tid)
            trainers.append({"id": tid, "name": s.get("trainer_name", str(tid))})
    return trainers

def _available_rooms(schedule: list[dict], exclude_id: int, min_capacity: int = 0) -> list[dict]:
    seen = set()
    rooms = []
    for s in schedule:
        rid = s.get("room_id")
        if rid and rid != exclude_id and rid not in seen:
            seen.add(rid)
            rooms.append({"id": rid, "name": s.get("room_name", str(rid))})
    return rooms


# =============================================================================
#  RESOLUTION STRATEGIES
# =============================================================================

def _resolve_trainer_conflict(anomaly: dict, schedule: list[dict]) -> list[Resolution]:
    details  = anomaly.get("details", {})
    trainer  = details.get("trainer_name", "?")
    alt_trainers = _available_trainers(schedule, exclude_id=details.get("trainer_id", -1))

    resolutions = [
        Resolution(
            action      = "move_session",
            description = f"Move one of the conflicting sessions to a different time slot.",
            priority    = 1,
            details     = {"anomaly": anomaly.get("title")},
            estimated_impact = "Resolves trainer double-booking.",
        )
    ]
    for t in alt_trainers[:2]:
        resolutions.append(Resolution(
            action      = "change_trainer",
            description = f"Assign session to trainer '{t['name']}' instead of '{trainer}'.",
            priority    = 2,
            details     = {"new_trainer_id": t["id"], "new_trainer_name": t["name"]},
            estimated_impact = "Resolves conflict by changing trainer assignment.",
        ))
    return resolutions


def _resolve_room_conflict(anomaly: dict, schedule: list[dict]) -> list[Resolution]:
    details = anomaly.get("details", {})
    room    = details.get("room_name", "?")
    alt_rooms = _available_rooms(schedule, exclude_id=details.get("room_id", -1))

    resolutions = [
        Resolution(
            action      = "move_session",
            description = f"Move one of the conflicting sessions to a different time slot.",
            priority    = 1,
            details     = {"anomaly": anomaly.get("title")},
            estimated_impact = "Resolves room double-booking.",
        )
    ]
    for r in alt_rooms[:2]:
        resolutions.append(Resolution(
            action      = "change_room",
            description = f"Move one session to room '{r['name']}' instead of '{room}'.",
            priority    = 2,
            details     = {"new_room_id": r["id"], "new_room_name": r["name"]},
            estimated_impact = "Resolves conflict by using a different room.",
        ))
    return resolutions


def _resolve_learner_conflict(anomaly: dict, schedule: list[dict]) -> list[Resolution]:
    return [
        Resolution(
            action      = "move_session",
            description = "Move one of the overlapping group sessions to a non-overlapping time slot.",
            priority    = 1,
            details     = {"anomaly": anomaly.get("title")},
            estimated_impact = "Learner group no longer has two concurrent sessions.",
        )
    ]


def _resolve_overload(anomaly: dict, schedule: list[dict]) -> list[Resolution]:
    details      = anomaly.get("details", {})
    entity_name  = details.get("trainer_name") or details.get("group_name") or "?"
    day          = details.get("day", "?")
    hours        = details.get("hours", 0)

    # Find sessions on that day for this entity
    trainer_id = details.get("trainer_id")
    group_id   = details.get("group_id")

    candidates = [
        s for s in schedule
        if (trainer_id and s.get("trainer_id") == trainer_id) or
           (group_id   and s.get("learner_group_id") == group_id)
    ]

    # Suggest other days in the same week
    try:
        day_dt = datetime.strptime(day, "%Y-%m-%d")
        other_days = [
            (day_dt + timedelta(days=i)).strftime("%A %d/%m")
            for i in range(1, 6)
            if (day_dt + timedelta(days=i)).weekday() < 5   # Mon-Fri only
        ]
    except Exception:
        other_days = ["Tuesday", "Wednesday", "Thursday"]

    resolutions = []
    for d in other_days[:2]:
        resolutions.append(Resolution(
            action      = "move_session",
            description = f"Move one session from {day} to {d} to reduce load for '{entity_name}'.",
            priority    = 1,
            details     = {"target_day": d, "current_hours": hours},
            estimated_impact = f"Reduces daily load for '{entity_name}' on {day}.",
        ))

    if trainer_id:
        alt_trainers = _available_trainers(schedule, exclude_id=trainer_id)
        for t in alt_trainers[:1]:
            resolutions.append(Resolution(
                action      = "change_trainer",
                description = f"Reassign one session to trainer '{t['name']}' to lighten '{entity_name}'s load.",
                priority    = 2,
                details     = {"new_trainer_id": t["id"], "new_trainer_name": t["name"]},
                estimated_impact = "Balances workload between trainers.",
            ))

    return resolutions


def _resolve_capacity(anomaly: dict, schedule: list[dict]) -> list[Resolution]:
    details = anomaly.get("details", {})
    room    = details.get("room_name", "?")
    size    = details.get("group_size", 0)
    alt_rooms = _available_rooms(schedule, exclude_id=details.get("room_id", -1))

    resolutions = [
        Resolution(
            action      = "change_room",
            description = f"Assign a room with capacity ≥ {size} instead of '{room}'.",
            priority    = 1,
            details     = {"required_capacity": size},
            estimated_impact = "Ensures adequate space for the learner group.",
        )
    ]
    for r in alt_rooms[:2]:
        resolutions.append(Resolution(
            action      = "change_room",
            description = f"Use room '{r['name']}' for this session.",
            priority    = 2,
            details     = {"new_room_id": r["id"], "new_room_name": r["name"]},
            estimated_impact = "Room change resolves capacity issue.",
        ))
    return resolutions


def _resolve_generic(anomaly: dict) -> list[Resolution]:
    return [
        Resolution(
            action      = "move_session",
            description = f"Review and reschedule: {anomaly.get('title', 'anomaly')}.",
            priority    = 3,
            details     = {},
            estimated_impact = anomaly.get("recommendation", ""),
        )
    ]


# =============================================================================
#  MAIN RESOLVER
# =============================================================================

_RESOLVERS = {
    "trainer_conflict":          _resolve_trainer_conflict,
    "room_conflict":             _resolve_room_conflict,
    "learner_conflict":          _resolve_learner_conflict,
    "teacher_overload":          _resolve_overload,
    "workload_exceeded":         _resolve_overload,
    "room_capacity_insufficient":_resolve_capacity,
}


def resolve(anomaly: dict, schedule: list[dict]) -> list[Resolution]:
    """
    Proposes solutions for a single anomaly.
    Never modifies the schedule — returns proposals only.
    """
    raw_type = anomaly.get("anomaly_type", "other")
    resolver_fn = _RESOLVERS.get(raw_type)

    if resolver_fn:
        resolutions = resolver_fn(anomaly, schedule)
    else:
        resolutions = _resolve_generic(anomaly)

    # Always add the "manual review" fallback
    resolutions.append(Resolution(
        action      = "manual_review",
        description = "Review this anomaly manually and apply a custom fix.",
        priority    = 9,
        details     = {},
        estimated_impact = "Admin determines the appropriate action.",
    ))

    return resolutions


def resolve_all(anomalies: list[dict], schedule: list[dict]) -> dict[int, list[Resolution]]:
    """
    Proposes solutions for all anomalies.
    Returns a dict keyed by anomaly index.
    """
    return {i: resolve(a, schedule) for i, a in enumerate(anomalies)}