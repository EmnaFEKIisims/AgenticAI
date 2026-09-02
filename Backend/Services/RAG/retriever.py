"""
Services/RAG/retriever.py
==========================
Retrieves relevant memories from ChromaDB.

Retrieval strategy:
  1. Filter by user_id (each user's memories are isolated)
  2. Filter by memory_type (optional — per agent)
  3. Semantic similarity (cosine distance via ChromaDB)
  4. Score = similarity × importance × recency_factor

This is the CORE of the adaptive behavior:
  "What does this system know about this user's preferences?"
"""

from datetime import datetime, timezone
from rag.rag_store    import query_memories
from rag.memory_types import MemoryDocument, MemoryType
from Services.RAG.document_ingestor import query_knowledge


# =============================================================================
#  SCORING
# =============================================================================

def _recency_score(created_at: str, half_life_days: int = 30) -> float:
    """
    Exponential decay: recent memories score higher.
    A memory created today scores 1.0; one from 30 days ago scores ~0.5.
    """
    if not created_at:
        return 0.5
    try:
        dt   = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        days = (datetime.now(timezone.utc) - dt).days
        import math
        return math.exp(-0.693 * days / half_life_days)   # ln(2)/half_life
    except Exception:
        return 0.5


def _relevance_score(mem: MemoryDocument, similarity: float) -> float:
    """
    Combined relevance score:
      score = similarity × importance_weight × recency_factor
    """
    importance_weight = {1: 0.7, 2: 1.0, 3: 1.4}.get(mem.importance, 1.0)
    recency           = _recency_score(mem.created_at)
    return similarity * importance_weight * recency


# =============================================================================
#  RETRIEVER CLASS
# =============================================================================

class RAGRetriever:
    """
    Retrieves memories for a specific user and context.

    Usage in PlanningAgent:
        retriever = RAGRetriever()
        context   = retriever.get_planning_context(user_id)
        # Inject context into LLM system prompt
    """

    def __init__(self, n_results: int = 5):
        self.n = n_results

    # ── Per-agent retrieval ────────────────────────────────────────────────────

    def get_planning_context(self, user_id: str) -> list[MemoryDocument]:
        """
        Retrieves context for PlanningAgent.
        Priority: USER_FEEDBACK (3) > USER_PREFERENCE (2) > DECISION_HISTORY (1)
        """
        return self._retrieve(
            user_id      = user_id,
            query        = ("training schedule preferences, session timing, day preferences, "
                           "avoided days, trainer availability, planning history, user feedback"),
            memory_types = [
                MemoryType.USER_FEEDBACK.value,
                MemoryType.USER_PREFERENCE.value,
                MemoryType.DECISION_HISTORY.value,
                MemoryType.PLANNING_HISTORY.value,
            ],
        )

    def get_constraint_context(self, user_id: str) -> list[MemoryDocument]:
        return self._retrieve(
            user_id      = user_id,
            query        = ("scheduling constraints, forbidden days, session duration, "
                           "trainer availability, past constraint decisions"),
            memory_types = [
                MemoryType.DECISION_HISTORY.value,
                MemoryType.USER_PREFERENCE.value,
                MemoryType.CONFLICT_CORRECTION.value,
            ],
        )

    def get_pedagogical_context(self, user_id: str) -> list[MemoryDocument]:
        return self._retrieve(
            user_id      = user_id,
            query        = ("pedagogical rules, theory before practice, session sequencing, "
                           "workload balance, ISO 21001, learning progression"),
            memory_types = [
                MemoryType.PEDAGOGICAL_KNOWLEDGE.value,
                MemoryType.USER_FEEDBACK.value,
                MemoryType.CONFLICT_CORRECTION.value,
            ],
        )

    def get_anomaly_context(self, user_id: str) -> list[MemoryDocument]:
        return self._retrieve(
            user_id      = user_id,
            query        = ("scheduling conflicts, trainer overload, room conflicts, "
                           "group double booking, conflict resolutions"),
            memory_types = [
                MemoryType.CONFLICT_CORRECTION.value,
                MemoryType.PLANNING_HISTORY.value,
                MemoryType.USER_FEEDBACK.value,
            ],
        )

    def get_custom_context(
        self,
        user_id:      str,
        query:        str,
        memory_types: list[str] | None = None,
    ) -> list[MemoryDocument]:
        return self._retrieve(user_id=user_id, query=query, memory_types=memory_types)

    # ── Core retrieval ─────────────────────────────────────────────────────────

    def _retrieve(
        self,
        user_id:      str,
        query:        str,
        memory_types: list[str] | None = None,
    ) -> list[MemoryDocument]:
        """
        Retrieves and re-ranks memories using relevance score.
        """
        raw = query_memories(
            query        = query,
            user_id      = user_id,
            memory_types = memory_types,
            n_results    = self.n * 2,    # over-fetch, then re-rank
            min_similarity = 0.2,
        )
        # Re-rank by composite score
        ranked = sorted(raw, key=lambda m: m.importance, reverse=True)
        return ranked[:self.n]

    # ── Knowledge base retrieval ───────────────────────────────────────────────

    def get_knowledge_context(self, query: str, n: int = 3) -> list[dict]:
        """Retrieves relevant chunks from pedagogical knowledge documents."""
        return query_knowledge(query=query, n_results=n)