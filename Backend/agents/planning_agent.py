"""
agents/planning_agent.py
========================
Fix: emploi du temps récurrent fixe.

AVANT (mauvais) :
  Semaine 1 Lundi 8h = Python   Session 1
  Semaine 2 Lundi 8h = Web Dev  Session 1  ← cours différent chaque semaine

APRÈS (correct) :
  Semaine 1 Lundi 8h = Python   Session 1
  Semaine 2 Lundi 8h = Python   Session 2  ← même cours, répété
  Semaine 3 Lundi 8h = Python   Session 3
  Semaine 4 Lundi 8h = Python   Session 4
  → Python occupe TOUJOURS Lundi 8h

Algorithme :
  Étape 1 : Trouver un créneau fixe (jour + slot) pour chaque paire (cours × groupe)
            → aucun groupe n'a 2 cours au même créneau
            → aucun formateur/salle n'est double-booké au même créneau
  Étape 2 : Répéter ce créneau fixe sur N semaines (une par séance)
"""

import csv
import io
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from db.DB import SessionLocal
from models.trainer     import Trainer
from models.learner     import LearnerGroup
from models.room        import Room
from models.equipment   import Equipment
from models.course      import Course
from models.constraints import Constraint
from Services.Llm.LlmService import _ask_ollama


# =============================================================================
#  PlanningResult
# =============================================================================

@dataclass
class PlanningResult:
    success:          bool
    total_sessions:   int
    constraints_used: dict
    schedule:         list[dict]
    engine:           str = "greedy"
    error:            str = ""


# =============================================================================
#  SYSTEM PROMPT
# =============================================================================

CONSTRAINT_EXTRACTION_PROMPT = """
You are a constraint extractor for a training planning system.
The user describes planning wishes in natural language (English or French).
Extract and return ONLY a valid JSON object. No markdown, no explanation, no extra text.

Return exactly this JSON structure (fill in values, keep defaults for missing fields):
{
  "forbidden_days": [],
  "trainer_availability": {},
  "session_duration_override": null,
  "sessions_per_day": null,
  "break_between_sessions_minutes": null,
  "lunch_break_after_n_sessions": null,
  "lunch_break_duration_minutes": null,
  "day_start_time": null,
  "min_room_capacity": null,
  "room_type_required": null,
  "group_priority": null,
  "no_parallel_sessions_same_group": false,
  "prefer_matching_specialization": true,
  "other": []
}
"""

# =============================================================================
#  DEFAULTS
# =============================================================================

DEFAULT_SESSION_DURATION_MINUTES = 180
DEFAULT_SESSIONS_PER_DAY         = 3
DEFAULT_BREAK_MINUTES            = 0
DEFAULT_LUNCH_AFTER_N_SESSIONS   = None
DEFAULT_LUNCH_DURATION_MINUTES   = 40
DEFAULT_DAY_START_TIME           = "08:00"

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
DAY_FR    = {"Monday": "lundi", "Tuesday": "mardi", "Wednesday": "mercredi",
             "Thursday": "jeudi", "Friday": "vendredi"}
MAX_WEEKS = 20


# =============================================================================
#  TIME SLOT GENERATOR
# =============================================================================

def _build_time_slots(constraints: dict) -> list[tuple[str, str]]:
    duration_min   = constraints.get("session_duration_override") or DEFAULT_SESSION_DURATION_MINUTES
    sessions_count = constraints.get("sessions_per_day")          or DEFAULT_SESSIONS_PER_DAY
    break_min      = constraints.get("break_between_sessions_minutes") or DEFAULT_BREAK_MINUTES
    lunch_after    = constraints.get("lunch_break_after_n_sessions")
    lunch_dur      = constraints.get("lunch_break_duration_minutes") or DEFAULT_LUNCH_DURATION_MINUTES
    start_str      = constraints.get("day_start_time") or DEFAULT_DAY_START_TIME

    h, m   = map(int, start_str.split(":"))
    cursor = datetime(2000, 1, 1, h, m)
    slots  = []

    for i in range(sessions_count):
        start = cursor
        end   = cursor + timedelta(minutes=duration_min)
        slots.append((start.strftime("%H:%M"), end.strftime("%H:%M")))
        cursor = end
        if i < sessions_count - 1:
            cursor += timedelta(minutes=break_min)
        if lunch_after and (i + 1) == lunch_after:
            cursor += timedelta(minutes=lunch_dur)
    return slots


def _slot_to_datetime(week, day, start, end, ref):
    base = ref + timedelta(weeks=week, days=DAY_ORDER.index(day))
    sh, sm = map(int, start.split(":"))
    eh, em = map(int, end.split(":"))
    return (base.replace(hour=sh, minute=sm, second=0, microsecond=0),
            base.replace(hour=eh, minute=em, second=0, microsecond=0))


# =============================================================================
#  CONSTRAINT HELPERS
# =============================================================================

def _load_constraints_from_db(db: Session) -> tuple[dict, int]:
    rows   = db.query(Constraint).all()
    merged = {
        "forbidden_days": [], "trainer_availability": {},
        "session_duration_override": None, "sessions_per_day": None,
        "break_between_sessions_minutes": None, "lunch_break_after_n_sessions": None,
        "lunch_break_duration_minutes": None, "day_start_time": None,
        "min_room_capacity": None, "room_type_required": None,
        "group_priority": None, "no_parallel_sessions_same_group": False,
        "prefer_matching_specialization": True, "other": []
    }
    for row in rows:
        ctype, cdata = row.constraint_type, row.constraint_data
        if   ctype == "forbidden_days":                   merged["forbidden_days"].extend(cdata.get("days", []))
        elif ctype == "trainer_availability":             merged["trainer_availability"].update(cdata)
        elif ctype == "session_duration_override":        merged["session_duration_override"] = cdata.get("value")
        elif ctype == "sessions_per_day":                 merged["sessions_per_day"] = cdata.get("value")
        elif ctype == "break_between_sessions_minutes":   merged["break_between_sessions_minutes"] = cdata.get("value")
        elif ctype == "lunch_break_after_n_sessions":     merged["lunch_break_after_n_sessions"] = cdata.get("value")
        elif ctype == "lunch_break_duration_minutes":     merged["lunch_break_duration_minutes"] = cdata.get("value")
        elif ctype == "day_start_time":                   merged["day_start_time"] = cdata.get("value")
        elif ctype == "min_room_capacity":                merged["min_room_capacity"] = cdata.get("value")
        elif ctype == "room_type_required":               merged["room_type_required"] = cdata.get("value")
        elif ctype == "group_priority":                   merged["group_priority"] = cdata.get("value")
        elif ctype == "no_parallel_sessions_same_group":  merged["no_parallel_sessions_same_group"] = cdata.get("value", False)
        elif ctype == "prefer_matching_specialization":   merged["prefer_matching_specialization"] = cdata.get("value", True)
        else:                                             merged["other"].append(cdata)
    return merged, len(rows)


def _extract_constraints_from_text(user_text: str) -> dict:
    print(f"\n  [LLM] Extracting constraints from: '{user_text[:80]}'")
    try:
        raw     = _ask_ollama(prompt=user_text, system=CONSTRAINT_EXTRACTION_PROMPT)
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        start   = cleaned.find("{")
        end     = cleaned.rfind("}") + 1
        if start == -1 or end == 0:
            return {}
        return json.loads(cleaned[start:end])
    except Exception as e:
        print(f"  [WARNING] {e}")
        return {}


def _merge_constraints(db_c: dict, user_c: dict) -> dict:
    m = dict(db_c)
    m["forbidden_days"] = list(set(m["forbidden_days"] + user_c.get("forbidden_days", [])))
    m["trainer_availability"].update(user_c.get("trainer_availability", {}))
    for k in ["session_duration_override", "sessions_per_day", "break_between_sessions_minutes",
              "lunch_break_after_n_sessions", "lunch_break_duration_minutes", "day_start_time",
              "min_room_capacity", "room_type_required", "group_priority"]:
        if user_c.get(k) is not None:
            m[k] = user_c[k]
    if user_c.get("no_parallel_sessions_same_group"):
        m["no_parallel_sessions_same_group"] = True
    if user_c.get("prefer_matching_specialization") is False:
        m["prefer_matching_specialization"] = False
    m["other"] = m.get("other", []) + user_c.get("other", [])
    return m


# =============================================================================
#  DATA LOADER
# =============================================================================

def _load_data_from_db(db: Session) -> dict | None:
    trainers   = db.query(Trainer).all()
    groups     = db.query(LearnerGroup).all()
    rooms      = db.query(Room).all()
    equipments = db.query(Equipment).all()
    courses    = db.query(Course).all()
    if not any([trainers, groups, rooms, courses]):
        return None
    return {
        "courses":  [{"id": c.id, "title": c.title, "total_hours": c.total_hours,
                      "session_duration": c.session_duration,
                      "required_equipments": [e.name for e in c.required_equipments]}
                     for c in courses],
        "trainers": [{"id": t.id, "name": t.name, "specialization": t.specialization or "",
                      "availability_notes": t.availability_notes or ""} for t in trainers],
        "groups":   [{"id": g.id, "name": g.name, "size": g.size, "level": g.level or ""}
                     for g in groups],
        "rooms":    [{"id": r.id, "name": r.name, "capacity": r.capacity,
                      "room_type": r.room_type or ""} for r in rooms],
        "equipments": [{"id": e.id, "name": e.name, "total_quantity": e.total_quantity}
                       for e in equipments],
    }


# =============================================================================
#  FIXED RECURRING SCHEDULE GENERATOR
#
#  Emploi du temps récurrent fixe — le modèle correct.
#
#  Étape 1 — Attribution fixe :
#    Pour chaque paire (cours × groupe), trouver UN créneau fixe (jour + slot)
#    + UN formateur + UNE salle.
#    Ce créneau sera utilisé TOUTES les semaines pour ce cours.
#
#    Contraintes à respecter sur le créneau fixe :
#      - Un groupe ne peut pas avoir 2 cours au même créneau
#      - Un formateur ne peut pas enseigner 2 cours au même créneau
#      - Une salle ne peut pas accueillir 2 cours au même créneau
#
#  Étape 2 — Répétition sur N semaines :
#    Le créneau fixe est répété N fois (N = nombre de séances du cours).
#    Résultat : Python est TOUJOURS Lundi 8h (semaines 1, 2, 3, 4...)
# =============================================================================

def _generate_schedule_recurring(
    data:           dict,
    constraints:    dict,
    reference_date: datetime | None = None,
) -> list[dict]:

    if reference_date is None:
        today          = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        days_to_mon    = (7 - today.weekday()) % 7 or 7
        reference_date = today + timedelta(days=days_to_mon)

    # ── Setup ──────────────────────────────────────────────────────────────────
    time_slots   = _build_time_slots(constraints)
    forbidden    = [d.lower() for d in constraints.get("forbidden_days", [])]
    allowed_days = [
        d for d in DAY_ORDER
        if d.lower() not in forbidden and DAY_FR[d].lower() not in forbidden
    ]

    session_duration = constraints.get("session_duration_override") or DEFAULT_SESSION_DURATION_MINUTES
    prefer_match     = constraints.get("prefer_matching_specialization", True)
    min_cap          = constraints.get("min_room_capacity")
    room_type_req    = (constraints.get("room_type_required") or "").lower()

    trainer_avail = {
        k.lower(): v.lower()
        for k, v in constraints.get("trainer_availability", {}).items()
    }

    def trainer_available_on(trainer: dict, day: str) -> bool:
        name = trainer["name"].lower()
        for key, avail in trainer_avail.items():
            if key in name:
                day_l  = day.lower()
                day_fr = DAY_FR.get(day, "").lower()
                any_day_in_avail = any(
                    d in avail
                    for d in [x.lower() for x in DAY_ORDER] + list(DAY_FR.values())
                )
                if any_day_in_avail:
                    return day_l in avail or day_fr in avail
        return True

    # Filter rooms
    all_rooms = data.get("rooms", [])
    if min_cap:
        all_rooms = [r for r in all_rooms if r["capacity"] >= min_cap]
    if room_type_req:
        f = [r for r in all_rooms if room_type_req in r.get("room_type", "").lower()]
        if f:
            all_rooms = f

    # ── ÉTAPE 1 : Attribution des créneaux fixes ──────────────────────────────
    #
    # On cherche pour chaque (cours × groupe) un créneau (jour + slot_idx)
    # unique, avec formateur et salle disponibles à ce créneau toutes les semaines.
    #
    # Les sets ci-dessous représentent les créneaux DÉJÀ PRIS (permanents) :
    #   (jour, slot_idx) → occupation permanente sur toutes les semaines
    #
    # Un (jour, slot_idx) pris par le groupe A ne peut pas être pris par le groupe A
    # pour un autre cours.
    # Un (jour, slot_idx) pris par formateur X ne peut pas être pris par X pour
    # un autre cours.

    # Créneaux permanents occupés par (groupe, jour, slot_idx)
    group_fixed_slots:   dict[int, set] = {}   # group_id → set of (day, slot_idx)
    trainer_fixed_slots: dict[int, set] = {}   # trainer_id → set of (day, slot_idx)
    room_fixed_slots:    dict[int, set] = {}   # room_id → set of (day, slot_idx)

    # Attribution : (course_id, group_id) → (day, slot_idx, trainer, room, nb_sessions)
    fixed_assignments: dict[tuple, tuple] = {}

    # Construire toutes les paires (cours × groupe)
    pairs = []
    for course in data.get("courses", []):
        course_dur = session_duration or int(course.get("session_duration", 3) * 60)
        nb         = math.ceil((course["total_hours"] * 60) / course_dur)
        for group in data.get("groups", []):
            pairs.append((course, group, nb))

    total_available_slots = len(allowed_days) * len(time_slots)
    print(f"  [Greedy] {len(pairs)} pairs à placer | {total_available_slots} créneaux disponibles")

    unplaced_pairs = []

    for course, group, nb in pairs:
        placed = False

        # Trier les formateurs par spécialisation correspondante
        sorted_trainers = sorted(
            data.get("trainers", []),
            key=lambda t: course["title"].lower() in t.get("specialization", "").lower(),
            reverse=prefer_match,
        )

        # Rooms valides pour ce groupe
        valid_rooms = [r for r in all_rooms if r["capacity"] >= group["size"]]

        for day in allowed_days:
            if placed: break
            for slot_idx, (slot_start, slot_end) in enumerate(time_slots):
                if placed: break

                # ── Vérifier que le groupe est libre à ce créneau ─────────────
                g_used = group_fixed_slots.get(group["id"], set())
                if (day, slot_idx) in g_used:
                    continue   # groupe déjà occupé à ce créneau

                # ── Trouver un formateur libre à ce créneau ───────────────────
                trainer = None
                for t in sorted_trainers:
                    if not trainer_available_on(t, day):
                        continue
                    t_used = trainer_fixed_slots.get(t["id"], set())
                    if (day, slot_idx) not in t_used:
                        trainer = t
                        break

                if trainer is None:
                    continue

                # ── Trouver une salle libre à ce créneau ──────────────────────
                room = None
                for r in sorted(valid_rooms, key=lambda r: r["capacity"]):
                    r_used = room_fixed_slots.get(r["id"], set())
                    if (day, slot_idx) not in r_used:
                        room = r
                        break

                if room is None:
                    continue

                # ── Créneau trouvé → l'attribuer définitivement ───────────────
                group_fixed_slots.setdefault(group["id"], set()).add((day, slot_idx))
                trainer_fixed_slots.setdefault(trainer["id"], set()).add((day, slot_idx))
                room_fixed_slots.setdefault(room["id"], set()).add((day, slot_idx))

                fixed_assignments[(course["id"], group["id"])] = (
                    day, slot_idx, slot_start, slot_end, trainer, room, nb
                )
                placed = True

        if not placed:
            unplaced_pairs.append(f"{course['title']} × {group['name']}")

    if unplaced_pairs:
        print(f"  [Greedy] ⚠️  {len(unplaced_pairs)} paire(s) sans créneau :")
        for u in unplaced_pairs[:5]:
            print(f"    - {u}")
        if len(allowed_days) * len(time_slots) < len(pairs):
            print(f"  [Greedy] 💡 Suggestion : augmenter sessions_per_day ou réduire le nombre de cours.")

    # ── ÉTAPE 2 : Répéter le créneau fixe sur N semaines ─────────────────────
    schedule  = []
    global_sn = 1

    for (course_id, group_id), (day, slot_idx, slot_start, slot_end, trainer, room, nb) in fixed_assignments.items():
        # Récupérer les objets cours et groupe
        course = next(c for c in data["courses"] if c["id"] == course_id)
        group  = next(g for g in data["groups"]  if g["id"] == group_id)

        for week in range(nb):
            # Semaine week (0-indexed) → Semaine week+1 (display)
            start_dt, end_dt = _slot_to_datetime(week, day, slot_start, slot_end, reference_date)

            schedule.append({
                # Champs DB
                "course_id":               course_id,
                "trainer_id":              trainer["id"],
                "room_id":                 room["id"],
                "learner_group_id":        group_id,
                "start_time":              start_dt.isoformat(),
                "end_time":                end_dt.isoformat(),
                "status":                  "draft",
                "is_validated":            False,
                "quality_score":           0.0,
                "pedagogical_audit_score": 0.0,
                # Champs d'affichage
                "session_number":  global_sn,
                "course_title":    course["title"],
                "trainer_name":    trainer["name"],
                "room_name":       room["name"],
                "group_name":      group["name"],
                "suggested_day":   f"Week {week + 1} — {day}",
                "suggested_time":  f"{slot_start} → {slot_end}",
                "reasoning": (
                    f"Récurrent | {group['name']} | "
                    f"{course['title']} = {day} {slot_start} fixe | "
                    f"Séance {week+1}/{nb} | "
                    f"{trainer['name']} | {room['name']}"
                ),
            })
            global_sn += 1

    # Trier par semaine puis par jour puis par heure
    schedule.sort(key=lambda s: s["start_time"])
    print(f"  [Greedy] ✅ {len(schedule)} séances planifiées sur {MAX_WEEKS} semaines max.")
    return schedule


# =============================================================================
#  EXPORT CSV
# =============================================================================

FIELDNAMES = [
    "session_number", "course_id", "course_title", "trainer_id", "trainer_name",
    "room_id", "room_name", "learner_group_id", "group_name",
    "suggested_day", "suggested_time", "start_time", "end_time",
    "status", "quality_score", "reasoning",
]

def schedule_to_csv_bytes(schedule: list[dict]) -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=FIELDNAMES, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(schedule)
    return output.getvalue().encode("utf-8")


# =============================================================================
#  PLANNING AGENT
# =============================================================================

class PlanningAgent:

    def __init__(self, db: Session):
        self.db = db

    def run(
        self,
        extra_constraints: str | None = None,
        constraints_dict:  dict | None = None,
    ) -> PlanningResult:

        terminal_mode = extra_constraints is None and constraints_dict is None

        print("\n" + "=" * 60)
        print("       PLANNING AGENT")
        print("=" * 60)

        # ── Constraints ────────────────────────────────────────────────────────
        if constraints_dict is not None:
            print("\n[CONSTRAINTS] Using ConstraintAgent output.")
            final = constraints_dict
        else:
            print("\n[1/5] Loading constraints from DB...")
            db_constraints, nb_rows = _load_constraints_from_db(self.db)
            print(f"  -> {nb_rows} constraint(s).")
            user_constraints = {}
            if terminal_mode:
                if input("  Add extra constraints? (Y/N): ").strip().upper() == "Y":
                    text = input("  Constraints: ").strip()
                    user_constraints = _extract_constraints_from_text(text)
            elif extra_constraints:
                user_constraints = _extract_constraints_from_text(extra_constraints)
            print("\n[2/5] Merging constraints...")
            final = _merge_constraints(db_constraints, user_constraints)

        # ── Load data ──────────────────────────────────────────────────────────
        print("\n[3/5] Loading data from DB...")
        data = _load_data_from_db(self.db)
        if not data:
            return PlanningResult(success=False, total_sessions=0,
                                  constraints_used=final, schedule=[],
                                  error="No data in DB.")
        print(f"  -> {len(data['courses'])} cours | {len(data['trainers'])} formateurs | "
              f"{len(data['groups'])} groupes | {len(data['rooms'])} salles")

        # ── Generate ───────────────────────────────────────────────────────────
        print("\n[4/5] Generating schedule...")
        schedule = None
        engine   = "greedy"

        # Try OR-Tools first
        try:
            from agents.planner import Planner
            schedule = Planner(time_limit_seconds=30).solve(data, final)
            if schedule:
                engine = "ortools"
                print(f"  ✅ OR-Tools: {len(schedule)} séances.")
        except ImportError:
            print("  [INFO] ortools not installed → greedy. (pip install ortools)")
        except Exception as e:
            print(f"  [WARNING] OR-Tools error: {e}")

        # Greedy fallback (recurring model)
        if not schedule:
            print("  [Greedy] Modèle récurrent fixe...")
            schedule = _generate_schedule_recurring(data, final)
            engine   = "greedy"

        if not schedule:
            return PlanningResult(success=False, total_sessions=0,
                                  constraints_used=final, schedule=[],
                                  error="Aucune séance planifiable.")

        print(f"\n[5/5] Done: {len(schedule)} séances [{engine}].")

        if terminal_mode:
            for s in schedule[:5]:
                print(f"  #{s['session_number']} | {s['course_title']} | "
                      f"{s['group_name']} | {s['suggested_day']} {s['suggested_time']}")
            if input("  Export CSV? (Y/N): ").strip().upper() == "Y":
                path = input("  Path: ").strip() or "outputs/schedule.csv"
                os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
                with open(path, "w", newline="", encoding="utf-8") as f:
                    f.write(schedule_to_csv_bytes(schedule).decode("utf-8"))
                print(f"  Saved → {path}")

        return PlanningResult(
            success          = True,
            total_sessions   = len(schedule),
            constraints_used = final,
            schedule         = schedule,
            engine           = engine,
        )

    def get_constraints(self) -> tuple[dict, int]:
        return _load_constraints_from_db(self.db)


# =============================================================================
#  TERMINAL
# =============================================================================

if __name__ == "__main__":
    db: Session = SessionLocal()
    try:
        PlanningAgent(db=db).run()
    finally:
        db.close()