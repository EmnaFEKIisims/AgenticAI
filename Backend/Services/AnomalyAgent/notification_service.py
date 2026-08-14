"""
Services/AnomalyAgent/notification_service.py
===============================================
Anomaly → Notification

Functions:
  notify_anomaly()   → one anomaly → one notification in DB
  notify_many()      → batch (skips LOW severity)
  mark_as_read()     → admin reads a notification
  mark_all_read()    → mark all as read
  get_unread()       → all unread notifications
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from models.notification import Notification, NotificationType, NotificationStatus


# =============================================================================
#  SEVERITY → NOTIFICATION TYPE
# =============================================================================

SEVERITY_TO_TYPE = {
    "high":   NotificationType.ERROR,
    "medium": NotificationType.WARNING,
    "low":    NotificationType.INFO,
}

ACTION_URLS = {
    "trainer_conflict":           "/planning",
    "room_conflict":              "/planning",
    "learner_conflict":           "/planning",
    "equipment_conflict":         "/planning",
    "teacher_overload":           "/planning",
    "workload_exceeded":          "/pedagogical-audit",
    "wrong_progression":          "/pedagogical-audit",
    "practice_before_theory":     "/pedagogical-audit",
    "room_capacity_insufficient": "/planning",
    "other":                      "/planning",
}


# =============================================================================
#  MESSAGE BUILDERS
# =============================================================================

def _build_title(anomaly: dict) -> str:
    icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
        anomaly.get("severity", "medium"), "⚠️"
    )
    return f"{icon} {anomaly.get('title', 'Anomaly detected')}"


def _build_message(anomaly: dict) -> str:
    parts = [anomaly.get("description", "An anomaly was detected in the planning.")]
    d = anomaly.get("details") or {}
    if d.get("day"):          parts.append(f"Day: {d['day']}.")
    if d.get("hours"):        parts.append(f"Hours: {d['hours']}h.")
    if d.get("trainer_name"): parts.append(f"Trainer: {d['trainer_name']}.")
    if d.get("group_name"):   parts.append(f"Group: {d['group_name']}.")
    if anomaly.get("recommendation"):
        parts.append(f"Suggestion: {anomaly['recommendation']}")
    return " ".join(parts)


# =============================================================================
#  NOTIFY SINGLE ANOMALY
# =============================================================================

def notify_anomaly(
    anomaly:    dict,
    db:         Session,
    admin_id:   int | None = None,
    anomaly_id: int | None = None,
) -> Notification:
    """Creates one Notification in DB from one anomaly dict."""
    severity   = anomaly.get("severity", "medium")
    notif_type = SEVERITY_TO_TYPE.get(severity, NotificationType.WARNING)
    url        = ACTION_URLS.get(anomaly.get("anomaly_type", "other"), "/planning")
    pid        = anomaly.get("planning_id")
    if pid:
        url = f"{url}?planning_id={pid}"

    notif = Notification(
        anomaly_id = anomaly_id,
        admin_id   = admin_id,
        notif_type = notif_type,
        status     = NotificationStatus.UNREAD,
        title      = _build_title(anomaly),
        message    = _build_message(anomaly),
        action_url = url,
        is_read    = False,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    print(f"  [NotifService] [{notif_type.value.upper()}] {notif.title[:70]}")
    return notif


# =============================================================================
#  BATCH
# =============================================================================

def notify_many(
    anomalies:   list[dict],
    db:          Session,
    admin_id:    int | None = None,
    anomaly_ids: list[int]  = None,
) -> list[Notification]:
    """Creates notifications for HIGH + MEDIUM anomalies only."""
    ids    = anomaly_ids or [None] * len(anomalies)
    result = []
    for anomaly, aid in zip(anomalies, ids):
        if anomaly.get("severity") == "low":
            continue
        result.append(notify_anomaly(anomaly, db, admin_id=admin_id, anomaly_id=aid))
    print(f"  [NotifService] {len(result)} notification(s) created.")
    return result


# =============================================================================
#  READ / UNREAD
# =============================================================================

def mark_as_read(notification_id: int, db: Session) -> Notification | None:
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        return None
    notif.is_read = True
    notif.status  = NotificationStatus.READ
    notif.read_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(notif)
    return notif


def mark_all_read(db: Session, admin_id: int | None = None) -> int:
    q = db.query(Notification).filter(Notification.is_read == False)
    if admin_id:
        q = q.filter(Notification.admin_id == admin_id)
    count = q.count()
    q.update({"is_read": True, "status": NotificationStatus.READ,
               "read_at": datetime.now(timezone.utc)})
    db.commit()
    return count


def get_unread(db: Session, admin_id: int | None = None) -> list[Notification]:
    q = db.query(Notification).filter(Notification.is_read == False)
    if admin_id:
        q = q.filter(Notification.admin_id == admin_id)
    return q.order_by(Notification.created_at.desc()).all()