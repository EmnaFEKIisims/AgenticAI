import csv
import io
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from db.DB import SessionLocal
from models.trainer import Trainer
from models.learner import LearnerGroup
from models.room import Room
from models.equipment import Equipment
from models.course import Course
from models.constraints import Constraint
from Services.LlmService import _ask_ollama


# =============================================================================
#  PlanningResult
# =============================================================================

@dataclass
class PlanningResult:
    success:          bool
    total_sessions:   int
    constraints_used: dict
    schedule:         list[dict]
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

Field explanations and extraction rules:

"forbidden_days": list of strings
  -> Days of the week where NO session can be scheduled.
  -> Values must be English day names: "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"
  -> Example: "no Friday", "pas le vendredi" -> ["Friday"]

"trainer_availability": dict { trainer_name: availability_description }
  -> Named trainer availability. Key = trainer name, value = free description.
  -> Example: "Ahmed available Monday morning only" -> {"Ahmed": "Monday morning"}

"session_duration_override": integer or null
  -> Duration of each session in MINUTES (not hours).
  -> Example: "sessions of 1h30" -> 90, "2 hour sessions" -> 120, "sessions de 45 min" -> 45

"sessions_per_day": integer or null
  -> How many sessions happen per day.
  -> Example: "5 sessions per day", "3 séances par jour" -> 3

"break_between_sessions_minutes": integer or null
  -> Short break between consecutive sessions, in minutes.
  -> Example: "5 min break between sessions", "pause de 10 minutes" -> 10

"lunch_break_after_n_sessions": integer or null
  -> After how many sessions a lunch break is inserted.
  -> Example: "lunch break after 3 sessions" -> 3, "après 2 séances pause déjeuner" -> 2

"lunch_break_duration_minutes": integer or null
  -> Duration of the lunch break in minutes.
  -> Example: "40 minute lunch break", "pause déjeuner de 1h" -> 60

"day_start_time": string or null
  -> Time the first session starts, in HH:MM format (24h).
  -> Example: "sessions start at 8am" -> "08:00", "début à 9h30" -> "09:30"

"min_room_capacity": integer or null
  -> Minimum seats a room must have.

"room_type_required": string or null
  -> Required room type e.g. "Lab", "Classroom", "Virtual"

"group_priority": string or null
  -> Name of group to schedule first.

"no_parallel_sessions_same_group": boolean
  -> If true, one group cannot attend two sessions at the same time.

"prefer_matching_specialization": boolean
  -> If true (default), prefer trainers whose specialization matches the course.
  -> Set to false only if user says "any trainer can teach any course".

"other": list of strings
  -> Anything else that does not fit above categories.

General rules:
- Fields not mentioned -> keep default value (null, false, [], {})
- Day names must always be in English
- Duration values must be in MINUTES
- Time values must be in HH:MM 24h format
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
    lunch_after    = constraints.get("lunch_break_after_n_sessions")   or DEFAULT_LUNCH_AFTER_N_SESSIONS
    lunch_dur      = constraints.get("lunch_break_duration_minutes")   or DEFAULT_LUNCH_DURATION_MINUTES
    start_str      = constraints.get("day_start_time")                 or DEFAULT_DAY_START_TIME

    h, m   = map(int, start_str.split(":"))
    cursor = datetime(2000, 1, 1, h, m)

    slots = []
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


def _slot_to_datetime(week: int, day: str, slot_start: str, slot_end: str,
                      reference_date: datetime) -> tuple[datetime, datetime]:
    day_offset = DAY_ORDER.index(day)
    base_date  = reference_date + timedelta(weeks=week, days=day_offset)
    sh, sm = map(int, slot_start.split(":"))
    eh, em = map(int, slot_end.split(":"))
    start_dt = base_date.replace(hour=sh, minute=sm, second=0, microsecond=0)
    end_dt   = base_date.replace(hour=eh, minute=em, second=0, microsecond=0)
    return start_dt, end_dt


# =============================================================================
#  CONSTRAINT HELPERS  (used in Mode 2 + Mode 3 only)
# =============================================================================

def _load_constraints_from_db(db: Session) -> tuple[dict, int]:
    rows = db.query(Constraint).all()
    merged = {
        "forbidden_days": [], "trainer_availability": {},
        "session_duration_override": None, "sessions_per_day": None,
        "break_between_sessions_minutes": None,
        "lunch_break_after_n_sessions": None, "lunch_break_duration_minutes": None,
        "day_start_time": None, "min_room_capacity": None,
        "room_type_required": None, "group_priority": None,
        "no_parallel_sessions_same_group": False,
        "prefer_matching_specialization": True, "other": []
    }
    for row in rows:
        ctype, cdata = row.constraint_type, row.constraint_data
        if   ctype == "forbidden_days":                  merged["forbidden_days"].extend(cdata.get("days", []))
        elif ctype == "trainer_availability":            merged["trainer_availability"].update(cdata)
        elif ctype == "session_duration_override":       merged["session_duration_override"] = cdata.get("value")
        elif ctype == "sessions_per_day":                merged["sessions_per_day"] = cdata.get("value")
        elif ctype == "break_between_sessions_minutes":  merged["break_between_sessions_minutes"] = cdata.get("value")
        elif ctype == "lunch_break_after_n_sessions":    merged["lunch_break_after_n_sessions"] = cdata.get("value")
        elif ctype == "lunch_break_duration_minutes":    merged["lunch_break_duration_minutes"] = cdata.get("value")
        elif ctype == "day_start_time":                  merged["day_start_time"] = cdata.get("value")
        elif ctype == "min_room_capacity":               merged["min_room_capacity"] = cdata.get("value")
        elif ctype == "room_type_required":              merged["room_type_required"] = cdata.get("value")
        elif ctype == "group_priority":                  merged["group_priority"] = cdata.get("value")
        elif ctype == "no_parallel_sessions_same_group": merged["no_parallel_sessions_same_group"] = cdata.get("value", False)
        elif ctype == "prefer_matching_specialization":  merged["prefer_matching_specialization"] = cdata.get("value", True)
        else:                                            merged["other"].append(cdata)
    return merged, len(rows)


def _extract_constraints_from_text(user_text: str) -> dict:
    print(f"\n  [LLM] Extracting constraints from: '{user_text[:80]}'")
    try:
        raw = _ask_ollama(prompt=user_text, system=CONSTRAINT_EXTRACTION_PROMPT)
        print(f"  [LLM raw]: {raw[:300]}")
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        start = cleaned.find("{")
        end   = cleaned.rfind("}") + 1
        if start == -1 or end == 0:
            print("  [WARNING] No JSON found. Using defaults.")
            return {}
        result = json.loads(cleaned[start:end])
        print(f"  [LLM] Extracted: {result}")
        return result
    except Exception as e:
        print(f"  [WARNING] Extraction failed: {e}")
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
    if user_c.get("no_parallel_sessions_same_group"):        m["no_parallel_sessions_same_group"] = True
    if user_c.get("prefer_matching_specialization") is False: m["prefer_matching_specialization"] = False
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
        "courses":    [{"id":c.id,"title":c.title,"total_hours":c.total_hours,
                        "session_duration":c.session_duration,
                        "required_equipments":[e.name for e in c.required_equipments]} for c in courses],
        "trainers":   [{"id":t.id,"name":t.name,"specialization":t.specialization or "",
                        "availability_notes":t.availability_notes or ""} for t in trainers],
        "groups":     [{"id":g.id,"name":g.name,"size":g.size,"level":g.level or ""} for g in groups],
        "rooms":      [{"id":r.id,"name":r.name,"capacity":r.capacity,"room_type":r.room_type or ""} for r in rooms],
        "equipments": [{"id":e.id,"name":e.name,"total_quantity":e.total_quantity} for e in equipments],
    }


# =============================================================================
#  SCHEDULE GENERATOR
# =============================================================================

def _generate_schedule(data: dict, constraints: dict,
                       reference_date: datetime | None = None) -> list[dict]:
    if reference_date is None:
        today          = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        days_to_mon    = (7 - today.weekday()) % 7 or 7
        reference_date = today + timedelta(days=days_to_mon)

    time_slots = _build_time_slots(constraints)
    print(f"\n  [Agent] Time slots ({len(time_slots)} per day):")
    for s, e in time_slots:
        print(f"    {s} -> {e}")

    forbidden    = [d.lower() for d in constraints.get("forbidden_days", [])]
    allowed_days = [d for d in DAY_ORDER
                    if d.lower() not in forbidden and DAY_FR[d].lower() not in forbidden]

    min_cap       = constraints.get("min_room_capacity")
    room_type_req = (constraints.get("room_type_required") or "").lower()
    trainer_avail = {k.lower(): v.lower() for k, v in constraints.get("trainer_availability", {}).items()}
    prefer_match  = constraints.get("prefer_matching_specialization", True)

    trainer_busy: dict = {}
    room_busy:    dict = {}
    group_busy:   dict = {}

    def is_free(t, eid, w, d, si): return not t.get((eid, w, d, si), False)
    def book(t, eid, w, d, si):    t[(eid, w, d, si)] = True

    rooms = data.get("rooms", [])
    if min_cap:
        rooms = [r for r in rooms if r["capacity"] >= min_cap]
    if room_type_req:
        f = [r for r in rooms if room_type_req in r.get("room_type", "").lower()]
        if f: rooms = f

    def trainer_ok(trainer, day):
        name = trainer["name"].lower()
        for key, avail in trainer_avail.items():
            if key in name:
                if day.lower() in avail or DAY_FR.get(day, "").lower() in avail: return True
                all_days = [x.lower() for x in DAY_ORDER] + list(DAY_FR.values())
                if any(d in avail for d in all_days): return False
        return True

    def pick_trainer(course, week, day, si):
        for t in sorted(data.get("trainers", []),
                        key=lambda t: course["title"].lower() in t.get("specialization", "").lower(),
                        reverse=prefer_match):
            if trainer_ok(t, day) and is_free(trainer_busy, t["id"], week, day, si):
                return t
        return None

    def pick_room(group, week, day, si):
        for r in sorted([r for r in rooms if r["capacity"] >= group["size"]], key=lambda r: r["capacity"]):
            if is_free(room_busy, r["id"], week, day, si): return r
        return None

    schedule, sg = [], 1

    for course in data.get("courses", []):
        course_dur_min = (constraints.get("session_duration_override")
                          or int(course.get("session_duration", 3) * 60))
        nb = math.ceil((course["total_hours"] * 60) / course_dur_min)

        for group in data.get("groups", []):
            placed, sn = 0, 1
            for week in range(MAX_WEEKS):
                if placed >= nb: break
                for day in allowed_days:
                    if placed >= nb: break
                    for si, (slot_start, slot_end) in enumerate(time_slots):
                        if placed >= nb: break
                        if not is_free(group_busy, group["id"], week, day, si): continue
                        t = pick_trainer(course, week, day, si)
                        r = pick_room(group, week, day, si)
                        if t and r:
                            start_dt, end_dt = _slot_to_datetime(week, day, slot_start, slot_end, reference_date)
                            schedule.append({
                                "course_id":               course["id"],
                                "trainer_id":              t["id"],
                                "room_id":                 r["id"],
                                "learner_group_id":        group["id"],
                                "start_time":              start_dt.isoformat(),
                                "end_time":                end_dt.isoformat(),
                                "status":                  "draft",
                                "is_validated":            False,
                                "quality_score":           0.0,
                                "pedagogical_audit_score": 0.0,
                                "session_number":          sg,
                                "course_title":            course["title"],
                                "trainer_name":            t["name"],
                                "room_name":               r["name"],
                                "group_name":              group["name"],
                                "suggested_day":           f"Week {week+1} — {day}",
                                "suggested_time":          f"{slot_start} → {slot_end}",
                                "reasoning": (
                                    f"S{sn}/{nb} | W{week+1} | "
                                    f"{t['name']} [{t.get('specialization','')}] | "
                                    f"{r['name']} cap={r['capacity']}>={group['size']}"
                                )
                            })
                            book(trainer_busy, t["id"], week, day, si)
                            book(room_busy,    r["id"], week, day, si)
                            book(group_busy, group["id"], week, day, si)
                            placed += 1; sn += 1; sg += 1

            if placed < nb:
                print(f"  [WARNING] {placed}/{nb} sessions placed for '{course['title']}'/'{group['name']}'")

    return schedule


# =============================================================================
#  DISPLAY + EXPORT
# =============================================================================

def _print_schedule(schedule: list[dict]):
    W = 132
    print(f"\n{'=' * W}")
    print("  GENERATED SCHEDULE — Planning Agent")
    print(f"{'=' * W}")
    print(f"  {'#':<4} {'Course':<18} {'Trainer':<20} {'Room':<16} {'Group':<15} {'Day':<22} {'Time':<18} Reasoning")
    print(f"  {'-' * W}")
    for s in schedule:
        print(f"  {s['session_number']:<4} {str(s['course_title'])[:17]:<18} "
              f"{str(s['trainer_name'])[:19]:<20} {str(s['room_name'])[:15]:<16} "
              f"{str(s['group_name'])[:14]:<15} {str(s['suggested_day'])[:21]:<22} "
              f"{str(s['suggested_time'])[:17]:<18} {str(s['reasoning'])[:45]}")
    print(f"{'=' * W}")
    print(f"  Total: {len(schedule)} session(s)\n")


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

def _export_csv(schedule: list[dict], filepath: str):
    folder = os.path.dirname(filepath)
    if folder: os.makedirs(folder, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        f.write(schedule_to_csv_bytes(schedule).decode("utf-8"))
    print(f"  [SAVED] -> {os.path.abspath(filepath)}")


# =============================================================================
#  PLANNING AGENT
# =============================================================================

class PlanningAgent:

    def __init__(self, db: Session):
        self.db = db

    def run(
        self,
        extra_constraints: str | None = None,
        constraints_dict:  dict | None = None,   # ← NEW: ConstraintAgent output
    ) -> PlanningResult:
        """
        3 modes depending on arguments:

        Mode 1 — ConstraintAgent output (RECOMMENDED)
            run(constraints_dict=agent_result.planning_dict)
            → Skips all LLM extraction. Uses the pre-validated dict directly.
            → Fastest + most accurate (ISO + business rules already applied).

        Mode 2 — API / orchestrator with text
            run(extra_constraints="No Friday. Ahmed available Monday.")
            → LLM extracts from text, merges with DB constraints.

        Mode 3 — Terminal (interactive)
            run()  or  run(extra_constraints=None)
            → Prompts user interactively via input().
        """
        terminal_mode = extra_constraints is None and constraints_dict is None

        print("\n" + "=" * 60)
        print("       PLANNING AGENT")
        print("=" * 60)

        # ── Resolve final constraints ──────────────────────────────────────────

        if constraints_dict is not None:
            # ── MODE 1: ConstraintAgent output ─────────────────────────────────
            # Pre-validated by ConstraintAgent — skip all extraction steps.
            print("\n[CONSTRAINTS] Using ConstraintAgent output (pre-validated).")
            final = constraints_dict

        else:
            # ── MODE 2 / 3: Extract from DB + optional user text ───────────────
            print("\n[1/5] Loading constraints from DB...")
            db_constraints, nb_rows = _load_constraints_from_db(self.db)
            print(f"  -> {nb_rows} constraint(s) found.")

            user_constraints = {}
            if terminal_mode:
                # Mode 3: interactive
                print("\n  Add extra constraints? (Y/N)")
                if input("  -> ").strip().upper() == "Y":
                    text = input("  Constraints (English or French): ").strip()
                    user_constraints = _extract_constraints_from_text(text)
            elif extra_constraints:
                # Mode 2: API with text
                user_constraints = _extract_constraints_from_text(extra_constraints)

            print("\n[2/5] Merging constraints...")
            final = _merge_constraints(db_constraints, user_constraints)

        print(f"  -> forbidden_days={final.get('forbidden_days')}, "
              f"session_duration={final.get('session_duration_override')}min, "
              f"sessions_per_day={final.get('sessions_per_day')}, "
              f"break={final.get('break_between_sessions_minutes')}min")

        # ── Load data ──────────────────────────────────────────────────────────
        print("\n[3/5] Loading data from DB...")
        data = _load_data_from_db(self.db)
        if not data:
            return PlanningResult(success=False, total_sessions=0,
                                  constraints_used=final, schedule=[],
                                  error="No data in DB.")
        print(f"  -> {len(data['courses'])} courses | {len(data['trainers'])} trainers | "
              f"{len(data['groups'])} groups | {len(data['rooms'])} rooms")

        # ── Generate ───────────────────────────────────────────────────────────
        print("\n[4/5] Generating schedule...")
        schedule = _generate_schedule(data, final)

        if not schedule:
            return PlanningResult(success=False, total_sessions=0,
                                  constraints_used=final, schedule=[],
                                  error="No sessions could be scheduled with these constraints.")

        print(f"\n[5/5] Done: {len(schedule)} session(s) generated.")

        # ── Terminal mode: display + validate interactively ────────────────────
        if terminal_mode:
            _print_schedule(schedule)
            if input("  Validate? (Y/N): ").strip().upper() == "Y":
                if input("  Export CSV? (Y/N): ").strip().upper() == "Y":
                    path = input("  Path (Enter = outputs/schedule.csv): ").strip()
                    _export_csv(schedule, path or "outputs/schedule.csv")
            elif input("  Restart with new constraints? (Y/N): ").strip().upper() == "Y":
                return self.run()

        return PlanningResult(
            success=True,
            total_sessions=len(schedule),
            constraints_used=final,
            schedule=schedule,
        )

    def get_constraints(self) -> tuple[dict, int]:
        return _load_constraints_from_db(self.db)


# =============================================================================
#  ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    db: Session = SessionLocal()
    try:
        PlanningAgent(db=db).run()   # terminal mode
    finally:
        db.close()