"""
schemas/user.py
================
Pydantic schemas for User (no login — just identity for RAG).
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Called by frontend on first visit to register the anonymous UUID."""
    id:           str              # UUID from localStorage
    display_name: Optional[str] = "Administrator"
    role:         Optional[str] = "admin"


class UserResponse(BaseModel):
    id:           str
    display_name: str
    role:         str
    is_active:    bool
    created_at:   Optional[datetime]
    last_seen_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    role:         Optional[str] = None