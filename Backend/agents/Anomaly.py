"""
agents/Anomaly.py
================================
Main Anomaly Agent — orchestrates the full pipeline.

← CHANGED (real per-user notifications, milestone fix):
  - analyze() now takes `user_id: str` (the session user who owns this
    planning) and an optional `planning_group_id: str` (the planning
    VERSION being analyzed).
  - Step 0 (NEW): before anything else, wipes this user's previous
    anomalies AND notifications. This is what makes the requirement
    hold: "0 notifications on connect, N notifications after a
    generation, N automatically replaced by N' after a regeneration /
    modification / new generation" -- every analyze() run for a user
    starts by clearing that user's old state, so stale anomalies from a
    previous planning version can never linger.
  - Every AnomalyCreate and every notify_many() call is now stamped
    with user_id + planning_group_id, so anomalies/notifications are a
    real, queryable per-user relation instead of a global unscoped
    table.

Flow:
  analyze(user_id, planning_id, planning_group_id, schedule)
        │
        ▼
    [Clear]            wipe this user's previous anomalies + notifications   ← NEW
        │
        ▼
    [Detector]         detect_all() → raw anomaly dicts
        │
        ▼
    [Classifier]       classify_all() → typed + severity + ISO ref
        │
        ▼
    [DB Save]          AnomalyRepository.create_many()  (stamped with user_id)
        │
        ▼
    [Resolver]         resolve_all() → list of Resolution per anomaly
        │
        ▼
    [Notification]     notify_many() → Notification rows in DB (stamped with user_id)
        │
        ▼
    AnomalyAgentResult (anomalies + resolutions + notifications)
"""

from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from Services.AnomalyAgent.detector             import detect_all
from Services.AnomalyAgent.classifier           import classify_all
from Services.AnomalyAgent.resolver             import resolve_all, Resolution
from Services.AnomalyAgent.notification_service import notify_many, clear_previous_notifications
from Services.AnomalyAgent.Repositories.anomaly_repository import AnomalyRepository
from Services.AnomalyAgent.Schemas.anomaly                 import AnomalyCreate
from models.anomaly                              import AnomalyType, AnomalySeverity


# =============================================================================
#  RESULT
# =============================================================================

@dataclass
class AnomalyAgentResult:
    success:           bool
    total_detected:    int
    high_count:        int
    medium_count:      int
    low_count:         int
    anomalies:         list[dict]                  # classified anomaly dicts
    resolutions:       dict[int, list[Resolution]]  # index → proposals
    notification_ids:  list[int]                    # IDs of created notifications
    error:             str = ""

    @property
    def has_critical(self) -> bool:
        return self.high_count > 0

    @property
    def summary(self) -> str:
        return (
            f"{self.total_detected} anomaly(ies) detected — "
            f"HIGH={self.high_count} MEDIUM={self.medium_count} LOW={self.low_count}. "
            f"{len(self.notification_ids)} notification(s) created."
        )


# =============================================================================
#  ANOMALY AGENT
# =============================================================================

class AnomalyAgent:
    """
    Orchestrates: Clear-old → Detector → Classifier → DB → Resolver → Notifications.

    Usage (from AnomalyRouter or Orchestrator):
        agent  = AnomalyAgent(db=db)
        result = agent.analyze(
            schedule          = planning_result.schedule,
            user_id           = current_user_id,        # REQUIRED — session user
            planning_id       = 1,
            planning_group_id = "uuid-of-this-version",  # optional but recommended
            groups            = groups_data,
            rooms             = rooms_data,
        )
        print(result.summary)
        print(result.resolutions[0])   # proposals for first anomaly
    """

    def __init__(self, db: Session):
        self.db   = db
        self.repo = AnomalyRepository(db)

    def analyze(
        self,
        schedule:          list[dict],
        user_id:            str,
        planning_id:        int         = None,
        planning_group_id:  str         = None,
        groups:             list[dict]  = None,
        rooms:               list[dict]  = None,
        equipment_data:       list[dict]  = None,
        forbidden_days:        list[str]   = None,
    ) -> AnomalyAgentResult:
        """
        Full anomaly detection pipeline, scoped to ONE user's planning.

        Args:
            schedule:           sessions from PlanningAgent.run().schedule
            user_id:             REQUIRED — the session user who owns this planning.
                                  Every anomaly/notification created is stamped with
                                  this id, and this user's PREVIOUS anomalies/
                                  notifications are wiped before the new ones are
                                  saved (see Step 0 below).
            planning_id:         DB planning id (legacy field, kept for compatibility)
            planning_group_id:   UUID of the planning VERSION being analyzed
                                  (ScheduleSlot.planning_group_id)
            groups:               group data for capacity checks
            rooms:                 room data for capacity checks
            equipment_data:         equipment data for conflict checks
            forbidden_days:          days where no session is allowed
        """
        print(f"\n{'='*60}")
        print(f"  ANOMALY AGENT")
        print(f"  User     : {user_id}")
        print(f"  Sessions : {len(schedule)}")
        print(f"{'='*60}")

        # ── Step 0: Clear this user's PREVIOUS anomalies + notifications ──────
        # This is the core of the "new version replaces old" requirement:
        # every analyze() call (fresh generation, regeneration, or a HITL
        # modification that re-triggers analysis) starts from a clean slate
        # for this user, so old alerts never linger next to new ones.
        print("\n[0/4] Clearing previous anomalies/notifications for this user...")
        if user_id:
            cleared_anomalies = self.repo.delete_by_user(user_id)
            clear_previous_notifications(self.db, user_id)
            print(f"  → {cleared_anomalies} old anomaly(ies) cleared.")
        else:
            print("  ⚠️  No user_id provided — skipping per-user cleanup "
                  "(anomalies will NOT be scoped to a user).")

        # ── Step 1: Detect ────────────────────────────────────────────────────
        print("\n[1/4] Running detector...")
        raw_anomalies = detect_all(
            schedule       = schedule,
            planning_id    = planning_id,
            groups         = groups,
            rooms          = rooms,
            equipment_data = equipment_data,
            forbidden_days = forbidden_days,
        )

        if not raw_anomalies:
            print("  ✅ No anomalies detected.")
            return AnomalyAgentResult(
                success=True, total_detected=0,
                high_count=0, medium_count=0, low_count=0,
                anomalies=[], resolutions={}, notification_ids=[]
            )

        # ── Step 2: Classify ──────────────────────────────────────────────────
        print("\n[2/4] Classifying anomalies...")
        classified = classify_all(raw_anomalies)

        high   = sum(1 for a in classified if a.get("severity") == "high")
        medium = sum(1 for a in classified if a.get("severity") == "medium")
        low    = sum(1 for a in classified if a.get("severity") == "low")

        # ── Step 3: Save to DB + Resolve ─────────────────────────────────────
        print("\n[3/4] Saving anomalies + generating resolutions...")
        saved_ids = []
        for anomaly in classified:
            try:
                create_data = AnomalyCreate(
                    user_id            = user_id,
                    planning_group_id  = planning_group_id,
                    planning_id        = anomaly.get("planning_id"),
                    anomaly_type       = anomaly.get("anomaly_type", AnomalyType.OTHER),
                    severity           = anomaly.get("severity",     AnomalySeverity.MEDIUM),
                    title              = anomaly.get("title", "Anomaly"),
                    description        = anomaly.get("description"),
                    details            = anomaly.get("details"),
                    impact             = anomaly.get("impact"),
                    recommendation     = anomaly.get("recommendation"),
                    iso_reference      = anomaly.get("iso_reference"),
                )
                saved = self.repo.create(create_data)
                saved_ids.append(saved.id)
            except Exception as e:
                print(f"  ⚠️  Could not save anomaly to DB: {e}")
                saved_ids.append(None)

        resolutions = resolve_all(classified, schedule)

        # ── Step 4: Notify ────────────────────────────────────────────────────
        print("\n[4/4] Creating notifications...")
        notifications = notify_many(
            anomalies         = classified,
            db                = self.db,
            user_id           = user_id,
            planning_group_id = planning_group_id,
            anomaly_ids       = [i for i in saved_ids if i is not None],
        )
        notif_ids = [n.id for n in notifications]

        result = AnomalyAgentResult(
            success          = True,
            total_detected   = len(classified),
            high_count       = high,
            medium_count     = medium,
            low_count        = low,
            anomalies        = classified,
            resolutions      = resolutions,
            notification_ids = notif_ids,
        )

        print(f"\n  ✅ {result.summary}")
        return result

    def get_open_anomalies(self) -> list:
        """Returns all OPEN anomalies from DB (all users)."""
        return self.repo.get_open()

    def get_anomalies_for_user(self, user_id: str) -> list:
        """Returns all anomalies belonging to this user's current planning."""
        return self.repo.get_by_user(user_id)

    def resolve_anomaly(self, anomaly_id: int, status: str):
        """Updates anomaly status — called after admin takes action."""
        from models.anomaly import AnomalyStatus
        status_map = {
            "resolved":     AnomalyStatus.RESOLVED,
            "acknowledged": AnomalyStatus.ACKNOWLEDGED,
            "ignored":      AnomalyStatus.IGNORED,
        }
        return self.repo.update_status(
            anomaly_id,
            status_map.get(status, AnomalyStatus.ACKNOWLEDGED)
        )