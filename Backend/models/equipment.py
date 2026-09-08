from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from db.DB  import Base

# Association table for Course required equipment
course_equipment = Table(
    "course_equipment",
    Base.metadata,
    Column("course_id", Integer, ForeignKey("courses.id"), primary_key=True),
    Column("equipment_id", Integer, ForeignKey("equipments.id"), primary_key=True),
)

# Association table for ScheduleSlot used equipment
schedule_equipment = Table(
    "schedule_equipment",
    Base.metadata,
    Column("slot_id", Integer, ForeignKey("schedule_slots.id"), primary_key=True),
    Column("equipment_id", Integer, ForeignKey("equipments.id"), primary_key=True),
)


class Equipment(Base):
    __tablename__ = "equipments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    total_quantity = Column(Integer, default=1)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    courses = relationship("Course", secondary=course_equipment, back_populates="required_equipments")
    slots = relationship("ScheduleSlot", secondary=schedule_equipment, back_populates="allocated_equipments")
