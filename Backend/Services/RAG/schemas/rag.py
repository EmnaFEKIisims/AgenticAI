"""
schemas/rag.py
===============
Pydantic schemas for RAG operations (context retrieval, feedback, documents).
"""

from pydantic import BaseModel
from typing import Optional


class RAGContextRequest(BaseModel):
    user_id: str
    query:   Optional[str] = None     # custom query; if None, uses agent default


class RAGContextResponse(BaseModel):
    user_id:     str
    context:     str                  # formatted string injected into LLM prompt
    has_context: bool
    memory_count: int = 0


class FeedbackRequest(BaseModel):
    user_id:     str
    feedback:    str
    context:     Optional[str] = ""
    planning_id: Optional[str] = ""


class FeedbackResponse(BaseModel):
    success:   bool
    memory_id: Optional[str]
    message:   str


class DocumentIngestRequest(BaseModel):
    title:         str
    source:        Optional[str] = "ISO 21001:2018"
    document_type: Optional[str] = "pedagogical_guide"
    content:       str            # raw text content to chunk + embed


class DocumentIngestResponse(BaseModel):
    success:      bool
    document_id:  int
    chunks_count: int
    message:      str


class SeedRulesResponse(BaseModel):
    success:      bool
    seeded_count: int
    message:      str