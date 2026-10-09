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
    Checks that no single REAL calendar day (week + weekday — see
    Planning.days) exceeds max_daily_hours.
    Returns a partial score proportional to compliant days.
    """
    violations = []

    for day in planning.days:
        hours = day.total_hours
        if hours > MAX_DAILY_HOURS:
            label = f"{day.day.value}" if day.week is None else f"Week {day.week} {day.day.value}"
            violations.append({
                "day":   label,
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
    """
    Checks that EACH calendar week's total hours stays within
    max_weekly_hours — not the whole multi-week program's grand total.

    The previous version compared planning.total_hours (the SUM across
    every week of the program) against max_weekly_hours, which fails by
    construction for any program longer than one week (e.g. 159h across
    6 weeks vs a 30h/week limit → an automatic, unfixable HIGH violation
    that has nothing to do with the schedule's actual quality).
    """
    weekly_hours = planning.weeks

    if not weekly_hours:
        return passed("Maximum weekly workload", weight=WEIGHT,
                      message="No sessions to evaluate.", iso_reference=ISO_REF)

    violations = []
    for week, hours in weekly_hours.items():
        if hours > MAX_WEEKLY_HOURS:
            label = "week (unspecified)" if week is None else f"week {week}"
            violations.append({
                "week":  label,
                "hours": round(hours, 2),
                "limit": MAX_WEEKLY_HOURS,
                "over":  round(hours - MAX_WEEKLY_HOURS, 2),
            })

    total_weeks = len(weekly_hours)
    ok_weeks    = total_weeks - len(violations)
    score       = (ok_weeks / total_weeks) * WEIGHT if total_weeks else WEIGHT

    if not violations:
        return passed(
            rule          = "Maximum weekly workload",
            weight        = WEIGHT,
            message       = f"All {total_weeks} week(s) within the {MAX_WEEKLY_HOURS}h limit.",
            iso_reference = ISO_REF,
        )

    weeks_str = ", ".join(f"{v['week']} ({v['hours']}h)" for v in violations)
    return partial(
        rule           = "Maximum weekly workload",
        weight         = WEIGHT,
        score          = round(score, 2),
        severity       = Severity.HIGH,
        message        = f"{len(violations)}/{total_weeks} week(s) exceed {MAX_WEEKLY_HOURS}h: {weeks_str}.",
        recommendation = f"Reduce weekly load to ≤ {MAX_WEEKLY_HOURS}h per week.",
        iso_reference  = ISO_REF,
        details        = {"violations": violations, "compliant_weeks": ok_weeks, "total_weeks": total_weeks},
    )


# =============================================================================
#  RULE 3 — Hard course concentration
# =============================================================================

def validate_hard_course_concentration(planning: Planning) -> CriterionResult:
    """Checks that no REAL calendar day has more than max_hard_courses_per_day difficult sessions."""
    violations = []

    for day in planning.days:
        hard_count = day.hard_session_count
        if hard_count > MAX_HARD_COURSES_PER_DAY:
            label = f"{day.day.value}" if day.week is None else f"Week {day.week} {day.day.value}"
            violations.append({
                "day":   label,
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