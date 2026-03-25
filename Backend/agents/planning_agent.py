"""
agents/planning_agent.py
========================
Process:

  CONSTRAINTS:
    Source 1 -> DB  (Constraints table, already stored)
    Source 2 -> User types free text (English or French)
                   -> LLM extracts -> JSON
    Both are merged into final constraints

  DATA:
    -> Loaded from DB if records exist
    -> Otherwise manual JSON input from user

  OUTPUT:
    -> Schedule table printed in console
    -> User validation (Y/N)
    -> CSV export (Y/N)
"""

import csv
import json
import math
import os
from sqlalchemy.orm import Session

from db.DB import SessionLocal
from models.trainer import Trainer
from models.learner import LearnerGroup
from models.room import Room
from models.equipment import Equipment
from models.course import Course
from models.constraints import Constraint
from core.LlmService import _ask_ollama


# =============================================================================
#  SYSTEM PROMPT — LLM extracts constraints from user free text
# =============================================================================

CONSTRAINT_EXTRACTION_PROMPT = """
You are a constraint extractor for a training planning system.
The user describes planning wishes in natural language (English or French).
Extract and return ONLY a valid JSON object. No markdown, no explanation.

JSON format to return:
{
  "forbidden_days": [],
  "trainer_availability": { "<trainer_name>": "<availability description>" },
  "session_duration_override": null,
  "min_room_capacity": null,
  "room_type_required": null,
  "group_priority": null,
  "no_parallel_sessions_same_group": false,
  "prefer_matching_specialization": true,
  "other": []
}

Extraction rules:
- Forbidden day mentioned (e.g. "no Friday", "pas le vendredi") -> add to "forbidden_days"
- Trainer availability mentioned -> add to "trainer_availability" with trainer name as key
- Session duration specified -> integer value in "session_duration_override"
- Minimum room capacity mentioned -> integer value in "min_room_capacity"
- Room type required -> string value in "room_type_required"
- Group to prioritize -> group name in "group_priority"
- No parallel sessions for same group -> set "no_parallel_sessions_same_group" to true
- Anything else -> add as string in "other"
- If a field is not mentioned -> keep its default value
"""


# =============================================================================
#  STEP 1 — Load constraints from the DB (Constraints table)
# =============================================================================

def _load_constraints_from_db(db: Session) -> tuple[dict, int]:

    rows = db.query(Constraint).all()

    # Default constraint structure
    merged = {
        "forbidden_days": [],
        "trainer_availability": {},
        "session_duration_override": None,
        "min_room_capacity": None,
        "room_type_required": None,
        "group_priority": None,
        "no_parallel_sessions_same_group": False,
        "prefer_matching_specialization": True,
        "other": []
    }

    for row in rows:
        ctype = row.constraint_type
        cdata = row.constraint_data  # already a dict thanks to SQLAlchemy JSON type

        if ctype == "forbidden_days":
            merged["forbidden_days"].extend(cdata.get("days", []))

        elif ctype == "trainer_availability":
            merged["trainer_availability"].update(cdata)

        elif ctype == "session_duration_override":
            merged["session_duration_override"] = cdata.get("value")

        elif ctype == "min_room_capacity":
            merged["min_room_capacity"] = cdata.get("value")

        elif ctype == "room_type_required":
            merged["room_type_required"] = cdata.get("value")

        elif ctype == "group_priority":
            merged["group_priority"] = cdata.get("value")

        elif ctype == "no_parallel_sessions_same_group":
            merged["no_parallel_sessions_same_group"] = cdata.get("value", False)

        elif ctype == "prefer_matching_specialization":
            merged["prefer_matching_specialization"] = cdata.get("value", True)

        else:
            merged["other"].append(cdata)

    return merged, len(rows)


# =============================================================================
#  STEP 2 — LLM extracts constraints from user free text
# =============================================================================

def _extract_constraints_from_text(user_text: str) -> dict:

    print("\n  [LLM] Extracting constraints from text...")
    raw = _ask_ollama(prompt=user_text, system=CONSTRAINT_EXTRACTION_PROMPT)

    cleaned = (
        raw.strip()
           .removeprefix("```json").removeprefix("```")
           .removesuffix("```").strip()
    )
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        print(f"  [WARNING] LLM response could not be parsed, skipping. Raw:\n{raw[:300]}")
        return {}


# =============================================================================
#  STEP 3 — Merge DB constraints + user constraints
# =============================================================================

def _merge_constraints(db_constraints: dict, user_constraints: dict) -> dict:

    merged = dict(db_constraints)

    # forbidden_days: union of both lists (no duplicates)
    merged["forbidden_days"] = list(
        set(merged["forbidden_days"] + user_constraints.get("forbidden_days", []))
    )

    # trainer_availability: merge both dicts
    merged["trainer_availability"].update(
        user_constraints.get("trainer_availability", {})
    )

    # Simple values: user overrides DB only if not null
    for key in ["session_duration_override", "min_room_capacity",
                "room_type_required", "group_priority"]:
        if user_constraints.get(key) is not None:
            merged[key] = user_constraints[key]

    # Booleans: logical OR
    if user_constraints.get("no_parallel_sessions_same_group"):
        merged["no_parallel_sessions_same_group"] = True
    if user_constraints.get("prefer_matching_specialization") is False:
        merged["prefer_matching_specialization"] = False

    # other: concatenate both lists
    merged["other"] = merged.get("other", []) + user_constraints.get("other", [])

    return merged


# =============================================================================
#  STEP 4 — Load data from DB or collect from user (manual JSON input)
# =============================================================================

JSON_TEMPLATE = {
    "courses": [
        {"id": 1, "title": "Python", "total_hours": 12, "session_duration": 3,
         "required_equipments": ["Laptop"]}
    ],
    "trainers": [
        {"id": 1, "name": "Ahmed Ben Ali", "specialization": "Python, Data",
         "availability_notes": "Monday and Wednesday morning 08:00-13:00"}
    ],
    "groups": [
        {"id": 1, "name": "Group A", "size": 15, "level": "beginner"}
    ],
    "rooms": [
        {"id": 1, "name": "Lab Room 1", "capacity": 20, "room_type": "Lab"}
    ],
    "equipments": [
        {"id": 1, "name": "Laptop", "total_quantity": 20}
    ]
}

def _load_data_from_db(db: Session) -> dict | None:
    """Loads all entity data from the DB. Returns None if all tables are empty."""
    trainers   = db.query(Trainer).all()
    groups     = db.query(LearnerGroup).all()
    rooms      = db.query(Room).all()
    equipments = db.query(Equipment).all()
    courses    = db.query(Course).all()

    if not any([trainers, groups, rooms, courses]):
        return None

    return {
        "courses": [
            {"id": c.id, "title": c.title, "total_hours": c.total_hours,
             "session_duration": c.session_duration,
             "required_equipments": [e.name for e in c.required_equipments]}
            for c in courses
        ],
        "trainers": [
            {"id": t.id, "name": t.name,
             "specialization": t.specialization or "",
             "availability_notes": t.availability_notes or ""}
            for t in trainers
        ],
        "groups": [
            {"id": g.id, "name": g.name, "size": g.size, "level": g.level or ""}
            for g in groups
        ],
        "rooms": [
            {"id": r.id, "name": r.name, "capacity": r.capacity,
             "room_type": r.room_type or ""}
            for r in rooms
        ],
        "equipments": [
            {"id": e.id, "name": e.name, "total_quantity": e.total_quantity}
            for e in equipments
        ],
    }

def _collect_data_from_user() -> dict:

    print("\n" + "=" * 65)
    print("  [INPUT] Database is empty — please enter your data as JSON")
    print("=" * 65)
    print("  Use the following template (replace values with your own):\n")
    print(json.dumps(JSON_TEMPLATE, indent=2))
    print("\n" + "-" * 65)
    print("  Paste your JSON below, then press Enter twice to confirm:\n")

    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)

    raw = "\n".join(lines).strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(raw)
    print("  [OK] Data received successfully.")
    return data


# =============================================================================
#  STEP 5 — Agent generates the schedule (pure Python logic)
# =============================================================================

DAY_ORDER  = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
# French day names for bilingual constraint matching
DAY_FR     = {"Monday": "lundi", "Tuesday": "mardi", "Wednesday": "mercredi",
              "Thursday": "jeudi", "Friday": "vendredi"}
TIME_SLOTS = ["08:00-11:00", "11:00-14:00", "14:00-17:00"]

def _generate_schedule(data: dict, constraints: dict) -> list[dict]:


    # Build allowed days from constraints
    forbidden    = [d.lower() for d in constraints.get("forbidden_days", [])]
    allowed_days = [
        d for d in DAY_ORDER
        if d.lower() not in forbidden and DAY_FR[d].lower() not in forbidden
    ]

    min_cap       = constraints.get("min_room_capacity")
    room_type_req = (constraints.get("room_type_required") or "").lower()
    trainer_avail = {
        k.lower(): v.lower()
        for k, v in constraints.get("trainer_availability", {}).items()
    }
    prefer_match = constraints.get("prefer_matching_specialization", True)

    # Availability trackers: (entity_id, day, slot) -> True if booked
    trainer_busy: dict = {}
    room_busy:    dict = {}
    group_busy:   dict = {}

    def is_free(tracker, eid, day, slot): return not tracker.get((eid, day, slot), False)
    def book(tracker, eid, day, slot):    tracker[(eid, day, slot)] = True

    # Filter rooms by constraints
    rooms = data.get("rooms", [])
    if min_cap:
        rooms = [r for r in rooms if r["capacity"] >= min_cap]
    if room_type_req:
        filtered = [r for r in rooms if room_type_req in r.get("room_type", "").lower()]
        if filtered:
            rooms = filtered

    def trainer_available_on(trainer: dict, day: str) -> bool:

        name = trainer["name"].lower()
        for key, avail in trainer_avail.items():
            if key in name:
                day_en = day.lower()
                day_fr = DAY_FR.get(day, "").lower()
                if day_en in avail or day_fr in avail:
                    return True
                # If specific days are mentioned but this day is not among them
                all_day_names = [d.lower() for d in DAY_ORDER] + list(DAY_FR.values())
                if any(d in avail for d in all_day_names):
                    return False
        return True  # No specific constraint -> available

    def best_trainer(course, day, slot):

        candidates = sorted(
            data.get("trainers", []),
            key=lambda t: course["title"].lower() in t.get("specialization", "").lower(),
            reverse=prefer_match
        )
        for t in candidates:
            if trainer_available_on(t, day) and is_free(trainer_busy, t["id"], day, slot):
                return t
        return None

    def best_room(group, day, slot):

        candidates = sorted(
            [r for r in rooms if r["capacity"] >= group["size"]],
            key=lambda r: r["capacity"]
        )
        for r in candidates:
            if is_free(room_busy, r["id"], day, slot):
                return r
        return None

    # Schedule generation
    schedule       = []
    session_global = 1

    for course in data.get("courses", []):
        duration    = constraints.get("session_duration_override") or course.get("session_duration", 3)
        nb_sessions = math.ceil(course["total_hours"] / duration)

        for group in data.get("groups", []):
            placed = 0
            snum   = 1
            # Repeat the day cycle as many times as needed to place all sessions
            day_cycle = allowed_days * (math.ceil(nb_sessions / max(len(allowed_days), 1)) + 2)

            for day in day_cycle:
                if placed >= nb_sessions:
                    break
                for slot in TIME_SLOTS:
                    if placed >= nb_sessions:
                        break
                    if not is_free(group_busy, group["id"], day, slot):
                        continue

                    trainer = best_trainer(course, day, slot)
                    room    = best_room(group, day, slot)

                    if trainer and room:
                        schedule.append({
                            "session_number": session_global,
                            "course_id":      course["id"],
                            "course_title":   course["title"],
                            "trainer_id":     trainer["id"],
                            "trainer_name":   trainer["name"],
                            "room_id":        room["id"],
                            "room_name":      room["name"],
                            "group_id":       group["id"],
                            "group_name":     group["name"],
                            "suggested_day":  day,
                            "suggested_time": slot,
                            "reasoning": (
                                f"S{snum}/{nb_sessions} | "
                                f"{trainer['name']} [{trainer.get('specialization', '')}] | "
                                f"{room['name']} capacity={room['capacity']}>={group['size']}"
                            )
                        })
                        book(trainer_busy, trainer["id"], day, slot)
                        book(room_busy,    room["id"],    day, slot)
                        book(group_busy,   group["id"],   day, slot)
                        placed         += 1
                        snum           += 1
                        session_global += 1

            if placed < nb_sessions:
                print(f"  [WARNING] Only {placed}/{nb_sessions} sessions scheduled "
                      f"for '{course['title']}' / '{group['name']}'")

    return schedule


# =============================================================================
#  DISPLAY — Print schedule table in console
# =============================================================================

def _print_schedule(schedule: list[dict]):
    W = 132
    print(f"\n{'=' * W}")
    print("  GENERATED SCHEDULE — Produced by the Planning Agent")
    print(f"{'=' * W}")
    print(
        f"  {'#':<4} {'Course':<18} {'Trainer':<20} {'Room':<16}"
        f" {'Group':<15} {'Day':<12} {'Time':<14} Reasoning"
    )
    print(f"  {'-' * W}")
    for s in schedule:
        print(
            f"  {s['session_number']:<4} "
            f"{str(s['course_title'])[:17]:<18} "
            f"{str(s['trainer_name'])[:19]:<20} "
            f"{str(s['room_name'])[:15]:<16} "
            f"{str(s['group_name'])[:14]:<15} "
            f"{str(s['suggested_day'])[:11]:<12} "
            f"{str(s['suggested_time'])[:13]:<14} "
            f"{str(s['reasoning'])[:52]}"
        )
    print(f"{'=' * W}")
    print(f"  Total: {len(schedule)} session(s) scheduled\n")


# =============================================================================
#  EXPORT CSV
# =============================================================================

FIELDNAMES = [
    "session_number", "course_id", "course_title",
    "trainer_id", "trainer_name", "room_id", "room_name",
    "group_id", "group_name", "suggested_day", "suggested_time", "reasoning",
]

def _export_csv(schedule: list[dict], filepath: str):
    """Exports the schedule to a CSV file."""
    folder = os.path.dirname(filepath)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(schedule)
    print(f"  [SAVED] CSV exported -> {os.path.abspath(filepath)}")


# =============================================================================
#  VALIDATION + CSV EXPORT PROMPT
# =============================================================================

def _validate_and_export(schedule: list[dict]) -> bool:
    """Asks the user to validate the schedule and optionally export it to CSV."""
    ans = input("  Validate this schedule? (Y/N): ").strip().upper()
    if ans == "Y":
        print("  [OK] Schedule validated!")
        if input("  Download as CSV? (Y/N): ").strip().upper() == "Y":
            path = input("  File path (press Enter for default: outputs/schedule.csv): ").strip()
            _export_csv(schedule, path or "outputs/schedule.csv")
        return True
    print("  [CANCELLED] Schedule not validated.")
    return False


# =============================================================================
#  PLANNING AGENT — Main orchestrator
# =============================================================================

class PlanningAgent:

    def __init__(self, db: Session):
        self.db = db

    def run(self) -> list[dict]:

        print("\n" + "=" * 60)
        print("       PLANNING AGENT — Phase 1")
        print("=" * 60)

        # -- Step 1: Load constraints from DB ----------------------------------
        print("\n[1/5] Loading constraints from database...")
        db_constraints, nb_rows = _load_constraints_from_db(self.db)
        if nb_rows:
            print(f"  [OK] {nb_rows} constraint(s) loaded from DB:")
            print(json.dumps(db_constraints, indent=2))
        else:
            print("  [INFO] No constraints found in DB.")

        # -- Step 2: Optional extra constraints from user ----------------------
        print("\n" + "-" * 60)
        print("  Do you want to add extra constraints? (Y/N)")
        print("  (You can type in English or French)")
        user_constraints = {}
        if input("  -> ").strip().upper() == "Y":
            print("\n  Describe your constraints in natural language:")
            print("  e.g. 'No sessions on Friday. Ahmed available Monday morning only.'\n")
            user_text        = input("  Your constraints: ").strip()
            user_constraints = _extract_constraints_from_text(user_text)

        # -- Step 3: Merge DB + user constraints --------------------------------
        print("\n[2/5] Merging constraints...")
        final_constraints = _merge_constraints(db_constraints, user_constraints)
        print("  [OK] Final constraints (DB + user):")
        print(json.dumps(final_constraints, indent=2))

        # -- Step 4: Load data from DB or manual input -------------------------
        print("\n[3/5] Loading data...")
        data = _load_data_from_db(self.db)
        if data:
            print(
                f"  [OK] {len(data['courses'])} course(s) | "
                f"{len(data['trainers'])} trainer(s) | "
                f"{len(data['groups'])} group(s) | "
                f"{len(data['rooms'])} room(s)"
            )
        else:
            print("  [INFO] Database is empty — switching to manual input.")
            data = _collect_data_from_user()

        # -- Step 5: Agent generates the schedule ------------------------------
        print("\n[4/5] Generating schedule...")
        schedule = _generate_schedule(data, final_constraints)
        if not schedule:
            print("  [ERROR] No sessions could be scheduled with these constraints.")
            return []

        # -- Display the schedule table ----------------------------------------
        print("\n[5/5] Schedule ready:")
        _print_schedule(schedule)

        # -- Validation + CSV export -------------------------------------------
        validated = _validate_and_export(schedule)
        if not validated:
            if input("\n  Restart with new constraints? (Y/N): ").strip().upper() == "Y":
                return self.run()

        return schedule


# =============================================================================
#  ENTRY POINT  ->  python -m agents.planning_agent
# =============================================================================

if __name__ == "__main__":
    db: Session = SessionLocal()
    try:
        agent = PlanningAgent(db=db)
        agent.run()
    finally:
        db.close()