"""
schemas/notification.py
========================
Pydantic schemas for the Notification model.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models.notification import NotificationType, NotificationStatus


class NotificationCreate(BaseModel):
    anomaly_id:  Optional[int]          = None
    admin_id:    Optional[int]          = None
    notif_type:  NotificationType       = NotificationType.WARNING
    title:       str
    message:     str
    action_url:  Optional[str]          = None


class NotificationUpdate(BaseModel):
    status:   Optional[NotificationStatus] = None
    is_read:  Optional[bool]               = None
    read_at:  Optional[datetime]           = None


class NotificationResponse(BaseModel):
    id:          int
    anomaly_id:  Optional[int]
    admin_id:    Optional[int]
    notif_type:  str
    status:      str
    title:       str
    message:     str
    action_url:  Optional[str]
    is_read:     bool
    created_at:  datetime
    read_at:     Optional[datetime]

    class Config:
        from_attributes = True