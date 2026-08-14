"""
agents/planner.py
==================
High-level OR-Tools scheduling engine.

Called by PlanningAgent instead of the old greedy _generate_schedule().

Planner
  │
  ├── Prepares data (slots, sessions, forbidden slots)
  │
  ├── optimization/variables.py   → CP-SAT IntVar per session
  │
  ├── optimization/constraints.py → Hard constraints
  │
  ├── optimization/objectives.py  → Minimize makespan + specialization mismatch
  │
  ├── optimization/solver.py      → CP-SAT solve (30s time limit)
  │
  └── optimization/solution_mapper.py → OR-Tools ints → schedule list[dict]

If OR-Tools finds no solution → returns None → PlanningAgent falls back to greedy.
"""

import math
from datetime import datetime, timedelta

from ortools.sat.python import cp_model

from Services.PlanningAgent.optimization.variables      import create_session_variables
from Services.PlanningAgent.optimization.constraints    import (
    add_group_non_overlap,
    add_resource_non_overlap,
    add_forbidden_slots,
    add_trainer_forbidden_slots,
)
from Services.PlanningAgent.optimization.objectives     import build_objective
from Services.PlanningAgent.optimization.solver         import solve, is_usable
from Services.PlanningAgent.optimization.solution_mapper import build_schedule


# ── Same constants as planning_agent.py ───────────────────────────────────────
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
DAY_FR    = {"Monday": "lundi", "Tuesday": "mardi", "Wednesday": "mercredi",
             "Thursday": "jeudi", "Friday": "vendredi"}
MAX_WEEKS = 20

DEFAULT_SESSION_DURATION_MINUTES = 180
DEFAULT_SESSIONS_PER_DAY         = 3
DEFAULT_BREAK_MINUTES            = 0
DEFAULT_LUNCH_AFTER_N_SESSIONS   = None
DEFAULT_LUNCH_DURATION_MINUTES   = 40
DEFAULT_DAY_START_TIME           = "08:00"


class Planner:
    """
    OR-Tools CP-SAT scheduling engine.

    Usage (from PlanningAgent):
        planner  = Planner(time_limit_seconds=30)
        schedule = planner.solve(data, constraints, reference_date)
        if schedule is None:
            # Fall back to greedy algorithm
    """

    def __init__(self, time_limit_seconds: int = 30):
        self.time_limit = time_limit_seconds

    def solve(
        self,
        data:           dict,
        constraints:    dict,
        reference_date: datetime | None = None,
    ) -> list[dict] | None:
        """
        Runs OR-Tools on the scheduling problem.

        Args:
            data:           DB data (courses, trainers, groups, rooms)
            constraints:    Merged constraint dict from PlanningAgent
            reference_date: First Monday of the planning (datetime)

        Returns:
            list[dict] schedule if feasible, or None if OR-Tools fails.
        """
        print(f"\n  [Planner] Building OR-Tools model...")

        if reference_date is None:
            today          = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            days_to_mon    = (7 - today.weekday()) % 7 or 7
            reference_date = today + timedelta(days=days_to_mon)

        # ── Step 1: Pre-compute time slots ────────────────────────────────────
        slots = self._build_slots(constraints, reference_date)
        if not slots:
            print("  [Planner] ❌ No valid time slots.")
            return None
        print(f"  [Planner] {len(slots)} time slots available.")

        # ── Step 2: Build session tasks ───────────────────────────────────────
        sessions = self._build_sessions(data, constraints)
        if not sessions:
            print("  [Planner] ❌ No sessions to schedule.")
            return None
        print(f"  [Planner] {len(sessions)} sessions to schedule.")

        trainers = data.get("trainers", [])
        rooms    = data.get("rooms",    [])
        if not trainers or not rooms:
            print("  [Planner] ❌ No trainers or rooms available.")
            return None

        # ── Step 3: Compute forbidden slots ───────────────────────────────────
        forbidden_global  = self._global_forbidden_slots(constraints, slots)
        forbidden_trainer = self._trainer_forbidden_slots(constraints, slots, trainers)

        # ── Step 4: Build CP-SAT model ────────────────────────────────────────
        model     = cp_model.CpModel()
        sess_vars = create_session_variables(model, sessions, len(slots), trainers, rooms)

        # ── Step 5: Add constraints ───────────────────────────────────────────
        add_group_non_overlap(model, sess_vars, sessions)
        add_resource_non_overlap(model, sess_vars)
        add_forbidden_slots(model, sess_vars, forbidden_global)
        add_trainer_forbidden_slots(model, sess_vars, forbidden_trainer)

        # ── Step 6: Add objective ─────────────────────────────────────────────
        build_objective(model, sess_vars, sessions, trainers, len(slots))

        # ── Step 7: Solve ─────────────────────────────────────────────────────
        solver, status = solve(model, self.time_limit)

        if not is_usable(status):
            print(f"  [Planner] OR-Tools could not find a solution → falling back to greedy.")
            return None

        # ── Step 8: Map solution to schedule dicts ───────────────────────────
        schedule = build_schedule(solver, sess_vars, sessions, slots, trainers, rooms)
        print(f"  [Planner] ✅ {len(schedule)} session(s) scheduled by OR-Tools.")
        return schedule

    # ==========================================================================
    #  DATA PREPARATION
    # ==========================================================================

    def _build_slots(self, constraints: dict, reference_date: datetime) -> list[dict]:
        """
        Pre-computes all valid (week, day, slot_idx) combinations.
        Returns a list of slot dicts indexed 0..N-1 — used as IntVar domain.
        """
        duration_min   = constraints.get("session_duration_override") or DEFAULT_SESSION_DURATION_MINUTES
        sessions_count = constraints.get("sessions_per_day")          or DEFAULT_SESSIONS_PER_DAY
        break_min      = constraints.get("break_between_sessions_minutes") or DEFAULT_BREAK_MINUTES
        lunch_after    = constraints.get("lunch_break_after_n_sessions")
        lunch_dur      = constraints.get("lunch_break_duration_minutes")   or DEFAULT_LUNCH_DURATION_MINUTES
        start_str      = constraints.get("day_start_time") or DEFAULT_DAY_START_TIME
        forbidden      = [d.lower() for d in constraints.get("forbidden_days", [])]

        allowed_days = [
            d for d in DAY_ORDER
            if d.lower() not in forbidden and DAY_FR[d].lower() not in forbidden
        ]

        # Build time slots within a day
        h, m   = map(int, start_str.split(":"))
        cursor = datetime(2000, 1, 1, h, m)
        time_slots = []
        for i in range(sessions_count):
            start_t = cursor
            end_t   = cursor + timedelta(minutes=duration_min)
            time_slots.append((start_t.strftime("%H:%M"), end_t.strftime("%H:%M")))
            cursor = end_t
            if i < sessions_count - 1:
                cursor += timedelta(minutes=break_min)
            if lunch_after and (i + 1) == lunch_after:
                cursor += timedelta(minutes=lunch_dur)

        slots = []
        idx   = 0
        for week in range(MAX_WEEKS):
            for day in allowed_days:
                day_idx    = DAY_ORDER.index(day)
                base_date  = reference_date + timedelta(weeks=week, days=day_idx)
                for si, (start, end) in enumerate(time_slots):
                    sh, sm = map(int, start.split(":"))
                    eh, em = map(int, end.split(":"))
                    slots.append({
                        "index":    idx,
                        "week":     week,
                        "day":      day,
                        "day_idx":  day_idx,
                        "slot_idx": si,
                        "start":    start,
                        "end":      end,
                        "start_dt": base_date.replace(hour=sh, minute=sm, second=0, microsecond=0),
                        "end_dt":   base_date.replace(hour=eh, minute=em, second=0, microsecond=0),
                    })
                    idx += 1
        return slots

    def _build_sessions(self, data: dict, constraints: dict) -> list[dict]:
        """
        Expands (course × group) pairs into individual session tasks.
        """
        duration_min = constraints.get("session_duration_override") or DEFAULT_SESSION_DURATION_MINUTES
        sessions     = []

        for course in data.get("courses", []):
            course_dur = constraints.get("session_duration_override") or int(course.get("session_duration", 3) * 60)
            nb         = math.ceil((course["total_hours"] * 60) / course_dur)

            for group in data.get("groups", []):
                for sn in range(1, nb + 1):
                    sessions.append({
                        "course_id":    course["id"],
                        "course_title": course["title"],
                        "group_id":     group["id"],
                        "group_name":   group["name"],
                        "group_size":   group["size"],
                        "session_number": sn,
                        "nb_sessions":    nb,
                    })
        return sessions

    def _global_forbidden_slots(self, constraints: dict, slots: list[dict]) -> list[int]:
        """Returns slot indices that fall on forbidden days."""
        forbidden = [d.lower() for d in constraints.get("forbidden_days", [])]
        return [
            s["index"] for s in slots
            if s["day"].lower() in forbidden or DAY_FR.get(s["day"], "").lower() in forbidden
        ]

    def _trainer_forbidden_slots(
        self,
        constraints: dict,
        slots:       list[dict],
        trainers:    list[dict],
    ) -> dict[int, list[int]]:
        """
        For each trainer, returns the list of forbidden slot indices
        based on their availability constraints.
        """
        trainer_avail = {
            k.lower(): v.lower()
            for k, v in constraints.get("trainer_availability", {}).items()
        }
        if not trainer_avail:
            return {}

        forbidden: dict[int, list[int]] = {}

        for t_idx, trainer in enumerate(trainers):
            name    = trainer["name"].lower()
            matched = None
            for key, avail in trainer_avail.items():
                if key in name:
                    matched = avail
                    break
            if matched is None:
                continue

            # A trainer is forbidden in a slot if that day is NOT mentioned in their availability
            all_days_mentioned = [d.lower() for d in DAY_ORDER] + list(DAY_FR.values())
            day_mentioned = any(d in matched for d in all_days_mentioned)

            if day_mentioned:
                # Forbidden in slots whose day is not mentioned in availability
                forbidden[t_idx] = [
                    s["index"] for s in slots
                    if s["day"].lower() not in matched
                    and DAY_FR.get(s["day"], "").lower() not in matched
                ]

        return forbidden