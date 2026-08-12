"""
validators/break_validator.py
================================
Validates that mandatory breaks are respected.

Rules (from pedagogical_rules.json "breaks" section):
  - mandatory_break_after_minutes : break required after this many minutes
  - min_break_duration_minutes    : minimum duration of a break
  - lunch_break_duration_minutes  : minimum lunch break duration
  - lunch_after_hours             : lunch must occur after this many hours
"""

from models.criterion_result import CriterionResult, Severity, passed, partial
from Services.PedagogicalAgent.Schemas.Planning_schema import Planning, DayPlanning
from utils.rule_loader         import get_value


MAX_CONSECUTIVE_MINUTES  = get_value("breaks", "mandatory_break_after_minutes",  default=180)
MIN_BREAK_MINUTES        = get_value("breaks", "min_break_duration_minutes",      default=15)
LUNCH_DURATION_MINUTES   = get_value("breaks", "lunch_break_duration_minutes",    default=60)
LUNCH_AFTER_HOURS        = get_value("breaks", "lunch_after_hours",               default=3.0)
WEIGHT                   = get_value("breaks", "weight",                          default=20)
ISO_REF                  = "ISO 21001:2018 §8.3 / ISO 29993:2017 §6.2"


# =============================================================================
#  HELPER — compute gaps between consecutive sessions
# =============================================================================

def _gaps_for_day(day: DayPlanning) -> list[dict]:
    """
    Returns list of gaps (in minutes) between consecutive sessions.
    Each gap = {"after": session, "gap_minutes": N}
    """
    sessions = day.sessions_sorted
    gaps = []
    for i in range(len(sessions) - 1):
        current = sessions[i]
        next_s  = sessions[i + 1]
        gap = next_s.start_minutes - current.end_minutes
        gaps.append({
            "after_course": current.course,
            "before_course": next_s.course,
            "gap_minutes": gap,
            "end_time":    current.end,
            "start_time":  next_s.start,
        })
    return gaps


def _consecutive_block_minutes(day: DayPlanning) -> list[dict]:
    """
    Computes consecutive teaching blocks (uninterrupted by a sufficient break).
    Returns list of blocks that exceeded MAX_CONSECUTIVE_MINUTES.
    """
    sessions = day.sessions_sorted
    if not sessions:
        return []

    violations = []
    block_start  = sessions[0].start_minutes
    block_end    = sessions[0].end_minutes

    for i in range(1, len(sessions)):
        prev = sessions[i - 1]
        curr = sessions[i]
        gap  = curr.start_minutes - prev.end_minutes

        if gap >= MIN_BREAK_MINUTES:
            # break sufficient — reset block
            block_start = curr.start_minutes
            block_end   = curr.end_minutes
        else:
            # still in the same block
            block_end = curr.end_minutes

        block_duration = block_end - block_start
        if block_duration > MAX_CONSECUTIVE_MINUTES:
            violations.append({
                "day":              day.day.value,
                "block_minutes":    block_duration,
                "block_hours":      round(block_duration / 60, 2),
                "limit_hours":      round(MAX_CONSECUTIVE_MINUTES / 60, 2),
            })
            block_start = curr.end_minutes   # reset after recording
            block_end   = curr.end_minutes

    return violations


# =============================================================================
#  RULE 1 — Mandatory breaks between sessions
# =============================================================================

def check_breaks(planning: Planning) -> CriterionResult:
    """Checks that breaks between sessions meet the minimum duration."""
    all_short_gaps = []

    for day in planning.days:
        for gap_info in _gaps_for_day(day):
            gap = gap_info["gap_minutes"]
            if 0 < gap < MIN_BREAK_MINUTES:
                all_short_gaps.append({**gap_info, "day": day.day.value})

    if not all_short_gaps:
        return passed(
            rule          = "Mandatory break between sessions",
            weight        = WEIGHT,
            message       = f"All session gaps meet the minimum {MIN_BREAK_MINUTES}-minute break.",
            iso_reference = ISO_REF,
        )

    n = len(all_short_gaps)
    score = max(0, WEIGHT - n * (WEIGHT / 5))
    example = all_short_gaps[0]
    return partial(
        rule           = "Mandatory break between sessions",
        weight         = WEIGHT,
        score          = round(score, 2),
        severity       = Severity.HIGH,
        message        = f"{n} gap(s) shorter than {MIN_BREAK_MINUTES}min. "
                         f"Example: {example['after_course']} → {example['before_course']} "
                         f"({example['gap_minutes']}min) on {example['day']}.",
        recommendation = f"Ensure at least {MIN_BREAK_MINUTES} minutes between all sessions.",
        iso_reference  = ISO_REF,
        details        = {"short_gaps": all_short_gaps[:5]},
    )


# =============================================================================
#  RULE 2 — Consecutive teaching blocks
# =============================================================================

def check_consecutive_blocks(planning: Planning) -> CriterionResult:
    """Checks that no uninterrupted teaching block exceeds max_consecutive_hours."""
    all_violations = []

    for day in planning.days:
        all_violations.extend(_consecutive_block_minutes(day))

    if not all_violations:
        limit_h = round(MAX_CONSECUTIVE_MINUTES / 60, 1)
        return passed(
            rule          = "Maximum consecutive teaching block",
            weight        = WEIGHT,
            message       = f"No block exceeds {limit_h}h without a sufficient break.",
            iso_reference = ISO_REF,
        )

    total_days = len(planning.days)
    score      = max(0, WEIGHT - len(all_violations) * (WEIGHT / total_days)) if total_days else 0
    limit_h    = round(MAX_CONSECUTIVE_MINUTES / 60, 1)
    return partial(
        rule           = "Maximum consecutive teaching block",
        weight         = WEIGHT,
        score          = round(score, 2),
        severity       = Severity.HIGH,
        message        = f"{len(all_violations)} block(s) exceed {limit_h}h without a sufficient break.",
        recommendation = f"Insert a {MIN_BREAK_MINUTES}-minute break every {limit_h}h.",
        iso_reference  = ISO_REF,
        details        = {"violations": all_violations},
    )


# =============================================================================
#  MAIN ENTRY POINT
# =============================================================================

def validate(planning: Planning) -> list[CriterionResult]:
    return [
        check_breaks(planning),
        check_consecutive_blocks(planning),
    ]