from Services.constraintAgent.Schema import (
    ConstraintOutput,
    ValidationResult,
    ValidationIssue,
    ValidationStatus,
)
from Services.constraintAgent.Rules.iso_rules      import run_all_iso_checks
from Services.constraintAgent.Rules.business_rules import run_all_business_checks


class Validator:


    def validate(self, output: ConstraintOutput) -> ValidationResult:
        issues   = []
        warnings = []

        # ── ISO rules (limits, max hours, breaks, session duration...) ─────────
        issues += run_all_iso_checks(output)

        # ── Business rules (constraint integrity before schedule generation) ────
        issues += run_all_business_checks(output)

        # ── Coherence soft checks (warnings only) ─────────────────────────────
        issues   += self._check_coherence(output)
        warnings += self._collect_warnings(output)

        # ── Determine overall status ──────────────────────────────────────────
        if any(i.severity == ValidationStatus.INVALID  for i in issues):
            status = ValidationStatus.INVALID
        elif any(i.severity == ValidationStatus.CONFLICT for i in issues):
            status = ValidationStatus.CONFLICT
        elif any(i.severity == ValidationStatus.WARNING  for i in issues) or warnings:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.VALID

        is_valid = status not in (ValidationStatus.INVALID, ValidationStatus.CONFLICT)

        result = ValidationResult(
            status   = status,
            issues   = issues,
            warnings = warnings,
            is_valid = is_valid,
        )

        # ── Print summary ─────────────────────────────────────────────────────
        print(f"\n  [Validator] Status: {status.value.upper()}")
        for issue in issues:
            icon = "❌" if issue.severity == ValidationStatus.INVALID  else \
                   "⚠️ " if issue.severity == ValidationStatus.CONFLICT else "ℹ️ "
            print(f"  {icon} [{issue.field}] {issue.message}")
            if issue.suggestion:
                print(f"       → {issue.suggestion}")
        for w in warnings:
            print(f"  💡 {w}")

        return result

    # ==========================================================================
    #  COHERENCE CHECKS  (soft, non-blocking — not in iso_rules or business_rules)
    # ==========================================================================

    def _check_coherence(self, o: ConstraintOutput) -> list[ValidationIssue]:

        issues = []

        # Lunch break defined but sessions_per_day not set
        if o.lunch_break_after_n_sessions and not o.sessions_per_day:
            issues.append(ValidationIssue(
                field      = "lunch_break_after_n_sessions",
                message    = "A lunch break is defined but sessions_per_day is not set — cannot compute when to insert it.",
                severity   = ValidationStatus.WARNING,
                suggestion = "Also set sessions_per_day so the agent knows the full day structure.",
            ))

        # Session duration set but sessions_per_day missing
        if o.session_duration_override and not o.sessions_per_day:
            issues.append(ValidationIssue(
                field      = "sessions_per_day",
                message    = "session_duration_override is set but sessions_per_day is not — day structure is incomplete.",
                severity   = ValidationStatus.WARNING,
                suggestion = "Set sessions_per_day to define how many sessions happen per day.",
            ))

        # Trainer available only on a forbidden day
        for trainer, avail in o.trainer_availability.items():
            for day in o.forbidden_days:
                if day.lower() in avail.lower():
                    issues.append(ValidationIssue(
                        field      = "trainer_availability",
                        message    = f"Trainer '{trainer}' is available on '{day}', but '{day}' is a forbidden day.",
                        severity   = ValidationStatus.WARNING,
                        suggestion = f"Remove '{day}' from forbidden_days or update {trainer}'s availability.",
                    ))

        return issues

    # ==========================================================================
    #  SOFT WARNINGS  (informational — planning continues)
    # ==========================================================================

    def _collect_warnings(self, o: ConstraintOutput) -> list[str]:
        warnings = []

        if not o.forbidden_days:
            warnings.append(
                "No forbidden days set — sessions will be planned Monday to Friday."
            )

        if not o.trainer_availability:
            warnings.append(
                "No trainer availability constraints — all trainers are considered available every day."
            )

        if o.pedagogical_rules:
            preview = "; ".join(o.pedagogical_rules[:3])
            suffix  = "..." if len(o.pedagogical_rules) > 3 else ""
            warnings.append(
                f"{len(o.pedagogical_rules)} pedagogical rule(s) applied as preferences: "
                f"{preview}{suffix}"
            )

        if not o.session_duration_override:
            warnings.append(
                "No session duration specified — default of 180min (3h) will be used."
            )

        return warnings