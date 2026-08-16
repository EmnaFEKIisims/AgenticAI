"""
Services/AnomalyAgent/notification_service.py
===============================================
Transforms detected anomalies into Notification rows in DB.

Flow:
  AnomalyAgent detects anomalies
        ↓
  notify_many(anomalies, db)
        ↓
  Notification rows saved
        ↓
  GET /notifications → frontend shows alerts
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from models.notification import Notification, NotificationType, NotificationStatus

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
    sev  = anomaly.get("severity", "medium")
    icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(sev, "⚠️")
    return f"{icon} {anomaly.get('title', 'Anomaly detected')}"


def _build_message(anomaly: dict) -> str:
    parts = [anomaly.get("description", "An anomaly was detected.")]
    d = anomaly.get("details") or {}
    if d.get("day"):          parts.append(f"Day: {d['day']}.")
    if d.get("trainer_name"): parts.append(f"Trainer: {d['trainer_name']}.")
    if d.get("group_name"):   parts.append(f"Group: {d['group_name']}.")
    if anomaly.get("recommendation"):
        parts.append(f"→ {anomaly['recommendation']}")
    return " ".join(parts)


def notify_anomaly(
    anomaly:    dict,
    db:         Session,
    admin_id:   int | None = None,
    anomaly_id: int | None = None,
) -> Notification:
    """Creates one Notification from one anomaly dict."""
    severity   = anomaly.get("severity", "medium")
    notif_type = SEVERITY_TO_TYPE.get(severity, NotificationType.WARNING)
    url        = ACTION_URLS.get(anomaly.get("anomaly_type", "other"), "/planning")
    if anomaly.get("planning_id"):
        url = f"{url}?planning_id={anomaly['planning_id']}"

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
    return notif


def notify_many(
    anomalies:   list[dict],
    db:          Session,
    admin_id:    int | None = None,
    anomaly_ids: list[int]  = None,
) -> list[Notification]:
    """Creates notifications for HIGH + MEDIUM anomalies. Skips LOW."""
    ids    = anomaly_ids or [None] * len(anomalies)
    result = []
    for anomaly, aid in zip(anomalies, ids):
        if anomaly.get("severity") == "low":
            continue   # too noisy
        result.append(notify_anomaly(anomaly, db, admin_id=admin_id, anomaly_id=aid))
    print(f"  [NotifService] {len(result)} notification(s) created.")
    return result