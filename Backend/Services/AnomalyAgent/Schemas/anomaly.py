"""
schemas/anomaly.py  (Services/AnomalyAgent/Schemas/anomaly.py)
===================
Pydantic schemas for the Anomaly model.
Used by the API router and the Anomaly Agent.

FIX vs the version that caused the 7 "Cannot find reference" errors:
AnalyzeRequest / AnalyzeResponse / StatusUpdate / ImpactRequest /
ImpactResponse / SuggestionsResponse / Resolution did not exist anywhere in
your actual schemas file (it only had AnomalyCreate / AnomalyUpdate /
AnomalyResponse) — I had assumed they already lived here and imported them
in AnomalyRouter.py without ever defining them. They're added below, in
the same file, so the router's import line is now correct.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from models.anomaly import AnomalyType, AnomalySeverity, AnomalyStatus


# =============================================================================
#  CORE CRUD SCHEMAS (unchanged from your file — kept as-is)
# =============================================================================

class AnomalyCreate(BaseModel):
    user_id:           Optional[str]   = None   # owner of the planning
    planning_group_id: Optional[str]   = None   # planning version UUID
    planning_id:       Optional[int]   = None
    schedule_slot_id:  Optional[int]   = None
    anomaly_type:      AnomalyType     = AnomalyType.OTHER
    severity:          AnomalySeverity = AnomalySeverity.MEDIUM
    title:             str
    description:       Optional[str]   = None
    details:           Optional[dict]  = None
    impact:            Optional[str]   = None
    recommendation:    Optional[str]   = None
    iso_reference:     Optional[str]   = None


class AnomalyUpdate(BaseModel):
    status:      Optional[AnomalyStatus] = None
    resolved_at: Optional[datetime]      = None
    description: Optional[str]           = None


class AnomalyResponse(BaseModel):
    id:                int
    user_id:           Optional[str]
    planning_group_id: Optional[str]
    planning_id:       Optional[int]
    schedule_slot_id:  Optional[int]
    anomaly_type:      str
    severity:          str
    status:            str
    title:             str
    description:       Optional[str]
    details:           Optional[dict]
    impact:            Optional[str]
    recommendation:    Optional[str]
    iso_reference:     Optional[str]
    detected_at:       datetime
    resolved_at:       Optional[datetime]

    class Config:
        from_attributes = True


# =============================================================================
#  ANALYZE  (POST /anomalies/analyze/{planning_id})  — ADDED
# =============================================================================

class AnalyzeRequest(BaseModel):
    schedule:          list[dict[str, Any]]
    groups:             Optional[list[dict[str, Any]]] = None
    rooms:               Optional[list[dict[str, Any]]] = None
    equipment_data:       Optional[list[dict[str, Any]]] = None
    forbidden_days:        Optional[list[str]]           = None
    planning_group_id:      Optional[str]                = None


class AnalyzeResponse(BaseModel):
    success:          bool
    total_detected:   int
    high_count:       int
    medium_count:     int
    low_count:        int
    has_critical:     bool
    summary:          str
    anomalies:        list[dict[str, Any]]
    notification_ids: list[int]


# =============================================================================
#  STATUS UPDATE  (PATCH /anomalies/{id}/status)  — ADDED
# =============================================================================

class StatusUpdate(BaseModel):
    status: AnomalyStatus


# =============================================================================
#  SUGGESTIONS  (POST /anomalies/{id}/suggestions)  — ADDED
# =============================================================================

class SuggestionsRequest(BaseModel):
    schedule: Optional[list[dict[str, Any]]] = None


class Resolution(BaseModel):
    action:           str
    description:      str
    priority:         int
    details:          dict[str, Any]
    estimated_impact: str
    requires_hitl:    bool


class SuggestionsResponse(BaseModel):
    anomaly_id: int
    proposals:  list[Resolution]


# =============================================================================
#  IMPACT ANALYSIS  (POST /anomalies/impact-analysis)  — ADDED
# =============================================================================

class ImpactRequest(BaseModel):
    old_schedule:  list[dict[str, Any]]
    modified_slot: dict[str, Any]
    new_time:      dict[str, str]     # {"start_time": ..., "end_time": ...}
    planning_id:   Optional[int] = None
    groups:        Optional[list[dict[str, Any]]] = None
    rooms:         Optional[list[dict[str, Any]]]  = None


class ImpactResponse(BaseModel):
    modified_session:   dict[str, Any]
    old_time:           dict[str, str]
    new_time:           dict[str, str]
    affected_slots:     list[dict[str, Any]]
    new_conflicts:      list[dict[str, Any]]
    resolved_conflicts: list[dict[str, Any]]
    summary:            str