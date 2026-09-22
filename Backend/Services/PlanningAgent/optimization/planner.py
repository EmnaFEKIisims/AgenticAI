"""
agents/planner.py
==================
High-level OR-Tools scheduling engine.

Called by PlanningAgent instead of the old greedy _generate_schedule().

Planner
  │
  ├── Prepares data (WEEKLY slots, course x group PAIRS, forbidden slots)
  │
  ├── optimization/variables.py   → CP-SAT IntVar per PAIR (not per session)
  │
  ├── optimization/constraints.py → Hard constraints
  │
  ├── optimization/objectives.py  → Minimize makespan + specialization mismatch
  │
  ├── optimization/solver.py      → CP-SAT solve (30s time limit)
  │
  └── optimization/solution_mapper.py → OR-Tools solution → week-expanded schedule list[dict]

If OR-Tools finds no solution → returns None → PlanningAgent falls back to greedy.

← CHANGED (fix for "OR-Tools Status: UNKNOWN / always falls back to greedy"):
  This used to build one CP-SAT decision (slot, trainer, room) PER
  SESSION -- 240 of them in this project, one for every week-occurrence
  of every course x group combo, over the FULL 20-week slot list (300
  slots). That's the wrong shape for this problem: the actual planning
  model is "pick ONE fixed weekly slot per (course x group) PAIR, then
  repeat it every week" (see agents/planning_agent.py,
  _generate_schedule_recurring -- this is exactly what the greedy
  fallback already does, with only 66 pairs). Solving per-session made
  the CP-SAT search space ~3.6x too big and added thousands of useless
  constraints between sessions that were never meant to differ (same
  pair, different week) -- so the solver hit its 30s time limit without
  even finding a first feasible solution (status UNKNOWN).

  Now the CP-SAT model decides only the 66 pairs' weekly slots
  (n_weekly_slots ~= 15, not 300), matching the greedy engine's problem
  size exactly, then the solution is expanded into individual dated
  sessions in optimization/solution_mapper.py. Same guarantees, same
  output shape, orders of magnitude smaller search space.
"""

import math
from datetime import datetime, timedelta

from ortools.sat.python import cp_model

from Services.PlanningAgent.optimization.variables      import create_pair_variables
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

        # ── Step 1: Pre-compute WEEKLY time slots (one week only) ─────────────
        weekly_slots = self._build_weekly_slots(constraints)
        if not weekly_slots:
            print("  [Planner] ❌ No valid weekly slots.")
            return None
        print(f"  [Planner] {len(weekly_slots)} weekly slots available.")

        # ── Step 2: Build (course x group) pairs ──────────────────────────────
        pairs = self._build_pairs(data, constraints)
        if not pairs:
            print("  [Planner] ❌ No pairs to schedule.")
            return None
        print(f"  [Planner] {len(pairs)} pairs to schedule "
              f"({sum(p['nb_sessions'] for p in pairs)} sessions once expanded).")

        trainers = data.get("trainers", [])
        rooms    = data.get("rooms",    [])
        if not trainers or not rooms:
            print("  [Planner] ❌ No trainers or rooms available.")
            return None

        # ── Step 3: Compute forbidden WEEKLY slots ────────────────────────────
        forbidden_global  = self._global_forbidden_slots(constraints, weekly_slots)
        forbidden_trainer = self._trainer_forbidden_slots(constraints, weekly_slots, trainers)

        # ── Step 4: Build CP-SAT model ────────────────────────────────────────
        model     = cp_model.CpModel()
        pair_vars = create_pair_variables(model, pairs, len(weekly_slots), trainers, rooms)

        # ── Step 5: Add constraints ───────────────────────────────────────────
        add_group_non_overlap(model, pair_vars, pairs)
        add_resource_non_overlap(model, pair_vars)
        add_forbidden_slots(model, pair_vars, forbidden_global)
        add_trainer_forbidden_slots(model, pair_vars, forbidden_trainer)

        # ── Step 6: Add objective ─────────────────────────────────────────────
        build_objective(model, pair_vars, pairs, trainers, len(weekly_slots))

        # ── Step 7: Solve ─────────────────────────────────────────────────────
        solver, status = solve(model, self.time_limit)

        if not is_usable(status):
            print(f"  [Planner] OR-Tools could not find a solution → falling back to greedy.")
            return None

        # ── Step 8: Expand solution into a week-by-week schedule ─────────────
        schedule = build_schedule(
            solver, pair_vars, pairs, weekly_slots, trainers, rooms, reference_date,
        )
        print(f"  [Planner] ✅ {len(schedule)} session(s) scheduled by OR-Tools "
              f"({len(pairs)} pairs).")
        return schedule

    # ==========================================================================
    #  DATA PREPARATION
    # ==========================================================================

    def _build_weekly_slots(self, constraints: dict) -> list[dict]:
        """
        Pre-computes all valid (day, slot_idx) combinations for A SINGLE WEEK.
        Returns a list of weekly slot dicts indexed 0..N-1 -- used as the
        IntVar domain for each pair's slot_var. The actual per-week dates
        are computed later, in optimization/solution_mapper.py, once a
        pair's weekly slot has been decided by the solver.
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

        weekly_slots = []
        idx = 0
        for day in allowed_days:
            day_idx = DAY_ORDER.index(day)
            for si, (start, end) in enumerate(time_slots):
                weekly_slots.append({
                    "index":    idx,
                    "day":      day,
                    "day_idx":  day_idx,
                    "slot_idx": si,
                    "start":    start,
                    "end":      end,
                })
                idx += 1
        return weekly_slots

    def _build_pairs(self, data: dict, constraints: dict) -> list[dict]:
        """
        Builds the list of (course x group) pairs to schedule -- ONE entry
        per pair (not per session/week). Each pair carries nb_sessions
        (how many weeks it repeats), expanded later during solution mapping.
        """
        duration_min = constraints.get("session_duration_override") or DEFAULT_SESSION_DURATION_MINUTES
        pairs        = []

        for course in data.get("courses", []):
            course_dur = duration_min or int(course.get("session_duration", 3) * 60)
            nb         = math.ceil((course["total_hours"] * 60) / course_dur)

            for group in data.get("groups", []):
                pairs.append({
                    "course_id":      course["id"],
                    "course_title":   course["title"],
                    "group_id":       group["id"],
                    "group_name":     group["name"],
                    "group_size":     group["size"],
                    "nb_sessions":    nb,
                })
        return pairs

    def _global_forbidden_slots(self, constraints: dict, weekly_slots: list[dict]) -> list[int]:
        """Returns weekly slot indices that fall on forbidden days."""
        forbidden = [d.lower() for d in constraints.get("forbidden_days", [])]
        return [
            s["index"] for s in weekly_slots
            if s["day"].lower() in forbidden or DAY_FR.get(s["day"], "").lower() in forbidden
        ]

    def _trainer_forbidden_slots(
        self,
        constraints:  dict,
        weekly_slots: list[dict],
        trainers:     list[dict],
    ) -> dict[int, list[int]]:
        """
        For each trainer, returns the list of forbidden WEEKLY slot indices
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
                    s["index"] for s in weekly_slots
                    if s["day"].lower() not in matched
                    and DAY_FR.get(s["day"], "").lower() not in matched
                ]

        return forbidden