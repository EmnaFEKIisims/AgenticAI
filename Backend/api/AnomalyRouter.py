"""
api/AnomalyRouter.py
=====================
Anomaly detection & HITL endpoints.

KEY CHANGE vs previous version:
- user_id is NO LONGER read from the request body (AnalyzeRequest.user_id / admin_id).
  It now comes exclusively from the X-User-ID header via Depends(get_current_user_id),
  the same header src/services/api.ts already sends on every call.
- This guarantees the analysis, the anomalies created, and the notifications created
  are ALWAYS scoped to the real connected user — never a value the frontend could
  forget to fill in.
- Duplicate route definitions (the whole file pasted twice in an earlier version,
  which caused notify_many() to fire twice) have been removed — each route is
  defined exactly once.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import get_db, get_current_user_id
from agents.Anomaly import AnomalyAgent
from Services.AnomalyAgent.Repositories.anomaly_repository import AnomalyRepository
from Services.AnomalyAgent.Schemas.anomaly import (
    AnalyzeRequest,
    AnalyzeResponse,
    AnomalyResponse,
    StatusUpdate,
    ImpactRequest,
    ImpactResponse,
    SuggestionsRequest,
    SuggestionsResponse,
)

router = APIRouter(prefix="/anomalies", tags=["Anomaly Agent"])


# =============================================================================
#  ANALYZE — runs detection, wipes old notifications for this user, creates new ones
# =============================================================================

@router.post("/analyze/{planning_id}", response_model=AnalyzeResponse)
def analyze_planning(
    planning_id: int,
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    agent = AnomalyAgent(db)
    result = agent.analyze(
        planning_id=planning_id,
        schedule=payload.schedule,
        groups=payload.groups or [],
        rooms=payload.rooms or [],
        equipment_data=payload.equipment_data or [],
        forbidden_days=payload.forbidden_days or [],
        user_id=user_id,
        planning_group_id=payload.planning_group_id,
    )
    return result


# =============================================================================
#  READ
# =============================================================================

@router.get("/", response_model=list[AnomalyResponse])
def list_anomalies(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Returns only the anomalies belonging to the connected user."""
    return AnomalyRepository(db).get_by_user(user_id)


@router.get("/planning/{planning_id}", response_model=list[AnomalyResponse])
def list_anomalies_for_planning(
    planning_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return AnomalyRepository(db).get_by_planning(planning_id)


@router.get("/{anomaly_id}", response_model=AnomalyResponse)
def get_anomaly(
    anomaly_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    anomaly = AnomalyRepository(db).get(anomaly_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return anomaly


# =============================================================================
#  HITL — acknowledge / resolve / ignore
# =============================================================================

@router.patch("/{anomaly_id}/status", response_model=AnomalyResponse)
def update_anomaly_status(
    anomaly_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = AnomalyRepository(db)
    anomaly = repo.get(anomaly_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return repo.update_status(anomaly_id, payload.status)


# =============================================================================
#  SUGGESTIONS
# =============================================================================

@router.post("/{anomaly_id}/suggestions", response_model=SuggestionsResponse)
def get_suggestions(
    anomaly_id: int,
    payload: SuggestionsRequest = SuggestionsRequest(),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    agent = AnomalyAgent(db)
    # NOTE: not sure of suggest_resolutions()'s exact signature in your
    # agents/Anomaly.py — if it accepts a schedule, pass payload.schedule here.
    proposals = agent.suggest_resolutions(anomaly_id)
    return SuggestionsResponse(anomaly_id=anomaly_id, proposals=proposals)


# =============================================================================
#  IMPACT ANALYSIS — "what breaks if I move this session?"
# =============================================================================

@router.post("/impact-analysis", response_model=ImpactResponse)
def impact_analysis(
    payload: ImpactRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    agent = AnomalyAgent(db)
    return agent.analyze_impact(
        old_schedule=payload.old_schedule,
        modified_slot=payload.modified_slot,
        new_time=payload.new_time,
        planning_id=payload.planning_id,
        groups=payload.groups or [],
        rooms=payload.rooms or [],
    )