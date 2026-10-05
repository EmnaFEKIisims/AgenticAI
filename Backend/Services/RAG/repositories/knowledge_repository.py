"""
repositories/knowledge_repository.py
========================================
DB operations for KnowledgeDocument and KnowledgeChunk.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models.knowledge_document import KnowledgeDocument, KnowledgeChunk, DocumentType


class KnowledgeRepository:

    def __init__(self, db: Session):
        self.db = db

    # ── Documents ──────────────────────────────────────────────────────────────

    def create_document(
        self,
        title:         str,
        source:        str        = "",
        document_type: str        = "pedagogical_guide",
        file_path:     str | None = None,
    ) -> KnowledgeDocument:
        doc = KnowledgeDocument(
            title         = title,
            source        = source,
            document_type = DocumentType(document_type),
            file_path     = file_path,
            is_indexed    = False,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get_document(self, doc_id: int) -> KnowledgeDocument | None:
        return self.db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == doc_id
        ).first()

    def list_documents(self, indexed_only: bool = False) -> list[KnowledgeDocument]:
        q = self.db.query(KnowledgeDocument)
        if indexed_only:
            q = q.filter(KnowledgeDocument.is_indexed == True)
        return q.order_by(KnowledgeDocument.created_at.desc()).all()

    def mark_indexed(self, doc_id: int) -> None:
        doc = self.get_document(doc_id)
        if doc:
            doc.is_indexed = True
            doc.indexed_at = datetime.now(timezone.utc)
            self.db.commit()

    def delete_document(self, doc_id: int) -> bool:
        doc = self.get_document(doc_id)
        if not doc:
            return False
        self.db.delete(doc)
        self.db.commit()
        return True

    # ── Chunks ─────────────────────────────────────────────────────────────────

    def create_chunks(
        self,
        doc_id: int,
        chunks: list[dict],   # [{"content": "...", "chunk_index": 0, "chroma_id": "...", ...}]
    ) -> list[KnowledgeChunk]:
        rows = []
        for c in chunks:
            row = KnowledgeChunk(
                document_id = doc_id,
                content     = c["content"],
                qdrant_id   = c.get("chroma_id"),   # dict key stays "chroma_id" from document_ingestor, model column is qdrant_id
                chunk_index = c["chunk_index"],
                page_number = c.get("page_number"),
                section     = c.get("section"),
            )
            rows.append(row)
        self.db.add_all(rows)
        self.db.commit()
        return rows

    def get_chunks(self, doc_id: int) -> list[KnowledgeChunk]:
        return self.db.query(KnowledgeChunk).filter(
            KnowledgeChunk.document_id == doc_id
        ).order_by(KnowledgeChunk.chunk_index).all()

    def count_chunks(self, doc_id: int) -> int:
        return self.db.query(KnowledgeChunk).filter(
            KnowledgeChunk.document_id == doc_id
        ).count()