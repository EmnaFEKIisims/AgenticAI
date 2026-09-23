"""
repositories/notification_repository.py  (Services/Notification/notification_repository.py)
=========================================
DB operations for Notification model.

← CHANGED: every `admin_id: int | None` parameter is replaced with
  `user_id: str | None`, matching the new FK on models.notification.
  This is the ONLY place that reads/writes notification state now --
  Services/AnomalyAgent/notification_service.py no longer duplicates
  mark_as_read / mark_all_read / get_unread (see that file's docstring).

  Added delete_by_user() -- wipes a user's old notifications right
  before their new planning version's notifications are created.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from models.notification import Notification, NotificationStatus


class NotificationRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self, user_id: str | None = None, limit: int = 100) -> list[Notification]:
        q = self.db.query(Notification)
        if user_id:
            q = q.filter(Notification.user_id == user_id)
        return q.order_by(Notification.created_at.desc()).limit(limit).all()

    def get_unread(self, user_id: str | None = None) -> list[Notification]:
        q = self.db.query(Notification).filter(Notification.is_read == False)
        if user_id:
            q = q.filter(Notification.user_id == user_id)
        return q.order_by(Notification.created_at.desc()).all()

    def get_by_id(self, notification_id: int) -> Notification | None:
        return self.db.query(Notification).filter(Notification.id == notification_id).first()

    def mark_read(self, notification_id: int) -> Notification | None:
        notif = self.get_by_id(notification_id)
        if not notif:
            return None
        notif.is_read = True
        notif.status  = NotificationStatus.READ
        notif.read_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(notif)
        return notif

    def mark_all_read(self, user_id: str | None = None) -> int:
        q = self.db.query(Notification).filter(Notification.is_read == False)
        if user_id:
            q = q.filter(Notification.user_id == user_id)
        count = q.count()
        q.update({
            "is_read": True,
            "status":  NotificationStatus.READ,
            "read_at": datetime.now(timezone.utc),
        })
        self.db.commit()
        return count

    def delete(self, notification_id: int) -> bool:
        notif = self.get_by_id(notification_id)
        if not notif:
            return False
        self.db.delete(notif)
        self.db.commit()
        return True

    def delete_by_user(self, user_id: str) -> int:
        """
        Deletes EVERY notification currently owned by this user.

        Called right before AnomalyAgent creates notifications for a
        freshly (re)generated planning, so the notification bell only
        ever shows the CURRENT planning version's alerts -- never a
        stale set left over from a previous generation, regeneration,
        or drag-and-drop modification.
        """
        n = self.db.query(Notification).filter(Notification.user_id == user_id).delete()
        self.db.commit()
        return n

    def count_unread(self, user_id: str | None = None) -> int:
        q = self.db.query(Notification).filter(Notification.is_read == False)
        if user_id:
            q = q.filter(Notification.user_id == user_id)
        return q.count()

    def summary(self, user_id: str | None = None) -> dict:
        all_notifs = self.get_all(user_id=user_id, limit=10_000)
        return {
            "total":   len(all_notifs),
            "unread":  sum(1 for n in all_notifs if not n.is_read),
            "error":   sum(1 for n in all_notifs if n.notif_type.value == "error"),
            "warning": sum(1 for n in all_notifs if n.notif_type.value == "warning"),
            "info":    sum(1 for n in all_notifs if n.notif_type.value == "info"),
        }