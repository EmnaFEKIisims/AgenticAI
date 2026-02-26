from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from db.DB  import Base


class ScheduleSlot(Base):
    __tablename__ = "schedule_slots"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("trainers.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    learner_group_id = Column(Integer, ForeignKey("learner_groups.id"), nullable=False)

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    # AI generated metrics
    quality_score = Column(Float, default=0.0)
    pedagogical_audit_score = Column(Float, default=0.0)

    # HITL (Human In The Loop) validation
    is_validated = Column(Boolean, default=False)
    status = Column(String, default="draft")  # draft, validated, rejected

    # Relationships
    course = relationship("Course", back_populates="slots")
    trainer = relationship("Trainer", back_populates="slots")
    room = relationship("Room", back_populates="slots")
    learner_group = relationship("LearnerGroup", back_populates="slots")
    allocated_equipments = relationship("Equipment", secondary="schedule_equipment", back_populates="slots")
