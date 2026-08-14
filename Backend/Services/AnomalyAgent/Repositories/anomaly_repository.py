"""
repositories/anomaly_repository.py
=====================================
All DB operations for the Anomaly model.
No business logic here — only DB read/write.

Functions:
  create         → insert a new anomaly
  get            → get one anomaly by id
  get_by_planning → all anomalies for a planning
  get_open       → all OPEN anomalies
  update_status  → change status (acknowledge / resolve / ignore)
  delete         → remove an anomaly
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from models.anomaly import Anomaly, AnomalyStatus
from Services.AnomalyAgent.Schemas.anomaly import AnomalyCreate, AnomalyUpdate


class AnomalyRepository:

    def __init__(self, db: Session):
        self.db = db

    # ── CREATE ────────────────────────────────────────────────────────────────

    def create(self, data: AnomalyCreate) -> Anomaly:
        anomaly = Anomaly(**data.model_dump())
        self.db.add(anomaly)
        self.db.commit()
        self.db.refresh(anomaly)
        return anomaly

    def create_many(self, items: list[AnomalyCreate]) -> list[Anomaly]:
        anomalies = [Anomaly(**d.model_dump()) for d in items]
        self.db.add_all(anomalies)
        self.db.commit()
        for a in anomalies:
            self.db.refresh(a)
        return anomalies

    # ── READ ──────────────────────────────────────────────────────────────────

    def get(self, anomaly_id: int) -> Anomaly | None:
        return self.db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()

    def get_by_planning(self, planning_id: int) -> list[Anomaly]:
        return (
            self.db.query(Anomaly)
            .filter(Anomaly.planning_id == planning_id)
            .order_by(Anomaly.detected_at.desc())
            .all()
        )

    def get_open(self) -> list[Anomaly]:
        """Returns all anomalies with status = OPEN."""
        return (
            self.db.query(Anomaly)
            .filter(Anomaly.status == AnomalyStatus.OPEN)
            .order_by(Anomaly.detected_at.desc())
            .all()
        )

    def get_by_severity(self, severity: str) -> list[Anomaly]:
        return (
            self.db.query(Anomaly)
            .filter(Anomaly.severity == severity)
            .order_by(Anomaly.detected_at.desc())
            .all()
        )

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Anomaly]:
        return (
            self.db.query(Anomaly)
            .order_by(Anomaly.detected_at.desc())
            .offset(skip).limit(limit).all()
        )

    # ── UPDATE ────────────────────────────────────────────────────────────────

    def update_status(self, anomaly_id: int, status: AnomalyStatus) -> Anomaly | None:
        anomaly = self.get(anomaly_id)
        if not anomaly:
            return None
        anomaly.status = status
        if status == AnomalyStatus.RESOLVED:
            anomaly.resolved_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(anomaly)
        return anomaly

    def update(self, anomaly_id: int, data: AnomalyUpdate) -> Anomaly | None:
        anomaly = self.get(anomaly_id)
        if not anomaly:
            return None
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(anomaly, field, value)
        self.db.commit()
        self.db.refresh(anomaly)
        return anomaly

    # ── DELETE ────────────────────────────────────────────────────────────────

    def delete(self, anomaly_id: int) -> bool:
        anomaly = self.get(anomaly_id)
        if not anomaly:
            return False
        self.db.delete(anomaly)
        self.db.commit()
        return True

    def delete_by_planning(self, planning_id: int) -> int:
        """Deletes all anomalies for a planning. Returns deleted count."""
        n = (
            self.db.query(Anomaly)
            .filter(Anomaly.planning_id == planning_id)
            .delete()
        )
        self.db.commit()
        return n

