"""
models/memory.py
=================
Memory metadata stored in PostgreSQL.
The actual vector embedding lives in ChromaDB.
PostgreSQL stores the metadata for filtering, deduplication, and admin views.

Design:
  ChromaDB  → vector similarity search (fast semantic retrieval)
  PostgreSQL → metadata filtering, deduplication, importance scoring, audit trail
"""

import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.DB import Base


class MemoryTypeEnum(str, enum.Enum):
    USER_PREFERENCE       = "user_preference"
    DECISION_HISTORY      = "decision_history"
    PLANNING_HISTORY      = "planning_history"
    CONFLICT_CORRECTION   = "conflict_correction"
    USER_FEEDBACK         = "user_feedback"
    PEDAGOGICAL_KNOWLEDGE = "pedagogical_knowledge"


class Memory(Base):
    __tablename__ = "memories"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    memory_type = Column(String(50),   nullable=False, index=True)
    content     = Column(String(2000), nullable=False)
    qdrant_id   = Column(String(36),   nullable=True, unique=True)  # ID in Qdrant collection
    metadata_   = Column("metadata",   JSON, nullable=True)
    planning_id = Column(String(36),   nullable=True)
    source_id   = Column(Integer,      nullable=True)
    importance  = Column(Integer,  default=2)
    confidence  = Column(Float,    default=1.0)
    is_active   = Column(Boolean,  default=True)
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, nullable=True)