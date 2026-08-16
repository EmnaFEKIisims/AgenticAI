"""
api/NotificationRouter.py
==========================
Endpoints:
  GET    /notifications              → all notifications
  GET    /notifications/unread       → unread only
  GET    /notifications/summary      → counts by type
  PATCH  /notifications/{id}/read    → mark one as read
  PATCH  /notifications/read-all     → mark all as read
  DELETE /notifications/{id}         → delete one
"""

import traceback
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.DB import SessionLocal
from Services.Notification.notification_repository import NotificationRepository
from Services.Notification.notification_schema import NotificationResponse, NotificationSummary

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================================================================
#  GET /notifications
# =============================================================================

@router.get("", response_model=list[NotificationResponse])
def get_all(
    admin_id: Optional[int] = None,
    limit:    int            = 50,
    db:       Session        = Depends(get_db),
):
    """Returns all notifications, newest first."""
    try:
        return NotificationRepository(db).get_all(admin_id=admin_id, limit=limit)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


# =============================================================================
#  GET /notifications/unread
# =============================================================================

@router.get("/unread", response_model=list[NotificationResponse])
def get_unread(admin_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Returns only unread notifications."""
    try:
        return NotificationRepository(db).get_unread(admin_id=admin_id)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


# =============================================================================
#  GET /notifications/summary
# =============================================================================

@router.get("/summary", response_model=NotificationSummary)
def get_summary(admin_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Returns counts: total, unread, error, warning, info."""
    try:
        return NotificationRepository(db).summary(admin_id=admin_id)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


# =============================================================================
#  PATCH /notifications/{id}/read
# =============================================================================

@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(notification_id: int, db: Session = Depends(get_db)):
    """Mark one notification as read."""
    try:
        notif = NotificationRepository(db).mark_read(notification_id)
        if not notif:
            raise HTTPException(404, detail=f"Notification {notification_id} not found.")
        return notif
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


# =============================================================================
#  PATCH /notifications/read-all
# =============================================================================

@router.patch("/read-all")
def mark_all_read(admin_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Mark all unread notifications as read."""
    try:
        count = NotificationRepository(db).mark_all_read(admin_id=admin_id)
        return {"success": True, "marked_read": count}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


# =============================================================================
#  DELETE /notifications/{id}
# =============================================================================

@router.delete("/{notification_id}")
def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    """Delete a notification."""
    try:
        ok = NotificationRepository(db).delete(notification_id)
        if not ok:
            raise HTTPException(404, detail=f"Notification {notification_id} not found.")
        return {"success": True, "deleted_id": notification_id}
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))