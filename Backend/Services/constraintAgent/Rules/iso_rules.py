from Services.constraintAgent.Schema import (
    ConstraintOutput, ValidationIssue, ValidationStatus
)


# =============================================================================
#  ISO LIMITS  (constants — adjust per jurisdiction/standard)
# =============================================================================

ISO_MAX_HOURS_PER_DAY             = 8.0    # legal maximum training hours per day
ISO_MIN_SESSION_DURATION_MINUTES  = 30     # shortest acceptable session
ISO_MAX_SESSION_DURATION_MINUTES  = 480    # longest acceptable session (8h)
ISO_MIN_SESSIONS_PER_DAY          = 1
ISO_MAX_SESSIONS_PER_DAY          = 10
ISO_MIN_BREAK_BETWEEN_SESSIONS    = 5      # minimum break between sessions (minutes)
ISO_MIN_LUNCH_BREAK_DURATION      = 30     # minimum lunch break (minutes)
ISO_MAX_CONSECUTIVE_SESSIONS      = 4      # before a mandatory break is required


# =============================================================================
#  ISO RULE FUNCTIONS  (each returns a list of ValidationIssue)
# =============================================================================

def check_max_hours_per_day(o: ConstraintOutput) -> list[ValidationIssue]:

    issues = []

    # Check that max_hours_per_day itself does not exceed the legal limit
    if o.max_hours_per_day is not None and o.max_hours_per_day > ISO_MAX_HOURS_PER_DAY:
        issues.append(ValidationIssue(
            field    = "max_hours_per_day",
            message  = (
                f"max_hours_per_day={o.max_hours_per_day}h exceeds the ISO legal limit "
                f"of {ISO_MAX_HOURS_PER_DAY}h per day."
            ),
            severity = ValidationStatus.INVALID,
            suggestion = f"Set max_hours_per_day <= {ISO_MAX_HOURS_PER_DAY}.",
        ))

    # Check that the computed day duration does not exceed the limit
    if o.session_duration_override and o.sessions_per_day:
        sessions_min = o.session_duration_override * o.sessions_per_day
        breaks_min   = (o.break_between_sessions_minutes or 0) * max(o.sessions_per_day - 1, 0)
        lunch_min    = (o.lunch_break_duration_minutes or 0) if o.lunch_break_after_n_sessions else 0
        total_min    = sessions_min + breaks_min + lunch_min
        limit_min    = (o.max_hours_per_day or ISO_MAX_HOURS_PER_DAY) * 60

        if total_min > limit_min:
            issues.append(ValidationIssue(
                field    = "session_duration_override + sessions_per_day",
                message  = (
                    f"Computed day total = {total_min}min "
                    f"({o.sessions_per_day} sessions × {o.session_duration_override}min "
                    f"+ {breaks_min}min breaks + {lunch_min}min lunch) "
                    f"exceeds the ISO limit of {int(limit_min)}min "
                    f"({o.max_hours_per_day or ISO_MAX_HOURS_PER_DAY}h)."
                ),
                severity = ValidationStatus.CONFLICT,
                suggestion = (
                    "Reduce session count, session duration, or increase max_hours_per_day "
                    f"(max {ISO_MAX_HOURS_PER_DAY}h)."
                ),
            ))

    return issues


def check_mandatory_breaks(o: ConstraintOutput) -> list[ValidationIssue]:

    issues = []
    if (o.break_between_sessions_minutes is not None
            and o.break_between_sessions_minutes < ISO_MIN_BREAK_BETWEEN_SESSIONS):
        issues.append(ValidationIssue(
            field    = "break_between_sessions_minutes",
            message  = (
                f"Break between sessions = {o.break_between_sessions_minutes}min "
                f"is below the ISO minimum of {ISO_MIN_BREAK_BETWEEN_SESSIONS}min."
            ),
            severity = ValidationStatus.CONFLICT,
            suggestion = f"Set break_between_sessions_minutes >= {ISO_MIN_BREAK_BETWEEN_SESSIONS}.",
        ))
    return issues


def check_lunch_break(o: ConstraintOutput) -> list[ValidationIssue]:

    issues = []
    if (o.lunch_break_duration_minutes is not None
            and o.lunch_break_duration_minutes < ISO_MIN_LUNCH_BREAK_DURATION):
        issues.append(ValidationIssue(
            field    = "lunch_break_duration_minutes",
            message  = (
                f"Lunch break = {o.lunch_break_duration_minutes}min "
                f"is below the ISO minimum of {ISO_MIN_LUNCH_BREAK_DURATION}min."
            ),
            severity = ValidationStatus.CONFLICT,
            suggestion = f"Set lunch_break_duration_minutes >= {ISO_MIN_LUNCH_BREAK_DURATION}.",
        ))
    return issues


def check_consecutive_sessions(o: ConstraintOutput) -> list[ValidationIssue]:

    issues = []
    if (o.max_consecutive_sessions is not None
            and o.max_consecutive_sessions > ISO_MAX_CONSECUTIVE_SESSIONS):
        issues.append(ValidationIssue(
            field    = "max_consecutive_sessions",
            message  = (
                f"max_consecutive_sessions={o.max_consecutive_sessions} "
                f"exceeds the ISO maximum of {ISO_MAX_CONSECUTIVE_SESSIONS}."
            ),
            severity = ValidationStatus.CONFLICT,
            suggestion = f"Set max_consecutive_sessions <= {ISO_MAX_CONSECUTIVE_SESSIONS}.",
        ))

    # Cross-check: if lunch_break_after_n_sessions > max_consecutive_sessions
    if (o.lunch_break_after_n_sessions and o.max_consecutive_sessions
            and o.lunch_break_after_n_sessions > o.max_consecutive_sessions):
        issues.append(ValidationIssue(
            field    = "lunch_break_after_n_sessions",
            message  = (
                f"Lunch break is inserted after {o.lunch_break_after_n_sessions} sessions, "
                f"but max_consecutive_sessions = {o.max_consecutive_sessions}. "
                f"A mandatory break must occur before the lunch break."
            ),
            severity = ValidationStatus.CONFLICT,
            suggestion = (
                f"Set lunch_break_after_n_sessions <= {o.max_consecutive_sessions}."
            ),
        ))
    return issues


def check_session_duration(o: ConstraintOutput) -> list[ValidationIssue]:

    issues = []
    if o.session_duration_override is None:
        return issues

    if o.session_duration_override < ISO_MIN_SESSION_DURATION_MINUTES:
        issues.append(ValidationIssue(
            field    = "session_duration_override",
            message  = (
                f"Session duration {o.session_duration_override}min "
                f"is below the minimum of {ISO_MIN_SESSION_DURATION_MINUTES}min."
            ),
            severity = ValidationStatus.INVALID,
            suggestion = f"Set session_duration_override >= {ISO_MIN_SESSION_DURATION_MINUTES}.",
        ))
    if o.session_duration_override > ISO_MAX_SESSION_DURATION_MINUTES:
        issues.append(ValidationIssue(
            field    = "session_duration_override",
            message  = (
                f"Session duration {o.session_duration_override}min "
                f"exceeds the maximum of {ISO_MAX_SESSION_DURATION_MINUTES}min."
            ),
            severity = ValidationStatus.INVALID,
            suggestion = "Split into multiple sessions.",
        ))
    return issues


def check_sessions_per_day(o: ConstraintOutput) -> list[ValidationIssue]:

    issues = []
    if o.sessions_per_day is None:
        return issues
    if o.sessions_per_day < ISO_MIN_SESSIONS_PER_DAY:
        issues.append(ValidationIssue(
            field    = "sessions_per_day",
            message  = f"sessions_per_day={o.sessions_per_day} must be >= {ISO_MIN_SESSIONS_PER_DAY}.",
            severity = ValidationStatus.INVALID,
            suggestion = "Set sessions_per_day >= 1.",
        ))
    if o.sessions_per_day > ISO_MAX_SESSIONS_PER_DAY:
        issues.append(ValidationIssue(
            field    = "sessions_per_day",
            message  = f"sessions_per_day={o.sessions_per_day} exceeds ISO max of {ISO_MAX_SESSIONS_PER_DAY}.",
            severity = ValidationStatus.INVALID,
            suggestion = f"Set sessions_per_day <= {ISO_MAX_SESSIONS_PER_DAY}.",
        ))
    return issues


# =============================================================================
#  MASTER ISO CHECK — runs all ISO rules
# =============================================================================

def run_all_iso_checks(output: ConstraintOutput) -> list[ValidationIssue]:

    issues = []
    issues += check_max_hours_per_day(output)
    issues += check_mandatory_breaks(output)
    issues += check_lunch_break(output)
    issues += check_consecutive_sessions(output)
    issues += check_session_duration(output)
    issues += check_sessions_per_day(output)
    return issues