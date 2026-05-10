from sqlalchemy.orm import Session
from models.constraints import Constraint
from Services.constraintAgent.Schema import ISOConstraint, ConstraintSeverity


# Normalize DB type → internal type used by Analyzer
ISO_TYPE_MAP = {
    "iso_max_hours_per_day":                  "max_hours_per_day",
    "iso_mandatory_break_minutes":            "mandatory_break_minutes",
    "iso_max_consecutive_sessions":           "max_consecutive_sessions",
    "iso_min_break_between_sessions_minutes": "min_break_between_sessions_minutes",
    "iso_sessions_per_day":                   "sessions_per_day",
    "iso_lunch_break_after_n_sessions":       "lunch_break_after_n_sessions",
    "iso_lunch_break_duration_minutes":       "lunch_break_duration_minutes",
    "iso_day_start_time":                     "day_start_time",
    "iso_forbidden_days":                     "forbidden_days",
    # Without prefix (backward compatibility)
    "max_hours_per_day":                      "max_hours_per_day",
    "mandatory_break_minutes":                "mandatory_break_minutes",
    "max_consecutive_sessions":               "max_consecutive_sessions",
    "min_break_between_sessions_minutes":     "min_break_between_sessions_minutes",
}

ISO_SEVERITY = {
    "max_hours_per_day":                  ConstraintSeverity.HARD,
    "mandatory_break_minutes":            ConstraintSeverity.HARD,
    "max_consecutive_sessions":           ConstraintSeverity.HARD,
    "min_break_between_sessions_minutes": ConstraintSeverity.HARD,
    "sessions_per_day":                   ConstraintSeverity.SOFT,
    "lunch_break_after_n_sessions":       ConstraintSeverity.SOFT,
    "lunch_break_duration_minutes":       ConstraintSeverity.SOFT,
    "day_start_time":                     ConstraintSeverity.SOFT,
    "forbidden_days":                     ConstraintSeverity.HARD,
}

ISO_DESCRIPTIONS = {
    "max_hours_per_day":                  "Maximum training hours allowed per day.",
    "mandatory_break_minutes":            "Mandatory break between sessions.",
    "max_consecutive_sessions":           "Max consecutive sessions without a break.",
    "min_break_between_sessions_minutes": "Minimum break between two sessions.",
    "sessions_per_day":                   "Number of sessions per working day.",
    "lunch_break_after_n_sessions":       "Insert lunch break after N sessions.",
    "lunch_break_duration_minutes":       "Duration of the lunch break in minutes.",
    "day_start_time":                     "Time the first session starts (HH:MM).",
    "forbidden_days":                     "Days where no sessions can be scheduled.",
}


class ISOLoader:


    def __init__(self, db: Session):
        self.db = db

    def load(self) -> list[ISOConstraint]:
       
        rows   = self.db.query(Constraint).all()
        result = []

        for row in rows:
            normalized = ISO_TYPE_MAP.get(row.constraint_type)
            if normalized is None:
                continue  # not ISO → skip

            cdata = row.constraint_data  # already a dict (SQLAlchemy JSON)
            value = cdata.get("value") or cdata.get("days") or cdata

            result.append(ISOConstraint(
                constraint_type = normalized,
                value           = value,
                severity        = ISO_SEVERITY.get(normalized, ConstraintSeverity.HARD),
                description     = ISO_DESCRIPTIONS.get(normalized, ""),
            ))

        print(f"  [ISOLoader] {len(result)} ISO constraint(s) loaded from DB.")
        for c in result:
            print(f"    [{c.severity.value.upper()}] {c.constraint_type} = {c.value}")

        return result