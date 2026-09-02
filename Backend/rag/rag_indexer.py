"""
rag/rag_indexer.py
===================
High-level indexing — all operations go to Qdrant + PostgreSQL.
"""

from sqlalchemy.orm import Session
from rag.rag_store   import add_memory, add_memories
from rag.memory_types import (
    MemoryDocument, MemoryType,
    format_user_preference, format_decision_history,
    format_planning_history, format_conflict,
    format_feedback, format_pedagogical,
)


def index_user_preference(user_id: str, preference: str, db: Session,
                           source: str = "", importance: int = 2) -> int:
    return add_memory(MemoryDocument(
        content=format_user_preference(preference, source),
        memory_type=MemoryType.USER_PREFERENCE,
        user_id=user_id, importance=importance, tags=["preference"],
    ), db)


def index_decision(user_id: str, decision: str, reason: str, db: Session,
                   outcome: str = "", planning_id: str = "", importance: int = 2) -> int:
    return add_memory(MemoryDocument(
        content=format_decision_history(decision, reason, outcome),
        memory_type=MemoryType.DECISION_HISTORY,
        user_id=user_id, planning_id=planning_id, importance=importance, tags=["decision"],
    ), db)


def index_planning_result(user_id: str, action: str, summary: str,
                           constraints: dict, db: Session,
                           planning_id: str = "", importance: int = 2) -> int:
    parts = []
    if constraints.get("forbidden_days"):
        parts.append(f"Forbidden: {', '.join(constraints['forbidden_days'])}")
    if constraints.get("day_start_time"):
        parts.append(f"Start: {constraints['day_start_time']}")
    constraint_summary = "; ".join(parts) if parts else "default constraints"
    return add_memory(MemoryDocument(
        content=format_planning_history(action, summary, constraint_summary),
        memory_type=MemoryType.PLANNING_HISTORY,
        user_id=user_id, planning_id=planning_id, importance=importance, tags=["planning", action],
    ), db)


def index_conflict(user_id: str, conflict: str, resolution: str, db: Session,
                   affected: str = "", planning_id: str = "", importance: int = 3) -> int:
    return add_memory(MemoryDocument(
        content=format_conflict(conflict, resolution, affected),
        memory_type=MemoryType.CONFLICT_CORRECTION,
        user_id=user_id, planning_id=planning_id, importance=importance, tags=["conflict"],
    ), db)


def index_feedback(user_id: str, feedback: str, db: Session,
                   context: str = "", planning_id: str = "", importance: int = 3) -> int:
    return add_memory(MemoryDocument(
        content=format_feedback(feedback, context),
        memory_type=MemoryType.USER_FEEDBACK,
        user_id=user_id, planning_id=planning_id, importance=importance, tags=["feedback"],
    ), db)


def index_pedagogical_rule(user_id: str, rule: str, db: Session,
                            source: str = "ISO 21001") -> int:
    return add_memory(MemoryDocument(
        content=format_pedagogical(rule, source),
        memory_type=MemoryType.PEDAGOGICAL_KNOWLEDGE,
        user_id=user_id, importance=1, tags=["rule"],
    ), db)


def index_pedagogical_rules_bulk(user_id: str, rules: list[dict], db: Session) -> list[int]:
    docs = [
        MemoryDocument(
            content=format_pedagogical(r["rule"], r.get("source", "ISO 21001")),
            memory_type=MemoryType.PEDAGOGICAL_KNOWLEDGE,
            user_id=user_id, importance=1, tags=["rule"],
        )
        for r in rules
    ]
    return add_memories(docs, db)


def index_constraint_decision(user_id: str, constraints: dict, db: Session,
                               planning_id: str = "") -> int:
    parts = []
    if constraints.get("forbidden_days"):
        parts.append(f"Forbidden: {', '.join(constraints['forbidden_days'])}")
    if constraints.get("session_duration_override"):
        parts.append(f"Duration: {constraints['session_duration_override']} min")
    summary = "; ".join(parts) if parts else "default constraints"
    return index_decision(user_id, "Constraints applied", summary, db,
                          planning_id=planning_id, importance=2)