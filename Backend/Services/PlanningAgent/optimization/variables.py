"""
optimization/variables.py
===========================
Creates CP-SAT decision variables — one set per (course x group) PAIR,
NOT one set per individual session.

← CHANGED: previously this created one (slot, trainer, room) IntVar
  triple PER SESSION (240 in this project, one per week-occurrence of
  every course x group combo). That made the CP-SAT search space ~3.6x
  bigger than necessary and added useless pairwise constraints between
  sessions that are actually the SAME recurring pair on different
  weeks (they were never meant to differ -- see agents/planning_agent.py
  _generate_schedule_recurring, the "fixed slot repeated over N weeks"
  model). This was the direct cause of OR-Tools timing out
  (solver.Status == UNKNOWN after 30s) on a problem that is trivial once
  reduced to its real size: 66 pairs, not 240 sessions.

Now:
  - One PairVar per (course x group) pair (matches the greedy fallback's
    "66 pairs a placer").
  - slot_var is a WEEKLY slot index (0..n_weekly_slots-1), e.g. 0..14 for
    5 days x 3 sessions/day -- NOT an index into the full 20-week slot
    list. The same weekly slot is then repeated every week for
    nb_sessions weeks when the solution is expanded
    (see optimization/solution_mapper.py).
"""

from dataclasses import dataclass
from ortools.sat.python import cp_model


@dataclass
class PairVar:
    """CP-SAT variables for one (course x group) recurring pair."""
    index:       int             # pair index in the pairs list
    slot_var:    cp_model.IntVar   # WEEKLY slot (0..n_weekly_slots-1) -- fixed every week
    trainer_var: cp_model.IntVar
    room_var:    cp_model.IntVar


def create_pair_variables(
    model:          cp_model.CpModel,
    pairs:          list[dict],
    n_weekly_slots: int,
    trainers:       list[dict],
    rooms:          list[dict],
) -> list[PairVar]:
    """
    Creates one set of (weekly_slot, trainer, room) IntVar per pair.

    Args:
        model:          CP-SAT model
        pairs:          list of (course x group) pair dicts (from planner.py _build_pairs)
        n_weekly_slots: number of slots in a SINGLE week (allowed_days x sessions_per_day)
        trainers:       list of trainer dicts
        rooms:          list of room dicts

    Returns:
        list[PairVar] -- one per pair
    """
    n_trainers = len(trainers)
    pair_vars  = []

    for i, pair in enumerate(pairs):
        # Weekly slot: any valid weekly slot (fixed for all weeks of this pair)
        slot_var = model.NewIntVar(0, n_weekly_slots - 1, f"slot_{i}")

        # Trainer: any trainer (preferences handled in objectives)
        trainer_var = model.NewIntVar(0, n_trainers - 1, f"trainer_{i}")

        # Room: only rooms with sufficient capacity
        group_size = pair.get("group_size", 0)
        valid_rooms = [
            r_idx for r_idx, r in enumerate(rooms)
            if r["capacity"] >= group_size
        ]
        if not valid_rooms:
            valid_rooms = list(range(len(rooms)))  # fallback: all rooms

        room_var = model.NewIntVarFromDomain(
            cp_model.Domain.FromValues(valid_rooms),
            f"room_{i}"
        )

        pair_vars.append(PairVar(
            index       = i,
            slot_var    = slot_var,
            trainer_var = trainer_var,
            room_var    = room_var,
        ))

    return pair_vars