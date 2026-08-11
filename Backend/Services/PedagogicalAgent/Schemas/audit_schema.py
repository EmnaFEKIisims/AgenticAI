"""
schemas/audit_schema.py
========================
Pydantic models defining the Pedagogical Agent's output.

AuditReport is the single output type of the entire pedagogical pipeline.
It is returned by the API and consumed by the frontend.

Structure:
    AuditReport
        ├── score          : 0-100 weighted score
        ├── grade          : A / B / C / D / F
        ├── criteria       : list of CriterionReport (one per rule checked)
        └── recommendations: list of actionable suggestions
"""

from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


# =============================================================================
#  GRADE ENUM
# =============================================================================

class AuditGrade(str, Enum):
    A = "A"   # 90-100  — Excellent
    B = "B"   # 75-89   — Good
    C = "C"   # 60-74   — Acceptable
    D = "D"   # 45-59   — Needs improvement
    F = "F"   # 0-44    — Non-compliant


# =============================================================================
#  ONE CRITERION  (maps directly from CriterionResult.to_dict())
# =============================================================================

class CriterionReport(BaseModel):
    """
    The result of a single rule check.
    Maps 1:1 to CriterionResult.to_dict().
    """
    rule:           str
    status:         str              # "PASSED" | "FAILED"
    passed:         bool
    score:          float
    weight:         float
    score_ratio:    float            # 0.0 → 1.0
    severity:       str              # "high" | "medium" | "low"
    message:        str
    recommendation: str = ""
    iso_reference:  str = ""
    details:        dict = Field(default_factory=dict)


# =============================================================================
#  AUDIT REPORT  (full output of the Pedagogical Agent)
# =============================================================================

class AuditReport(BaseModel):
    """
    Complete pedagogical audit report.
    Produced by audit_service.build_report() and enriched by scoring_service.
    """

    # ── Scores ─────────────────────────────────────────────────────────────────
    score:           float           = Field(..., ge=0, le=100,
                                            description="Final weighted score (0-100)")
    max_score:       float           = Field(100.0,
                                            description="Maximum possible score")
    grade:           AuditGrade      = Field(...,
                                            description="Letter grade (A/B/C/D/F)")
    is_compliant:    bool            = Field(...,
                                            description="True if score >= 60 and no HIGH severity failures")

    # ── Detail ─────────────────────────────────────────────────────────────────
    criteria:        list[CriterionReport] = Field(default_factory=list,
                                                   description="One entry per rule checked")
    recommendations: list[str]            = Field(default_factory=list,
                                                   description="Actionable improvement suggestions")

    # ── Summary counters ───────────────────────────────────────────────────────
    total_criteria:  int  = 0
    passed_criteria: int  = 0
    failed_criteria: int  = 0
    high_violations: int  = 0    # severity=HIGH failures — most critical

    # ── Planning context ───────────────────────────────────────────────────────
    planning_id:     Optional[int] = None
    group_name:      Optional[str] = None
    total_sessions:  int           = 0
    total_hours:     float         = 0.0

    # ── ISO references applied ─────────────────────────────────────────────────
    iso_references:  list[str] = Field(
        default_factory=lambda: ["ISO 21001:2018", "ISO 29993:2017"],
        description="Standards applied in this audit"
    )

    # ── Computed helpers ───────────────────────────────────────────────────────

    @property
    def compliance_rate(self) -> float:
        """Percentage of criteria that passed."""
        if self.total_criteria == 0:
            return 0.0
        return round(self.passed_criteria / self.total_criteria * 100, 1)

    @property
    def score_label(self) -> str:
        """Human-readable score like '87/100'."""
        return f"{round(self.score, 1)}/100"

    def to_dict(self) -> dict:
        """Serializes to a plain dict for the API response."""
        return {
            "score":           round(self.score, 1),
            "max_score":       self.max_score,
            "score_label":     self.score_label,
            "grade":           self.grade.value,
            "is_compliant":    self.is_compliant,
            "compliance_rate": self.compliance_rate,
            "total_criteria":  self.total_criteria,
            "passed_criteria": self.passed_criteria,
            "failed_criteria": self.failed_criteria,
            "high_violations": self.high_violations,
            "planning_id":     self.planning_id,
            "group_name":      self.group_name,
            "total_sessions":  self.total_sessions,
            "total_hours":     round(self.total_hours, 2),
            "iso_references":  self.iso_references,
            "criteria":        [c.model_dump() for c in self.criteria],
            "recommendations": self.recommendations,
        }