"""
schemas/anomaly.py
===================
Pydantic schemas for the Anomaly model.
Used by the API router and the Anomaly Agent.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models.anomaly import AnomalyType, AnomalySeverity, AnomalyStatus


class AnomalyCreate(BaseModel):
    planning_id:      Optional[int]    = None
    schedule_slot_id: Optional[int]    = None
    anomaly_type:     AnomalyType      = AnomalyType.OTHER
    severity:         AnomalySeverity  = AnomalySeverity.MEDIUM
    title:            str
    description:      Optional[str]    = None
    details:          Optional[dict]   = None
    impact:           Optional[str]    = None
    recommendation:   Optional[str]    = None
    iso_reference:    Optional[str]    = None


class AnomalyUpdate(BaseModel):
    status:       Optional[AnomalyStatus] = None
    resolved_at:  Optional[datetime]      = None
    description:  Optional[str]           = None


class AnomalyResponse(BaseModel):
    id:               int
    planning_id:      Optional[int]
    schedule_slot_id: Optional[int]
    anomaly_type:     str
    severity:         str
    status:           str
    title:            str
    description:      Optional[str]
    details:          Optional[dict]
    impact:           Optional[str]
    recommendation:   Optional[str]
    iso_reference:    Optional[str]
    detected_at:      datetime
    resolved_at:      Optional[datetime]

    class Config:
        from_attributes = True