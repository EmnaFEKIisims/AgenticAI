"""
models/schedule.py
===================
Updated ScheduleSlot:
  - user_id           : links each slot to its owner
  - planning_group_id : groups all slots from the same generation batch
  - validated_at      : timestamp when admin validated
  - rejected_at       : timestamp when admin rejected
  - validation_notes  : admin's note on validation/rejection
  - move_history      : JSON list of past moves (drag & drop audit trail)

SQL migration (run once in pgAdmin):
  ALTER TABLE schedule_slots ADD COLUMN IF NOT EXISTS user_id VARCHAR(36) REFERENCES users(id);
  UPDATE schedule_slots SET user_id = '00000000-0000-0000-0000-000000000001' WHERE user_id IS NULL;
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.DB import Base


class ScheduleSlot(Base):
    __tablename__ = "schedule_slots"

    id = Column(Integer, primary_key=True, index=True)

    # ── Foreign keys ───────────────────────────────────────────────────────────
    course_id        = Column(Integer, ForeignKey("courses.id"),        nullable=False)
    trainer_id       = Column(Integer, ForeignKey("trainers.id"),       nullable=False)
    room_id          = Column(Integer, ForeignKey("rooms.id"),          nullable=False)
    learner_group_id = Column(Integer, ForeignKey("learner_groups.id"), nullable=False)

    # ── User ownership ────────────────────────────────────────────────────────
    # Links each slot to the user who generated the planning.
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    # ── Scheduling ────────────────────────────────────────────────────────────
    start_time = Column(DateTime, nullable=False)
    end_time   = Column(DateTime, nullable=False)

    # ── Planning batch ────────────────────────────────────────────────────────
    planning_group_id = Column(
        String(36), nullable=True, index=True,
        comment="UUID grouping all slots from the same generation batch",
    )
    session_number = Column(
        Integer, nullable=True,
        comment="1-based session number within this planning batch",
    )

    # ── AI metrics ────────────────────────────────────────────────────────────
    quality_score           = Column(Float, default=0.0)
    pedagogical_audit_score = Column(Float, default=0.0)

    # ── HITL — Human In The Loop ──────────────────────────────────────────────
    is_validated     = Column(Boolean, default=False)
    status           = Column(String,  default="draft")
    validated_at     = Column(DateTime(timezone=True), nullable=True)
    rejected_at      = Column(DateTime(timezone=True), nullable=True)
    validation_notes = Column(
        String(500), nullable=True,
        comment="Admin's comment when validating or rejecting",
    )

    # ── Drag & Drop audit trail ───────────────────────────────────────────────
    move_history = Column(JSON, nullable=True, default=list)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ── Relationships ─────────────────────────────────────────────────────────
    course        = relationship("Course",       back_populates="slots")
    trainer       = relationship("Trainer",      back_populates="slots")
    room          = relationship("Room",         back_populates="slots")
    learner_group = relationship("LearnerGroup", back_populates="slots")
    allocated_equipments = relationship(
        "Equipment", secondary="schedule_equipment", back_populates="slots"
    )

    def __repr__(self):
        return (
            f"<ScheduleSlot id={self.id} group={self.planning_group_id} "
            f"course_id={self.course_id} status={self.status} user={self.user_id}>"
        )