"""
api/AnomalyRouter.py
=====================
FastAPI router for the Anomaly Agent.

Endpoints:
  GET   /anomalies                           → All anomalies (auto-loaded by page)  ← NEW
  POST  /anomalies/analyze/{planning_id}     → Run full anomaly detection
  GET   /anomalies/planning/{planning_id}    → All anomalies for a planning
  GET   /anomalies/{anomaly_id}              → Single anomaly
  PATCH /anomalies/{anomaly_id}/status       → Acknowledge / Resolve / Ignore
  POST  /anomalies/{anomaly_id}/suggestions  → Get resolution proposals
  POST  /anomalies/impact-analysis           → Impact of moving a session
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.DB import SessionLocal
from agents.Anomaly                                    import AnomalyAgent
from Services.AnomalyAgent.impact_analyzer             import analyze_impact
from Services.AnomalyAgent.Repositories.anomaly_repository import AnomalyRepository
from Services.AnomalyAgent.Schemas.anomaly             import AnomalyResponse, AnomalyUpdate
from models.anomaly                                    import AnomalyStatus


router = APIRouter(prefix="/anomalies", tags=["Anomaly Agent"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================================================================
#  Schemas
# =============================================================================

class AnalyzeRequest(BaseModel):
    schedule:       list[dict]
    groups:         Optional[list[dict]] = None
    rooms:          Optional[list[dict]] = None
    equipment_data: Optional[list[dict]] = None
    forbidden_days: Optional[list[str]]  = None
    admin_id:       Optional[int]        = None


class AnalyzeResponse(BaseModel):
    success:         bool
    total_detected:  int
    high_count:      int
    medium_count:    int
    low_count:       int
    has_critical:    bool
    summary:         str
    anomalies:       list[dict]
    notification_ids: list[int]


class StatusUpdate(BaseModel):
    status: str


class SuggestionsResponse(BaseModel):
    anomaly_id: int
    proposals:  list[dict]


class ImpactRequest(BaseModel):
    old_schedule:  list[dict]
    modified_slot: dict
    new_time:      dict
    planning_id:   Optional[int] = None
    groups:        Optional[list[dict]] = None
    rooms:         Optional[list[dict]] = None


class ImpactResponse(BaseModel):
    modified_session:    dict
    old_time:            dict
    new_time:            dict
    affected_slots:      list[dict]
    new_conflicts:       list[dict]
    resolved_conflicts:  list[dict]
    summary:             str


# =============================================================================
#  ENDPOINT 0 — GET /anomalies                                                 ← NEW
#  Called automatically when the Anomaly Page loads (no ID required)
# =============================================================================

@router.get(
    "",
    response_model=list[AnomalyResponse],
    summary="Get all anomalies (auto-loaded by the Anomaly Page)",
)
def get_all_anomalies(
    severity: Optional[str] = None,
    status:   Optional[str] = None,
    limit:    int            = 200,
    db:       Session        = Depends(get_db),
):
    """
    Returns all anomalies in the DB.
    Called automatically by the frontend Anomaly Page on mount.
    No planning ID required.

    Optional query params:
      ?severity=high     → filter by severity
      ?status=open       → filter by status
      ?limit=50          → max results (default 200)
    """
    anomalies = AnomalyRepository(db).list_all(limit=limit)
    if severity:
        anomalies = [a for a in anomalies if a.severity == severity]
    if status:
        anomalies = [a for a in anomalies if a.status   == status]
    return anomalies


# =============================================================================
#  ENDPOINT 1 — POST /anomalies/analyze/{planning_id}
# =============================================================================

@router.post(
    "/analyze/{planning_id}",
    response_model=AnalyzeResponse,
    summary="Run full anomaly detection on a planning",
)
def analyze_planning(
    planning_id: int,
    body:        AnalyzeRequest,
    db:          Session = Depends(get_db),
):
    try:
        agent  = AnomalyAgent(db=db)
        result = agent.analyze(
            schedule       = body.schedule,
            planning_id    = planning_id,
            groups         = body.groups,
            rooms          = body.rooms,
            equipment_data = body.equipment_data,
            forbidden_days = body.forbidden_days,
            admin_id       = body.admin_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    return AnalyzeResponse(
        success          = result.success,
        total_detected   = result.total_detected,
        high_count       = result.high_count,
        medium_count     = result.medium_count,
        low_count        = result.low_count,
        has_critical     = result.has_critical,
        summary          = result.summary,
        anomalies        = result.anomalies,
        notification_ids = result.notification_ids,
    )


# =============================================================================
#  ENDPOINT 2 — GET /anomalies/planning/{planning_id}
# =============================================================================

@router.get(
    "/planning/{planning_id}",
    response_model=list[AnomalyResponse],
    summary="Get all anomalies for a planning",
)
def get_by_planning(planning_id: int, db: Session = Depends(get_db)):
    return AnomalyRepository(db).get_by_planning(planning_id)


# =============================================================================
#  ENDPOINT 3 — GET /anomalies/{anomaly_id}
# =============================================================================

@router.get(
    "/{anomaly_id}",
    response_model=AnomalyResponse,
    summary="Get a single anomaly by ID",
)
def get_anomaly(anomaly_id: int, db: Session = Depends(get_db)):
    anomaly = AnomalyRepository(db).get(anomaly_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail=f"Anomaly {anomaly_id} not found.")
    return anomaly


# =============================================================================
#  ENDPOINT 4 — PATCH /anomalies/{anomaly_id}/status
# =============================================================================

@router.patch(
    "/{anomaly_id}/status",
    response_model=AnomalyResponse,
    summary="Update anomaly status (HITL)",
)
def update_status(anomaly_id: int, body: StatusUpdate, db: Session = Depends(get_db)):
    status_map = {
        "acknowledged": AnomalyStatus.ACKNOWLEDGED,
        "resolved":     AnomalyStatus.RESOLVED,
        "ignored":      AnomalyStatus.IGNORED,
    }
    status = status_map.get(body.status.lower())
    if not status:
        raise HTTPException(status_code=422,
                            detail=f"Invalid status. Use: acknowledged | resolved | ignored")
    updated = AnomalyRepository(db).update_status(anomaly_id, status)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Anomaly {anomaly_id} not found.")
    return updated


# =============================================================================
#  ENDPOINT 5 — POST /anomalies/{anomaly_id}/suggestions
# =============================================================================

@router.post(
    "/{anomaly_id}/suggestions",
    response_model=SuggestionsResponse,
    summary="Get resolution proposals for an anomaly",
)
def get_suggestions(anomaly_id: int, body: dict, db: Session = Depends(get_db)):
    anomaly = AnomalyRepository(db).get(anomaly_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail=f"Anomaly {anomaly_id} not found.")

    from Services.AnomalyAgent.resolver import resolve
    schedule     = body.get("schedule", [])
    anomaly_dict = {
        "anomaly_type":   anomaly.anomaly_type,
        "severity":       anomaly.severity,
        "title":          anomaly.title,
        "details":        anomaly.details or {},
        "recommendation": anomaly.recommendation,
    }
    proposals = resolve(anomaly_dict, schedule)

    return SuggestionsResponse(
        anomaly_id = anomaly_id,
        proposals  = [
            {
                "action":           p.action,
                "description":      p.description,
                "priority":         p.priority,
                "details":          p.details,
                "estimated_impact": p.estimated_impact,
                "requires_hitl":    p.requires_hitl,
            }
            for p in proposals
        ],
    )


# =============================================================================
#  ENDPOINT 6 — POST /anomalies/impact-analysis
# =============================================================================

@router.post(
    "/impact-analysis",
    response_model=ImpactResponse,
    summary="Analyze cascading impact of moving a session",
)
def impact_analysis(body: ImpactRequest):
    try:
        result = analyze_impact(
            old_schedule  = body.old_schedule,
            modified_slot = body.modified_slot,
            new_time      = body.new_time,
            planning_id   = body.planning_id,
            groups        = body.groups,
            rooms         = body.rooms,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Impact analysis failed: {str(e)}")

    return ImpactResponse(
        modified_session   = result.modified_session,
        old_time           = result.old_time,
        new_time           = result.new_time,
        affected_slots     = result.affected_slots,
        new_conflicts      = result.new_conflicts,
        resolved_conflicts = result.resolved_conflicts,
        summary            = result.summary,
    )