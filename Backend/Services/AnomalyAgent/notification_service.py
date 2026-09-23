"""
Services/AnomalyAgent/notification_service.py
===============================================
Anomaly → Notification.

← CHANGED (real user relation):
  - notify_anomaly() / notify_many() now take `user_id: str` instead of
    the old unused `admin_id: int`, and stamp `planning_group_id` on
    every notification created.
  - Added clear_previous_notifications(): deletes ALL of a user's
    existing notifications. Called by agents/Anomaly.py at the START of
    every analyze() run (generation, regeneration, or a HITL
    modification that re-triggers analysis), so a user's notification
    bell always reflects ONLY their current planning version -- never a
    stale one.

← REMOVED (deduplication): this file used to also define
  mark_as_read() / mark_all_read() / get_unread(), duplicating
  Services/Notification/notification_repository.py's
  NotificationRepository. That meant two independent code paths could
  read/mutate notification state and drift apart. Now this file's ONLY
  job is turning anomalies into notifications; everything about
  reading/marking notifications goes through NotificationRepository
  (used by api/NotificationRouter.py), the single source of truth.

Flow:
  AnomalyAgent.analyze(user_id, ...)
        │
        ▼
  clear_previous_notifications(db, user_id)   ← wipe old version's alerts
        │
        ▼
  notify_many(anomalies, db, user_id, planning_group_id)
        │
        ▼
  Notification rows saved (scoped to this user)
        │
        ▼
  GET /notifications?user_id=... → frontend bell shows alerts
"""

from sqlalchemy.orm import Session

from models.notification import Notification, NotificationType, NotificationStatus
from Services.Notification.notification_repository import NotificationRepository

# ── Severity → notification type ─────────────────────────────────────────────
SEVERITY_TO_TYPE = {
    "high":   NotificationType.ERROR,
    "medium": NotificationType.WARNING,
    "low":    NotificationType.INFO,
}

# ── Anomaly type → frontend route ────────────────────────────────────────────
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
#  CLEAR OLD NOTIFICATIONS FOR THIS USER
# =============================================================================

def clear_previous_notifications(db: Session, user_id: str) -> int:
    """
    Deletes every existing notification owned by this user.

    Must be called BEFORE creating notifications for a (re)generated
    planning, so the user's notification bell only ever shows alerts
    for their CURRENT planning version. Returns the number deleted.
    """
    if not user_id:
        return 0
    deleted = NotificationRepository(db).delete_by_user(user_id)
    print(f"  [NotifService] Cleared {deleted} notification(s) from previous version for user={user_id}.")
    return deleted


# =============================================================================
#  NOTIFY SINGLE ANOMALY
# =============================================================================

def notify_anomaly(
    anomaly:            dict,
    db:                  Session,
    user_id:             str | None = None,
    planning_group_id:   str | None = None,
    anomaly_id:          int | None = None,
) -> Notification:
    """Creates one Notification in DB from one anomaly dict, scoped to user_id."""
    severity   = anomaly.get("severity", "medium")
    notif_type = SEVERITY_TO_TYPE.get(severity, NotificationType.WARNING)
    url        = ACTION_URLS.get(anomaly.get("anomaly_type", "other"), "/planning")
    pid        = anomaly.get("planning_id")
    if pid:
        url = f"{url}?planning_id={pid}"

    notif = Notification(
        anomaly_id         = anomaly_id,
        user_id            = user_id,
        planning_group_id  = planning_group_id,
        notif_type         = notif_type,
        status             = NotificationStatus.UNREAD,
        title              = _build_title(anomaly),
        message            = _build_message(anomaly),
        action_url         = url,
        is_read            = False,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    print(f"  [NotifService] [{notif_type.value.upper()}] user={user_id} {notif.title[:60]}")
    return notif


# =============================================================================
#  BATCH
# =============================================================================

def notify_many(
    anomalies:          list[dict],
    db:                 Session,
    user_id:            str | None = None,
    planning_group_id:  str | None = None,
    anomaly_ids:        list[int]  = None,
) -> list[Notification]:
    """Creates notifications for HIGH + MEDIUM anomalies only (skips LOW -- too noisy)."""
    ids    = anomaly_ids or [None] * len(anomalies)
    result = []
    for anomaly, aid in zip(anomalies, ids):
        if anomaly.get("severity") == "low":
            continue
        result.append(notify_anomaly(
            anomaly, db,
            user_id           = user_id,
            planning_group_id = planning_group_id,
            anomaly_id        = aid,
        ))
    print(f"  [NotifService] {len(result)} notification(s) created for user={user_id}.")
    return result