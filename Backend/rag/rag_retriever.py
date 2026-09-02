"""
rag/rag_retriever.py
=====================
Retrieves memories from Qdrant by agent type.
"""

from sqlalchemy.orm import Session
from rag.rag_store    import query_memories, get_user_memories
from rag.memory_types import MemoryDocument, MemoryType


class RAGRetriever:

    def __init__(self, db: Session, n_results: int = 5):
        self.db = db
        self.n  = n_results

    def get_planning_context(self, user_id: str) -> list[MemoryDocument]:
        return query_memories(
            query        = "training schedule preferences, session timing, day preferences, planning history, user feedback",
            user_id      = user_id,
            db           = self.db,
            memory_types = [
                MemoryType.USER_FEEDBACK.value,
                MemoryType.USER_PREFERENCE.value,
                MemoryType.DECISION_HISTORY.value,
                MemoryType.PLANNING_HISTORY.value,
            ],
            n_results = self.n,
        )

    def get_constraint_context(self, user_id: str) -> list[MemoryDocument]:
        return query_memories(
            query        = "scheduling constraints, forbidden days, session duration, trainer availability",
            user_id      = user_id,
            db           = self.db,
            memory_types = [
                MemoryType.DECISION_HISTORY.value,
                MemoryType.USER_PREFERENCE.value,
                MemoryType.CONFLICT_CORRECTION.value,
            ],
            n_results = self.n,
        )

    def get_pedagogical_context(self, user_id: str) -> list[MemoryDocument]:
        return query_memories(
            query        = "pedagogical rules, theory before practice, ISO 21001, workload balance",
            user_id      = user_id,
            db           = self.db,
            memory_types = [
                MemoryType.PEDAGOGICAL_KNOWLEDGE.value,
                MemoryType.USER_FEEDBACK.value,
            ],
            n_results = self.n,
        )

    def get_anomaly_context(self, user_id: str) -> list[MemoryDocument]:
        return query_memories(
            query        = "scheduling conflicts, trainer overload, room conflicts, conflict resolutions",
            user_id      = user_id,
            db           = self.db,
            memory_types = [
                MemoryType.CONFLICT_CORRECTION.value,
                MemoryType.PLANNING_HISTORY.value,
            ],
            n_results = self.n,
        )

    def get_knowledge_context(self, query: str, n: int = 3) -> list[dict]:
        """Retrieves pedagogical knowledge chunks from Qdrant."""
        from rag.rag_config import get_qdrant, embed, COLLECTION_KNOWLEDGE
        try:
            results = get_qdrant().search(
                collection_name = COLLECTION_KNOWLEDGE,
                query_vector    = embed(query),
                limit           = n,
                score_threshold = 0.3,
            )
            return [
                {
                    "content": r.payload.get("content", ""),
                    "source":  r.payload.get("source", ""),
                    "title":   r.payload.get("title", ""),
                }
                for r in results
            ]
        except Exception:
            return []