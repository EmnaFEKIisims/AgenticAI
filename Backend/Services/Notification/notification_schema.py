"""
schemas/notification.py
========================
Pydantic schemas for the Notification system.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationResponse(BaseModel):
    id:          int
    anomaly_id:  Optional[int]
    admin_id:    Optional[int]
    notif_type:  str          # "error" | "warning" | "info"
    status:      str          # "unread" | "read"
    title:       str
    message:     str
    action_url:  Optional[str]
    is_read:     bool
    read_at:     Optional[datetime]
    created_at:  Optional[datetime]

    class Config:
        from_attributes = True


class NotificationSummary(BaseModel):
    total:    int
    unread:   int
    error:    int
    warning:  int
    info:     int