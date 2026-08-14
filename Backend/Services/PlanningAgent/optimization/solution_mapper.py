"""
optimization/solution_mapper.py
=================================
Converts the CP-SAT solution (integer variable values) into
the schedule list[dict] format expected by the rest of the system.

OR-Tools solution:
  slot_var[i]    → integer index into slots list
  trainer_var[i] → integer index into trainers list
  room_var[i]    → integer index into rooms list

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

from ortools.sat.python import cp_model
from Services.PlanningAgent.optimization.variables import SessionVar


def build_schedule(
    solver:    cp_model.CpSolver,
    sess_vars: list[SessionVar],
    sessions:  list[dict],
    slots:     list[dict],
    trainers:  list[dict],
    rooms:     list[dict],
) -> list[dict]:
    """
    Extracts the CP-SAT solution and builds the schedule list.

    Args:
        solver:    Solved CP-SAT solver instance
        sess_vars: Decision variables (one per session)
        sessions:  Session task dicts (same order as sess_vars)
        slots:     Pre-computed time slot dicts (indexed by slot index)
        trainers:  Trainer dicts (indexed by trainer_var value)
        rooms:     Room dicts (indexed by room_var value)

    Returns:
        list[dict] schedule — one entry per session, sorted by slot index
    """
    schedule  = []
    sg        = 1   # global session number

    for sv in sess_vars:
        sess = sessions[sv.index]

        slot_idx    = solver.Value(sv.slot_var)
        trainer_idx = solver.Value(sv.trainer_var)
        room_idx    = solver.Value(sv.room_var)

        slot    = slots[slot_idx]
        trainer = trainers[trainer_idx]
        room    = rooms[room_idx]

        schedule.append({
            # DB-required fields
            "course_id":               sess["course_id"],
            "trainer_id":              trainer["id"],
            "room_id":                 room["id"],
            "learner_group_id":        sess["group_id"],
            "start_time":              slot["start_dt"].isoformat(),
            "end_time":                slot["end_dt"].isoformat(),
            "status":                  "draft",
            "is_validated":            False,
            "quality_score":           0.0,
            "pedagogical_audit_score": 0.0,

            # Display fields
            "session_number":  sg,
            "course_title":    sess["course_title"],
            "trainer_name":    trainer["name"],
            "room_name":       room["name"],
            "group_name":      sess["group_name"],
            "suggested_day":   f"Week {slot['week'] + 1} — {slot['day']}",
            "suggested_time":  f"{slot['start']} → {slot['end']}",
            "reasoning": (
                f"OR-Tools | S{sess['session_number']}/{sess['nb_sessions']} | "
                f"W{slot['week'] + 1} | "
                f"{trainer['name']} [{trainer.get('specialization', '')}] | "
                f"{room['name']} cap={room['capacity']}>={sess['group_size']}"
            ),
        })
        sg += 1

    # Sort by slot index (chronological order)
    schedule.sort(key=lambda s: s["start_time"])
    return schedule