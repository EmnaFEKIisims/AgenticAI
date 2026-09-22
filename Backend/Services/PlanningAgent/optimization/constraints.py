"""
optimization/constraints.py
=============================
Adds hard constraints to the CP-SAT model.

← CHANGED: operates on PairVar (one per course x group pair) instead of
  a SessionVar per individual session. Logic is unchanged -- these
  functions were already generic (they only touch .slot_var/.trainer_var/
  .room_var and a "group_id" key) -- only the import and type hints
  changed. But because there are now 66 pairs instead of 240 sessions,
  add_resource_non_overlap's O(n^2) pairwise loop goes from ~28,680
  pairs of constraints down to ~2,145 -- this is what makes the model
  solvable within the time limit.

Hard constraints (must NEVER be violated):
  1. Same group       -> different WEEKLY slots     (AllDifferent)
  2. Same trainer     -> different WEEKLY slots     (pairwise implication)
  3. Same room        -> different WEEKLY slots     (pairwise implication)
  4. Forbidden days   -> forbidden WEEKLY slots      (global exclusion)
  5. Trainer unavailability -> forbidden WEEKLY slots per trainer

Why pairwise implications for trainer/room?
  Because two pairs can share the same weekly slot IF they use different
  trainers or rooms. AllDifferent would be too strict.
"""

from collections import defaultdict
from ortools.sat.python import cp_model
from Services.PlanningAgent.optimization.variables import PairVar


def add_group_non_overlap(
    model:     cp_model.CpModel,
    pair_vars: list[PairVar],
    pairs:     list[dict],
) -> None:
    """
    Pairs of the same learner group must be in different weekly slots.
    Uses AddAllDifferent -- the cleanest constraint for this.
    """
    # Group pairs by group_id
    group_map: dict[int, list[cp_model.IntVar]] = defaultdict(list)
    for pv in pair_vars:
        gid = pairs[pv.index].get("group_id")
        if gid is not None:
            group_map[gid].append(pv.slot_var)

    for gid, slot_vars in group_map.items():
        if len(slot_vars) > 1:
            model.AddAllDifferent(slot_vars)


def add_resource_non_overlap(
    model:     cp_model.CpModel,
    pair_vars: list[PairVar],
) -> None:
    """
    If two pairs share the same trainer OR room, they must be in
    different weekly slots.

    Uses pairwise boolean implications:
      same_trainer[i,j] -> slot[i] != slot[j]
      same_room[i,j]    -> slot[i] != slot[j]
    """
    n = len(pair_vars)
    for i in range(n):
        for j in range(i + 1, n):
            pv_i = pair_vars[i]
            pv_j = pair_vars[j]

            # -- Trainer conflict --------------------------------------------
            same_trainer = model.NewBoolVar(f"same_trainer_{i}_{j}")
            model.Add(pv_i.trainer_var == pv_j.trainer_var).OnlyEnforceIf(same_trainer)
            model.Add(pv_i.trainer_var != pv_j.trainer_var).OnlyEnforceIf(same_trainer.Not())
            model.Add(pv_i.slot_var != pv_j.slot_var).OnlyEnforceIf(same_trainer)

            # -- Room conflict --------------------------------------------------
            same_room = model.NewBoolVar(f"same_room_{i}_{j}")
            model.Add(pv_i.room_var == pv_j.room_var).OnlyEnforceIf(same_room)
            model.Add(pv_i.room_var != pv_j.room_var).OnlyEnforceIf(same_room.Not())
            model.Add(pv_i.slot_var != pv_j.slot_var).OnlyEnforceIf(same_room)


def add_forbidden_slots(
    model:                  cp_model.CpModel,
    pair_vars:              list[PairVar],
    forbidden_slot_indices: list[int],
) -> None:
    """
    Global forbidden weekly slots (forbidden days from constraints).
    No pair can be placed in these weekly slots.
    """
    if not forbidden_slot_indices:
        return
    for pv in pair_vars:
        for f in forbidden_slot_indices:
            model.Add(pv.slot_var != f)


def add_trainer_forbidden_slots(
    model:                   cp_model.CpModel,
    pair_vars:               list[PairVar],
    trainer_forbidden_slots: dict[int, list[int]],
) -> None:
    """
    Per-trainer forbidden weekly slots (trainer unavailability).

    If pair i uses trainer t, its weekly slot must not be in trainer t's
    forbidden slots.

    Uses boolean implications:
      uses_trainer_t[i] -> slot[i] not in forbidden_slots[t]
    """
    for t_idx, forbidden in trainer_forbidden_slots.items():
        if not forbidden:
            continue
        for pv in pair_vars:
            uses_t = model.NewBoolVar(f"uses_t{t_idx}_p{pv.index}")
            model.Add(pv.trainer_var == t_idx).OnlyEnforceIf(uses_t)
            model.Add(pv.trainer_var != t_idx).OnlyEnforceIf(uses_t.Not())
            for f_slot in forbidden:
                model.Add(pv.slot_var != f_slot).OnlyEnforceIf(uses_t)