"""
Services/RAG/memory_writer.py
================================
Stores extracted memories into Qdrant + PostgreSQL with deduplication.
"""

from sqlalchemy.orm import Session
from rag.rag_store         import add_memory, delete_user_memories, query_memories
from rag.memory_types      import MemoryDocument
from models.memory         import Memory
from Services.RAG.memory_extractor import ExtractedMemory

DEDUP_THRESHOLD = 0.85


class MemoryWriter:

    def __init__(self, db: Session):
        self.db = db

    def write(self, extracted: ExtractedMemory, user_id: str, planning_id: str = "") -> int | None:
        content = extracted.content.strip()
        if not content:
            return None

        # Deduplication check via Qdrant
        existing = query_memories(
            query        = content,
            user_id      = user_id,
            db           = self.db,
            memory_types = [extracted.memory_type.value],
            n_results    = 3,
            min_similarity = DEDUP_THRESHOLD,
        )
        if existing:
            dup_id = int(existing[0].doc_id)
            row    = self.db.query(Memory).filter(Memory.id == dup_id).first()
            if row:
                row.importance = min(3, row.importance + 1)
                self.db.commit()
            print(f"  [MemoryWriter] Duplicate → boosted importance of memory #{dup_id}.")
            return dup_id

        doc = MemoryDocument(
            content     = content,
            memory_type = extracted.memory_type,
            user_id     = user_id,
            planning_id = planning_id,
            importance  = extracted.importance,
            tags        = extracted.tags or [],
        )
        return add_memory(doc, self.db)

    def write_many(self, extracted_list: list[ExtractedMemory], user_id: str,
                   planning_id: str = "") -> list[int]:
        return [i for em in extracted_list if (i := self.write(em, user_id, planning_id))]

    def delete(self, memory_id: int) -> bool:
        from rag.rag_store import delete_memory
        return delete_memory(memory_id, self.db)

    def clear_user(self, user_id: str) -> int:
        count = delete_user_memories(user_id, self.db)
        print(f"  [MemoryWriter] Cleared {count} memories for user {user_id[:8]}...")
        return count