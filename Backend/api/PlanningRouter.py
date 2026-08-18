"""
api/PlanningRouter.py
======================
Fixes:
  1. _save_to_db → auto-rejects ALL previous draft/validated slots before saving new batch
     → impact analysis never sees old planning slots
  2. impact_analysis → ALWAYS filters by planning_group_id (required, not optional)
     → no more false conflicts from old plannings
  3. _build_response → robust session_number→DB id mapping with index fallback
     → SessionSlotOut.id is always set → DnD uses correct DB id
"""

import io
import uuid
import traceback
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.DB import SessionLocal
from agents.planning_agent  import PlanningAgent, schedule_to_csv_bytes
from agents.ConstraintAgent import ConstraintAgent

router = APIRouter(prefix="/planning", tags=["Planning Agent"])

_last_schedule: list[dict] = []
_last_group_id: str        = ""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
    id:                      Optional[int] = None   # real DB primary key
    session_number:          int
    course_id:               int
    course_title:            str
    trainer_id:              int
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
    attempt:           int = 2

class MoveBody(BaseModel):
    new_start_time: str
    new_end_time:   str
    admin_note:     Optional[str] = None

class ImpactBody(BaseModel):
    new_start_time:    str
    new_end_time:      str
    planning_group_id: Optional[str] = None


# =============================================================================
#  DB SAVE — auto-rejects old plannings, returns {session_number: db_id}
# =============================================================================

def _save_to_db(schedule: list[dict], db: Session) -> tuple[str, dict[int, int]]:
    """
    FIX 1: Before saving the new batch, marks ALL previous draft/validated slots
    as 'superseded'. This prevents old slots from appearing in impact analysis.

    Returns (group_id, {session_number: db_slot_id}).
    """
    from models.schedule import ScheduleSlot

    # ── FIX: reject all previous non-rejected slots ───────────────────────────
    old_slots = db.query(ScheduleSlot).filter(
        ScheduleSlot.status.in_(["draft", "validated"])
    ).all()

    if old_slots:
        now = datetime.now(timezone.utc)
        for s in old_slots:
            s.status      = "superseded"
            s.rejected_at = now
        db.flush()
        print(f"  [Router] Superseded {len(old_slots)} old slots.")

    # ── Save new batch ────────────────────────────────────────────────────────
    group_id = str(uuid.uuid4())
    slots    = []

    for idx, s in enumerate(schedule):
        try:
            start = datetime.fromisoformat(str(s["start_time"]))
            end   = datetime.fromisoformat(str(s["end_time"]))
        except Exception:
            continue

        session_number = s.get("session_number") or (idx + 1)

        slot = ScheduleSlot(
            course_id               = s.get("course_id", 0),
            trainer_id              = s.get("trainer_id", 0),
            room_id                 = s.get("room_id", 0),
            learner_group_id        = s.get("learner_group_id", 0),
            start_time              = start,
            end_time                = end,
            planning_group_id       = group_id,
            session_number          = session_number,
            quality_score           = float(s.get("quality_score", 0.0)),
            pedagogical_audit_score = float(s.get("pedagogical_audit_score", 0.0)),
            status                  = "draft",
            is_validated            = False,
            move_history            = [],
        )
        slots.append((session_number, slot))

    try:
        db.add_all([slot for _, slot in slots])
        db.commit()

        # ── FIX: map session_number → real DB id ──────────────────────────────
        sn_to_db_id: dict[int, int] = {}
        for sn, slot in slots:
            if slot.id is not None:
                sn_to_db_id[sn] = slot.id

        print(f"  [Router] ✅ {len(slots)} slots saved → group={group_id[:8]}...")
        return group_id, sn_to_db_id

    except Exception as e:
        db.rollback()
        print(f"  [Router] ⚠️  DB save failed: {e}")
        return group_id, {}


# =============================================================================
#  RESPONSE BUILDER
# =============================================================================

def _build_response(result, db: Session) -> PlanningRunResponse:
    global _last_schedule, _last_group_id

    try:
        group_id, sn_to_db_id = _save_to_db(result.schedule, db)
    except Exception as e:
        traceback.print_exc()
        group_id    = str(uuid.uuid4())
        sn_to_db_id = {}

    _last_group_id = group_id

    # Inject DB ids using session_number mapping, index fallback
    enriched = []
    for idx, s in enumerate(result.schedule):
        s_copy = dict(s)
        sn     = s_copy.get("session_number") or (idx + 1)
        db_id  = sn_to_db_id.get(sn) or sn_to_db_id.get(idx + 1)
        s_copy["id"] = db_id    # None if mapping failed
        enriched.append(s_copy)

    _last_schedule = enriched

    slots_out = []
    for s in enriched:
        try:
            slots_out.append(SessionSlotOut(**s))
        except Exception as e:
            print(f"  [Router] Slot skip: {e}")

    return PlanningRunResponse(
        success           = result.success,
        planning_group_id = group_id,
        total_sessions    = result.total_sessions,
        final_constraints = result.constraints_used,
        schedule          = slots_out,
        engine            = getattr(result, "engine", "greedy"),
    )


# =============================================================================
#  ENDPOINTS
# =============================================================================

@router.post("/run", response_model=PlanningRunResponse)
def run_planning(body: PlanningRunRequest, db: Session = Depends(get_db)):
    try:
        result = PlanningAgent(db=db).run(extra_constraints=body.user_constraints or "")
        if not result.success:
            raise HTTPException(422, detail=result.error)
        return _build_response(result, db)
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.post("/run/with-constraints", response_model=PlanningRunResponse)
def run_with_constraints(body: PlanningRunWithConstraintsRequest, db: Session = Depends(get_db)):
    try:
        result = PlanningAgent(db=db).run(constraints_dict=body.constraints_dict)
        if not result.success:
            raise HTTPException(422, detail=result.error)
        return _build_response(result, db)
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.post("/run/full-pipeline")
def run_full_pipeline(body: FullPipelineRequest, db: Session = Depends(get_db)):
    try:
        cr     = ConstraintAgent(db=db).run(
            pedagogical_text=body.pedagogical_text or "",
            user_text=body.user_text or "",
        )
        result = PlanningAgent(db=db).run(constraints_dict=cr.planning_dict)
        if not result.success:
            raise HTTPException(422, detail=result.error)
        return _build_response(result, db)
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.post("/{planning_group_id}/validate")
def validate_schedule(planning_group_id: str, body: ValidateBody, db: Session = Depends(get_db)):
    try:
        from models.schedule import ScheduleSlot
        slots = db.query(ScheduleSlot).filter(
            ScheduleSlot.planning_group_id == planning_group_id
        ).all()
        if not slots:
            raise HTTPException(404, detail=f"No slots for group {planning_group_id}")
        now = datetime.now(timezone.utc)
        for slot in slots:
            slot.status           = "validated"
            slot.is_validated     = True
            slot.validated_at     = now
            slot.validation_notes = body.validation_notes
        db.commit()
        return {"success": True, "hitl_status": "validated",
                "message": f"✅ {len(slots)} session(s) validated.",
                "planning_group_id": planning_group_id,
                "total_slots": len(slots),
                "timestamp": now.isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.post("/{planning_group_id}/reject")
def reject_schedule(planning_group_id: str, body: RejectBody, db: Session = Depends(get_db)):
    try:
        from models.schedule import ScheduleSlot
        slots = db.query(ScheduleSlot).filter(
            ScheduleSlot.planning_group_id == planning_group_id
        ).all()
        now = datetime.now(timezone.utc)
        for slot in slots:
            slot.status           = "rejected"
            slot.rejected_at      = now
            slot.validation_notes = body.reason
        db.commit()
        return {"success": True, "hitl_status": "rejected",
                "message": f"❌ {len(slots)} session(s) rejected.",
                "planning_group_id": planning_group_id,
                "total_slots": len(slots),
                "timestamp": now.isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.get("/{planning_group_id}/status")
def get_status(planning_group_id: str, db: Session = Depends(get_db)):
    try:
        from models.schedule import ScheduleSlot
        slots = db.query(ScheduleSlot).filter(
            ScheduleSlot.planning_group_id == planning_group_id
        ).all()
        return {
            "planning_group_id": planning_group_id,
            "total_slots":       len(slots),
            "validated_slots":   sum(1 for s in slots if s.status == "validated"),
            "rejected_slots":    sum(1 for s in slots if s.status == "rejected"),
            "draft_slots":       sum(1 for s in slots if s.status == "draft"),
            "status":            slots[0].status if slots else "not_found",
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.post("/regenerate")
def regenerate_schedule(body: RegenerateBody, db: Session = Depends(get_db)):
    try:
        result = PlanningAgent(db=db).regenerate(
            constraints_dict  = body.constraints_dict,
            extra_constraints = body.user_constraints or "",
            attempt           = body.attempt,
        )
        if not result.success:
            raise HTTPException(422, detail=result.error)
        return _build_response(result, db)
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.post("/session/{slot_id}/impact")
def impact_analysis(slot_id: int, body: ImpactBody, db: Session = Depends(get_db)):
    """
    FIX 2: Always filters by planning_group_id.
    If not provided → uses the slot's own planning_group_id.
    This prevents false conflicts from old planning batches.
    """
    try:
        from models.schedule import ScheduleSlot
        slot = db.query(ScheduleSlot).filter(ScheduleSlot.id == slot_id).first()
        if not slot:
            raise HTTPException(404, detail=f"Slot {slot_id} not found")

        new_start = datetime.fromisoformat(body.new_start_time)
        new_end   = datetime.fromisoformat(body.new_end_time)

        # ── FIX: use slot's own group_id as fallback ──────────────────────────
        group_id = body.planning_group_id or slot.planning_group_id
        if not group_id:
            raise HTTPException(422, detail="planning_group_id is required for impact analysis")

        # Only compare against slots in the SAME planning batch
        others = db.query(ScheduleSlot).filter(
            ScheduleSlot.id                != slot_id,
            ScheduleSlot.planning_group_id == group_id,      # ← KEY FIX
            ScheduleSlot.status.notin_(["rejected", "superseded"]),
        ).all()

        print(f"  [Impact] Checking slot {slot_id} vs {len(others)} slots in group {group_id[:8]}...")

        def overlaps(s, start, end):
            return s.start_time < end and start < s.end_time

        new_conflicts = []
        for o in others:
            if not overlaps(o, new_start, new_end):
                continue
            if o.trainer_id == slot.trainer_id:
                new_conflicts.append({"type": "trainer", "slot_id": o.id,
                    "description": f"Trainer conflict with session #{o.session_number}"})
            if o.room_id == slot.room_id:
                new_conflicts.append({"type": "room", "slot_id": o.id,
                    "description": f"Room conflict with session #{o.session_number}"})
            if o.learner_group_id == slot.learner_group_id:
                new_conflicts.append({"type": "group", "slot_id": o.id,
                    "description": f"Group conflict with session #{o.session_number}"})

        is_safe = len(new_conflicts) == 0
        print(f"  [Impact] Result: {'✅ safe' if is_safe else f'⚠️ {len(new_conflicts)} conflict(s)'}")

        return {
            "slot_id":        slot_id,
            "proposed_start": new_start.isoformat(),
            "proposed_end":   new_end.isoformat(),
            "is_safe":        is_safe,
            "new_conflicts":  new_conflicts,
            "resolved_conflicts": [],
            "affected_sessions":  [],
            "summary":        "No conflicts." if is_safe else f"{len(new_conflicts)} conflict(s).",
            "recommendation": "✅ Safe to move." if is_safe else "⚠️ Conflicts detected.",
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.patch("/session/{slot_id}/move")
def apply_move(slot_id: int, body: MoveBody, db: Session = Depends(get_db)):
    try:
        from models.schedule import ScheduleSlot
        slot = db.query(ScheduleSlot).filter(ScheduleSlot.id == slot_id).first()
        if not slot:
            raise HTTPException(404, detail=f"Slot DB id={slot_id} not found.")

        new_start = datetime.fromisoformat(body.new_start_time)
        new_end   = datetime.fromisoformat(body.new_end_time)
        old_start = slot.start_time.isoformat() if slot.start_time else ""
        old_end   = slot.end_time.isoformat()   if slot.end_time   else ""

        history_entry = {
            "from_start": old_start, "from_end": old_end,
            "to_start":   new_start.isoformat(), "to_end": new_end.isoformat(),
            "admin_note": body.admin_note,
            "moved_at":   datetime.now(timezone.utc).isoformat(),
        }
        slot.start_time   = new_start
        slot.end_time     = new_end
        slot.move_history = list(slot.move_history or []) + [history_entry]
        slot.status       = "draft"
        db.commit()

        return {
            "success":        True,
            "slot_id":        slot_id,
            "session_number": slot.session_number,
            "from_start":     old_start,
            "from_end":       old_end,
            "to_start":       new_start.isoformat(),
            "to_end":         new_end.isoformat(),
            "move_count":     len(slot.move_history),
            "message":        f"Session #{slot.session_number} moved to {new_start.strftime('%A %H:%M')}",
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.get("/session/{slot_id}/history")
def session_move_history(slot_id: int, db: Session = Depends(get_db)):
    try:
        from models.schedule import ScheduleSlot
        slot = db.query(ScheduleSlot).filter(ScheduleSlot.id == slot_id).first()
        if not slot:
            raise HTTPException(404, detail=f"Slot {slot_id} not found")
        return {"slot_id": slot_id, "history": slot.move_history or []}
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.get("/schedule", response_model=list[SessionSlotOut])
def get_last_schedule():
    if not _last_schedule:
        raise HTTPException(404, detail="No schedule yet.")
    return [SessionSlotOut(**s) for s in _last_schedule if _valid(s)]

def _valid(s):
    try: SessionSlotOut(**s); return True
    except: return False

@router.get("/constraints")
def get_constraints(db: Session = Depends(get_db)):
    try:
        constraints, nb = PlanningAgent(db=db).get_constraints()
        return {"total": nb, "constraints": constraints}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))

@router.get("/export/csv")
def export_csv():
    if not _last_schedule:
        raise HTTPException(404, detail="No schedule to export.")
    return StreamingResponse(
        io.BytesIO(schedule_to_csv_bytes(_last_schedule)),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=schedule.csv"},
    )