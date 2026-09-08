from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db.DB  import Base

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    room_type = Column(String) # e.g., 'Lab', 'Classroom', 'Virtual'
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    # Relationships
    slots = relationship("ScheduleSlot", back_populates="room")
