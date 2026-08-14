"""
Services/AnomalyAgent/impact_analyzer.py
==========================================
Analyzes the cascading impact of modifying a schedule slot.

Input:
  old_schedule   : current full schedule (list[dict])
  modified_slot  : the session being changed (dict)
  new_time       : {"start_time": "...", "end_time": "..."} — new timing

Output (ImpactResult):
  affected_slots      : sessions whose trainer/room/group is involved
  new_conflicts       : new anomalies created by the move
  resolved_conflicts  : anomalies that disappear after the move
  new_anomalies       : classified new conflicts (ready for DB insert)
  summary             : human-readable summary string

Example:
  Session S10 moved from Monday 08:00 to Tuesday 14:00
  →  affected:  S11 (same trainer), S15 (same room)
     new:       S15 → room conflict on Tuesday
     resolved:  S10 → trainer overload on Monday (now fixed)
"""

from dataclasses import dataclass, field
from copy import deepcopy

from Services.AnomalyAgent.detector   import detect_all
from Services.AnomalyAgent.classifier import classify_all


# =============================================================================
#  RESULT TYPE
# =============================================================================

@dataclass
class ImpactResult:
    modified_session:   dict
    old_time:           dict                    # {"start_time": ..., "end_time": ...}
    new_time:           dict
    affected_slots:     list[dict] = field(default_factory=list)
    new_conflicts:      list[dict] = field(default_factory=list)
    resolved_conflicts: list[dict] = field(default_factory=list)
    new_anomalies:      list[dict] = field(default_factory=list)
    summary:            str        = ""


# =============================================================================
#  HELPERS
# =============================================================================

def _find_shared_resource_sessions(
    modified_slot: dict,
    schedule: list[dict],
) -> list[dict]:
    """
    Returns sessions that share a resource (trainer / room / group)
    with the modified slot — excluding the slot itself.
    """
    sid        = modified_slot.get("session_number") or modified_slot.get("id")
    trainer_id = modified_slot.get("trainer_id")
    room_id    = modified_slot.get("room_id")
    group_id   = modified_slot.get("learner_group_id")

    affected = []
    for s in schedule:
        s_id = s.get("session_number") or s.get("id")
        if s_id == sid:
            continue
        if (
            (trainer_id and s.get("trainer_id")        == trainer_id) or
            (room_id    and s.get("room_id")           == room_id)    or
            (group_id   and s.get("learner_group_id")  == group_id)
        ):
            affected.append(s)

    return affected


def _apply_new_time(slot: dict, new_time: dict) -> dict:
    """Returns a copy of slot with updated start/end times."""
    updated = deepcopy(slot)
    updated["start_time"]   = new_time["start_time"]
    updated["end_time"]     = new_time["end_time"]
    updated["suggested_time"] = (
        f"{new_time['start_time'][-8:-3]} → {new_time['end_time'][-8:-3]}"
        if len(new_time.get("start_time", "")) >= 8
        else updated.get("suggested_time", "")
    )
    return updated


def _anomaly_key(a: dict) -> str:
    """Unique key for deduplicating anomalies."""
    return f"{a.get('anomaly_type')}|{a.get('details', {})}"


# =============================================================================
#  IMPACT ANALYZER
# =============================================================================

def analyze_impact(
    old_schedule:  list[dict],
    modified_slot: dict,
    new_time:      dict,
    planning_id:   int  = None,
    groups:        list[dict] = None,
    rooms:         list[dict] = None,
) -> ImpactResult:
    """
    Analyzes the cascading impact of moving a session to a new time.

    Steps:
      1. Detect anomalies in the CURRENT schedule (before move)
      2. Build the NEW schedule with the modified slot
      3. Detect anomalies in the NEW schedule (after move)
      4. Compare: new_conflicts = after - before, resolved = before - after
      5. Identify affected sessions (share trainer / room / group)

    Args:
        old_schedule:  full current schedule
        modified_slot: the session being moved
        new_time:      {"start_time": "2025-09-01T14:00:00", "end_time": "..."}
        planning_id:   optional planning id for DB linking
        groups:        group data for capacity check
        rooms:         room data for capacity check

    Returns:
        ImpactResult
    """
    sid = modified_slot.get("session_number") or modified_slot.get("id")
    print(f"\n  [ImpactAnalyzer] Analyzing move of session #{sid}...")
    print(f"    Old: {modified_slot.get('start_time')} → {modified_slot.get('end_time')}")
    print(f"    New: {new_time.get('start_time')} → {new_time.get('end_time')}")

    old_time = {
        "start_time": modified_slot.get("start_time", ""),
        "end_time":   modified_slot.get("end_time",   ""),
    }

    # ── Step 1: Detect anomalies BEFORE the move ──────────────────────────────
    before_raw        = detect_all(old_schedule, planning_id=planning_id,
                                   groups=groups, rooms=rooms)
    before_classified = classify_all(before_raw)
    before_keys       = {_anomaly_key(a) for a in before_classified}

    # ── Step 2: Build new schedule with the slot moved ────────────────────────
    updated_slot    = _apply_new_time(modified_slot, new_time)
    new_schedule    = [
        updated_slot if (
            (s.get("session_number") or s.get("id")) == sid
        ) else s
        for s in old_schedule
    ]

    # ── Step 3: Detect anomalies AFTER the move ───────────────────────────────
    after_raw        = detect_all(new_schedule, planning_id=planning_id,
                                  groups=groups, rooms=rooms)
    after_classified = classify_all(after_raw)
    after_keys       = {_anomaly_key(a) for a in after_classified}

    # ── Step 4: Diff ──────────────────────────────────────────────────────────
    new_conflicts      = [a for a in after_classified if _anomaly_key(a) not in before_keys]
    resolved_conflicts = [a for a in before_classified if _anomaly_key(a) not in after_keys]

    # ── Step 5: Affected sessions ─────────────────────────────────────────────
    affected = _find_shared_resource_sessions(modified_slot, old_schedule)

    # ── Build summary ─────────────────────────────────────────────────────────
    summary = (
        f"Session #{sid} ({modified_slot.get('course_title', '?')}) moved "
        f"from {old_time['start_time']} to {new_time['start_time']}. "
        f"{len(affected)} related session(s) affected. "
        f"{len(new_conflicts)} new conflict(s) introduced. "
        f"{len(resolved_conflicts)} existing conflict(s) resolved."
    )

    print(f"  [ImpactAnalyzer] {summary}")

    return ImpactResult(
        modified_session   = updated_slot,
        old_time           = old_time,
        new_time           = new_time,
        affected_slots     = affected,
        new_conflicts      = new_conflicts,
        resolved_conflicts = resolved_conflicts,
        new_anomalies      = new_conflicts,   # ready for AnomalyCreate
        summary            = summary,
    )