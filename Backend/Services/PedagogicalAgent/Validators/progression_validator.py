"""
validators/progression_validator.py
=====================================
Validates that sessions follow a logical pedagogical sequence.

Rules (from pedagogical_rules.json "progression" section):
  - theory_before_practice        : theory must precede practice
  - prerequisites_must_be_respected: course prerequisites come first
  - evaluation_after_module       : evaluations come after all content sessions
"""

from collections import defaultdict

from models.criterion_result import CriterionResult, Severity, passed, partial
from Services.PedagogicalAgent.Schemas.Planning_schema import Planning, Session
from utils.rule_loader         import get_value


THEORY_BEFORE_PRACTICE    = get_value("progression", "theory_before_practice",          default=True)
CHECK_PREREQUISITES        = get_value("progression", "prerequisites_must_be_respected", default=True)
EVALUATION_AFTER_MODULE    = get_value("progression", "evaluation_after_module",         default=True)
WEIGHT                     = get_value("progression", "weight",                          default=20)
ISO_REF                    = "ISO 29993:2017 §6.3 / ISO 21001:2018 §8.2"


# =============================================================================
#  RULE 1 — Theory before Practice
# =============================================================================

def check_theory_before_practice(planning: Planning) -> CriterionResult:
    """
    For each course: checks that at least one theory session occurs
    before the first practice session on the same day or earlier in the week.
    """
    if not THEORY_BEFORE_PRACTICE:
        return passed("Theory before practice", weight=WEIGHT,
                      message="Rule disabled in configuration.", iso_reference=ISO_REF)

    # Group sessions by course, ordered by day then start time
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    sessions_by_course: dict[str, list[Session]] = defaultdict(list)
    for s in planning.sessions:
        sessions_by_course[s.course].append(s)

    violations = []

    for course, sessions in sessions_by_course.items():
        # Sort by day index then start time
        sorted_sessions = sorted(
            sessions,
            key=lambda s: (
                day_order.index(s.day.value) if s.day.value in day_order else 99,
                s.start_minutes
            )
        )

        first_practice = next((s for s in sorted_sessions if s.is_practice), None)
        first_theory   = next((s for s in sorted_sessions if s.is_theory),   None)

        if first_practice and not first_theory:
            violations.append({
                "course":  course,
                "problem": "Practice session exists but no theory session found.",
            })
        elif first_practice and first_theory:
            theory_idx   = sorted_sessions.index(first_theory)
            practice_idx = sorted_sessions.index(first_practice)
            if practice_idx < theory_idx:
                violations.append({
                    "course":          course,
                    "problem":         "Practice session scheduled before theory session.",
                    "practice_day":    first_practice.day.value,
                    "practice_start":  first_practice.start,
                    "theory_day":      first_theory.day.value,
                    "theory_start":    first_theory.start,
                })

    total_courses = len(sessions_by_course)
    ok_courses    = total_courses - len(violations)
    score         = (ok_courses / total_courses) * WEIGHT if total_courses else WEIGHT

    if not violations:
        return passed(
            rule          = "Theory before practice",
            weight        = WEIGHT,
            message       = f"All {total_courses} course(s) schedule theory before practice.",
            iso_reference = ISO_REF,
        )

    examples = violations[:3]
    return partial(
        rule           = "Theory before practice",
        weight         = WEIGHT,
        score          = round(score, 2),
        severity       = Severity.HIGH,
        message        = f"{len(violations)}/{total_courses} course(s) violate theory-before-practice order.",
        recommendation = "Reschedule practice sessions to occur after their corresponding theory sessions.",
        iso_reference  = ISO_REF,
        details        = {"violations": examples},
    )


# =============================================================================
#  RULE 2 — Prerequisites respected
# =============================================================================

def check_prerequisites(planning: Planning) -> CriterionResult:
    """
    Checks that courses listed as prerequisites are scheduled
    before the courses that depend on them.
    """
    if not CHECK_PREREQUISITES:
        return passed("Prerequisites respected", weight=WEIGHT,
                      message="Rule disabled in configuration.", iso_reference=ISO_REF)

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Map: course_title → earliest (day_index, start_minutes) in planning
    course_first_slot: dict[str, tuple[int, int]] = {}
    for s in planning.sessions:
        day_idx = day_order.index(s.day.value) if s.day.value in day_order else 99
        key     = (day_idx, s.start_minutes)
        if s.course not in course_first_slot or key < course_first_slot[s.course]:
            course_first_slot[s.course] = key

    violations = []
    for s in planning.sessions:
        day_idx = day_order.index(s.day.value) if s.day.value in day_order else 99
        for prereq in s.prerequisites:
            prereq_slot = course_first_slot.get(prereq)
            if prereq_slot is None:
                violations.append({
                    "course":      s.course,
                    "prerequisite": prereq,
                    "problem":     f"Prerequisite '{prereq}' not found in planning.",
                })
            elif prereq_slot >= (day_idx, s.start_minutes):
                violations.append({
                    "course":      s.course,
                    "prerequisite": prereq,
                    "problem":     f"'{prereq}' is scheduled after or at the same time as '{s.course}'.",
                })

    if not violations:
        return passed(
            rule          = "Prerequisites respected",
            weight        = WEIGHT,
            message       = "All prerequisites are scheduled before their dependent courses.",
            iso_reference = ISO_REF,
        )

    total = len({s.course for s in planning.sessions if s.prerequisites})
    ok    = max(0, total - len(violations))
    score = (ok / total) * WEIGHT if total else WEIGHT

    return partial(
        rule           = "Prerequisites respected",
        weight         = WEIGHT,
        score          = round(score, 2),
        severity       = Severity.HIGH,
        message        = f"{len(violations)} prerequisite violation(s) found.",
        recommendation = "Ensure prerequisite courses are completed before dependent ones.",
        iso_reference  = ISO_REF,
        details        = {"violations": violations[:5]},
    )


# =============================================================================
#  RULE 3 — Evaluation after module
# =============================================================================

def check_learning_path(planning: Planning) -> CriterionResult:
    """
    Checks that evaluation sessions for a course are scheduled
    after all theory and practice sessions for that same course.
    """
    if not EVALUATION_AFTER_MODULE:
        return passed("Evaluation after module", weight=WEIGHT,
                      message="Rule disabled in configuration.", iso_reference=ISO_REF)

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    sessions_by_course: dict[str, list[Session]] = defaultdict(list)
    for s in planning.sessions:
        sessions_by_course[s.course].append(s)

    violations = []

    for course, sessions in sessions_by_course.items():
        sorted_s = sorted(
            sessions,
            key=lambda s: (
                day_order.index(s.day.value) if s.day.value in day_order else 99,
                s.start_minutes
            )
        )
        evals   = [s for s in sorted_s if s.is_evaluation]
        content = [s for s in sorted_s if not s.is_evaluation]

        for ev in evals:
            ev_idx = sorted_s.index(ev)
            after  = [s for s in sorted_s[:ev_idx] if not s.is_evaluation]
            remaining = [s for s in sorted_s[ev_idx + 1:] if not s.is_evaluation]
            if remaining:
                violations.append({
                    "course":  course,
                    "problem": f"Evaluation on {ev.day.value} at {ev.start} "
                               f"has {len(remaining)} content session(s) after it.",
                })

    total = len([c for c, ss in sessions_by_course.items()
                 if any(s.is_evaluation for s in ss)])
    ok    = max(0, total - len(violations))
    score = (ok / total) * WEIGHT if total else WEIGHT

    if not violations:
        return passed(
            rule          = "Evaluation after module",
            weight        = WEIGHT,
            message       = "All evaluations are scheduled after their corresponding content sessions.",
            iso_reference = ISO_REF,
        )

    return partial(
        rule           = "Evaluation after module",
        weight         = WEIGHT,
        score          = round(score, 2),
        severity       = Severity.MEDIUM,
        message        = f"{len(violations)} course(s) have evaluations before all content is delivered.",
        recommendation = "Move evaluation sessions to after all theory and practice sessions.",
        iso_reference  = ISO_REF,
        details        = {"violations": violations[:5]},
    )


# =============================================================================
#  MAIN ENTRY POINT
# =============================================================================

def validate(planning: Planning) -> list[CriterionResult]:
    return [
        check_theory_before_practice(planning),
        check_prerequisites(planning),
        check_learning_path(planning),
    ]