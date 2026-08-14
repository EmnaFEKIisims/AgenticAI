"""
optimization/objectives.py
============================
Defines what "best planning" means for the CP-SAT solver.

Objective = minimize( makespan + specialization_penalty )

  makespan:               latest slot used → compact scheduling
  specialization_penalty: penalty when trainer specialization ≠ course title
                          → prefer matching trainers (soft constraint)
"""

from ortools.sat.python import cp_model
from Services.PlanningAgent.optimization.variables import SessionVar


def build_objective(
    model:    cp_model.CpModel,
    sess_vars: list[SessionVar],
    sessions:  list[dict],
    trainers:  list[dict],
    n_slots:   int,
) -> None:
    """
    Minimizes:
      1. Makespan  — latest slot index used (compact scheduling)
      2. Specialization mismatch — soft preference for matching trainers

    Args:
        model:     CP-SAT model
        sess_vars: list of SessionVar (one per session)
        sessions:  list of session task dicts
        trainers:  list of trainer dicts
        n_slots:   total number of slots
    """
    cost_terms = []

    # ── 1. Makespan: minimize the maximum slot used ─────────────────────────
    makespan = model.NewIntVar(0, n_slots - 1, "makespan")
    for sv in sess_vars:
        model.Add(makespan >= sv.slot_var)
    cost_terms.append(makespan)

    # ── 2. Specialization mismatch penalty ──────────────────────────────────
    # For each session × trainer: if trainer specialization doesn't match
    # the course title → add a penalty when that trainer is chosen.
    penalty_weight = 3   # each mismatch costs 3× more than 1 extra slot

    for sv in sess_vars:
        sess      = sessions[sv.index]
        course_lc = sess.get("course_title", "").lower()

        for t_idx, trainer in enumerate(trainers):
            spec = trainer.get("specialization", "").lower()
            if course_lc and spec and course_lc not in spec:
                # This trainer doesn't match → add penalty if chosen
                uses_t = model.NewBoolVar(f"obj_t{t_idx}_s{sv.index}")
                model.Add(sv.trainer_var == t_idx).OnlyEnforceIf(uses_t)
                model.Add(sv.trainer_var != t_idx).OnlyEnforceIf(uses_t.Not())
                # Penalty = penalty_weight when uses_t = 1
                penalty = model.NewIntVar(0, penalty_weight, f"pen_t{t_idx}_s{sv.index}")
                model.Add(penalty == penalty_weight).OnlyEnforceIf(uses_t)
                model.Add(penalty == 0).OnlyEnforceIf(uses_t.Not())
                cost_terms.append(penalty)

    # ── Minimize total cost ──────────────────────────────────────────────────
    model.Minimize(sum(cost_terms))