"""
services/scoring_service.py
=============================
Computes the final pedagogical score from all CriterionResult objects.

Responsibilities:
  - compute_score()   : weighted sum of all criterion scores
  - normalize_score() : scale to 0-100
  - grade()           : convert numeric score to letter grade

Why separate from audit_service?
  Scoring formula can change independently.
  Tomorrow: change weights, add penalties, add bonuses → only this file changes.
"""

from models.criterion_result import CriterionResult, Severity
from Services.PedagogicalAgent.Schemas.audit_schema import AuditGrade


# =============================================================================
#  GRADE THRESHOLDS
# =============================================================================

GRADE_THRESHOLDS = [
    (90, AuditGrade.A),   # 90-100 → Excellent
    (75, AuditGrade.B),   # 75-89  → Good
    (60, AuditGrade.C),   # 60-74  → Acceptable
    (45, AuditGrade.D),   # 45-59  → Needs improvement
    (0,  AuditGrade.F),   # 0-44   → Non-compliant
]

# Penalty applied per HIGH-severity failure (on top of the score loss)
HIGH_SEVERITY_PENALTY = 2.0   # extra points deducted per HIGH failure


# =============================================================================
#  STEP 1 — Compute raw weighted score
# =============================================================================

def compute_score(results: list[CriterionResult]) -> float:
    """
    Computes the raw weighted score from all criterion results.

    Formula:
        raw_score = Σ (criterion.score / criterion.weight) × criterion.weight
                  = Σ criterion.score

    Since each validator already sets score ∈ [0, weight],
    the raw score is just the sum of all criterion scores.

    Args:
        results: list of CriterionResult from all validators

    Returns:
        Raw score (0 → sum of all weights)
    """
    if not results:
        return 0.0
    return sum(r.score for r in results)


# =============================================================================
#  STEP 2 — Normalize to 0-100
# =============================================================================

def normalize_score(raw_score: float, results: list[CriterionResult]) -> float:
    """
    Normalizes the raw score to a 0-100 scale.

    Formula:
        normalized = (raw_score / total_weight) × 100

    Then applies a penalty for HIGH-severity failures.

    Args:
        raw_score : output of compute_score()
        results   : same list, used to compute total_weight and penalties

    Returns:
        Final score between 0 and 100.
    """
    total_weight = sum(r.weight for r in results)
    if total_weight == 0:
        return 0.0

    normalized = (raw_score / total_weight) * 100

    # Apply penalty for every HIGH-severity failure
    high_failures = sum(
        1 for r in results
        if not r.passed and r.severity == Severity.HIGH
    )
    penalty = high_failures * HIGH_SEVERITY_PENALTY
    final   = max(0.0, normalized - penalty)

    return round(final, 2)


# =============================================================================
#  STEP 3 — Letter grade
# =============================================================================

def grade(score: float) -> AuditGrade:
    """
    Converts a 0-100 score to a letter grade.

    Thresholds:
        A : 90-100  — Excellent — fully compliant
        B : 75-89   — Good — minor improvements needed
        C : 60-74   — Acceptable — moderate improvements needed
        D : 45-59   — Needs improvement — significant violations
        F : 0-44    — Non-compliant — major pedagogical issues
    """
    for threshold, letter in GRADE_THRESHOLDS:
        if score >= threshold:
            return letter
    return AuditGrade.F


# =============================================================================
#  STEP 4 — Collect recommendations
# =============================================================================

def collect_recommendations(results: list[CriterionResult]) -> list[str]:
    """
    Extracts all non-empty recommendations from failed criteria.
    Orders them by severity: HIGH first, then MEDIUM, then LOW.
    """
    priority = {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2}

    failed = [r for r in results if not r.passed and r.recommendation.strip()]
    failed.sort(key=lambda r: priority.get(r.severity, 99))

    # Deduplicate while preserving order
    seen  = set()
    recs  = []
    for r in failed:
        rec = r.recommendation.strip()
        if rec not in seen:
            seen.add(rec)
            recs.append(rec)

    return recs


# =============================================================================
#  MAIN ENTRY POINT  — called by audit_service
# =============================================================================

def compute_full_score(results: list[CriterionResult]) -> dict:
    """
    Runs the complete scoring pipeline.

    Args:
        results: all CriterionResult objects from all validators

    Returns:
        {
            "score":           87.5,
            "grade":           "B",
            "is_compliant":    True,
            "high_violations": 0,
            "recommendations": ["..."]
        }
    """
    raw_score     = compute_score(results)
    final_score   = normalize_score(raw_score, results)
    letter        = grade(final_score)
    recs          = collect_recommendations(results)
    high_failures = sum(1 for r in results
                        if not r.passed and r.severity == Severity.HIGH)

    print(f"  [ScoringService] Raw={round(raw_score,2)} | "
          f"Final={final_score}/100 | Grade={letter.value} | "
          f"HIGH violations={high_failures}")

    return {
        "score":           final_score,
        "grade":           letter,
        "is_compliant":    final_score >= 60 and high_failures == 0,
        "high_violations": high_failures,
        "recommendations": recs,
    }