"""
api/RAGRouter.py
=================
RAG system REST API — uses RAGService as the only facade.

Endpoints:
  POST /rag/context/planning      → context for PlanningAgent
  POST /rag/context/constraints   → context for ConstraintAgent
  POST /rag/context/pedagogical   → context for PedagogicalAgent
  GET  /rag/memories              → list user memories
  GET  /rag/memories/summary      → counts by type
  POST /rag/feedback              → store explicit feedback
  POST /rag/memory                → store a memory manually
  DELETE /rag/memories/{id}       → delete one memory
  DELETE /rag/memories            → clear all user memories
  POST /rag/seed-rules            → seed ISO 21001 pedagogical rules
  POST /rag/documents             → ingest a text document
  GET  /rag/documents             → list ingested documents
  POST /rag/events/planning-validated   → trigger memory storage after validation
  POST /rag/events/planning-rejected    → trigger memory storage after rejection
  POST /rag/events/session-moved        → trigger memory storage after DnD move
"""

import traceback
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.DB import SessionLocal
from Services.RAG.rag_service import RAGService
from Services.RAG.repositories.knowledge_repository import KnowledgeRepository
from Services.RAG.schemas.rag import (
    FeedbackRequest, FeedbackResponse,
    DocumentIngestRequest, DocumentIngestResponse, SeedRulesResponse,
    RAGContextRequest, RAGContextResponse,
)

router = APIRouter(prefix="/rag", tags=["RAG Memory"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Event schemas ──────────────────────────────────────────────────────────────

class PlanningValidatedEvent(BaseModel):
    user_id:     str
    planning_id: str
    notes:       Optional[str] = ""
    schedule:    list[dict]    = []
    constraints: dict          = {}


class PlanningRejectedEvent(BaseModel):
    user_id:     str
    planning_id: str
    reason:      Optional[str] = ""


class SessionMovedEvent(BaseModel):
    user_id:      str
    planning_id:  str
    course_title: str
    from_day:     str
    to_day:       str
    from_time:    str
    to_time:      str
    admin_note:   Optional[str] = ""


class ManualMemoryRequest(BaseModel):
    user_id:     str
    content:     str
    memory_type: str
    planning_id: Optional[str] = ""
    importance:  int           = 2
    tags:        list[str]     = []


# =============================================================================
#  CONTEXT RETRIEVAL
# =============================================================================

@router.post("/context/planning", response_model=RAGContextResponse)
def get_planning_context(body: RAGContextRequest, db: Session = Depends(get_db)):
    """
    Retrieves adaptive context for PlanningAgent.
    Called by the frontend BEFORE triggering planning generation.
    The context is injected into the LLM system prompt.
    """
    try:
        svc     = RAGService(db)
        svc.ensure_user(body.user_id)
        context = svc.get_planning_context(body.user_id)
        memories_count = len(context.split("\n")) if context else 0
        return RAGContextResponse(
            user_id      = body.user_id,
            context      = context,
            has_context  = bool(context),
            memory_count = memories_count,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.post("/context/constraints", response_model=RAGContextResponse)
def get_constraint_context(body: RAGContextRequest, db: Session = Depends(get_db)):
    """Context for ConstraintAgent."""
    try:
        svc     = RAGService(db)
        context = svc.get_constraint_context(body.user_id)
        return RAGContextResponse(user_id=body.user_id, context=context,
                                   has_context=bool(context))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.post("/context/pedagogical", response_model=RAGContextResponse)
def get_pedagogical_context(body: RAGContextRequest, db: Session = Depends(get_db)):
    """Context for PedagogicalAgent."""
    try:
        svc     = RAGService(db)
        context = svc.get_pedagogical_context(body.user_id)
        return RAGContextResponse(user_id=body.user_id, context=context,
                                   has_context=bool(context))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


# =============================================================================
#  EVENTS — memory storage triggered by frontend actions
# =============================================================================

@router.post("/events/planning-validated")
def event_planning_validated(body: PlanningValidatedEvent, db: Session = Depends(get_db)):
    """
    Called by PlanningPage after admin clicks 'Validate'.
    Stores positive planning signal in RAG memory.
    """
    try:
        svc = RAGService(db)
        svc.ensure_user(body.user_id)
        svc.after_planning_validated(
            user_id     = body.user_id,
            schedule    = body.schedule,
            constraints = body.constraints,
            notes       = body.notes or "",
            planning_id = body.planning_id,
        )
        return {"success": True, "message": "Validation memory stored."}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.post("/events/planning-rejected")
def event_planning_rejected(body: PlanningRejectedEvent, db: Session = Depends(get_db)):
    """
    Called by PlanningPage after admin clicks 'Reject'.
    Extracts and stores negative feedback memories.
    """
    try:
        svc = RAGService(db)
        svc.ensure_user(body.user_id)
        svc.after_planning_rejected(
            user_id     = body.user_id,
            reason      = body.reason or "",
            planning_id = body.planning_id,
        )
        return {"success": True, "message": "Rejection memory stored."}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.post("/events/session-moved")
def event_session_moved(body: SessionMovedEvent, db: Session = Depends(get_db)):
    """
    Called by PlanningPage after admin confirms a DnD move.
    Stores the move as a decision/preference signal.
    """
    try:
        svc = RAGService(db)
        svc.ensure_user(body.user_id)
        svc.after_move(
            user_id      = body.user_id,
            course_title = body.course_title,
            from_day     = body.from_day,
            to_day       = body.to_day,
            from_time    = body.from_time,
            to_time      = body.to_time,
            admin_note   = body.admin_note or "",
            planning_id  = body.planning_id,
        )
        return {"success": True, "message": "Move memory stored."}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


# =============================================================================
#  MEMORIES — list and manage
# =============================================================================

@router.get("/memories")
def list_memories(
    user_id:     str,
    memory_type: Optional[str] = None,
    limit:       int           = 50,
    db:          Session       = Depends(get_db),
):
    try:
        from rag.rag_store import get_user_memories
        memories = get_user_memories(user_id, db, memory_type=memory_type, limit=limit)
        return {
            "user_id":  user_id,
            "total":    len(memories),
            "memories": [
                {
                    "id":          m.doc_id,
                    "content":     m.content,
                    "type":        m.memory_type.value,
                    "importance":  m.importance,
                    "created_at":  m.created_at,
                    "planning_id": m.planning_id,
                    "tags":        m.tags,
                }
                for m in memories
            ],
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.get("/memories/summary")
def get_summary(user_id: str, db: Session = Depends(get_db)):
    try:
        return RAGService(db).get_summary(user_id)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.post("/feedback", response_model=FeedbackResponse)
def add_feedback(body: FeedbackRequest, db: Session = Depends(get_db)):
    """Stores explicit user feedback on a planning."""
    try:
        svc = RAGService(db)
        svc.ensure_user(body.user_id)
        memory_id = svc.store_feedback(
            user_id     = body.user_id,
            feedback    = body.feedback,
            context     = body.context or "",
            planning_id = body.planning_id or "",
        )
        return FeedbackResponse(success=True, memory_id=memory_id,
                                 message="Feedback stored. Will improve future plannings.")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.post("/memory")
def add_memory_manual(body: ManualMemoryRequest, db: Session = Depends(get_db)):
    """Manually adds a memory (admin use)."""
    try:
        svc = RAGService(db)
        svc.ensure_user(body.user_id)   # ← FIX: create the user first, avoids ForeignKeyViolation

        from rag.memory_types import MemoryType, MemoryDocument
        from rag.rag_store import add_memory

        mt = MemoryType(body.memory_type)
        doc = MemoryDocument(
            content     = body.content,
            memory_type = mt,
            user_id     = body.user_id,
            planning_id = body.planning_id,
            importance  = body.importance,
            tags        = body.tags,
        )
        mem_id = add_memory(doc, db)
        return {"success": True, "memory_id": mem_id}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.delete("/memories/{memory_id}")
def delete_one_memory(memory_id: str, db: Session = Depends(get_db)):
    try:
        from rag.rag_store import delete_memory
        ok = delete_memory(memory_id, db)
        if not ok:
            raise HTTPException(404, detail=f"Memory {memory_id} not found.")
        return {"success": True, "deleted_id": memory_id}
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.delete("/memories")
def clear_memories(user_id: str, db: Session = Depends(get_db)):
    try:
        count = RAGService(db).clear_memories(user_id)
        return {"success": True, "deleted_count": count}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


# =============================================================================
#  SEED & DOCUMENTS
# =============================================================================

@router.post("/seed-rules", response_model=SeedRulesResponse)
def seed_rules(user_id: str, db: Session = Depends(get_db)):
    """Seeds ISO 21001 pedagogical rules for a user."""
    try:
        svc   = RAGService(db)
        svc.ensure_user(user_id)
        count = svc.seed_pedagogical_rules(user_id)
        return SeedRulesResponse(success=True, seeded_count=count,
                                  message=f"{count} rules seeded into RAG memory.")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.post("/documents", response_model=DocumentIngestResponse)
def ingest_document(body: DocumentIngestRequest, db: Session = Depends(get_db)):
    """
    Ingests a text document (rules, guidelines) into the knowledge base.
    Chunks + embeds automatically.
    """
    try:
        from Services.RAG.document_ingestor import ingest_text
        result = ingest_text(
            text          = body.content,
            title         = body.title,
            source        = body.source or "Manual",
            document_type = body.document_type or "pedagogical_guide",
            db            = db,
        )
        return DocumentIngestResponse(
            success     = True,
            document_id = result["document_id"],
            chunks_count = result["chunks_count"],
            message     = f"Document ingested: {result['chunks_count']} chunks indexed.",
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    """Lists all knowledge documents."""
    try:
        repo = KnowledgeRepository(db)
        docs = repo.list_documents()
        return {
            "total":     len(docs),
            "documents": [
                {"id": d.id, "title": d.title, "source": d.source,
                 "type": d.document_type, "is_indexed": d.is_indexed,
                 "chunks": repo.count_chunks(d.id)}
                for d in docs
            ],
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))