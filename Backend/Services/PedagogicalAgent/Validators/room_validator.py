"""
validators/room_validator.py
==============================
Validates room suitability for each session.

Rules (from pedagogical_rules.json "room" section):
  - practice_requires_lab      : practice/lab sessions need a Lab room
  - min_room_capacity_ratio    : room capacity must cover at least X% of group size

Functions:
  check_capacity()   → room size vs group size
  check_resources()  → room type vs session type
  validate()         → runs both, returns list[CriterionResult]
"""

from models.criterion_result import CriterionResult, Severity, passed, failed, partial
from Services.PedagogicalAgent.Schemas.Planning_schema  import Planning, Session, SessionType, RoomType
from utils.rule_loader         import get_value


PRACTICE_REQUIRES_LAB   = get_value("room", "practice_requires_lab",        default=True)
MIN_CAPACITY_RATIO      = get_value("room", "min_room_capacity_ratio",       default=0.8)
WEIGHT                  = get_value("room", "weight",                        default=5)
ISO_REF                 = "ISO 21001:2018 §7.1.3"


# =============================================================================
#  RULE 1 — Room capacity vs group size
# =============================================================================

def check_capacity(planning: Planning) -> CriterionResult:
    """
    Checks that every session's room can fit the learner group.
    A session without group size info is skipped.

    Uses min_room_capacity_ratio: if ratio=0.8, a group of 25 needs
    a room with capacity >= 20 (80% of 25).
    """
    # Build group size map from planning context
    # Sessions carry room_type but not explicit capacity → we use hints from planning
    # If no capacity info is available we skip gracefully
    violations = []
    skipped    = 0

    for s in planning.sessions:
        # We can only check if both room and group context exist
        # Planning.from_schedule() doesn't always carry capacity numbers —
        # so we check what we have via session details
        details = getattr(s, "details", {}) or {}
        room_capacity = details.get("room_capacity")
        group_size    = details.get("group_size")

        if room_capacity is None or group_size is None:
            skipped += 1
            continue

        required = group_size * MIN_CAPACITY_RATIO
        if room_capacity < required:
            violations.append({
                "session":        f"{s.course} — {s.day.value} {s.start}",
                "room":           s.room,
                "room_capacity":  room_capacity,
                "group_size":     group_size,
                "required_min":   round(required, 0),
            })

    if skipped == len(planning.sessions):
        # No capacity data available — skip with a soft pass
        return passed(
            rule          = "Room capacity",
            weight        = WEIGHT,
            message       = "Room capacity data not available — check skipped.",
            iso_reference = ISO_REF,
        )

    total    = len(planning.sessions) - skipped
    ok       = total - len(violations)
    score    = (ok / total) * WEIGHT if total else WEIGHT

    if not violations:
        return passed(
            rule          = "Room capacity",
            weight        = WEIGHT,
            message       = f"All {total} session(s) have rooms with adequate capacity.",
            iso_reference = ISO_REF,
        )

    ex = violations[0]
    return partial(
        rule           = "Room capacity",
        weight         = WEIGHT,
        score          = round(score, 2),
        severity       = Severity.MEDIUM,
        message        = (
            f"{len(violations)} session(s) have undersized rooms. "
            f"Example: '{ex['room']}' (cap={ex['room_capacity']}) "
            f"for group size {ex['group_size']}."
        ),
        recommendation = f"Assign rooms with capacity ≥ {round(MIN_CAPACITY_RATIO * 100)}% of group size.",
        iso_reference  = ISO_REF,
        details        = {"violations": violations[:5]},
    )


# =============================================================================
#  RULE 2 — Room type vs session type (resources/equipment check)
# =============================================================================

def check_resources(planning: Planning) -> CriterionResult:
    """
    Checks that practice and lab sessions are held in Lab-type rooms.
    Theory sessions can use any room type.
    """
    if not PRACTICE_REQUIRES_LAB:
        return passed(
            rule          = "Room type suitability",
            weight        = WEIGHT,
            message       = "Room type check disabled in configuration.",
            iso_reference = ISO_REF,
        )

    violations = []
    practice_sessions = [
        s for s in planning.sessions
        if s.session_type in (SessionType.PRACTICE,)
    ]

    for s in practice_sessions:
        if s.room_type != RoomType.LAB:
            violations.append({
                "session":      f"{s.course} — {s.day.value} {s.start}",
                "session_type": s.session_type.value,
                "room":         s.room,
                "room_type":    s.room_type.value,
                "expected":     "lab",
            })

    total = len(practice_sessions)
    if total == 0:
        return passed(
            rule          = "Room type suitability",
            weight        = WEIGHT,
            message       = "No practice sessions found — room type check not applicable.",
            iso_reference = ISO_REF,
        )

    ok    = total - len(violations)
    score = (ok / total) * WEIGHT

    if not violations:
        return passed(
            rule          = "Room type suitability",
            weight        = WEIGHT,
            message       = f"All {total} practice session(s) use Lab-type rooms.",
            iso_reference = ISO_REF,
        )

    ex = violations[0]
    return partial(
        rule           = "Room type suitability",
        weight         = WEIGHT,
        score          = round(score, 2),
        severity       = Severity.LOW,
        message        = (
            f"{len(violations)}/{total} practice session(s) are not in a Lab room. "
            f"Example: '{ex['course'] if 'course' in ex else ex['session']}' in '{ex['room']}' ({ex['room_type']})."
        ),
        recommendation = "Assign Lab-type rooms to all practice and hands-on sessions.",
        iso_reference  = ISO_REF,
        details        = {"violations": violations[:5]},
    )


# =============================================================================
#  MAIN ENTRY POINT
# =============================================================================

def validate(planning: Planning) -> list[CriterionResult]:
    return [
        check_capacity(planning),
        check_resources(planning),
    ]