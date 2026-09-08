"""
schemas/memory.py
==================
Pydantic schemas for Memory.
"""

from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class MemoryCreate(BaseModel):
    user_id:     str
    memory_type: str
    content:     str
    metadata_:   Optional[dict] = None
    planning_id: Optional[str]  = None
    source_id:   Optional[int]  = None
    importance:  int            = 2
    confidence:  float          = 1.0


class MemoryResponse(BaseModel):
    id:          int
    user_id:     str
    memory_type: str
    content:     str
    chroma_id:   Optional[str]
    metadata_:   Optional[dict]
    planning_id: Optional[str]
    importance:  int
    confidence:  float
    is_active:   bool
    created_at:  Optional[datetime]

    class Config:
        from_attributes = True


class MemoryListResponse(BaseModel):
    user_id:  str
    total:    int
    memories: list[MemoryResponse]


class MemoryCountByType(BaseModel):
    user_id:  str
    total:    int
    by_type:  dict[str, int]
    recent:   list[dict]