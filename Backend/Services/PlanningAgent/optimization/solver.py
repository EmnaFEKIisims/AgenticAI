"""
optimization/solver.py
========================
Runs the CP-SAT solver and returns the status.

Statuses:
  OPTIMAL   → best possible solution found
  FEASIBLE  → valid solution found (not proven optimal, time limit hit)
  INFEASIBLE → no solution exists with these constraints
  UNKNOWN   → time limit hit before any solution found
"""

from ortools.sat.python import cp_model


# Status codes we consider "usable"
USABLE_STATUSES = {cp_model.OPTIMAL, cp_model.FEASIBLE}


def solve(
    model:              cp_model.CpModel,
    time_limit_seconds: int = 30,
) -> tuple[cp_model.CpSolver, int]:
    """
    Runs the CP-SAT solver on the model.

    Args:
        model:              Built CP-SAT model (variables + constraints + objective)
        time_limit_seconds: Maximum solving time (default 30s)
                            If time runs out → FEASIBLE if any solution was found

    Returns:
        (solver, status) where status is one of:
          cp_model.OPTIMAL   → use this solution
          cp_model.FEASIBLE  → use this solution (not optimal but valid)
          cp_model.INFEASIBLE → no solution → fall back to greedy
          cp_model.UNKNOWN   → timeout with no solution → fall back to greedy
    """
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_search_workers  = 4    # use multiple cores
    solver.parameters.log_search_progress = False # set True to see CP-SAT logs

    print(f"  [OR-Tools] Solving (time limit: {time_limit_seconds}s)...")
    status = solver.Solve(model)

    status_name = solver.StatusName(status)
    print(f"  [OR-Tools] Status: {status_name}")

    if status in USABLE_STATUSES:
        print(f"  [OR-Tools] Objective: {solver.ObjectiveValue():.1f}")
        print(f"  [OR-Tools] Wall time: {solver.WallTime():.2f}s")

    return solver, status


def is_usable(status: int) -> bool:
    """Returns True if the solver found a valid solution."""
    return status in USABLE_STATUSES