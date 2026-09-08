from sqlalchemy import Column, Integer, String, Text , ForeignKey
from sqlalchemy.orm import relationship
from db.DB  import Base

class Trainer(Base):
    __tablename__ = "trainers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    specialization = Column(String)
    availability_notes = Column(Text)
    user_id            = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    # Relationships
    slots = relationship("ScheduleSlot", back_populates="trainer")
