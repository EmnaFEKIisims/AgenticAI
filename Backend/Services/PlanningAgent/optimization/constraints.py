"""
optimization/constraints.py
=============================
Adds hard constraints to the CP-SAT model.

Hard constraints (must NEVER be violated):
  1. Same group       → different slots     (AllDifferent)
  2. Same trainer     → different slots     (pairwise implication)
  3. Same room        → different slots     (pairwise implication)
  4. Forbidden days   → forbidden slots     (global exclusion)
  5. Trainer unavailability → forbidden slots per trainer

Why pairwise implications for trainer/room?
  Because two sessions can share the same slot IF they use different
  trainers or rooms. AllDifferent would be too strict.
"""

from collections import defaultdict
from ortools.sat.python import cp_model
from Services.PlanningAgent.optimization.variables import SessionVar


def add_group_non_overlap(
    model:     cp_model.CpModel,
    sess_vars: list[SessionVar],
    sessions:  list[dict],
) -> None:
    """
    Sessions of the same learner group must be in different slots.
    Uses AddAllDifferent — the cleanest constraint for this.
    """
    # Group sessions by group_id
    group_map: dict[int, list[cp_model.IntVar]] = defaultdict(list)
    for sv in sess_vars:
        gid = sessions[sv.index].get("group_id")
        if gid is not None:
            group_map[gid].append(sv.slot_var)

    for gid, slot_vars in group_map.items():
        if len(slot_vars) > 1:
            model.AddAllDifferent(slot_vars)


def add_resource_non_overlap(
    model:     cp_model.CpModel,
    sess_vars: list[SessionVar],
) -> None:
    """
    If two sessions share the same trainer OR room, they must be in different slots.

    Uses pairwise boolean implications:
      same_trainer[i,j] → slot[i] != slot[j]
      same_room[i,j]    → slot[i] != slot[j]
    """
    n = len(sess_vars)
    for i in range(n):
        for j in range(i + 1, n):
            sv_i = sess_vars[i]
            sv_j = sess_vars[j]

            # ── Trainer conflict ───────────────────────────────────────────
            same_trainer = model.NewBoolVar(f"same_trainer_{i}_{j}")
            model.Add(sv_i.trainer_var == sv_j.trainer_var).OnlyEnforceIf(same_trainer)
            model.Add(sv_i.trainer_var != sv_j.trainer_var).OnlyEnforceIf(same_trainer.Not())
            model.Add(sv_i.slot_var != sv_j.slot_var).OnlyEnforceIf(same_trainer)

            # ── Room conflict ──────────────────────────────────────────────
            same_room = model.NewBoolVar(f"same_room_{i}_{j}")
            model.Add(sv_i.room_var == sv_j.room_var).OnlyEnforceIf(same_room)
            model.Add(sv_i.room_var != sv_j.room_var).OnlyEnforceIf(same_room.Not())
            model.Add(sv_i.slot_var != sv_j.slot_var).OnlyEnforceIf(same_room)


def add_forbidden_slots(
    model:                  cp_model.CpModel,
    sess_vars:              list[SessionVar],
    forbidden_slot_indices: list[int],
) -> None:
    """
    Global forbidden slots (forbidden days from constraints).
    No session can be placed in these slots.
    """
    if not forbidden_slot_indices:
        return
    forbidden_domain = cp_model.Domain.FromValues(forbidden_slot_indices).Complement()
    for sv in sess_vars:
        model.AddLinearConstraintWithBounds(
            [sv.slot_var], forbidden_domain.FlattenedIntervals()[0],
            forbidden_domain.FlattenedIntervals()[-1]
        )
    # Simpler alternative: explicit inequality per forbidden slot
    for sv in sess_vars:
        for f in forbidden_slot_indices:
            model.Add(sv.slot_var != f)


def add_trainer_forbidden_slots(
    model:                   cp_model.CpModel,
    sess_vars:               list[SessionVar],
    trainer_forbidden_slots: dict[int, list[int]],
) -> None:
    """
    Per-trainer forbidden slots (trainer unavailability).

    If session i uses trainer t, its slot must not be in trainer t's
    forbidden slots.

    Uses boolean implications:
      uses_trainer_t[i] → slot[i] ∉ forbidden_slots[t]
    """
    n = len(sess_vars)
    for t_idx, forbidden in trainer_forbidden_slots.items():
        if not forbidden:
            continue
        for sv in sess_vars:
            uses_t = model.NewBoolVar(f"uses_t{t_idx}_s{sv.index}")
            model.Add(sv.trainer_var == t_idx).OnlyEnforceIf(uses_t)
            model.Add(sv.trainer_var != t_idx).OnlyEnforceIf(uses_t.Not())
            for f_slot in forbidden:
                model.Add(sv.slot_var != f_slot).OnlyEnforceIf(uses_t)