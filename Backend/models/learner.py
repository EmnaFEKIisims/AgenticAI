from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db.DB  import Base

class LearnerGroup(Base):
    __tablename__ = "learner_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    size = Column(Integer, default=1)
    level = Column(String)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    # Relationships
    slots = relationship("ScheduleSlot", back_populates="learner_group")
