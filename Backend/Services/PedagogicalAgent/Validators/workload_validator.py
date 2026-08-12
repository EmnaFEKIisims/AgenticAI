"""
validators/workload_validator.py
==================================
Validates cognitive and time load per day and per week.

Rules (from pedagogical_rules.json "workload" section):
  - max_daily_hours           : total hours per learner per day
  - max_weekly_hours          : total hours per learner per week
  - max_consecutive_hours     : hours before a mandatory break
  - max_hard_courses_per_day  : max cognitively demanding sessions per day
"""

from models.criterion_result import CriterionResult, Severity, passed, failed, partial
from Services.PedagogicalAgent.Schemas.Planning_schema import Planning
from utils.rule_loader         import get_value


# =============================================================================
#  RULE CONSTANTS  (loaded from pedagogical_rules.json)
# =============================================================================

MAX_DAILY_HOURS          = get_value("workload", "max_daily_hours",          default=6.0)
MAX_WEEKLY_HOURS         = get_value("workload", "max_weekly_hours",          default=30.0)
MAX_CONSECUTIVE_HOURS    = get_value("workload", "max_consecutive_hours",     default=3.0)
MAX_HARD_COURSES_PER_DAY = get_value("workload", "max_hard_courses_per_day", default=2)
WEIGHT                   = get_value("workload", "weight",                   default=25)
ISO_REF                  = "ISO 21001:2018 §8.3"


# =============================================================================
#  RULE 1 — Daily workload
# =============================================================================

def validate_daily_workload(planning: Planning) -> CriterionResult:
    """
    Checks that no single day exceeds max_daily_hours.
    Returns a partial score proportional to compliant days.
    """
    violations = []

    for day in planning.days:
        hours = day.total_hours
        if hours > MAX_DAILY_HOURS:
            violations.append({
                "day":   day.day.value,
                "hours": round(hours, 2),
                "limit": MAX_DAILY_HOURS,
                "over":  round(hours - MAX_DAILY_HOURS, 2),
            })

    total_days = len(planning.days)
    if total_days == 0:
        return passed("Maximum daily workload", weight=WEIGHT,
                      message="No sessions to evaluate.", iso_reference=ISO_REF)

    ok_days = total_days - len(violations)
    score   = (ok_days / total_days) * WEIGHT

    if not violations:
        return passed(
            rule          = "Maximum daily workload",
            weight        = WEIGHT,
            message       = f"All {total_days} day(s) within the {MAX_DAILY_HOURS}h limit.",
            iso_reference = ISO_REF,
        )

    days_str = ", ".join(f"{v['day']} ({v['hours']}h)" for v in violations)
    return partial(
        rule           = "Maximum daily workload",
        weight         = WEIGHT,
        score          = round(score, 2),
        severity       = Severity.HIGH,
        message        = f"{len(violations)}/{total_days} day(s) exceed {MAX_DAILY_HOURS}h: {days_str}.",
        recommendation = f"Move sessions to reduce daily load to ≤ {MAX_DAILY_HOURS}h.",
        iso_reference  = ISO_REF,
        details        = {"violations": violations, "compliant_days": ok_days, "total_days": total_days},
    )


# =============================================================================
#  RULE 2 — Weekly workload
# =============================================================================

def validate_weekly_workload(planning: Planning) -> CriterionResult:
    """Checks that the total weekly hours do not exceed max_weekly_hours."""
    total = planning.total_hours

    if total <= MAX_WEEKLY_HOURS:
        return passed(
            rule          = "Maximum weekly workload",
            weight        = WEIGHT,
            message       = f"Total weekly hours: {round(total, 1)}h (limit: {MAX_WEEKLY_HOURS}h).",
            iso_reference = ISO_REF,
        )

    over = round(total - MAX_WEEKLY_HOURS, 2)
    return failed(
        rule           = "Maximum weekly workload",
        weight         = WEIGHT,
        score          = 0,
        severity       = Severity.HIGH,
        message        = f"Weekly total {round(total, 1)}h exceeds the {MAX_WEEKLY_HOURS}h limit by {over}h.",
        recommendation = f"Reduce total sessions by approximately {over}h across the week.",
        iso_reference  = ISO_REF,
        details        = {"total_hours": round(total, 2), "limit": MAX_WEEKLY_HOURS},
    )


# =============================================================================
#  RULE 3 — Hard course concentration
# =============================================================================

def validate_hard_course_concentration(planning: Planning) -> CriterionResult:
    """Checks that no day has more than max_hard_courses_per_day difficult sessions."""
    violations = []

    for day in planning.days:
        hard_count = day.hard_session_count
        if hard_count > MAX_HARD_COURSES_PER_DAY:
            violations.append({
                "day":   day.day.value,
                "count": hard_count,
                "limit": MAX_HARD_COURSES_PER_DAY,
            })

    total_days = len(planning.days)
    ok_days    = total_days - len(violations)
    score      = (ok_days / total_days) * WEIGHT if total_days else WEIGHT

    if not violations:
        return passed(
            rule          = "Difficult course concentration",
            weight        = WEIGHT,
            message       = f"No day exceeds {MAX_HARD_COURSES_PER_DAY} difficult course(s).",
            iso_reference = ISO_REF,
        )

    days_str = ", ".join(f"{v['day']} ({v['count']} hard)" for v in violations)
    return partial(
        rule           = "Difficult course concentration",
        weight         = WEIGHT,
        score          = round(score, 2),
        severity       = Severity.MEDIUM,
        message        = f"{len(violations)} day(s) have too many difficult sessions: {days_str}.",
        recommendation = f"Spread difficult courses — max {MAX_HARD_COURSES_PER_DAY} per day.",
        iso_reference  = ISO_REF,
        details        = {"violations": violations},
    )


# =============================================================================
#  MAIN ENTRY POINT
# =============================================================================

def validate(planning: Planning) -> list[CriterionResult]:
    """
    Runs all workload checks and returns a list of CriterionResult.
    Called by audit_service.py.
    """
    return [
        validate_daily_workload(planning),
        validate_weekly_workload(planning),
        validate_hard_course_concentration(planning),
    ]