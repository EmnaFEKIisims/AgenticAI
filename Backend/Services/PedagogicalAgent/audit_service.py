"""
services/audit_service.py
==========================
Orchestrates ALL 6 validators and assembles the AuditReport.

Validators:
  1. workload_validator     → daily + weekly hours + hard course concentration
  2. break_validator        → mandatory breaks + consecutive blocks
  3. progression_validator  → theory→practice order + prerequisites + evaluation order
  4. prerequisite_validator → TP must come after theory (focused single rule)
  5. teacher_validator      → trainer daily load + consecutive hours
  6. room_validator         → room capacity + room type vs session type

To add a new validator:
  1. Create validators/my_validator.py  with  validate() → list[CriterionResult]
  2. Import it here
  3. Add it to VALIDATORS — nothing else changes.
"""

from models.criterion_result  import CriterionResult
from Services.PedagogicalAgent.Schemas.Planning_schema import Planning
from Services.PedagogicalAgent.Schemas.audit_schema import AuditReport, CriterionReport

# All validators — add new ones here only
from Services.PedagogicalAgent.Validators.workload_validator      import validate as validate_workload
from Services.PedagogicalAgent.Validators.break_validator         import validate as validate_breaks
from Services.PedagogicalAgent.Validators.progression_validator   import validate as validate_progression
from Services.PedagogicalAgent.Validators.prerequisite_validator  import validate as validate_practice
from Services.PedagogicalAgent.Validators.teacher_validator       import validate as validate_teacher
from Services.PedagogicalAgent.Validators.room_validator         import validate as validate_room
from Services.PedagogicalAgent.Validators.prerequisite_validator import validate as validate_prerequisite

# Scoring
from Services.PedagogicalAgent.scoring_service import compute_full_score




# =============================================================================
#  VALIDATOR REGISTRY
# =============================================================================

VALIDATORS = [
    ("Workload",       validate_workload),
    ("Breaks",         validate_breaks),
    ("Progression",    validate_progression),
    ("Prerequisite",   validate_prerequisite),   # TP after theory
    ("Teacher",        validate_teacher),
    ("Room",           validate_room),
]


# =============================================================================
#  STEP 1 — Run all validators
# =============================================================================

def run_validators(planning: Planning) -> list[CriterionResult]:
    """Runs every validator and collects all CriterionResult objects."""
    all_results: list[CriterionResult] = []

    for name, fn in VALIDATORS:
        print(f"  [AuditService] Running {name} validator...")
        try:
            results = fn(planning)
            all_results.extend(results)
            ok = sum(1 for r in results if r.passed)
            print(f"    → {ok}/{len(results)} criterion(a) passed.")
        except Exception as e:
            print(f"  [AuditService] ❌ {name} failed: {e}")

    print(f"  [AuditService] Total: {len(all_results)} criterion(a) evaluated.")
    return all_results


# =============================================================================
#  STEP 2 — Build AuditReport
# =============================================================================

def build_report(planning: Planning, results: list[CriterionResult]) -> AuditReport:
    """Converts raw CriterionResult list into a structured AuditReport."""
    scoring  = compute_full_score(results)
    criteria = [CriterionReport(**r.to_dict()) for r in results]
    total    = len(results)
    passed   = sum(1 for r in results if r.passed)

    return AuditReport(
        score           = scoring["score"],
        grade           = scoring["grade"],
        is_compliant    = scoring["is_compliant"],
        criteria        = criteria,
        recommendations = scoring["recommendations"],
        total_criteria  = total,
        passed_criteria = passed,
        failed_criteria = total - passed,
        high_violations = scoring["high_violations"],
        planning_id     = planning.planning_id,
        group_name      = planning.group_name,
        total_sessions  = len(planning.sessions),
        total_hours     = round(planning.total_hours, 2),
    )


# =============================================================================
#  MAIN ENTRY POINT
# =============================================================================

def audit(planning: Planning) -> AuditReport:
    """Full pedagogical audit pipeline — planning → validators → score → report."""
    print(f"\n{'='*60}")
    print(f"  AUDIT SERVICE")
    print(f"  Sessions : {len(planning.sessions)}")
    print(f"  Hours    : {round(planning.total_hours, 1)}h")
    print(f"{'='*60}")

    results = run_validators(planning)
    report  = build_report(planning, results)

    print(f"\n  ✅ Score={report.score_label}  Grade={report.grade.value}  "
          f"Compliant={report.is_compliant}")
    return report