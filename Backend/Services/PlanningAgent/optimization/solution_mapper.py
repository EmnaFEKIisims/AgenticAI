"""
optimization/solution_mapper.py
=================================
Converts the CP-SAT solution (integer variable values) into the full,
week-expanded schedule list[dict] format expected by the rest of the
system.

← CHANGED: each solved PairVar now gives ONE fixed WEEKLY (day, slot,
  trainer, room) for a (course x group) pair -- not a full schedule
  entry per session. This module expands that single fixed weekly
  assignment into `nb_sessions` actual dated sessions (one per week),
  exactly like the greedy fallback's "Etape 2" in
  agents/planning_agent.py (_generate_schedule_recurring), so both
  engines produce the exact same "recurring fixed schedule" shape and
  the same dict fields.

OR-Tools solution (per pair):
  slot_var[i]    -> integer index into the WEEKLY slots list
  trainer_var[i] -> integer index into trainers list
  room_var[i]    -> integer index into rooms list

Output (matches PlanningAgent's existing schedule format):
  [
    {
      "course_id", "course_title", "trainer_id", "trainer_name",
      "room_id", "room_name", "learner_group_id", "group_name",
      "start_time", "end_time", "suggested_day", "suggested_time",
      "session_number", "status", "is_validated", ...
    },
    ...
  ]
"""

from datetime import datetime, timedelta

from ortools.sat.python import cp_model
from Services.PlanningAgent.optimization.variables import PairVar

# Same day order as agents/planner.py and agents/planning_agent.py
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def _slot_to_datetime(
    week: int, day: str, start: str, end: str, ref: datetime,
) -> tuple[datetime, datetime]:
    """Same helper as agents/planning_agent.py._slot_to_datetime."""
    base = ref + timedelta(weeks=week, days=DAY_ORDER.index(day))
    sh, sm = map(int, start.split(":"))
    eh, em = map(int, end.split(":"))
    return (
        base.replace(hour=sh, minute=sm, second=0, microsecond=0),
        base.replace(hour=eh, minute=em, second=0, microsecond=0),
    )


def build_schedule(
    solver:         cp_model.CpSolver,
    pair_vars:      list[PairVar],
    pairs:          list[dict],
    weekly_slots:   list[dict],
    trainers:       list[dict],
    rooms:          list[dict],
    reference_date: datetime,
) -> list[dict]:
    """
    Extracts the CP-SAT solution (one fixed weekly slot per pair) and
    expands it into individual dated sessions, one per week, for
    nb_sessions weeks.

    Args:
        solver:         Solved CP-SAT solver instance
        pair_vars:      Decision variables (one per course x group pair)
        pairs:          Pair dicts (same order as pair_vars)
        weekly_slots:   Pre-computed WEEKLY slot dicts (indexed by slot index)
        trainers:       Trainer dicts (indexed by trainer_var value)
        rooms:          Room dicts (indexed by room_var value)
        reference_date: First Monday of the planning

    Returns:
        list[dict] schedule -- one entry per session, sorted chronologically
    """
    schedule  = []
    global_sn = 1

    for pv in pair_vars:
        pair = pairs[pv.index]

        weekly_idx  = solver.Value(pv.slot_var)
        trainer_idx = solver.Value(pv.trainer_var)
        room_idx    = solver.Value(pv.room_var)

        wslot   = weekly_slots[weekly_idx]
        trainer = trainers[trainer_idx]
        room    = rooms[room_idx]

        nb = pair["nb_sessions"]
        for week in range(nb):
            start_dt, end_dt = _slot_to_datetime(
                week, wslot["day"], wslot["start"], wslot["end"], reference_date,
            )

            schedule.append({
                # DB-required fields
                "course_id":               pair["course_id"],
                "trainer_id":              trainer["id"],
                "room_id":                 room["id"],
                "learner_group_id":        pair["group_id"],
                "start_time":              start_dt.isoformat(),
                "end_time":                end_dt.isoformat(),
                "status":                  "draft",
                "is_validated":            False,
                "quality_score":           0.0,
                "pedagogical_audit_score": 0.0,

                # Display fields
                "session_number":  global_sn,
                "course_title":    pair["course_title"],
                "trainer_name":    trainer["name"],
                "room_name":       room["name"],
                "group_name":      pair["group_name"],
                "suggested_day":   f"Week {week + 1} — {wslot['day']}",
                "suggested_time":  f"{wslot['start']} → {wslot['end']}",
                "reasoning": (
                    f"OR-Tools | {pair['group_name']} | "
                    f"{pair['course_title']} = {wslot['day']} {wslot['start']} fixe | "
                    f"Séance {week + 1}/{nb} | "
                    f"{trainer['name']} [{trainer.get('specialization', '')}] | "
                    f"{room['name']} cap={room['capacity']}>={pair['group_size']}"
                ),
            })
            global_sn += 1

    # Sort by start time (chronological order)
    schedule.sort(key=lambda s: s["start_time"])
    return schedule