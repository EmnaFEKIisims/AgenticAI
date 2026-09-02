"""
models/knowledge_document.py
==============================
Represents an external pedagogical document (ISO, guide, rules, etc.)
The document is chunked and each chunk is vectorized in ChromaDB.

Distinction from Memory:
  KnowledgeDocument = stable external knowledge (ISO 21001, pedagogical rules)
  Memory            = user-specific experience (preferences, decisions, feedback)

Relationship:
  KnowledgeDocument → [KnowledgeChunk, KnowledgeChunk, ...]
  Each chunk has its own ChromaDB vector.
"""

import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.DB import Base


class DocumentType(str, enum.Enum):
    ISO_STANDARD    = "iso_standard"
    PEDAGOGICAL_GUIDE = "pedagogical_guide"
    INTERNAL_RULE   = "internal_rule"
    REGULATION      = "regulation"
    BEST_PRACTICE   = "best_practice"
    OTHER           = "other"


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    source = Column(String(255), nullable=True)
    document_type = Column(String(50), nullable=True, default="pedagogical_guide")
    file_path = Column(String(500), nullable=True)
    is_indexed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    indexed_at = Column(DateTime, nullable=True)

    chunks = relationship("KnowledgeChunk", back_populates="document",
                          cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id"), nullable=False)
    content = Column(Text, nullable=False)
    qdrant_id = Column(String(36), nullable=True, unique=True)  # ID in Qdrant
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)
    section = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    document = relationship("KnowledgeDocument", back_populates="chunks")