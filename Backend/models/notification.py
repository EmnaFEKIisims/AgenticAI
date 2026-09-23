"""
models/notification.py
=======================
Anomaly → Notification
An anomaly is a detected problem.
A notification is the message sent to the user about it.

← CHANGED: `admin_id` (a bare, unlinked Integer -- never actually wired
  to a real user anywhere in the app) is replaced with `user_id`, a real
  FK to `users.id` (String(36), matching models/user.py). This is what
  makes "this notification belongs to THIS user's session" a real,
  queryable relationship instead of an unused column.

  Also added `planning_group_id` so notifications can be tied to a
  specific planning VERSION -- used to wipe out a user's old
  notifications the moment a new planning version (generation /
  regeneration / modification) produces new ones.
  See Services/AnomalyAgent/notification_service.py -> clear_previous_notifications().
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from db.DB import Base


class NotificationType(str, enum.Enum):
    WARNING  = "warning"
    ERROR    = "error"
    INFO     = "info"
    SUCCESS  = "success"


class NotificationStatus(str, enum.Enum):
    UNREAD  = "unread"
    READ    = "read"
    DISMISSED = "dismissed"


class Notification(Base):
    __tablename__ = "notifications"

    id           = Column(Integer, primary_key=True, index=True)
    anomaly_id   = Column(Integer, ForeignKey("anomalies.id"), nullable=True)

    # ← CHANGED: was `admin_id = Column(Integer, ...)`, never linked to a
    #   real table. Now a proper FK to the session user.
    user_id      = Column(String(36), ForeignKey("users.id"), nullable=True, index=True,
                          comment="Target user of the session (null = broadcast)")
    user         = relationship("User")

    # ← ADDED: which planning version this notification refers to.
    planning_group_id = Column(String(36), nullable=True, index=True,
                          comment="UUID of the planning version this notification refers to")

    notif_type   = Column(SAEnum(NotificationType, name="notif_type_enum"),
                          nullable=False, default=NotificationType.WARNING)
    status       = Column(SAEnum(NotificationStatus, name="notif_status_enum"),
                          nullable=False, default=NotificationStatus.UNREAD)

    title        = Column(String(255), nullable=False)
    message      = Column(Text,        nullable=False)
    action_url   = Column(String(500), nullable=True,
                          comment="Frontend route to navigate to on click")

    is_read      = Column(Boolean, default=False)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    read_at      = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Notification id={self.id} user={self.user_id} type={self.notif_type} status={self.status}>"