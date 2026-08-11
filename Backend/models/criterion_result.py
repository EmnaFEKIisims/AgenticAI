"""
models/criterion_result.py
===========================
Standard return type used by ALL validators.

Every validator returns exactly one CriterionResult.
This guarantees that audit_service.py can aggregate them
without knowing anything about the internal logic of each validator.

Structure:
    CriterionResult
        rule            → name of the rule checked
        passed          → True / False
        score           → points earned (0 → weight)
        weight          → maximum points for this criterion
        message         → what was found (factual)
        recommendation  → what to do to fix it (actionable)
        details         → optional extra data for the frontend
"""

from dataclasses import dataclass, field
from enum import Enum


# =============================================================================
#  SEVERITY  — how serious is a failure?
# =============================================================================

class Severity(str, Enum):
    HIGH   = "high"     # blocks planning quality — must fix
    MEDIUM = "medium"   # degrades learning experience — should fix
    LOW    = "low"      # minor issue — nice to fix


# =============================================================================
#  CRITERION RESULT  — returned by every single validator
# =============================================================================

@dataclass
class CriterionResult:
    """
    The standard output of every validator.

    Example (workload_validator):
        CriterionResult(
            rule           = "Maximum daily workload",
            passed         = False,
            score          = 0,
            weight         = 25,
            severity       = Severity.HIGH,
            message        = "7.5h scheduled on Monday — limit is 6h.",
            recommendation = "Move 1 session from Monday to Tuesday.",
        )
    """

    # ── Required ──────────────────────────────────────────────────────────────
    rule:           str             # human-readable rule name
    passed:         bool            # True = compliant, False = violation
    score:          float           # points earned
    weight:         float           # max possible points for this criterion

    # ── Contextual ────────────────────────────────────────────────────────────
    severity:       Severity = Severity.MEDIUM
    message:        str      = ""   # what was found
    recommendation: str      = ""   # how to fix it

    # ── Optional extra data ────────────────────────────────────────────────────
    details: dict = field(default_factory=dict)
    # e.g. {"day": "Monday", "hours": 7.5, "limit": 6}

    # ── Reference ─────────────────────────────────────────────────────────────
    iso_reference: str = ""
    # e.g. "ISO 21001:2018 §8.3"

    # ── Computed ──────────────────────────────────────────────────────────────

    @property
    def score_ratio(self) -> float:
        """Score as a percentage of the maximum weight (0.0 → 1.0)."""
        return (self.score / self.weight) if self.weight > 0 else 0.0

    @property
    def status(self) -> str:
        """'PASSED' or 'FAILED' — used by the frontend table."""
        return "PASSED" if self.passed else "FAILED"

    def to_dict(self) -> dict:
        """Serializes to a plain dict for the API response."""
        return {
            "rule":           self.rule,
            "status":         self.status,
            "passed":         self.passed,
            "score":          round(self.score,  2),
            "weight":         round(self.weight, 2),
            "score_ratio":    round(self.score_ratio, 3),
            "severity":       self.severity.value,
            "message":        self.message,
            "recommendation": self.recommendation,
            "iso_reference":  self.iso_reference,
            "details":        self.details,
        }


# =============================================================================
#  HELPER FACTORIES — used by validators for consistent construction
# =============================================================================

def passed(
    rule:           str,
    weight:         float,
    message:        str  = "",
    iso_reference:  str  = "",
    details:        dict = None,
) -> CriterionResult:
    """
    Shortcut to create a fully-passing criterion result.

    Example:
        return passed("Maximum daily workload", weight=25,
                      message="All days within the 6h limit.")
    """
    return CriterionResult(
        rule          = rule,
        passed        = True,
        score         = weight,
        weight        = weight,
        severity      = Severity.LOW,
        message       = message,
        recommendation= "",
        iso_reference = iso_reference,
        details       = details or {},
    )


def failed(
    rule:           str,
    weight:         float,
    score:          float,
    severity:       Severity,
    message:        str,
    recommendation: str  = "",
    iso_reference:  str  = "",
    details:        dict = None,
) -> CriterionResult:
    """
    Shortcut to create a failed criterion result.

    Example:
        return failed(
            rule           = "Maximum daily workload",
            weight         = 25,
            score          = 0,
            severity       = Severity.HIGH,
            message        = "Monday: 7.5h > 6h limit.",
            recommendation = "Move 1 session from Monday to Tuesday.",
            iso_reference  = "ISO 21001:2018 §8.3",
            details        = {"day": "Monday", "hours": 7.5},
        )
    """
    return CriterionResult(
        rule           = rule,
        passed         = False,
        score          = max(0.0, min(score, weight)),
        weight         = weight,
        severity       = severity,
        message        = message,
        recommendation = recommendation,
        iso_reference  = iso_reference,
        details        = details or {},
    )


def partial(
    rule:           str,
    weight:         float,
    score:          float,
    severity:       Severity,
    message:        str,
    recommendation: str  = "",
    iso_reference:  str  = "",
    details:        dict = None,
) -> CriterionResult:
    """
    Shortcut for a partial pass — some violations found but not all.

    Example: 3 days OK, 1 day exceeded workload → partial score.
    """
    return CriterionResult(
        rule           = rule,
        passed         = score >= weight * 0.5,  # passed if ≥ 50% score
        score          = max(0.0, min(score, weight)),
        weight         = weight,
        severity       = severity,
        message        = message,
        recommendation = recommendation,
        iso_reference  = iso_reference,
        details        = details or {},
    )