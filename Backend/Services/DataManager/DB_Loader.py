"""
agents/data_manager/loader/db_loader.py
========================================
Inserts validated, transformed records into the PostgreSQL database.
Skips duplicates (checks by name/title before inserting).

Input  : validated dict (output of data_validator.validate().valid)
         OR raw list[dict] (from temp_storage, after HITL approval)
Output : report dict { "courses": N, "trainers": N, ... }
"""

from sqlalchemy.orm import Session

from models.trainer     import Trainer
from models.learner     import LearnerGroup
from models.room        import Room
from models.equipment   import Equipment
from models.course      import Course
from models.constraints import Constraint


# =============================================================================
#  Per-entity insert functions (all skip duplicates)
# =============================================================================

def _insert_course(fields: dict, db: Session) -> bool:
    if db.query(Course).filter_by(title=fields["title"]).first():
        print(f"  [Loader] Skipped duplicate course: '{fields['title']}'")
        return False
    db.add(Course(
        title                  = fields["title"],
        description            = fields.get("description"),
        total_hours            = float(fields.get("total_hours", 0)),
        session_duration       = int(fields.get("session_duration", 3)),
        pedagogical_objectives = fields.get("pedagogical_objectives"),
    ))
    return True


def _insert_trainer(fields: dict, db: Session) -> bool:
    if db.query(Trainer).filter_by(name=fields["name"]).first():
        print(f"  [Loader] Skipped duplicate trainer: '{fields['name']}'")
        return False
    db.add(Trainer(
        name               = fields["name"],
        email              = fields.get("email") or f"{fields['name'].lower().replace(' ','.')}@import.local",
        specialization     = fields.get("specialization"),
        availability_notes = fields.get("availability_notes"),
    ))
    return True


def _insert_room(fields: dict, db: Session) -> bool:
    if db.query(Room).filter_by(name=fields["name"]).first():
        print(f"  [Loader] Skipped duplicate room: '{fields['name']}'")
        return False
    db.add(Room(
        name      = fields["name"],
        capacity  = int(fields.get("capacity", 1)),
        room_type = fields.get("room_type"),
    ))
    return True


def _insert_group(fields: dict, db: Session) -> bool:
    if db.query(LearnerGroup).filter_by(name=fields["name"]).first():
        print(f"  [Loader] Skipped duplicate group: '{fields['name']}'")
        return False
    db.add(LearnerGroup(
        name  = fields["name"],
        size  = int(fields.get("size", 1)),
        level = fields.get("level"),
    ))
    return True


def _insert_equipment(fields: dict, db: Session) -> bool:
    if db.query(Equipment).filter_by(name=fields["name"]).first():
        print(f"  [Loader] Skipped duplicate equipment: '{fields['name']}'")
        return False
    db.add(Equipment(
        name           = fields["name"],
        description    = fields.get("description"),
        total_quantity = int(fields.get("total_quantity", 1)),
    ))
    return True


def _insert_constraint(fields: dict, db: Session) -> bool:
    cdata = fields.get("constraint_data", {})
    if isinstance(cdata, str):
        import json
        try:    cdata = json.loads(cdata)
        except: cdata = {"value": cdata}
    db.add(Constraint(
        planning_id      = 1,  # default planning_id
        constraint_type  = fields.get("constraint_type", "other"),
        constraint_data  = cdata,
    ))
    return True


# =============================================================================
#  Dispatcher
# =============================================================================

_INSERTERS = {
    "courses":     _insert_course,
    "trainers":    _insert_trainer,
    "rooms":       _insert_room,
    "groups":      _insert_group,
    "equipments":  _insert_equipment,
    "constraints": _insert_constraint,
}


# =============================================================================
#  Main load function
# =============================================================================

def load_to_db(data: dict | list, db: Session) -> dict:
    """
    Inserts records into PostgreSQL.

    Args:
        data: either a grouped dict (from transformer/validator)
              OR a flat list[dict] with an "entity_type" key (from temp_storage)
        db:   SQLAlchemy session

    Returns:
        Report dict: { "courses": N, "trainers": N, ... }
    """
    report = {k: 0 for k in ["courses","trainers","rooms","groups","equipments","constraints","errors"]}

    # Normalize input: flat list -> grouped dict
    if isinstance(data, list):
        data = _flat_list_to_grouped(data)

    for entity_key, records in data.items():
        inserter = _INSERTERS.get(entity_key)
        if not inserter:
            continue  # skip "unknown"

        for record in records:
            # Strip internal keys added by transformer/validator
            fields = {k: v for k, v in record.items() if not k.startswith("_")}
            try:
                inserted = inserter(fields, db)
                if inserted:
                    report[entity_key] += 1
            except Exception as e:
                print(f"  [Loader] Error inserting {entity_key}: {e}")
                report["errors"] += 1

    try:
        db.commit()
        total = sum(v for k, v in report.items() if k != "errors")
        print(f"  [Loader] Committed {total} record(s) to DB. Errors: {report['errors']}")
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"DB commit failed: {e}")

    return report


# =============================================================================
#  Helper — normalize flat list to grouped dict
# =============================================================================

def _flat_list_to_grouped(records: list[dict]) -> dict:
    """
    Converts a flat list like:
      [{"entity_type": "course", "title": "Python", ...}, ...]
    into:
      {"courses": [{"title": "Python", ...}], ...}
    """
    grouped = {k: [] for k in ["courses","trainers","rooms","groups","equipments","constraints"]}
    for record in records:
        etype = record.get("entity_type", "unknown")
        key   = etype + "s"
        if key in grouped:
            fields = {k: v for k, v in record.items() if k != "entity_type"}
            grouped[key].append(fields)
    return grouped