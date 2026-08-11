"""
validators/teacher_validator.py
=================================
Validates trainer workload and availability.

Rules (from pedagogical_rules.json "teacher_workload" section):
  - max_daily_hours_per_teacher   : max teaching hours per trainer per day
  - max_consecutive_hours_teacher : max consecutive hours before trainer needs a break
"""

from collections import defaultdict

from models.criterion_result import CriterionResult, Severity, passed, partial
from Services.PedagogicalAgent.Schemas.Planning_schema import Planning, Session
from utils.rule_loader         import get_value


MAX_DAILY_HOURS       = get_value("teacher_workload", "max_daily_hours_per_teacher",    default=6.0)
MAX_CONSEC_HOURS      = get_value("teacher_workload", "max_consecutive_hours_teacher",  default=3.0)
WEIGHT                = get_value("teacher_workload", "weight",                         default=10)
ISO_REF               = "ISO 21001:2018 §7.1.2 / ISO 29993:2017 §5.2"


# =============================================================================
#  RULE 1 — Daily teacher load
# =============================================================================

def check_teacher_load(planning: Planning) -> CriterionResult:
    """
    Checks that no trainer teaches more than max_daily_hours_per_teacher in a day.
    """
    # Build: teacher → day → total_hours
    teacher_day_hours: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for s in planning.sessions:
        hours = (s.duration_minutes or 0) / 60
        teacher_day_hours[s.teacher][s.day.value] += hours

    violations = []
    for teacher, day_map in teacher_day_hours.items():
        for day, hours in day_map.items():
            if hours > MAX_DAILY_HOURS:
                violations.append({
                    "teacher": teacher,
                    "day":     day,
                    "hours":   round(hours, 2),
                    "limit":   MAX_DAILY_HOURS,
                    "over":    round(hours - MAX_DAILY_HOURS, 2),
                })

    total_combos = sum(len(dm) for dm in teacher_day_hours.values())
    ok_combos    = total_combos - len(violations)
    score        = (ok_combos / total_combos) * WEIGHT if total_combos else WEIGHT

    if not violations:
        return passed(
            rule          = "Trainer daily workload",
            weight        = WEIGHT,
            message       = f"All trainers stay within the {MAX_DAILY_HOURS}h/day limit.",
            iso_reference = ISO_REF,
        )

    ex = violations[0]
    return partial(
        rule           = "Trainer daily workload",
        weight         = WEIGHT,
        score          = round(score, 2),
        severity       = Severity.MEDIUM,
        message        = f"{len(violations)} trainer-day combination(s) exceed {MAX_DAILY_HOURS}h. "
                         f"Example: {ex['teacher']} on {ex['day']} ({ex['hours']}h).",
        recommendation = f"Redistribute sessions so no trainer teaches more than {MAX_DAILY_HOURS}h/day.",
        iso_reference  = ISO_REF,
        details        = {"violations": violations},
    )


# =============================================================================
#  RULE 2 — Consecutive teaching hours per trainer
# =============================================================================

def check_availability(planning: Planning) -> CriterionResult:
    """
    Checks that no trainer teaches more than max_consecutive_hours_teacher
    without a sufficient break.
    """
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    MIN_BREAK = 15   # minutes — reuse from breaks config if preferred

    # Build per-teacher, per-day sorted session list
    teacher_day_sessions: dict[str, dict[str, list[Session]]] = defaultdict(lambda: defaultdict(list))
    for s in planning.sessions:
        teacher_day_sessions[s.teacher][s.day.value].append(s)

    violations = []
    MAX_CONSEC_MINUTES = MAX_CONSEC_HOURS * 60

    for teacher, day_map in teacher_day_sessions.items():
        for day, sessions in day_map.items():
            sorted_s = sorted(sessions, key=lambda s: s.start_minutes)

            block_minutes = (sorted_s[0].duration_minutes or 0)
            for i in range(1, len(sorted_s)):
                prev = sorted_s[i - 1]
                curr = sorted_s[i]
                gap  = curr.start_minutes - prev.end_minutes
                if gap >= MIN_BREAK:
                    block_minutes = curr.duration_minutes or 0
                else:
                    block_minutes += curr.duration_minutes or 0

                if block_minutes > MAX_CONSEC_MINUTES:
                    violations.append({
                        "teacher":       teacher,
                        "day":           day,
                        "block_hours":   round(block_minutes / 60, 2),
                        "limit_hours":   MAX_CONSEC_HOURS,
                    })
                    block_minutes = curr.duration_minutes or 0   # reset

    total_days = sum(len(dm) for dm in teacher_day_sessions.values())
    ok_days    = total_days - len(violations)
    score      = (ok_days / total_days) * WEIGHT if total_days else WEIGHT

    if not violations:
        return passed(
            rule          = "Trainer consecutive hours",
            weight        = WEIGHT,
            message       = f"No trainer teaches more than {MAX_CONSEC_HOURS}h consecutively.",
            iso_reference = ISO_REF,
        )

    ex = violations[0]
    return partial(
        rule           = "Trainer consecutive hours",
        weight         = WEIGHT,
        score          = round(score, 2),
        severity       = Severity.MEDIUM,
        message        = f"{len(violations)} instance(s) of consecutive overload. "
                         f"Example: {ex['teacher']} on {ex['day']} ({ex['block_hours']}h block).",
        recommendation = f"Insert breaks so trainers never teach more than {MAX_CONSEC_HOURS}h without a pause.",
        iso_reference  = ISO_REF,
        details        = {"violations": violations},
    )


# =============================================================================
#  MAIN ENTRY POINT
# =============================================================================

def validate(planning: Planning) -> list[CriterionResult]:
    return [
        check_teacher_load(planning),
        check_availability(planning),
    ]