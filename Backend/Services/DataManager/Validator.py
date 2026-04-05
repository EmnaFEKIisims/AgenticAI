"""
agents/data_manager/validator/data_validator.py
================================================
Validates transformed records before DB insertion.

Checks per entity:
  - Required fields present and non-empty
  - Numeric fields have valid values (> 0)
  - No duplicate names within the same batch
  - Cross-entity coherence (e.g. session_duration <= total_hours)

Input  : transformed dict (output of data_transformer.transform())
Output : ValidationResult with valid records + list of issues
"""

from dataclasses import dataclass, field


# =============================================================================
#  Result type
# =============================================================================

@dataclass
class ValidationIssue:
    entity_type: str
    record:      dict
    issues:      list[str]


@dataclass
class ValidationResult:
    valid:    dict          # same structure as transformer output — only valid records
    issues:   list[ValidationIssue]
    is_clean: bool          # True if zero issues


# =============================================================================
#  Per-entity validation rules
# =============================================================================

def _validate_course(record: dict) -> list[str]:
    issues = []
    if not record.get("title"):
        issues.append("Missing required field: 'title'")
    if _to_float(record.get("total_hours")) <= 0:
        issues.append(f"Invalid 'total_hours': {record.get('total_hours')} (must be > 0)")
    if _to_int(record.get("session_duration")) <= 0:
        issues.append(f"Invalid 'session_duration': {record.get('session_duration')} (must be > 0)")
    duration = _to_float(record.get("session_duration", 1))
    hours    = _to_float(record.get("total_hours", 0))
    if duration > 0 and hours > 0 and duration > hours:
        issues.append(
            f"'session_duration' ({duration}h) cannot be greater than 'total_hours' ({hours}h)"
        )
    return issues

def _validate_trainer(record: dict) -> list[str]:
    issues = []
    if not record.get("name"):
        issues.append("Missing required field: 'name'")
    if record.get("email") and "@" not in record["email"]:
        issues.append(f"Invalid email format: '{record['email']}'")
    return issues

def _validate_room(record: dict) -> list[str]:
    issues = []
    if not record.get("name"):
        issues.append("Missing required field: 'name'")
    if _to_int(record.get("capacity")) <= 0:
        issues.append(f"Invalid 'capacity': {record.get('capacity')} (must be > 0)")
    return issues

def _validate_group(record: dict) -> list[str]:
    issues = []
    if not record.get("name"):
        issues.append("Missing required field: 'name'")
    if _to_int(record.get("size")) <= 0:
        issues.append(f"Invalid 'size': {record.get('size')} (must be > 0)")
    return issues

def _validate_equipment(record: dict) -> list[str]:
    issues = []
    if not record.get("name"):
        issues.append("Missing required field: 'name'")
    if _to_int(record.get("total_quantity")) <= 0:
        issues.append(f"Invalid 'total_quantity': {record.get('total_quantity')} (must be > 0)")
    return issues

def _validate_constraint(record: dict) -> list[str]:
    issues = []
    if not record.get("constraint_type"):
        issues.append("Missing required field: 'constraint_type'")
    if not isinstance(record.get("constraint_data"), dict):
        issues.append("'constraint_data' must be a JSON object")
    return issues


_VALIDATORS = {
    "courses":     _validate_course,
    "trainers":    _validate_trainer,
    "rooms":       _validate_room,
    "groups":      _validate_group,
    "equipments":  _validate_equipment,
    "constraints": _validate_constraint,
}


# =============================================================================
#  Duplicate detection within the same batch
# =============================================================================

def _check_duplicates(records: list[dict], name_field: str) -> list[ValidationIssue]:
    seen   = {}
    issues = []
    for i, record in enumerate(records):
        name = record.get(name_field, "").lower()
        if name and name in seen:
            issues.append(ValidationIssue(
                entity_type = "duplicate",
                record      = record,
                issues      = [f"Duplicate {name_field}: '{record.get(name_field)}' "
                               f"(also at row {seen[name]})"]
            ))
        else:
            seen[name] = i
    return issues


# =============================================================================
#  Helpers
# =============================================================================

def _to_float(val) -> float:
    try:    return float(str(val).replace(",", "."))
    except: return 0.0

def _to_int(val) -> int:
    try:    return int(float(str(val).replace(",", ".")))
    except: return 0


# =============================================================================
#  Main validation function
# =============================================================================

def validate(transformed: dict) -> ValidationResult:
    """
    Validates all transformed records.

    Args:
        transformed: output of data_transformer.transform()

    Returns:
        ValidationResult with:
          - valid   : only records that passed all checks
          - issues  : list of ValidationIssue for failed records
          - is_clean: True if no issues found
    """
    valid  = {k: [] for k in transformed}
    issues = []

    # Per-entity field validation
    for entity_key, records in transformed.items():
        validator = _VALIDATORS.get(entity_key)
        if not validator:
            valid[entity_key] = records  # unknown/no validator -> pass through
            continue

        for record in records:
            record_issues = validator(record)
            if record_issues:
                issues.append(ValidationIssue(
                    entity_type = entity_key,
                    record      = record,
                    issues      = record_issues,
                ))
            else:
                valid[entity_key].append(record)

    # Duplicate detection (by "name" field)
    name_keyed = ["courses", "trainers", "rooms", "groups", "equipments"]
    for key in name_keyed:
        issues.extend(_check_duplicates(valid.get(key, []), "name"))

    # Print summary
    total_valid   = sum(len(v) for v in valid.values())
    total_invalid = len(issues)
    print(f"  [Validator] {total_valid} valid record(s), {total_invalid} issue(s) found.")
    for issue in issues:
        print(f"    ⚠️  [{issue.entity_type}] {issue.issues} | record: {str(issue.record)[:80]}")

    return ValidationResult(
        valid    = valid,
        issues   = issues,
        is_clean = len(issues) == 0,
    )