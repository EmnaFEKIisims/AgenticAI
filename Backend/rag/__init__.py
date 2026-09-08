"""
rag/__init__.py
================
RAG package — Qdrant vector database backend.
"""

from rag.memory_types import (
    MemoryType, MemoryDocument,
    format_user_preference, format_decision_history,
    format_planning_history, format_conflict,
    format_feedback, format_pedagogical,
)

from rag.rag_config import embed, embed_batch, get_qdrant, test_rag_connection

from rag.rag_store import (
    add_memory, add_memories, delete_memory,
    delete_user_memories, query_memories,
    get_user_memories, count_user_memories,
)

from rag.rag_indexer import (
    index_user_preference, index_decision,
    index_planning_result, index_conflict,
    index_feedback, index_pedagogical_rule,
    index_pedagogical_rules_bulk, index_constraint_decision,
)

from rag.rag_retriever import RAGRetriever

__all__ = [
    "MemoryType", "MemoryDocument",
    "embed", "embed_batch", "get_qdrant", "test_rag_connection",
    "add_memory", "add_memories", "delete_memory",
    "delete_user_memories", "query_memories",
    "get_user_memories", "count_user_memories",
    "index_user_preference", "index_decision",
    "index_planning_result", "index_conflict",
    "index_feedback", "index_pedagogical_rule",
    "index_pedagogical_rules_bulk", "index_constraint_decision",
    "RAGRetriever",
]