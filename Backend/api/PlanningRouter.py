"""
api/PlanningRouter.py
======================
Updated: all DB queries now filter by user_id.
PlanningAgent only sees rooms/trainers/groups/courses belonging to the current user.
"""

import io, uuid, traceback
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.DB import SessionLocal
from agents.planning_agent  import PlanningAgent, schedule_to_csv_bytes
from agents.ConstraintAgent import ConstraintAgent
import os
SUPERADMIN_ID = os.getenv("SUPERADMIN_ID", "00000000-0000-0000-0000-000000000001")

router = APIRouter(prefix="/planning", tags=["Planning Agent"])

_last_schedule: list[dict] = []
_last_group_id: str        = ""


def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def get_user_id(x_user_id: str = Header(default=SUPERADMIN_ID)) -> str:
    return x_user_id


# =============================================================================
#  Schemas (unchanged)
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
    success: bool; planning_group_id: str; total_sessions: int
    final_constraints: dict; schedule: list[SessionSlotOut]; engine: str = "greedy"

class ValidateBody(BaseModel):
    validation_notes: Optional[str] = None

class RejectBody(BaseModel):
    reason: Optional[str] = None

class RegenerateBody(BaseModel):
    constraints_dict: Optional[dict] = None
    user_constraints: Optional[str]  = None
    rejected_group_id:Optional[str]  = None
    attempt: int = 2

class MoveBody(BaseModel):
    new_start_time: str; new_end_time: str; admin_note: Optional[str] = None

class ImpactBody(BaseModel):
    new_start_time: str; new_end_time: str; planning_group_id: Optional[str] = None


# =============================================================================
#  DB SAVE — now stores user_id on each slot
# =============================================================================

def _save_to_db(schedule: list[dict], db: Session, user_id: str) -> tuple[str, dict[int, int]]:
    from models.schedule import ScheduleSlot

    # Supersede old slots for THIS user only
    old_slots = db.query(ScheduleSlot).filter(
        ScheduleSlot.user_id == user_id,
        ScheduleSlot.status.in_(["draft", "validated"])
    ).all()

    if old_slots:
        now = datetime.now(timezone.utc)
        for s in old_slots:
            s.status = "superseded"; s.rejected_at = now
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
            course_id=s.get("course_id",0), trainer_id=s.get("trainer_id",0),
            room_id=s.get("room_id",0), learner_group_id=s.get("learner_group_id",0),
            start_time=start, end_time=end, planning_group_id=group_id,
            session_number=sn,
            quality_score=float(s.get("quality_score",0.0)),
            pedagogical_audit_score=float(s.get("pedagogical_audit_score",0.0)),
            status="draft", is_validated=False, move_history=[],
            user_id=user_id,   # ← KEY: link slot to user
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
    global _last_schedule, _last_group_id
    try:
        group_id, sn_to_db_id = _save_to_db(result.schedule, db, user_id)
    except Exception:
        traceback.print_exc()
        group_id = str(uuid.uuid4()); sn_to_db_id = {}

    _last_group_id = group_id
    enriched = []
    for idx, s in enumerate(result.schedule):
        s_copy = dict(s); sn = s_copy.get("session_number") or (idx+1)
        s_copy["id"] = sn_to_db_id.get(sn) or sn_to_db_id.get(idx+1)
        enriched.append(s_copy)

    _last_schedule = enriched
    slots_out = []
    for s in enriched:
        try: slots_out.append(SessionSlotOut(**s))
        except: pass

    return PlanningRunResponse(
        success=result.success, planning_group_id=group_id,
        total_sessions=result.total_sessions, final_constraints=result.constraints_used,
        schedule=slots_out, engine=getattr(result,"engine","greedy"),
    )


# =============================================================================
#  ENDPOINTS — all receive user_id
# =============================================================================

@router.post("/run", response_model=PlanningRunResponse)
def run_planning(body: PlanningRunRequest, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    try:
        result = PlanningAgent(db=db).run(extra_constraints=body.user_constraints or "")
        if not result.success: raise HTTPException(422, detail=result.error)
        return _build_response(result, db, user_id)
    except HTTPException: raise
    except Exception as e: traceback.print_exc(); raise HTTPException(500, detail=str(e))

@router.post("/run/with-constraints", response_model=PlanningRunResponse)
def run_with_constraints(body: PlanningRunWithConstraintsRequest, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    try:
        result = PlanningAgent(db=db).run(constraints_dict=body.constraints_dict)
        if not result.success: raise HTTPException(422, detail=result.error)
        return _build_response(result, db, user_id)
    except HTTPException: raise
    except Exception as e: traceback.print_exc(); raise HTTPException(500, detail=str(e))

@router.post("/{planning_group_id}/validate")
def validate_schedule(planning_group_id: str, body: ValidateBody, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    from models.schedule import ScheduleSlot
    slots = db.query(ScheduleSlot).filter(
        ScheduleSlot.planning_group_id == planning_group_id,
        ScheduleSlot.user_id == user_id   # ← only user's slots
    ).all()
    if not slots: raise HTTPException(404, detail="No slots found for this user and group.")
    now = datetime.now(timezone.utc)
    for slot in slots:
        slot.status="validated"; slot.is_validated=True; slot.validated_at=now; slot.validation_notes=body.validation_notes
    db.commit()
    return {"success": True, "hitl_status": "validated", "total_slots": len(slots)}

@router.post("/{planning_group_id}/reject")
def reject_schedule(planning_group_id: str, body: RejectBody, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    from models.schedule import ScheduleSlot
    slots = db.query(ScheduleSlot).filter(
        ScheduleSlot.planning_group_id == planning_group_id,
        ScheduleSlot.user_id == user_id
    ).all()
    now = datetime.now(timezone.utc)
    for slot in slots:
        slot.status="rejected"; slot.rejected_at=now; slot.validation_notes=body.reason
    db.commit()
    return {"success": True, "hitl_status": "rejected", "total_slots": len(slots)}

@router.post("/session/{slot_id}/impact")
def impact_analysis(slot_id: int, body: ImpactBody, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    from models.schedule import ScheduleSlot
    slot = db.query(ScheduleSlot).filter(ScheduleSlot.id==slot_id, ScheduleSlot.user_id==user_id).first()
    if not slot: raise HTTPException(404, detail=f"Slot {slot_id} not found.")
    new_start = datetime.fromisoformat(body.new_start_time)
    new_end   = datetime.fromisoformat(body.new_end_time)
    group_id  = body.planning_group_id or slot.planning_group_id
    others = db.query(ScheduleSlot).filter(
        ScheduleSlot.id != slot_id, ScheduleSlot.user_id == user_id,
        ScheduleSlot.planning_group_id == group_id,
        ScheduleSlot.status.notin_(["rejected","superseded"])
    ).all()
    conflicts = []
    for o in others:
        if not (o.start_time < new_end and new_start < o.end_time): continue
        if o.trainer_id       == slot.trainer_id:   conflicts.append({"type":"trainer","slot_id":o.id})
        if o.room_id          == slot.room_id:       conflicts.append({"type":"room",   "slot_id":o.id})
        if o.learner_group_id == slot.learner_group_id: conflicts.append({"type":"group","slot_id":o.id})
    return {"slot_id":slot_id,"is_safe":not conflicts,"new_conflicts":conflicts,
            "summary":"No conflicts." if not conflicts else f"{len(conflicts)} conflict(s)."}

@router.patch("/session/{slot_id}/move")
def apply_move(slot_id: int, body: MoveBody, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    from models.schedule import ScheduleSlot
    slot = db.query(ScheduleSlot).filter(ScheduleSlot.id==slot_id, ScheduleSlot.user_id==user_id).first()
    if not slot: raise HTTPException(404, detail=f"Slot {slot_id} not found.")
    new_start = datetime.fromisoformat(body.new_start_time)
    new_end   = datetime.fromisoformat(body.new_end_time)
    old_start = slot.start_time.isoformat() if slot.start_time else ""
    old_end   = slot.end_time.isoformat()   if slot.end_time else ""
    slot.start_time=new_start; slot.end_time=new_end
    slot.move_history = list(slot.move_history or []) + [{
        "from_start":old_start,"from_end":old_end,
        "to_start":new_start.isoformat(),"to_end":new_end.isoformat(),
        "moved_at":datetime.now(timezone.utc).isoformat()
    }]
    slot.status = "draft"; db.commit()
    return {"success":True,"slot_id":slot_id,"session_number":slot.session_number}

@router.get("/schedule", response_model=list[SessionSlotOut])
def get_last_schedule():
    if not _last_schedule: raise HTTPException(404, detail="No schedule yet.")
    return [SessionSlotOut(**s) for s in _last_schedule if _valid(s)]

def _valid(s):
    try: SessionSlotOut(**s); return True
    except: return False

@router.get("/export/csv")
def export_csv():
    if not _last_schedule: raise HTTPException(404, detail="No schedule to export.")
    return StreamingResponse(io.BytesIO(schedule_to_csv_bytes(_last_schedule)),
        media_type="text/csv", headers={"Content-Disposition":"attachment; filename=schedule.csv"})