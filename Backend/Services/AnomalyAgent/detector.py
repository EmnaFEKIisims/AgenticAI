"""
Services/AnomalyAgent/detector.py
===================================
Core anomaly detector.

Receives a planning (list of session dicts from PlanningAgent)
and returns a list of detected anomaly dicts.

Each detection function is independent:
  detect_trainer_conflicts()  → same trainer, same time slot
  detect_room_conflicts()     → same room, same time slot
  detect_learner_conflicts()  → same group, two sessions at same time
  detect_equipment_conflicts()→ required equipment not available
  detect_overload()           → trainer or group exceeds daily hours
  detect_capacity()           → room too small for group
  detect_invalid_slots()      → session outside allowed hours / forbidden day
"""

from collections import defaultdict
from datetime import datetime


# =============================================================================
#  CONSTANTS
# =============================================================================

MAX_TRAINER_HOURS_PER_DAY = 6.0
MAX_LEARNER_HOURS_PER_DAY = 6.0
FORBIDDEN_DAYS            = []     # loaded from DB constraints at runtime
ALLOWED_START_HOUR        = 8
ALLOWED_END_HOUR          = 18


# =============================================================================
#  HELPERS
# =============================================================================

def _parse_dt(iso_str: str) -> datetime:
    try:
        return datetime.fromisoformat(iso_str)
    except Exception:
        return datetime(2000, 1, 1)


def _duration_hours(session: dict) -> float:
    start = _parse_dt(session.get("start_time", ""))
    end   = _parse_dt(session.get("end_time",   ""))
    delta = (end - start).total_seconds()
    return max(0.0, delta / 3600)


def _day_key(session: dict) -> str:
    """Returns 'YYYY-MM-DD' from start_time."""
    try:
        return _parse_dt(session["start_time"]).strftime("%Y-%m-%d")
    except Exception:
        return session.get("suggested_day", "unknown")


def _slots_overlap(s1: dict, s2: dict) -> bool:
    """Returns True if two sessions overlap in time."""
    s1_start = _parse_dt(s1.get("start_time", ""))
    s1_end   = _parse_dt(s1.get("end_time",   ""))
    s2_start = _parse_dt(s2.get("start_time", ""))
    s2_end   = _parse_dt(s2.get("end_time",   ""))
    return s1_start < s2_end and s2_start < s1_end


def _anomaly(anomaly_type: str, severity: str, title: str,
             description: str, details: dict,
             planning_id: int = None,
             slot_id: int     = None,
             recommendation:  str = "") -> dict:
    return {
        "anomaly_type":   anomaly_type,
        "severity":       severity,
        "title":          title,
        "description":    description,
        "details":        details,
        "impact":         None,
        "recommendation": recommendation,
        "planning_id":    planning_id,
        "schedule_slot_id": slot_id,
    }


# =============================================================================
#  DETECTION FUNCTIONS
# =============================================================================

def detect_trainer_conflicts(schedule: list[dict]) -> list[dict]:
    """
    Detects cases where the same trainer is assigned to two overlapping sessions.
    """
    anomalies = []
    by_trainer: dict[int, list[dict]] = defaultdict(list)
    for s in schedule:
        if s.get("trainer_id"):
            by_trainer[s["trainer_id"]].append(s)

    for trainer_id, sessions in by_trainer.items():
        for i in range(len(sessions)):
            for j in range(i + 1, len(sessions)):
                if _slots_overlap(sessions[i], sessions[j]):
                    anomalies.append(_anomaly(
                        anomaly_type   = "trainer_conflict",
                        severity       = "high",
                        title          = f"Trainer double-booking: {sessions[i].get('trainer_name', trainer_id)}",
                        description    = (
                            f"Trainer '{sessions[i].get('trainer_name')}' is assigned to "
                            f"'{sessions[i].get('course_title')}' and "
                            f"'{sessions[j].get('course_title')}' at the same time."
                        ),
                        details        = {
                            "trainer_id":   trainer_id,
                            "trainer_name": sessions[i].get("trainer_name"),
                            "session_1":    sessions[i].get("session_number"),
                            "session_2":    sessions[j].get("session_number"),
                            "start_time":   sessions[i].get("start_time"),
                        },
                        slot_id        = sessions[i].get("id"),
                        recommendation = "Assign one of the sessions to a different trainer or time slot.",
                    ))
    return anomalies


def detect_room_conflicts(schedule: list[dict]) -> list[dict]:
    """
    Detects cases where the same room hosts two overlapping sessions.
    """
    anomalies = []
    by_room: dict[int, list[dict]] = defaultdict(list)
    for s in schedule:
        if s.get("room_id"):
            by_room[s["room_id"]].append(s)

    for room_id, sessions in by_room.items():
        for i in range(len(sessions)):
            for j in range(i + 1, len(sessions)):
                if _slots_overlap(sessions[i], sessions[j]):
                    anomalies.append(_anomaly(
                        anomaly_type   = "room_conflict",
                        severity       = "high",
                        title          = f"Room double-booking: {sessions[i].get('room_name', room_id)}",
                        description    = (
                            f"Room '{sessions[i].get('room_name')}' is booked for "
                            f"'{sessions[i].get('course_title')}' and "
                            f"'{sessions[j].get('course_title')}' simultaneously."
                        ),
                        details        = {
                            "room_id":    room_id,
                            "room_name":  sessions[i].get("room_name"),
                            "session_1":  sessions[i].get("session_number"),
                            "session_2":  sessions[j].get("session_number"),
                            "start_time": sessions[i].get("start_time"),
                        },
                        slot_id        = sessions[i].get("id"),
                        recommendation = "Move one session to a different room or time slot.",
                    ))
    return anomalies


def detect_learner_conflicts(schedule: list[dict]) -> list[dict]:
    """
    Detects cases where the same learner group has two overlapping sessions.
    """
    anomalies = []
    by_group: dict[int, list[dict]] = defaultdict(list)
    for s in schedule:
        if s.get("learner_group_id"):
            by_group[s["learner_group_id"]].append(s)

    for group_id, sessions in by_group.items():
        for i in range(len(sessions)):
            for j in range(i + 1, len(sessions)):
                if _slots_overlap(sessions[i], sessions[j]):
                    anomalies.append(_anomaly(
                        anomaly_type   = "learner_conflict",
                        severity       = "high",
                        title          = f"Group overlap: {sessions[i].get('group_name', group_id)}",
                        description    = (
                            f"Group '{sessions[i].get('group_name')}' is scheduled in "
                            f"'{sessions[i].get('course_title')}' and "
                            f"'{sessions[j].get('course_title')}' at the same time."
                        ),
                        details        = {
                            "group_id":   group_id,
                            "group_name": sessions[i].get("group_name"),
                            "session_1":  sessions[i].get("session_number"),
                            "session_2":  sessions[j].get("session_number"),
                        },
                        slot_id        = sessions[i].get("id"),
                        recommendation = "Stagger the two sessions to different time slots.",
                    ))
    return anomalies


def detect_equipment_conflicts(schedule: list[dict], equipment_data: list[dict] = None) -> list[dict]:
    """
    Detects cases where required equipment is overbooked.
    equipment_data = [{"name": "Projector", "total_quantity": 2}, ...]
    """
    if not equipment_data:
        return []

    anomalies = []
    equipment_map = {e["name"]: e["total_quantity"] for e in equipment_data}

    # Count concurrent equipment usage per time slot
    # Group sessions by overlapping time windows
    for equip_name, total_qty in equipment_map.items():
        needing = [
            s for s in schedule
            if equip_name in (s.get("required_equipments") or [])
        ]
        for i in range(len(needing)):
            concurrent = [
                s for s in needing[i + 1:]
                if _slots_overlap(needing[i], s)
            ]
            if len(concurrent) >= total_qty:
                anomalies.append(_anomaly(
                    anomaly_type   = "equipment_conflict",
                    severity       = "medium",
                    title          = f"Equipment overbooked: {equip_name}",
                    description    = (
                        f"'{equip_name}' (qty={total_qty}) is required by "
                        f"{len(concurrent) + 1} concurrent sessions."
                    ),
                    details        = {
                        "equipment":       equip_name,
                        "total_quantity":  total_qty,
                        "concurrent_count": len(concurrent) + 1,
                    },
                    recommendation = f"Stagger sessions requiring '{equip_name}' or procure more units.",
                ))
    return anomalies


def detect_overload(schedule: list[dict]) -> list[dict]:
    """
    Detects trainers or groups with more than MAX hours in a single day.
    """
    anomalies = []

    # Trainer daily hours
    trainer_day: dict[tuple, float] = defaultdict(float)
    for s in schedule:
        key = (s.get("trainer_id"), _day_key(s))
        trainer_day[key] += _duration_hours(s)

    for (trainer_id, day), hours in trainer_day.items():
        if hours > MAX_TRAINER_HOURS_PER_DAY:
            name = next((s.get("trainer_name") for s in schedule
                         if s.get("trainer_id") == trainer_id), str(trainer_id))
            anomalies.append(_anomaly(
                anomaly_type   = "teacher_overload",
                severity       = "high",
                title          = f"Trainer overloaded: {name}",
                description    = f"Trainer '{name}' has {round(hours, 1)}h on {day} (limit: {MAX_TRAINER_HOURS_PER_DAY}h).",
                details        = {"trainer_id": trainer_id, "trainer_name": name, "day": day, "hours": round(hours, 2)},
                recommendation = f"Move some sessions to another day to stay under {MAX_TRAINER_HOURS_PER_DAY}h/day.",
            ))

    # Learner group daily hours
    group_day: dict[tuple, float] = defaultdict(float)
    for s in schedule:
        key = (s.get("learner_group_id"), _day_key(s))
        group_day[key] += _duration_hours(s)

    for (group_id, day), hours in group_day.items():
        if hours > MAX_LEARNER_HOURS_PER_DAY:
            name = next((s.get("group_name") for s in schedule
                         if s.get("learner_group_id") == group_id), str(group_id))
            anomalies.append(_anomaly(
                anomaly_type   = "workload_exceeded",
                severity       = "high",
                title          = f"Group overloaded: {name}",
                description    = f"Group '{name}' has {round(hours, 1)}h on {day} (limit: {MAX_LEARNER_HOURS_PER_DAY}h).",
                details        = {"group_id": group_id, "group_name": name, "day": day, "hours": round(hours, 2)},
                recommendation = f"Spread sessions across multiple days.",
            ))

    return anomalies


def detect_capacity(schedule: list[dict], groups: list[dict] = None, rooms: list[dict] = None) -> list[dict]:
    """
    Detects sessions where room capacity < group size.
    """
    if not groups or not rooms:
        return []

    anomalies   = []
    group_map   = {g["id"]: g for g in groups}
    room_map    = {r["id"]: r for r in rooms}

    for s in schedule:
        group = group_map.get(s.get("learner_group_id"))
        room  = room_map.get(s.get("room_id"))
        if not group or not room:
            continue
        if room["capacity"] < group["size"]:
            anomalies.append(_anomaly(
                anomaly_type   = "room_capacity_insufficient",
                severity       = "medium",
                title          = f"Room too small: {room.get('name')}",
                description    = (
                    f"Room '{room.get('name')}' (cap={room['capacity']}) is too small "
                    f"for group '{group.get('name')}' (size={group['size']})."
                ),
                details        = {
                    "room_id":       room["id"],
                    "room_name":     room.get("name"),
                    "room_capacity": room["capacity"],
                    "group_id":      group["id"],
                    "group_name":    group.get("name"),
                    "group_size":    group["size"],
                },
                slot_id        = s.get("id"),
                recommendation = f"Assign a room with capacity ≥ {group['size']}.",
            ))

    return anomalies


def detect_invalid_slots(schedule: list[dict], forbidden_days: list[str] = None) -> list[dict]:
    """
    Detects sessions on forbidden days or outside allowed hours.
    """
    anomalies  = []
    forbidden  = [d.lower() for d in (forbidden_days or FORBIDDEN_DAYS)]

    for s in schedule:
        start_dt  = _parse_dt(s.get("start_time", ""))
        end_dt    = _parse_dt(s.get("end_time",   ""))
        weekday   = start_dt.strftime("%A").lower()

        if weekday in forbidden:
            anomalies.append(_anomaly(
                anomaly_type   = "other",
                severity       = "high",
                title          = f"Session on forbidden day: {weekday.capitalize()}",
                description    = (
                    f"Session #{s.get('session_number')} ({s.get('course_title')}) "
                    f"is scheduled on {weekday.capitalize()} which is forbidden."
                ),
                details        = {"session": s.get("session_number"), "day": weekday, "date": str(start_dt.date())},
                slot_id        = s.get("id"),
                recommendation = "Reschedule to an allowed weekday.",
            ))

        if start_dt.hour < ALLOWED_START_HOUR:
            anomalies.append(_anomaly(
                anomaly_type   = "other",
                severity       = "medium",
                title          = f"Session starts too early: {start_dt.strftime('%H:%M')}",
                description    = f"Session #{s.get('session_number')} starts at {start_dt.strftime('%H:%M')} before {ALLOWED_START_HOUR:02d}:00.",
                details        = {"session": s.get("session_number"), "start": str(start_dt)},
                slot_id        = s.get("id"),
                recommendation = f"Move session start to {ALLOWED_START_HOUR:02d}:00 or later.",
            ))

        if end_dt.hour > ALLOWED_END_HOUR:
            anomalies.append(_anomaly(
                anomaly_type   = "other",
                severity       = "medium",
                title          = f"Session ends too late: {end_dt.strftime('%H:%M')}",
                description    = f"Session #{s.get('session_number')} ends at {end_dt.strftime('%H:%M')} after {ALLOWED_END_HOUR:02d}:00.",
                details        = {"session": s.get("session_number"), "end": str(end_dt)},
                slot_id        = s.get("id"),
                recommendation = f"End session by {ALLOWED_END_HOUR:02d}:00.",
            ))

    return anomalies


# =============================================================================
#  MASTER DETECTOR
# =============================================================================

def detect_all(
    schedule:       list[dict],
    planning_id:    int          = None,
    groups:         list[dict]   = None,
    rooms:          list[dict]   = None,
    equipment_data: list[dict]   = None,
    forbidden_days: list[str]    = None,
) -> list[dict]:
    """
    Runs all detection functions and returns the combined list of anomaly dicts.
    Each dict is ready to be passed to AnomalyCreate schema.

    Args:
        schedule:       list of session dicts from PlanningAgent
        planning_id:    id of the planning being checked
        groups:         list of group dicts (for capacity check)
        rooms:          list of room dicts (for capacity check)
        equipment_data: list of equipment dicts (for equipment conflict check)
        forbidden_days: list of day names to check against

    Returns:
        list[dict] — one dict per detected anomaly
    """
    all_anomalies = []

    print(f"  [Detector] Analyzing {len(schedule)} sessions...")

    all_anomalies += detect_trainer_conflicts(schedule)
    all_anomalies += detect_room_conflicts(schedule)
    all_anomalies += detect_learner_conflicts(schedule)
    all_anomalies += detect_equipment_conflicts(schedule, equipment_data)
    all_anomalies += detect_overload(schedule)
    all_anomalies += detect_capacity(schedule, groups, rooms)
    all_anomalies += detect_invalid_slots(schedule, forbidden_days)

    # Attach planning_id to all
    for a in all_anomalies:
        a["planning_id"] = planning_id

    print(f"  [Detector] {len(all_anomalies)} anomaly(ies) detected.")
    return all_anomalies