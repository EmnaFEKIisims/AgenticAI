"""
optimization/variables.py
===========================
Creates CP-SAT decision variables for each session.

For each session to schedule, we create 3 IntVar:
  slot_var    → which time slot (0 to n_slots-1)
  trainer_var → which trainer index (0 to n_trainers-1)
  room_var    → which room index (limited to rooms with enough capacity)

Using Domain.FromValues allows restricting room_var to only rooms
that fit the group — this reduces the search space significantly.
"""

from dataclasses import dataclass
from ortools.sat.python import cp_model


@dataclass
class SessionVar:
    """CP-SAT variables for one session to schedule."""
    index:       int             # session index in the sessions list
    slot_var:    cp_model.IntVar
    trainer_var: cp_model.IntVar
    room_var:    cp_model.IntVar


def create_session_variables(
    model:                  cp_model.CpModel,
    sessions:               list[dict],
    n_slots:                int,
    trainers:               list[dict],
    rooms:                  list[dict],
) -> list[SessionVar]:
    """
    Creates one set of (slot, trainer, room) IntVar per session.

    Args:
        model:    CP-SAT model
        sessions: list of session task dicts (from planner.py)
        n_slots:  total number of available time slots
        trainers: list of trainer dicts
        rooms:    list of room dicts

    Returns:
        list[SessionVar] — one per session
    """
    n_trainers = len(trainers)
    sess_vars  = []

    for i, sess in enumerate(sessions):
        # Slot: any valid slot
        slot_var = model.NewIntVar(0, n_slots - 1, f"slot_{i}")

        # Trainer: any trainer (preferences handled in objectives)
        trainer_var = model.NewIntVar(0, n_trainers - 1, f"trainer_{i}")

        # Room: only rooms with sufficient capacity
        group_size = sess.get("group_size", 0)
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

        sess_vars.append(SessionVar(
            index       = i,
            slot_var    = slot_var,
            trainer_var = trainer_var,
            room_var    = room_var,
        ))

    return sess_vars