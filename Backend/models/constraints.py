from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.DB import Base


class Constraint(Base):
    __tablename__ = "constraints"

    id = Column(Integer, primary_key=True, index=True)
    constraint_type = Column(String, nullable=False)
    constraint_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # user_id = None  → global/ISO constraint, visible to every user
    # user_id = uuid   → personal constraint, visible only to that user
    # (matches Services/DataManager/DB_Loader.py's ISO vs user_defined logic
    # and agents/planning_agent.py's _load_constraints_from_db filter)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)