"""
repositories/memory_repository.py
====================================
DB operations for Memory model (PostgreSQL side).
ChromaDB operations are handled in rag/rag_store.py.
"""

from sqlalchemy.orm import Session
from models.memory import Memory, MemoryTypeEnum


class MemoryRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, memory: Memory) -> Memory:
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        return memory

    def get_by_id(self, memory_id: int) -> Memory | None:
        return self.db.query(Memory).filter(Memory.id == memory_id).first()

    def get_by_chroma_id(self, chroma_id: str) -> Memory | None:
        return self.db.query(Memory).filter(Memory.chroma_id == chroma_id).first()

    def get_for_user(
        self,
        user_id:     str,
        memory_type: str | None = None,
        active_only: bool       = True,
        limit:       int        = 100,
    ) -> list[Memory]:
        q = self.db.query(Memory).filter(Memory.user_id == user_id)
        if memory_type:
            q = q.filter(Memory.memory_type == MemoryTypeEnum(memory_type))
        if active_only:
            q = q.filter(Memory.is_active == True)
        return q.order_by(Memory.created_at.desc()).limit(limit).all()

    def count_by_type(self, user_id: str) -> dict[str, int]:
        counts = {}
        for mt in MemoryTypeEnum:
            n = self.db.query(Memory).filter(
                Memory.user_id     == user_id,
                Memory.memory_type == mt,
                Memory.is_active   == True,
            ).count()
            counts[mt.value] = n
        return counts

    def find_similar_content(
        self, user_id: str, content: str, memory_type: str, threshold: int = 80
    ) -> Memory | None:
        """
        Simple text-based deduplication: checks if a very similar memory already exists.
        For proper semantic dedup, use ChromaDB similarity.
        """
        existing = self.db.query(Memory).filter(
            Memory.user_id     == user_id,
            Memory.memory_type == MemoryTypeEnum(memory_type),
            Memory.is_active   == True,
        ).all()
        # Simple word overlap check
        new_words = set(content.lower().split())
        for mem in existing:
            old_words = set(mem.content.lower().split())
            if len(new_words) == 0:
                continue
            overlap = len(new_words & old_words) / len(new_words | old_words)
            if overlap > (threshold / 100):
                return mem
        return None

    def deactivate(self, memory_id: int, superseded_by: int | None = None) -> bool:
        mem = self.get_by_id(memory_id)
        if not mem:
            return False
        mem.is_active     = False
        mem.superseded_by = superseded_by
        self.db.commit()
        return True

    def delete(self, memory_id: int) -> str | None:
        """Returns the chroma_id before deleting (for ChromaDB cleanup)."""
        mem = self.get_by_id(memory_id)
        if not mem:
            return None
        chroma_id = mem.chroma_id
        self.db.delete(mem)
        self.db.commit()
        return chroma_id

    def delete_all_for_user(self, user_id: str) -> tuple[int, list[str]]:
        """Returns (count, list of chroma_ids) for ChromaDB cleanup."""
        mems = self.get_for_user(user_id, active_only=False)
        chroma_ids = [m.chroma_id for m in mems if m.chroma_id]
        count = len(mems)
        for m in mems:
            self.db.delete(m)
        self.db.commit()
        return count, chroma_ids