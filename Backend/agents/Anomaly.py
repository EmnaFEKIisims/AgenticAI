"""
agents/Anomaly.py
================================
Main Anomaly Agent — orchestrates the full pipeline.

Flow:
  analyze(planning_id, schedule)
        │
        ▼
    [Detector]         detect_all() → raw anomaly dicts
        │
        ▼
    [Classifier]       classify_all() → typed + severity + ISO ref
        │
        ▼
    [DB Save]          AnomalyRepository.create_many()
        │
        ▼
    [Resolver]         resolve_all() → list of Resolution per anomaly
        │
        ▼
    [Notification]     notify_many() → Notification rows in DB
        │
        ▼
    AnomalyAgentResult (anomalies + resolutions + notifications)
"""

from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from Services.AnomalyAgent.detector            import detect_all
from Services.AnomalyAgent.classifier          import classify_all
from Services.AnomalyAgent.resolver            import resolve_all, Resolution
from Services.AnomalyAgent.notification_service import notify_many
from Services.AnomalyAgent.Repositories.anomaly_repository           import AnomalyRepository
from Services.AnomalyAgent.Schemas.anomaly                            import AnomalyCreate
from models.anomaly                             import AnomalyType, AnomalySeverity


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
    anomalies:         list[dict]              # classified anomaly dicts
    resolutions:       dict[int, list[Resolution]]  # index → proposals
    notification_ids:  list[int]              # IDs of created notifications
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
    Orchestrates: Detector → Classifier → DB → Resolver → Notifications.

    Usage (from PlanningRouter or Orchestrator):
        agent  = AnomalyAgent(db=db)
        result = agent.analyze(
            schedule    = planning_result.schedule,
            planning_id = 1,
            groups      = groups_data,
            rooms       = rooms_data,
        )
        print(result.summary)
        print(result.resolutions[0])   # proposals for first anomaly
    """

    def __init__(self, db: Session):
        self.db   = db
        self.repo = AnomalyRepository(db)

    def analyze(
        self,
        schedule:       list[dict],
        planning_id:    int         = None,
        groups:         list[dict]  = None,
        rooms:          list[dict]  = None,
        equipment_data: list[dict]  = None,
        forbidden_days: list[str]   = None,
        admin_id:       int         = None,
    ) -> AnomalyAgentResult:
        """
        Full anomaly detection pipeline.

        Args:
            schedule:       sessions from PlanningAgent.run().schedule
            planning_id:    DB planning id
            groups:         group data for capacity checks
            rooms:          room data for capacity checks
            equipment_data: equipment data for conflict checks
            forbidden_days: days where no session is allowed
            admin_id:       admin to notify (None = broadcast)
        """
        print(f"\n{'='*60}")
        print(f"  ANOMALY AGENT")
        print(f"  Sessions : {len(schedule)}")
        print(f"{'='*60}")

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
                    planning_id    = anomaly.get("planning_id"),
                    anomaly_type   = anomaly.get("anomaly_type", AnomalyType.OTHER),
                    severity       = anomaly.get("severity",     AnomalySeverity.MEDIUM),
                    title          = anomaly.get("title", "Anomaly"),
                    description    = anomaly.get("description"),
                    details        = anomaly.get("details"),
                    impact         = anomaly.get("impact"),
                    recommendation = anomaly.get("recommendation"),
                    iso_reference  = anomaly.get("iso_reference"),
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
            anomalies   = classified,
            db          = self.db,
            admin_id    = admin_id,
            anomaly_ids = [i for i in saved_ids if i is not None],
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
        """Returns all OPEN anomalies from DB."""
        return self.repo.get_open()

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