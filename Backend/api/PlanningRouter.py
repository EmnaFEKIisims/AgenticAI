"""
api/PlanningRouter.py
======================
Your original code + fixes:
  + _last_constraints global variable            (kept — ephemeral, see note below)
  + GET  /planning/last-state   → PlanningPage loads on mount
  + POST /planning/regenerate   → HITL revision
  + impact_analysis returns full shape → fixes ImpactSummary crash
  + /validate / /reject write to DB (unchanged — this always worked)

  ← FIXED (root cause of "à chaque retour sur /planning, ça revient à
    l'état initial même si validé"):
    GET /last-state, GET /schedule and GET /export/csv used to read
    EXCLUSIVELY from _last_schedule / _last_group_id — plain Python module
    globals. Those are wiped every time the process restarts, which
    `uvicorn --reload` does on ANY file save during dev, and they were
    never re-derived from the DB. So even though /validate and /reject
    correctly persisted status='validated'/'rejected' to schedule_slots,
    a reload between "validate" and "come back to /planning" made
    /last-state answer has_planning=false / stale data, and the frontend
    had no choice but to look empty/pending again.

    Now /last-state, /schedule and /export/csv ALWAYS query
    schedule_slots directly for the latest non-superseded
    planning_group_id belonging to the user, and rebuild the enriched
    session dicts (course/trainer/room/group names, suggested_day /
    suggested_time) via a DB join instead of trusting any in-memory
    cache. The DB is now the only source of truth for "what is the
    current planning and its validation state" — exactly what was asked.

    Known limitation (not a regression — this data was NEVER persisted):
    `reasoning` (the AI agent's free-text justification per session) has
    no column in ScheduleSlot, so it can only be shown right after
    generation (POST /run, /run/with-constraints, /regenerate — which
    still return the fresh, fully-enriched data). Once reconstructed
    from DB on a later GET, `reasoning` comes back as "" instead of the
    original text. If you want it to survive reloads too, add a
    `reasoning = Column(Text, nullable=True)` column to ScheduleSlot and
    save `s.get("reasoning", "")` in `_save_to_db` — happy to wire that
    up once the column exists.

  ← NEW (per-user data isolation):
    PlanningAgent now requires user_id and only ever loads THAT user's
    own trainers/rooms/groups/courses/equipment (see agents/planning_agent.py).
    The 3 endpoints that instantiate it (/run, /run/with-constraints,
    /regenerate) now pass user_id=user_id — before, they had user_id
    available via Depends(get_user_id) but never forwarded it to the
    agent, so a planning could be built from every user's data mixed
    together. Fixed below.
"""

import io, os, uuid, traceback
from datetime import datetime, date, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from db.DB import SessionLocal
from agents.planning_agent  import PlanningAgent, schedule_to_csv_bytes
from agents.ConstraintAgent import ConstraintAgent

SUPERADMIN_ID = os.getenv("SUPERADMIN_ID", "00000000-0000-0000-0000-000000000001")

router = APIRouter(prefix="/planning", tags=["Planning Agent"])

# ← These are now PURELY a best-effort, ephemeral convenience — nothing
#   that decides "is there a planning / is it validated" reads from them
#   anymore. `_last_constraints` in particular has nowhere to live in the
#   DB (ScheduleSlot has no constraints column), so it stays in-memory and
#   WILL be lost on restart — that's a real, disclosed gap, but it only
#   affects the "Active Constraints" display chips, never the HITL status
#   or the schedule itself, which are now 100% DB-sourced.
_last_constraints: dict = {}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def get_db():
    db = SessionLocal()
    try:    yield db
    finally: db.close()

def get_user_id(x_user_id: str = Header(default=SUPERADMIN_ID)) -> str:
    return x_user_id


# =============================================================================
#  Schemas
# =============================================================================

class PlanningRunRequest(BaseModel):
    user_constraints: Optional[str] = None

class PlanningRunWithConstraintsRequest(BaseModel):
    constraints_dict: dict

class FullPipelineRequest(BaseModel):
    pedagogical_text: Optional[str] = ""
    user_text:        Optional[str] = ""

class SessionSlotOut(BaseModel):
    id:                      Optional[int] = None
    session_number:          int
    course_id:               int
    course_title:            str
    trainer_id:               int
    trainer_name:            str
    room_id:                 int
    room_name:               str
    group_name:              str
    suggested_day:           str
    suggested_time:          str
    reasoning:               str
    learner_group_id:        int
    start_time:              str
    end_time:                str
    status:                  str
    is_validated:            bool
    quality_score:           float
    pedagogical_audit_score: float
    planning_group_id:       Optional[str] = None
    class Config:
        extra = "ignore"

class PlanningRunResponse(BaseModel):
    success:           bool
    planning_group_id: str
    total_sessions:    int
    final_constraints: dict
    schedule:          list[SessionSlotOut]
    engine:            str = "greedy"

class ValidateBody(BaseModel):
    validation_notes: Optional[str] = None

class RejectBody(BaseModel):
    reason: Optional[str] = None

class RegenerateBody(BaseModel):
    constraints_dict:  Optional[dict] = None
    user_constraints:  Optional[str]  = None
    rejected_group_id: Optional[str]  = None
    attempt:           int             = 2

class MoveBody(BaseModel):
    new_start_time: str
    new_end_time:   str
    admin_note:     Optional[str] = None

class ImpactBody(BaseModel):
    new_start_time:    str
    new_end_time:      str
    planning_group_id: Optional[str] = None


# =============================================================================
#  DB SAVE
# =============================================================================

def _save_to_db(schedule: list[dict], db: Session, user_id: str) -> tuple[str, dict[int, int]]:
    from models.schedule import ScheduleSlot

    old_slots = db.query(ScheduleSlot).filter(
        ScheduleSlot.user_id == user_id,
        ScheduleSlot.status.in_(["draft", "validated"])
    ).all()

    if old_slots:
        now = datetime.now(timezone.utc)
        for s in old_slots:
            s.status = "superseded"
            s.rejected_at = now
        db.flush()
        print(f"  [Router] Superseded {len(old_slots)} old slots for user {user_id[:8]}...")

    group_id = str(uuid.uuid4())
    slots    = []

    for idx, s in enumerate(schedule):
        try:
            start = datetime.fromisoformat(str(s["start_time"]))
            end   = datetime.fromisoformat(str(s["end_time"]))
        except Exception:
            continue

        sn   = s.get("session_number") or (idx + 1)
        slot = ScheduleSlot(
            course_id               = s.get("course_id", 0),
            trainer_id              = s.get("trainer_id", 0),
            room_id                 = s.get("room_id", 0),
            learner_group_id        = s.get("learner_group_id", 0),
            start_time              = start,
            end_time                = end,
            planning_group_id       = group_id,
            session_number          = sn,
            quality_score           = float(s.get("quality_score", 0.0)),
            pedagogical_audit_score = float(s.get("pedagogical_audit_score", 0.0)),
            status                  = "draft",
            is_validated            = False,
            move_history            = [],
            user_id                 = user_id,
        )
        slots.append((sn, slot))

    try:
        db.add_all([slot for _, slot in slots])
        db.commit()
        sn_to_db_id = {sn: slot.id for sn, slot in slots if slot.id is not None}
        print(f"  [Router] ✅ {len(slots)} slots saved → group={group_id[:8]}... user={user_id[:8]}...")
        return group_id, sn_to_db_id
    except Exception as e:
        db.rollback()
        print(f"  [Router] ⚠️  DB save failed: {e}")
        return group_id, {}


def _build_response(result, db: Session, user_id: str) -> PlanningRunResponse:
    global _last_constraints
    try:
        group_id, sn_to_db_id = _save_to_db(result.schedule, db, user_id)
    except Exception:
        traceback.print_exc()
        group_id    = str(uuid.uuid4())
        sn_to_db_id = {}

    # Best-effort only — see module docstring. Never read back to decide
    # HITL/schedule state, only used to pre-fill the "Active Constraints"
    # chips right after a fresh generation in the same process lifetime.
    _last_constraints = result.constraints_used if hasattr(result, "constraints_used") else {}

    enriched = []
    for idx, s in enumerate(result.schedule):
        s_copy = dict(s)
        sn = s_copy.get("session_number") or (idx + 1)
        s_copy["id"] = sn_to_db_id.get(sn) or sn_to_db_id.get(idx + 1)
        s_copy["planning_group_id"] = group_id
        enriched.append(s_copy)

    slots_out = []
    for s in enriched:
        try:
            slots_out.append(SessionSlotOut(**s))
        except Exception:
            pass

    return PlanningRunResponse(
        success           = result.success,
        planning_group_id = group_id,
        total_sessions    = result.total_sessions,
        final_constraints = _last_constraints,
        schedule          = slots_out,
        engine            = getattr(result, "engine", "greedy"),
    )


# =============================================================================
#  DB-SOURCED READ HELPERS  ← the actual fix
# =============================================================================

def _week_reference_monday(start_times: list[datetime]) -> date:
    """Monday of the earliest session's week — used to compute 'Week N'."""
    real_starts = [t for t in start_times if t is not None]
    if not real_starts:
        return date.today()
    earliest = min(real_starts)
    return (earliest - timedelta(days=earliest.weekday())).date()


def _slot_to_out_dict(slot, reference_monday: date) -> dict:
    """
    Rebuilds the enriched session dict straight from the DB row + its
    joined Course/Trainer/Room/LearnerGroup — this is what makes
    /last-state and /schedule independent of any in-memory cache.
    """
    start = slot.start_time
    end   = slot.end_time
    week_number = ((start.date() - reference_monday).days // 7) + 1 if start else 1
    day_name = DAYS[start.weekday()] if start and start.weekday() < len(DAYS) else "Monday"

    return {
        "id":                      slot.id,
        "planning_group_id":       slot.planning_group_id,
        "session_number":          slot.session_number or slot.id,
        "course_id":               slot.course_id,
        "course_title":            slot.course.title if slot.course else f"Course #{slot.course_id}",
        "trainer_id":              slot.trainer_id,
        "trainer_name":            slot.trainer.name if slot.trainer else f"Trainer #{slot.trainer_id}",
        "room_id":                 slot.room_id,
        "room_name":               slot.room.name if slot.room else f"Room #{slot.room_id}",
        "group_name":              slot.learner_group.name if slot.learner_group else f"Group #{slot.learner_group_id}",
        "learner_group_id":        slot.learner_group_id,
        "suggested_day":           f"Week {week_number} — {day_name}",
        "suggested_time":          f"{start.strftime('%H:%M')} → {end.strftime('%H:%M')}" if start and end else "",
        # ← Not persisted anywhere (no `reasoning` column on ScheduleSlot).
        #   See module docstring for how to add it if you want it to
        #   survive reloads too.
        "reasoning":               "",
        "start_time":              start.isoformat() if start else "",
        "end_time":                end.isoformat()   if end   else "",
        "status":                  slot.status,
        "is_validated":            bool(slot.is_validated),
        "quality_score":           float(slot.quality_score or 0.0),
        "pedagogical_audit_score": float(slot.pedagogical_audit_score or 0.0),
    }


def _get_latest_group_id_for_user(db: Session, user_id: str) -> Optional[str]:
    """
    The current planning for a user = the most recently created batch of
    slots that hasn't been superseded by a newer generation. This is the
    single source of truth for "what planning is active right now" —
    replaces the old `_last_group_id` global entirely.
    """
    from models.schedule import ScheduleSlot

    row = (
        db.query(ScheduleSlot.planning_group_id)
        .filter(
            ScheduleSlot.user_id == user_id,
            ScheduleSlot.status != "superseded",
            ScheduleSlot.planning_group_id.isnot(None),
        )
        .order_by(ScheduleSlot.created_at.desc())
        .first()
    )
    return row[0] if row else None


def _get_schedule_for_group(db: Session, user_id: str, group_id: str) -> list[dict]:
    from models.schedule import ScheduleSlot

    slots = (
        db.query(ScheduleSlot)
        .options(
            joinedload(ScheduleSlot.course),
            joinedload(ScheduleSlot.trainer),
            joinedload(ScheduleSlot.room),
            joinedload(ScheduleSlot.learner_group),
        )
        .filter(
            ScheduleSlot.user_id           == user_id,
            ScheduleSlot.planning_group_id == group_id,
        )
        .order_by(ScheduleSlot.session_number.asc(), ScheduleSlot.id.asc())
        .all()
    )
    if not slots:
        return []

    reference_monday = _week_reference_monday([s.start_time for s in slots])
    return [_slot_to_out_dict(s, reference_monday) for s in slots]


def _compute_hitl_status(schedule: list[dict]) -> str:
    statuses = {s.get("status") for s in schedule}
    if "validated" in statuses:
        return "validated"
    if statuses and statuses <= {"rejected"}:
        return "rejected"
    return "pending" if schedule else "idle"


# =============================================================================
#  ENDPOINTS
# =============================================================================

@router.get("/last-state")
def get_last_state(
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_user_id),
):
    # ← FIXED: was reading `_last_schedule` (an in-memory global, wiped on
    #   every backend restart). Now always re-derives the current planning
    #   and its real HITL status straight from schedule_slots — a
    #   `uvicorn --reload` restart, a server redeploy, or any other reason
    #   the process restarted no longer loses "is this planning validated".
    group_id = _get_latest_group_id_for_user(db, user_id)
    if not group_id:
        return {
            "has_planning":      False,
            "planning_group_id": "",
            "total_sessions":    0,
            "schedule":          [],
            "constraints":       {},
            "hitl_status":       "idle",
        }

    schedule = _get_schedule_for_group(db, user_id, group_id)
    return {
        "has_planning":      len(schedule) > 0,
        "planning_group_id": group_id,
        "total_sessions":    len(schedule),
        "schedule":          schedule,
        "constraints":       _last_constraints,   # best-effort only, see docstring
        "hitl_status":       _compute_hitl_status(schedule),
    }


@router.post("/run", response_model=PlanningRunResponse)
def run_planning(
    body:    PlanningRunRequest,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_user_id),
):
    try:
        # ← FIXED: user_id is now forwarded to PlanningAgent, which requires
        #   it and uses it to load ONLY this user's own data (see
        #   agents/planning_agent.py — _load_data_from_db / _load_constraints_from_db).
        result = PlanningAgent(db=db, user_id=user_id).run(extra_constraints=body.user_constraints or "")
        if not result.success:
            raise HTTPException(422, detail=result.error)
        return _build_response(result, db, user_id)
    except HTTPException: raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.post("/run/with-constraints", response_model=PlanningRunResponse)
def run_with_constraints(
    body:    PlanningRunWithConstraintsRequest,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_user_id),
):
    try:
        result = PlanningAgent(db=db, user_id=user_id).run(constraints_dict=body.constraints_dict)
        if not result.success:
            raise HTTPException(422, detail=result.error)
        return _build_response(result, db, user_id)
    except HTTPException: raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.post("/regenerate", response_model=PlanningRunResponse)
def regenerate_planning(
    body:    RegenerateBody,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_user_id),
):
    try:
        result = PlanningAgent(db=db, user_id=user_id).regenerate(
            constraints_dict  = body.constraints_dict,
            extra_constraints = body.user_constraints,
            attempt           = body.attempt,
        )
        if not result.success:
            raise HTTPException(422, detail=result.error)
        return _build_response(result, db, user_id)
    except HTTPException: raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.post("/{planning_group_id}/validate")
def validate_schedule(
    planning_group_id: str,
    body:    ValidateBody,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_user_id),
):
    from models.schedule import ScheduleSlot
    slots = db.query(ScheduleSlot).filter(
        ScheduleSlot.planning_group_id == planning_group_id,
        ScheduleSlot.user_id           == user_id,
    ).all()
    if not slots:
        raise HTTPException(404, detail="No slots found for this user and group.")
    now = datetime.now(timezone.utc)
    for slot in slots:
        slot.status           = "validated"
        slot.is_validated     = True
        slot.validated_at     = now
        slot.validation_notes = body.validation_notes
    db.commit()

    # ← No more _last_schedule sync needed here — /last-state and
    #   /schedule now re-read this exact commit straight from the DB on
    #   every call, so there is nothing else to keep "in sync" anymore.
    return {"success": True, "hitl_status": "validated", "total_slots": len(slots)}


@router.post("/{planning_group_id}/reject")
def reject_schedule(
    planning_group_id: str,
    body:    RejectBody,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_user_id),
):
    from models.schedule import ScheduleSlot
    slots = db.query(ScheduleSlot).filter(
        ScheduleSlot.planning_group_id == planning_group_id,
        ScheduleSlot.user_id           == user_id,
    ).all()
    now = datetime.now(timezone.utc)
    for slot in slots:
        slot.status           = "rejected"
        slot.rejected_at      = now
        slot.validation_notes = body.reason
    db.commit()

    return {"success": True, "hitl_status": "rejected", "total_slots": len(slots)}


@router.post("/session/{slot_id}/impact")
def impact_analysis(
    slot_id: int,
    body:    ImpactBody,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_user_id),
):
    from models.schedule import ScheduleSlot
    slot = db.query(ScheduleSlot).filter(
        ScheduleSlot.id      == slot_id,
        ScheduleSlot.user_id == user_id,
    ).first()
    if not slot:
        raise HTTPException(404, detail=f"Slot {slot_id} not found.")

    new_start = datetime.fromisoformat(body.new_start_time)
    new_end   = datetime.fromisoformat(body.new_end_time)
    group_id  = body.planning_group_id or slot.planning_group_id

    others = db.query(ScheduleSlot).filter(
        ScheduleSlot.id                != slot_id,
        ScheduleSlot.user_id           == user_id,
        ScheduleSlot.planning_group_id == group_id,
        ScheduleSlot.status.notin_(["rejected", "superseded"]),
    ).all()

    conflicts = []
    for o in others:
        if not (o.start_time < new_end and new_start < o.end_time):
            continue
        if o.trainer_id       == slot.trainer_id:
            conflicts.append({"type": "trainer", "slot_id": o.id,
                              "description": f"Trainer conflict with session #{o.session_number}"})
        if o.room_id          == slot.room_id:
            conflicts.append({"type": "room", "slot_id": o.id,
                              "description": f"Room conflict with session #{o.session_number}"})
        if o.learner_group_id == slot.learner_group_id:
            conflicts.append({"type": "group", "slot_id": o.id,
                              "description": f"Group conflict with session #{o.session_number}"})

    return {
        "slot_id":            slot_id,
        "is_safe":            not conflicts,
        "new_conflicts":      conflicts,
        "resolved_conflicts": [],
        "affected_sessions":  [],
        "recommendation":     "Safe to move." if not conflicts
                              else f"{len(conflicts)} conflict(s) detected.",
        "summary":            "No conflicts." if not conflicts
                              else f"{len(conflicts)} conflict(s).",
    }


@router.patch("/session/{slot_id}/move")
def apply_move(
    slot_id: int,
    body:    MoveBody,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_user_id),
):
    from models.schedule import ScheduleSlot
    slot = db.query(ScheduleSlot).filter(
        ScheduleSlot.id      == slot_id,
        ScheduleSlot.user_id == user_id,
    ).first()
    if not slot:
        raise HTTPException(404, detail=f"Slot {slot_id} not found.")

    new_start = datetime.fromisoformat(body.new_start_time)
    new_end   = datetime.fromisoformat(body.new_end_time)
    old_start = slot.start_time.isoformat() if slot.start_time else ""
    old_end   = slot.end_time.isoformat()   if slot.end_time   else ""

    slot.start_time   = new_start
    slot.end_time     = new_end
    slot.move_history = list(slot.move_history or []) + [{
        "from_start": old_start,
        "from_end":   old_end,
        "to_start":   new_start.isoformat(),
        "to_end":     new_end.isoformat(),
        "moved_at":   datetime.now(timezone.utc).isoformat(),
    }]
    slot.status = "draft"
    db.commit()

    # ← No more _last_schedule sync needed — the next /last-state or
    #   /schedule call re-reads this row (new start/end, status='draft')
    #   straight from the DB.
    return {
        "success":        True,
        "slot_id":        slot_id,
        "session_number": slot.session_number,
        "new_start_time": new_start.isoformat(),
        "new_end_time":   new_end.isoformat(),
    }


@router.get("/schedule", response_model=list[SessionSlotOut])
def get_last_schedule(
    planning_group_id: Optional[str] = None,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_user_id),
):
    # ← FIXED: was `[SessionSlotOut(**s) for s in _last_schedule ...]` — the
    #   same fragile in-memory global. Now reads the latest (or explicitly
    #   requested) planning_group_id straight from the DB.
    group_id = planning_group_id or _get_latest_group_id_for_user(db, user_id)
    if not group_id:
        raise HTTPException(404, detail="No schedule yet.")

    schedule = _get_schedule_for_group(db, user_id, group_id)
    if not schedule:
        raise HTTPException(404, detail="No schedule yet.")

    return [SessionSlotOut(**s) for s in schedule]


@router.get("/export/csv")
def export_csv(
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_user_id),
):
    # ← FIXED: same root cause as above — was reading `_last_schedule`.
    group_id = _get_latest_group_id_for_user(db, user_id)
    if not group_id:
        raise HTTPException(404, detail="No schedule to export.")

    schedule = _get_schedule_for_group(db, user_id, group_id)
    if not schedule:
        raise HTTPException(404, detail="No schedule to export.")

    return StreamingResponse(
        io.BytesIO(schedule_to_csv_bytes(schedule)),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=schedule.csv"},
    )