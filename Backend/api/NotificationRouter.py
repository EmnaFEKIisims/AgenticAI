"""
api/NotificationRouter.py
==========================
Notification endpoints — every route is now scoped to the connected user via
Depends(get_current_user_id), reading the X-User-ID header. No more
Optional[int] admin_id query params that the frontend never filled in.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import get_db, get_current_user_id
from Services.Notification.notification_repository import NotificationRepository
from Services.Notification.notification_schema import (
    NotificationResponse,
    NotificationSummary,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=list[NotificationResponse])
def get_all_notifications(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return NotificationRepository(db).get_all(user_id=user_id)


@router.get("/unread", response_model=list[NotificationResponse])
def get_unread_notifications(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return NotificationRepository(db).get_unread(user_id=user_id)


@router.get("/summary", response_model=NotificationSummary)
def get_notification_summary(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return NotificationRepository(db).summary(user_id=user_id)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = NotificationRepository(db)
    notif = repo.mark_as_read(notification_id, user_id=user_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif


@router.patch("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    count = NotificationRepository(db).mark_all_read(user_id=user_id)
    return {"success": True, "marked_read": count}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = NotificationRepository(db)
    deleted = repo.delete(notification_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}