"""
this file define the data structures used by this agent

There are 3 types of constraints:
  A. ISO        -> loaded from DB (max hours, mandatory breaks, etc.)
  B. Pedagogical -> free text from user -> LLM extracts
  C. User        -> free text from user -> LLM extracts (availability, forbidden days...)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# =============================================================================
#  ENUMS
# =============================================================================

class ConstraintType(str, Enum):
    ISO         = "iso"
    PEDAGOGICAL = "pedagogical"
    USER        = "user"


class ConstraintSeverity(str, Enum):
    HARD = "hard"   # must be respected — blocks planning if violated
    SOFT = "soft"   # preferred — planning continues but noted as warning


class ValidationStatus(str, Enum):
    VALID       = "valid"
    WARNING     = "warning"
    CONFLICT    = "conflict"
    INVALID     = "invalid"


# =============================================================================
#  A. ISO CONSTRAINT  (from DB)
# =============================================================================

@dataclass
class ISOConstraint:

    constraint_type: str          # snake_case key e.g. "max_hours_per_day"
    value:           Any          # int, float, str, list, dict
    severity:        ConstraintSeverity = ConstraintSeverity.HARD
    description:     str = ""     # human-readable explanation


# =============================================================================
#  B. PEDAGOGICAL CONSTRAINT  (from user text)
# =============================================================================

@dataclass
class PedagogicalConstraint:

    rule:        str                                   # normalized rule text
    severity:    ConstraintSeverity = ConstraintSeverity.SOFT
    category:    str = ""                              # "progression" | "load" | "balance" | "other"
    raw_text:    str = ""                              # original user text


# =============================================================================
#  C. USER CONSTRAINT  (from user text)
# =============================================================================

@dataclass
class UserConstraint:

    constraint_key:   str          # snake_case key matching planning_agent fields
    constraint_value: Any          # string, int, list, dict
    severity:         ConstraintSeverity = ConstraintSeverity.HARD
    raw_text:         str = ""     # original user text fragment


# =============================================================================
#  INPUT — what the ConstraintAgent receives
# =============================================================================

@dataclass
class ConstraintInput:

    iso_constraints:   list[ISOConstraint]    = field(default_factory=list)
    pedagogical_text:  str                    = ""   # raw text, LLM will analyze
    user_text:         str                    = ""   # raw text, LLM will analyze


# =============================================================================
#  OUTPUT — what the ConstraintAgent returns (after Analyzer + Validator)
# =============================================================================

@dataclass
class ConstraintOutput:

    # Merged + validated constraints (ready for PlanningAgent)
    forbidden_days:                    list[str]         = field(default_factory=list)
    trainer_availability:              dict[str, str]    = field(default_factory=dict)
    session_duration_override:         int | None        = None   # minutes
    sessions_per_day:                  int | None        = None
    break_between_sessions_minutes:    int | None        = None
    lunch_break_after_n_sessions:      int | None        = None
    lunch_break_duration_minutes:      int | None        = None
    day_start_time:                    str | None        = None   # "HH:MM"
    max_hours_per_day:                 float | None      = None   # from ISO
    max_consecutive_sessions:          int | None        = None   # from ISO
    min_room_capacity:                 int | None        = None
    room_type_required:                str | None        = None
    group_priority:                    str | None        = None
    no_parallel_sessions_same_group:   bool              = False
    prefer_matching_specialization:    bool              = True
    pedagogical_rules:                 list[str]         = field(default_factory=list)
    other:                             list[str]         = field(default_factory=list)

    # Traceability — which source set each field
    sources: dict[str, str] = field(default_factory=dict)
    # e.g. {"max_hours_per_day": "iso", "forbidden_days": "user", "pedagogical_rules": "pedagogical"}


# =============================================================================
#  VALIDATION RESULT  (from Validator)
# =============================================================================

@dataclass
class ValidationIssue:

    field:       str                  # which constraint field
    message:     str                  # human-readable explanation
    severity:    ValidationStatus     # WARNING | CONFLICT | INVALID
    suggestion:  str = ""             # how to fix it


@dataclass
class ValidationResult:

    status:   ValidationStatus          # overall status (worst issue wins)
    issues:   list[ValidationIssue]     = field(default_factory=list)
    warnings: list[str]                 = field(default_factory=list)
    is_valid: bool                      = True
    # True if no CONFLICT or INVALID issues (WARNINGs are acceptable)

    def worst_status(self) -> ValidationStatus:
        if any(i.severity == ValidationStatus.INVALID  for i in self.issues): return ValidationStatus.INVALID
        if any(i.severity == ValidationStatus.CONFLICT for i in self.issues): return ValidationStatus.CONFLICT
        if any(i.severity == ValidationStatus.WARNING  for i in self.issues): return ValidationStatus.WARNING
        return ValidationStatus.VALID