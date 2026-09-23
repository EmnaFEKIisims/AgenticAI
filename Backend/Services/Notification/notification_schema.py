"""
Services/Notification/notification_schema.py
================================================
Pydantic schemas for the Notification system.

← CHANGED: `admin_id: Optional[int]` -> `user_id: Optional[str]` (matches
  the real FK now on models.notification.Notification -- users.id is a
  String(36)). Added `planning_group_id`. Added NotificationCreate,
  which didn't exist here before (the service built the model directly);
  having it here makes the contract explicit and reusable.

  NOTE: there was a second, near-duplicate schema file
  (Services/AnomalyAgent/Schemas/notification.py) with an Integer
  admin_id and its own Create/Update/Response. It was never actually
  used by api/NotificationRouter.py (which imports from
  Services.Notification.notification_schema, i.e. THIS file) -- it's
  dead code. Delete it to avoid the two definitions drifting apart.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationCreate(BaseModel):
    anomaly_id:         Optional[int] = None
    user_id:            Optional[str] = None
    planning_group_id:  Optional[str] = None
    notif_type:         str = "warning"   # "error" | "warning" | "info" | "success"
    title:              str
    message:            str
    action_url:         Optional[str] = None


class NotificationUpdate(BaseModel):
    status:   Optional[str]      = None
    is_read:  Optional[bool]     = None
    read_at:  Optional[datetime] = None


class NotificationResponse(BaseModel):
    id:                 int
    anomaly_id:         Optional[int]
    user_id:            Optional[str]        # ← CHANGED from admin_id
    planning_group_id:  Optional[str]        # ← ADDED
    notif_type:         str          # "error" | "warning" | "info"
    status:             str          # "unread" | "read"
    title:              str
    message:            str
    action_url:         Optional[str]
    is_read:             bool
    read_at:              Optional[datetime]
    created_at:            Optional[datetime]

    class Config:
        from_attributes = True


class NotificationSummary(BaseModel):
    total:    int
    unread:   int
    error:    int
    warning:  int
    info:     int