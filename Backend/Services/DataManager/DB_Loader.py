"""
Services/DataManager/DB_Loader.py
===================================
Updated DB_Loader:
  - Injects user_id into ALL records (rooms, trainers, groups, courses, equipment)
  - Handles 'constraint' entity type:
      * source="ISO_21001" → user_id=None (global rule, shared)
      * source="user_defined" or anything else → user_id=current user (personal constraint)
"""

from sqlalchemy.orm import Session


# ISO standards are global — not user-specific
ISO_SOURCES = {"ISO_21001", "ISO 21001", "iso21001", "ISO_29993", "ISO 29993"}


def load_to_db(data: list[dict], db: Session, user_id: str = None) -> dict:
    """
    Inserts all records into their respective DB tables.

    Args:
        data:    flat list of dicts with 'entity_type' key
        db:      SQLAlchemy session
        user_id: the owner of this data (None = global/ISO)

    Returns:
        dict with insertion counts per entity type
    """
    report = {
        "trainers":       0,
        "rooms":          0,
        "learner_groups": 0,
        "courses":        0,
        "equipments":     0,
        "constraints":    0,
        "errors":         [],
    }

    for record in data:
        entity_type = record.get("entity_type", "").lower().strip()
        clean = {k: v for k, v in record.items() if not k.startswith("_") and k != "entity_type"}

        try:
            if entity_type in ("trainer", "trainers"):
                _insert_trainer(clean, db, user_id)
                report["trainers"] += 1

            elif entity_type in ("room", "rooms"):
                _insert_room(clean, db, user_id)
                report["rooms"] += 1

            elif entity_type in ("learner_group", "learnergroup", "group", "learner_groups"):
                _insert_learner_group(clean, db, user_id)
                report["learner_groups"] += 1

            elif entity_type in ("course", "courses"):
                _insert_course(clean, db, user_id)
                report["courses"] += 1

            elif entity_type in ("equipment", "equipments"):
                _insert_equipment(clean, db, user_id)
                report["equipments"] += 1

            elif entity_type in ("constraint", "constraints", "rule", "rules"):
                # ── Key logic: ISO constraints are global, others are user-specific ──
                source = clean.get("source", "user_defined")
                constraint_user_id = None if source in ISO_SOURCES else user_id
                _insert_constraint(clean, db, constraint_user_id)
                report["constraints"] += 1

            else:
                print(f"  [DB_Loader] ⚠️  Unknown entity type: '{entity_type}' — skipped.")

        except Exception as e:
            err = f"[{entity_type}] {e} — record: {clean}"
            report["errors"].append(err)
            print(f"  [DB_Loader] ❌ {err}")

    try:
        db.commit()
        print(f"  [DB_Loader] ✅ Committed: {report}")
    except Exception as e:
        db.rollback()
        report["errors"].append(f"Commit failed: {e}")
        print(f"  [DB_Loader] ❌ Commit failed: {e}")

    return report


# =============================================================================
#  Individual inserters
# =============================================================================

def _insert_trainer(data: dict, db: Session, user_id: str):
    from models.trainer import Trainer
    t = Trainer(
        name               = data.get("name", ""),
        email              = data.get("email", ""),
        specialization     = data.get("specialization"),
        availability_notes = data.get("availability_notes"),
        user_id            = user_id,
    )
    db.add(t)


def _insert_room(data: dict, db: Session, user_id: str):
    from models.room import Room
    r = Room(
        name      = data.get("name", ""),
        capacity  = int(data.get("capacity", 1)),
        room_type = data.get("room_type"),
        user_id   = user_id,
    )
    db.add(r)


def _insert_learner_group(data: dict, db: Session, user_id: str):
    from models.learner import LearnerGroup
    g = LearnerGroup(
        name    = data.get("name", ""),
        size    = int(data.get("size", 1)),
        level   = data.get("level"),
        user_id = user_id,
    )
    db.add(g)


def _insert_course(data: dict, db: Session, user_id: str):
    from models.course import Course
    c = Course(
        title                  = data.get("title", data.get("name", "")),
        description            = data.get("description"),
        total_hours            = float(data.get("total_hours", 1)),
        session_duration       = int(data.get("session_duration", 180)),
        pedagogical_objectives = data.get("pedagogical_objectives"),
        user_id                = user_id,
    )
    db.add(c)


def _insert_equipment(data: dict, db: Session, user_id: str):
    from models.equipment import Equipment
    e = Equipment(
        name           = data.get("name", ""),
        description    = data.get("description"),
        total_quantity = int(data.get("total_quantity", data.get("quantity", 1))),
        user_id        = user_id,
    )
    db.add(e)


def _insert_constraint(data: dict, db: Session, user_id: str | None):
    """
    Inserts a constraint record.
    user_id=None  → global ISO rule (visible to all users)
    user_id=uuid  → user-specific constraint (only visible to that user)
    """
    from models.constraints import Constraint   # adapt to your actual model
    c = Constraint(
        constraint_type = data.get("constraint_type", data.get("type", "custom")),
        description     = data.get("description", data.get("rule", "")),
        value           = data.get("value"),
        source          = data.get("source", "user_defined"),
        is_active       = True,
        user_id         = user_id,   # None for ISO, uuid for user-defined
    )
    db.add(c)