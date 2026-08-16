"""
repositories/notification_repository.py
=========================================
DB operations for Notification model.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from models.notification import Notification, NotificationStatus


class NotificationRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self, admin_id: int | None = None, limit: int = 100) -> list[Notification]:
        q = self.db.query(Notification)
        if admin_id:
            q = q.filter(Notification.admin_id == admin_id)
        return q.order_by(Notification.created_at.desc()).limit(limit).all()

    def get_unread(self, admin_id: int | None = None) -> list[Notification]:
        q = self.db.query(Notification).filter(Notification.is_read == False)
        if admin_id:
            q = q.filter(Notification.admin_id == admin_id)
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

    def mark_all_read(self, admin_id: int | None = None) -> int:
        q = self.db.query(Notification).filter(Notification.is_read == False)
        if admin_id:
            q = q.filter(Notification.admin_id == admin_id)
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

    def count_unread(self, admin_id: int | None = None) -> int:
        q = self.db.query(Notification).filter(Notification.is_read == False)
        if admin_id:
            q = q.filter(Notification.admin_id == admin_id)
        return q.count()

    def summary(self, admin_id: int | None = None) -> dict:
        all_notifs = self.get_all(admin_id=admin_id)
        return {
            "total":   len(all_notifs),
            "unread":  sum(1 for n in all_notifs if not n.is_read),
            "error":   sum(1 for n in all_notifs if n.notif_type.value == "error"),
            "warning": sum(1 for n in all_notifs if n.notif_type.value == "warning"),
            "info":    sum(1 for n in all_notifs if n.notif_type.value == "info"),
        }