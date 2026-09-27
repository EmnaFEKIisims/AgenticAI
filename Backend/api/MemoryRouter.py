"""
api/MemoryRouter.py
====================
Memory management endpoints.

Endpoints:
  GET    /memories              → list user memories (with optional type filter)
  GET    /memories/summary      → counts by type
  GET    /memories/{id}         → get one memory
  DELETE /memories/{id}         → delete one memory
  DELETE /memories              → clear all user memories
  POST   /memories/feedback     → store explicit feedback

FIX: `m.memory_type.value` crashed with `AttributeError: 'str' object has
no attribute 'value'` — the `memory_type` column on your Memory model
returns a plain Python str at the ORM level (not an Enum member), so
calling `.value` on it fails. Replaced with a small helper that works
whether memory_type comes back as a str OR an Enum member, so it's safe
either way and doesn't depend on how the column happens to be typed.
"""

import traceback
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.DB import SessionLocal
from Services.RAG.rag_service import RAGService
from Services.RAG.repositories.memory_repository import MemoryRepository
from Services.RAG.schemas.rag import FeedbackRequest, FeedbackResponse

router = APIRouter(prefix="/memories", tags=["Memories"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _type_str(memory_type) -> str:
    """memory_type may come back as a str or an Enum member depending on
    how the column is mapped — handle both without crashing."""
    return memory_type.value if hasattr(memory_type, "value") else memory_type


@router.get("")
def list_memories(
    user_id:     str,
    memory_type: Optional[str] = None,
    limit:       int           = 50,
    db:          Session       = Depends(get_db),
):
    """Lists memories for a user, optionally filtered by type."""
    try:
        repo     = MemoryRepository(db)
        memories = repo.get_for_user(user_id, memory_type=memory_type, limit=limit)
        return {
            "user_id":  user_id,
            "total":    len(memories),
            "memories": [
                {
                    "id":          m.id,
                    "content":     m.content,
                    "type":        _type_str(m.memory_type),
                    "importance":  m.importance,
                    "confidence":  m.confidence,
                    "planning_id": m.planning_id,
                    "created_at":  m.created_at.isoformat() if m.created_at else None,
                    "tags":        m.metadata_.get("tags", []) if m.metadata_ else [],
                }
                for m in memories
            ],
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.get("/summary")
def get_summary(user_id: str, db: Session = Depends(get_db)):
    """Returns memory counts by type + 5 most recent."""
    try:
        return RAGService(db).get_summary(user_id)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.get("/{memory_id}")
def get_memory(memory_id: int, db: Session = Depends(get_db)):
    try:
        mem = MemoryRepository(db).get_by_id(memory_id)
        if not mem:
            raise HTTPException(404, detail=f"Memory {memory_id} not found.")
        return {
            "id":         mem.id,
            "content":    mem.content,
            "type":       _type_str(mem.memory_type),
            "importance": mem.importance,
            "created_at": mem.created_at.isoformat() if mem.created_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.delete("/{memory_id}")
def delete_memory(memory_id: int, db: Session = Depends(get_db)):
    """Deletes one memory from PostgreSQL + ChromaDB."""
    try:
        from Services.RAG.memory_writer import MemoryWriter
        ok = MemoryWriter(db).delete(memory_id)
        if not ok:
            raise HTTPException(404, detail=f"Memory {memory_id} not found.")
        return {"success": True, "deleted_id": memory_id}
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.delete("")
def clear_memories(user_id: str, db: Session = Depends(get_db)):
    """Clears ALL memories for a user from PostgreSQL + ChromaDB."""
    try:
        count = RAGService(db).clear_memories(user_id)
        return {"success": True, "deleted_count": count,
                "message": f"Cleared {count} memories for user {user_id[:8]}..."}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.post("/feedback", response_model=FeedbackResponse)
def store_feedback(body: FeedbackRequest, db: Session = Depends(get_db)):
    """Stores explicit user feedback. Always stored (importance=3)."""
    try:
        memory_id = RAGService(db).store_feedback(
            user_id     = body.user_id,
            feedback    = body.feedback,
            context     = body.context or "",
            planning_id = body.planning_id or "",
        )
        return FeedbackResponse(
            success   = True,
            memory_id = memory_id,
            message   = "Feedback stored. Will improve future plannings.",
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))