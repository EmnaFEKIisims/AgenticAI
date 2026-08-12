from Services.constraintAgent.Schema import (
    ConstraintOutput, ValidationIssue, ValidationStatus
)


# =============================================================================
#  BUSINESS RULE FUNCTIONS
# =============================================================================

def check_no_double_booking_trainer(schedule: list[dict]) -> list[ValidationIssue]:

    issues = []
    seen: dict[tuple, int] = {}   # (trainer_id, start_time) → session_number

    for s in schedule:
        key = (s["trainer_id"], s["start_time"])
        if key in seen:
            issues.append(ValidationIssue(
                field    = "trainer_id",
                message  = (
                    f"Trainer {s['trainer_name']} (id={s['trainer_id']}) is double-booked: "
                    f"session #{seen[key]} and session #{s['session_number']} "
                    f"both start at {s['start_time']}."
                ),
                severity = ValidationStatus.CONFLICT,
                suggestion = "Assign a different trainer or time slot to one of these sessions.",
            ))
        else:
            seen[key] = s["session_number"]

    return issues


def check_no_double_booking_room(schedule: list[dict]) -> list[ValidationIssue]:

    issues = []
    seen: dict[tuple, int] = {}   # (room_id, start_time) → session_number

    for s in schedule:
        key = (s["room_id"], s["start_time"])
        if key in seen:
            issues.append(ValidationIssue(
                field    = "room_id",
                message  = (
                    f"Room '{s['room_name']}' (id={s['room_id']}) is double-booked: "
                    f"session #{seen[key]} and session #{s['session_number']} "
                    f"both start at {s['start_time']}."
                ),
                severity = ValidationStatus.CONFLICT,
                suggestion = "Assign a different room or time slot to one of these sessions.",
            ))
        else:
            seen[key] = s["session_number"]

    return issues


def check_no_group_overlap(schedule: list[dict]) -> list[ValidationIssue]:

    issues = []
    seen: dict[tuple, int] = {}   # (learner_group_id, start_time) → session_number

    for s in schedule:
        key = (s["learner_group_id"], s["start_time"])
        if key in seen:
            issues.append(ValidationIssue(
                field    = "learner_group_id",
                message  = (
                    f"Group '{s['group_name']}' (id={s['learner_group_id']}) "
                    f"is scheduled in two sessions at the same time: "
                    f"session #{seen[key]} and session #{s['session_number']} "
                    f"both start at {s['start_time']}."
                ),
                severity = ValidationStatus.CONFLICT,
                suggestion = "Move one of these sessions to a different time slot.",
            ))
        else:
            seen[key] = s["session_number"]

    return issues


def check_room_capacity(schedule: list[dict], groups: list[dict], rooms: list[dict]) -> list[ValidationIssue]:

    issues = []
    group_map = {g["id"]: g for g in groups}
    room_map  = {r["id"]: r for r in rooms}

    for s in schedule:
        group = group_map.get(s["learner_group_id"])
        room  = room_map.get(s["room_id"])
        if not group or not room:
            continue

        if room["capacity"] < group["size"]:
            issues.append(ValidationIssue(
                field    = "room_id",
                message  = (
                    f"Session #{s['session_number']}: Room '{room['name']}' "
                    f"(capacity={room['capacity']}) is too small for group "
                    f"'{group['name']}' (size={group['size']})."
                ),
                severity = ValidationStatus.CONFLICT,
                suggestion = (
                    f"Assign a room with capacity >= {group['size']} "
                    f"for group '{group['name']}'."
                ),
            ))

    return issues


def check_trainer_specialization(schedule: list[dict], courses: list[dict],
                                  trainers: list[dict]) -> list[ValidationIssue]:

    issues = []
    course_map  = {c["id"]: c for c in courses}
    trainer_map = {t["id"]: t for t in trainers}

    for s in schedule:
        course  = course_map.get(s["course_id"])
        trainer = trainer_map.get(s["trainer_id"])
        if not course or not trainer:
            continue

        specialization = trainer.get("specialization", "").lower()
        course_title   = course.get("title", "").lower()

        if specialization and course_title not in specialization:
            issues.append(ValidationIssue(
                field    = "trainer_id",
                message  = (
                    f"Session #{s['session_number']}: Trainer '{trainer['name']}' "
                    f"(specialization: '{trainer.get('specialization', 'N/A')}') "
                    f"is assigned to course '{course['title']}' — no specialization match."
                ),
                severity = ValidationStatus.WARNING,
                suggestion = (
                    f"Consider assigning a trainer specialized in '{course['title']}'."
                ),
            ))

    return issues


def check_constraint_output_integrity(output: ConstraintOutput) -> list[ValidationIssue]:

    issues = []

    # All 5 weekdays forbidden
    all_weekdays = {"monday", "tuesday", "wednesday", "thursday", "friday"}
    forbidden_lower = {d.lower() for d in output.forbidden_days}
    if all_weekdays.issubset(forbidden_lower):
        issues.append(ValidationIssue(
            field    = "forbidden_days",
            message  = "All weekdays are forbidden — no sessions can be scheduled.",
            severity = ValidationStatus.INVALID,
            suggestion = "Remove at least one weekday from forbidden_days.",
        ))

    # Trainer available only on forbidden days
    for trainer_name, avail in output.trainer_availability.items():
        avail_lower = avail.lower()
        mentioned_days = [d for d in list(all_weekdays) + list(
            {"lundi","mardi","mercredi","jeudi","vendredi"}
        ) if d in avail_lower]
        available_non_forbidden = [
            d for d in mentioned_days
            if d not in forbidden_lower
        ]
        if mentioned_days and not available_non_forbidden:
            issues.append(ValidationIssue(
                field    = "trainer_availability",
                message  = (
                    f"Trainer '{trainer_name}' is only available on forbidden day(s): "
                    f"{mentioned_days}. They cannot be scheduled."
                ),
                severity = ValidationStatus.WARNING,
                suggestion = (
                    f"Remove '{trainer_name}'s days from forbidden_days, "
                    f"or update their availability."
                ),
            ))

    # min_room_capacity suspiciously high
    if output.min_room_capacity and output.min_room_capacity > 500:
        issues.append(ValidationIssue(
            field    = "min_room_capacity",
            message  = f"min_room_capacity={output.min_room_capacity} is unrealistically high.",
            severity = ValidationStatus.WARNING,
            suggestion = "Double-check this value — it may exclude all available rooms.",
        ))

    return issues


# =============================================================================
#  MASTER BUSINESS RULES CHECK
# =============================================================================

def run_all_business_checks(
    output:   ConstraintOutput,
    schedule: list[dict] | None = None,
    groups:   list[dict] | None = None,
    rooms:    list[dict] | None = None,
    courses:  list[dict] | None = None,
    trainers: list[dict] | None = None,
) -> list[ValidationIssue]:

    issues = []

    # Pre-generation: constraint integrity
    issues += check_constraint_output_integrity(output)

    # Post-generation: schedule integrity
    if schedule:
        issues += check_no_double_booking_trainer(schedule)
        issues += check_no_double_booking_room(schedule)
        issues += check_no_group_overlap(schedule)

        if groups and rooms:
            issues += check_room_capacity(schedule, groups, rooms)

        if courses and trainers:
            issues += check_trainer_specialization(schedule, courses, trainers)

    return issues