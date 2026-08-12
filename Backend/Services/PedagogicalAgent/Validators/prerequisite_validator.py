"""
validators/prerequisite_validator.py
=======================================
Responsabilité unique :
  Vérifier que les séances de TP (pratique) arrivent APRÈS les séances théoriques
  pour le même cours, dans la même journée.

    Cours (Théorie)
         ↓
    TP   (Pratique)

Functions:
  check_theory_before_practice()  → vérifie l'ordre théorie → TP par jour + cours
  validate()                      → point d'entrée, retourne list[CriterionResult]
"""

from collections import defaultdict

from models.criterion_result import CriterionResult, Severity, passed, partial
from Services.PedagogicalAgent.Schemas.Planning_schema  import Planning, Session, SessionType
from utils.rule_loader         import get_value


WEIGHT  = get_value("progression", "weight", default=20)
ISO_REF = "ISO 29993:2017 §6.3.3"

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# =============================================================================
#  check_theory_before_practice
# =============================================================================

def check_theory_before_practice(planning: Planning) -> CriterionResult:
    """
    For each (course, day) pair: verifies that the first theory session
    starts BEFORE the first practice/TP session.

    If a course has practice on a given day but no theory on that day,
    checks whether theory was scheduled on a previous day in the week.
    """
    # Group sessions by (course, day)
    by_course_day: dict[tuple, list[Session]] = defaultdict(list)
    for s in planning.sessions:
        by_course_day[(s.course, s.day.value)].append(s)

    # Map course → earliest day that has theory (for cross-day check)
    course_first_theory_day: dict[str, int] = {}
    for s in planning.sessions:
        if s.is_theory:
            day_idx = DAY_ORDER.index(s.day.value) if s.day.value in DAY_ORDER else 99
            if s.course not in course_first_theory_day:
                course_first_theory_day[s.course] = day_idx
            else:
                course_first_theory_day[s.course] = min(
                    course_first_theory_day[s.course], day_idx
                )

    violations = []

    for (course, day), sessions in by_course_day.items():
        sorted_s     = sorted(sessions, key=lambda s: s.start_minutes)
        has_theory   = any(s.is_theory   for s in sorted_s)
        has_practice = any(s.is_practice for s in sorted_s)

        if not has_practice:
            continue   # no TP on this day → nothing to check

        if has_theory:
            # Both on the same day → check order
            first_theory   = next(s for s in sorted_s if s.is_theory)
            first_practice = next(s for s in sorted_s if s.is_practice)
            if first_practice.start_minutes < first_theory.start_minutes:
                violations.append({
                    "course":         course,
                    "day":            day,
                    "problem":        "TP starts before theory on the same day.",
                    "practice_start": first_practice.start,
                    "theory_start":   first_theory.start,
                })
        else:
            # Practice on this day, theory on another day → check day ordering
            practice_day_idx = DAY_ORDER.index(day) if day in DAY_ORDER else 99
            theory_day_idx   = course_first_theory_day.get(course)

            if theory_day_idx is None:
                violations.append({
                    "course":  course,
                    "day":     day,
                    "problem": "TP session found but no theory session exists for this course.",
                })
            elif practice_day_idx < theory_day_idx:
                violations.append({
                    "course":         course,
                    "day":            day,
                    "problem":        "TP scheduled on an earlier day than theory.",
                    "practice_day":   day,
                    "theory_day":     DAY_ORDER[theory_day_idx],
                })

    total_checked = len(set(
        (course, day)
        for (course, day), sessions in by_course_day.items()
        if any(s.is_practice for s in sessions)
    ))

    if total_checked == 0:
        return passed(
            rule          = "Theory before practice (TP ordering)",
            weight        = WEIGHT,
            message       = "No practice sessions found — ordering check not applicable.",
            iso_reference = ISO_REF,
        )

    ok    = total_checked - len(violations)
    score = (ok / total_checked) * WEIGHT if total_checked else WEIGHT

    if not violations:
        return passed(
            rule          = "Theory before practice (TP ordering)",
            weight        = WEIGHT,
            message       = (
                f"All {total_checked} practice session(s) are correctly scheduled "
                f"after theory sessions."
            ),
            iso_reference = ISO_REF,
        )

    ex = violations[0]
    return partial(
        rule           = "Theory before practice (TP ordering)",
        weight         = WEIGHT,
        score          = round(score, 2),
        severity       = Severity.HIGH,
        message        = (
            f"{len(violations)}/{total_checked} practice session(s) violate the "
            f"theory-before-practice rule. "
            f"Example: '{ex['course']}' on {ex['day']} — {ex['problem']}"
        ),
        recommendation = (
            "Reschedule TP sessions so they always follow the corresponding "
            "theory session, either on the same day or on a later day."
        ),
        iso_reference  = ISO_REF,
        details        = {"violations": violations[:5]},
    )


# =============================================================================
#  MAIN ENTRY POINT
# =============================================================================

def validate(planning: Planning) -> list[CriterionResult]:
    """Called by audit_service and pedagogical_agent."""
    return [check_theory_before_practice(planning)]