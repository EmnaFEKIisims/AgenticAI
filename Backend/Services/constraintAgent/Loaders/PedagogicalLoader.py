from sqlalchemy.orm import Session
from models.constraints import Constraint
from Services.constraintAgent.Schema import PedagogicalConstraint, ConstraintSeverity


# =============================================================================
#  PEDAGOGICAL CONSTRAINT TYPES  (stored in DB)
# =============================================================================

PEDAGOGICAL_TYPE_MAP = {
    "pedagogical_progression":       "progression",
    "pedagogical_load":              "load",
    "pedagogical_balance":           "balance",
    "pedagogical_rule":              "other",
    "pedagogical_hard_constraint":   "other",
    "pedagogical_soft_constraint":   "other",
}

PEDAGOGICAL_SEVERITY_MAP = {
    "pedagogical_hard_constraint": ConstraintSeverity.HARD,
    "pedagogical_progression":     ConstraintSeverity.HARD,
    "pedagogical_load":            ConstraintSeverity.SOFT,
    "pedagogical_balance":         ConstraintSeverity.SOFT,
    "pedagogical_rule":            ConstraintSeverity.SOFT,
    "pedagogical_soft_constraint": ConstraintSeverity.SOFT,
}


class PedagogicalLoader:


    def __init__(self, db: Session):
        self.db = db

    def load(self, user_text: str = "") -> tuple[list[PedagogicalConstraint], str]:

        db_rules = self._load_from_db()

        print(f"  [PedagogicalLoader] {len(db_rules)} rule(s) from DB.")
        if user_text.strip():
            print(f"  [PedagogicalLoader] User pedagogical text received ({len(user_text)} chars).")
        else:
            print(f"  [PedagogicalLoader] No user pedagogical text provided.")

        return db_rules, user_text

    def _load_from_db(self) -> list[PedagogicalConstraint]:
        rows   = self.db.query(Constraint).all()
        result = []

        for row in rows:
            category = PEDAGOGICAL_TYPE_MAP.get(row.constraint_type)
            if category is None:
                continue  # not pedagogical → skip

            cdata    = row.constraint_data
            rule     = cdata.get("rule") or cdata.get("value") or str(cdata)
            severity = PEDAGOGICAL_SEVERITY_MAP.get(
                row.constraint_type, ConstraintSeverity.SOFT
            )

            result.append(PedagogicalConstraint(
                rule     = str(rule),
                severity = severity,
                category = category,
                raw_text = str(cdata),
            ))

        return result