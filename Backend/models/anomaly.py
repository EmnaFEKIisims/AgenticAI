"""
models/anomaly.py
==================
SQLAlchemy model for a detected anomaly in a planning.

An anomaly is produced by the Anomaly Agent after the Pedagogical Agent's audit.
One AuditReport criterion failure = one or more Anomaly rows.

Statuses:
  OPEN         → just detected, needs attention
  ACKNOWLEDGED → admin has seen it but not yet resolved
  RESOLVED     → admin has fixed the underlying issue
  IGNORED      → admin chose to ignore this anomaly
"""

from sqlalchemy import (
    Column, Integer, String, Text, JSON,
    DateTime, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from db.DB import Base


# =============================================================================
#  ENUMS
# =============================================================================

class AnomalyType(str, enum.Enum):
    WORKLOAD_EXCEEDED          = "workload_exceeded"
    INSUFFICIENT_BREAK         = "insufficient_break"
    WRONG_PROGRESSION          = "wrong_progression"
    PRACTICE_BEFORE_THEORY     = "practice_before_theory"
    TEACHER_OVERLOAD           = "teacher_overload"
    WRONG_ROOM_TYPE            = "wrong_room_type"
    ROOM_CAPACITY_INSUFFICIENT = "room_capacity_insufficient"
    PREREQUISITE_VIOLATED      = "prerequisite_violated"
    EVALUATION_MISPLACED       = "evaluation_misplaced"
    OTHER                      = "other"


class AnomalySeverity(str, enum.Enum):
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"


class AnomalyStatus(str, enum.Enum):
    OPEN         = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED     = "resolved"
    IGNORED      = "ignored"


# =============================================================================
#  MODEL
# =============================================================================

class Anomaly(Base):
    __tablename__ = "anomalies"

    id               = Column(Integer, primary_key=True, index=True)

    # FK links
    planning_id      = Column(Integer, ForeignKey("schedule_slots.id"), nullable=True,
                              comment="Planning that generated this anomaly")
    schedule_slot_id = Column(Integer, ForeignKey("schedule_slots.id"), nullable=True,
                              comment="Specific session slot affected (if applicable)")

    # Classification
    anomaly_type     = Column(
        SAEnum(AnomalyType, name="anomaly_type_enum"),
        nullable=False,
        default=AnomalyType.OTHER,
    )
    severity         = Column(
        SAEnum(AnomalySeverity, name="anomaly_severity_enum"),
        nullable=False,
        default=AnomalySeverity.MEDIUM,
    )

    # Human-readable content
    title            = Column(String(255), nullable=False)
    description      = Column(Text,        nullable=True)

    # Machine-readable payload (JSON)
    details          = Column(JSON, nullable=True,
                              comment="Extra context: {day, course, teacher, hours, limit, ...}")
    impact           = Column(Text, nullable=True,
                              comment="Explanation of the impact on learners or trainers")
    recommendation   = Column(Text, nullable=True,
                              comment="Suggested fix from the Pedagogical Agent")

    # Lifecycle
    status           = Column(
        SAEnum(AnomalyStatus, name="anomaly_status_enum"),
        nullable=False,
        default=AnomalyStatus.OPEN,
    )
    detected_at      = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at      = Column(DateTime(timezone=True), nullable=True)

    # ISO reference
    iso_reference    = Column(String(100), nullable=True,
                              comment="e.g. ISO 21001:2018 §8.3")

    def __repr__(self) -> str:
        return (
            f"<Anomaly id={self.id} type={self.anomaly_type} "
            f"severity={self.severity} status={self.status}>"
        )