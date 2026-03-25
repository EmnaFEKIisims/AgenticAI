from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.DB import Base


from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from db.DB import Base

class Constraint(Base):
    __tablename__ = "constraints"

    id = Column(Integer, primary_key=True, index=True)
    planning_id = Column(Integer, ForeignKey("schedule_slots.id"), nullable=False)
    constraint_type = Column(String, nullable=False)
    constraint_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    schedule_slot = relationship("ScheduleSlot", back_populates="constraints")
