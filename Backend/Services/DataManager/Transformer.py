"""
agents/data_manager/transformer/data_transformer.py
=====================================================
Transforms classified records (from LLM extractor)
into clean, DB-ready dicts matching the SQLAlchemy models exactly.

Input  : list of classified dicts (entity_type + standardized fields)
Output : dict grouped by entity type, ready for the DB loader
"""

import json


# =============================================================================
#  Type coercion helpers
# =============================================================================

def _to_str(val, default: str = "") -> str:
    return str(val).strip() if val is not None and str(val).strip() else default

def _to_int(val, default: int = 0) -> int:
    try:    return int(float(str(val).replace(",", ".")))
    except: return default

def _to_float(val, default: float = 0.0) -> float:
    try:    return float(str(val).replace(",", "."))
    except: return default

def _to_list(val) -> list:
    if isinstance(val, list):   return val
    if isinstance(val, str):
        if val.strip() == "":   return []
        return [v.strip() for v in val.split(",") if v.strip()]
    return []

def _to_json(val) -> dict:
    if isinstance(val, dict):   return val
    if isinstance(val, str):
        try:    return json.loads(val)
        except: return {"value": val}
    return {}


# =============================================================================
#  Per-entity transformers
# =============================================================================

def _transform_course(fields: dict) -> dict:
    return {
        "title":                  _to_str(fields.get("title"), "Untitled Course"),
        "description":            _to_str(fields.get("description")),
        "total_hours":            _to_float(fields.get("total_hours", 0)),
        "session_duration":       _to_int(fields.get("session_duration", 3)),
        "pedagogical_objectives": _to_str(fields.get("pedagogical_objectives")),
        "required_equipments":    _to_list(fields.get("required_equipments", [])),
    }

def _transform_trainer(fields: dict) -> dict:
    name = _to_str(fields.get("name"), "Unknown Trainer")
    return {
        "name":               name,
        "email":              _to_str(fields.get("email"))
                              or f"{name.lower().replace(' ', '.')}@import.local",
        "specialization":     _to_str(fields.get("specialization")),
        "availability_notes": _to_str(fields.get("availability_notes")),
    }

def _transform_room(fields: dict) -> dict:
    return {
        "name":      _to_str(fields.get("name"), "Unnamed Room"),
        "capacity":  _to_int(fields.get("capacity", 1)),
        "room_type": _to_str(fields.get("room_type")),
    }

def _transform_group(fields: dict) -> dict:
    return {
        "name":  _to_str(fields.get("name"), "Unnamed Group"),
        "size":  _to_int(fields.get("size", 1)),
        "level": _to_str(fields.get("level")),
    }

def _transform_equipment(fields: dict) -> dict:
    return {
        "name":           _to_str(fields.get("name"), "Unnamed Equipment"),
        "description":    _to_str(fields.get("description")),
        "total_quantity": _to_int(fields.get("total_quantity", 1)),
    }

def _transform_constraint(fields: dict) -> dict:
    return {
        "constraint_type": _to_str(fields.get("constraint_type"), "other"),
        "constraint_data": _to_json(fields.get("constraint_data", {})),
    }


# =============================================================================
#  Dispatcher
# =============================================================================

_TRANSFORMERS = {
    "course":     _transform_course,
    "trainer":    _transform_trainer,
    "room":       _transform_room,
    "group":      _transform_group,
    "equipment":  _transform_equipment,
    "constraint": _transform_constraint,
}


# =============================================================================
#  Main transform function
# =============================================================================

def transform(classified_records: list[dict]) -> dict:
    """
    Transforms classified records into DB-ready dicts grouped by entity type.

    Args:
        classified_records: output of llm_extractor.extract_entities()

    Returns:
        Dict grouped by entity type:
        {
            "courses":     [ { title, total_hours, ... }, ... ],
            "trainers":    [ { name, email, ... }, ... ],
            "rooms":       [ ... ],
            "groups":      [ ... ],
            "equipments":  [ ... ],
            "constraints": [ ... ],
            "unknown":     [ ... ],   # records that could not be classified
        }
    """
    result = {
        "courses":     [],
        "trainers":    [],
        "rooms":       [],
        "groups":      [],
        "equipments":  [],
        "constraints": [],
        "unknown":     [],
    }

    for item in classified_records:
        entity_type = item.get("entity_type", "unknown")
        raw_fields  = item.get("standardized", {})

        transformer = _TRANSFORMERS.get(entity_type)

        if transformer:
            try:
                cleaned = transformer(raw_fields)
                result[entity_type + "s"].append({
                    **cleaned,
                    "_original": item.get("original", {}),  # kept for validation display
                })
            except Exception as e:
                print(f"  [Transformer] Failed to transform {entity_type}: {e}")
                result["unknown"].append(item)
        else:
            result["unknown"].append(item)

    # Print summary
    for key, items in result.items():
        if items:
            print(f"  [Transformer] {key}: {len(items)} record(s) ready.")

    return result