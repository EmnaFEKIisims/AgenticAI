from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from db.DB  import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    total_hours = Column(Float, nullable=False)
    session_duration = Column(Integer, nullable=False)
    pedagogical_objectives = Column(Text)
    user_id                 = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    # Relationships
    required_equipments = relationship("Equipment", secondary="course_equipment", back_populates="courses")
    slots = relationship("ScheduleSlot", back_populates="course")
