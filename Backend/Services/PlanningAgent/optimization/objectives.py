"""
optimization/objectives.py
============================
Defines what "best planning" means for the CP-SAT solver.

← CHANGED: operates on PairVar (one per course x group pair, 66 in this
  project) instead of a SessionVar per individual session (240). Same
  objective terms as before -- makespan + specialization penalty -- just
  computed over the smaller, correctly-sized decision space.

Objective = minimize( makespan + specialization_penalty )

  makespan:               latest WEEKLY slot used -> compact scheduling
  specialization_penalty: penalty when trainer specialization != course title
                          -> prefer matching trainers (soft constraint)
"""

from ortools.sat.python import cp_model
from Services.PlanningAgent.optimization.variables import PairVar


def build_objective(
    model:          cp_model.CpModel,
    pair_vars:      list[PairVar],
    pairs:          list[dict],
    trainers:       list[dict],
    n_weekly_slots: int,
) -> None:
    """
    Minimizes:
      1. Makespan  -- latest weekly slot index used (compact scheduling)
      2. Specialization mismatch -- soft preference for matching trainers

    Args:
        model:          CP-SAT model
        pair_vars:      list of PairVar (one per course x group pair)
        pairs:          list of pair dicts
        trainers:       list of trainer dicts
        n_weekly_slots: total number of weekly slots
    """
    cost_terms = []

    # -- 1. Makespan: minimize the maximum weekly slot used -----------------
    makespan = model.NewIntVar(0, n_weekly_slots - 1, "makespan")
    for pv in pair_vars:
        model.Add(makespan >= pv.slot_var)
    cost_terms.append(makespan)

    # -- 2. Specialization mismatch penalty ----------------------------------
    # For each pair x trainer: if trainer specialization doesn't match
    # the course title -> add a penalty when that trainer is chosen.
    penalty_weight = 3   # each mismatch costs 3x more than 1 extra slot

    for pv in pair_vars:
        pair      = pairs[pv.index]
        course_lc = pair.get("course_title", "").lower()

        for t_idx, trainer in enumerate(trainers):
            spec = trainer.get("specialization", "").lower()
            if course_lc and spec and course_lc not in spec:
                # This trainer doesn't match -> add penalty if chosen
                uses_t = model.NewBoolVar(f"obj_t{t_idx}_p{pv.index}")
                model.Add(pv.trainer_var == t_idx).OnlyEnforceIf(uses_t)
                model.Add(pv.trainer_var != t_idx).OnlyEnforceIf(uses_t.Not())
                # Penalty = penalty_weight when uses_t = 1
                penalty = model.NewIntVar(0, penalty_weight, f"pen_t{t_idx}_p{pv.index}")
                model.Add(penalty == penalty_weight).OnlyEnforceIf(uses_t)
                model.Add(penalty == 0).OnlyEnforceIf(uses_t.Not())
                cost_terms.append(penalty)

    # -- Minimize total cost ---------------------------------------------------
    model.Minimize(sum(cost_terms))