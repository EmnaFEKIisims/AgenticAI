"""
models/notification.py
=======================
Anomaly → Notification
An anomaly is a detected problem.
A notification is the message sent to the admin about it.
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
    admin_id     = Column(Integer, nullable=True, comment="Target admin (null = broadcast)")

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
        return f"<Notification id={self.id} type={self.notif_type} status={self.status}>"