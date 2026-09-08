"""
Services/RAG/rag_service.py
=============================
Main RAG facade — Qdrant vector database backend.
"""

from sqlalchemy.orm import Session

from rag.rag_indexer import (
    index_user_preference, index_decision, index_planning_result,
    index_feedback, index_pedagogical_rules_bulk,
)
from rag.rag_store import count_user_memories, get_user_memories
from rag.rag_retriever import RAGRetriever

from Services.RAG.repositories.user_repository  import UserRepository
from Services.RAG.memory_writer     import MemoryWriter
from Services.RAG.memory_extractor  import MemoryExtractor
from Services.RAG.prompt_builder    import (
    build_planning_context, build_constraint_context,
    build_pedagogical_context, build_anomaly_context, is_context_useful,
)


class RAGService:

    def __init__(self, db: Session):
        self.db        = db
        self.user_repo = UserRepository(db)
        self.retriever = RAGRetriever(db=db, n_results=5)
        self.writer    = MemoryWriter(db)
        self.extractor = MemoryExtractor()

    def ensure_user(self, user_id: str, display_name: str = "Administrator"):
        return self.user_repo.get_or_create(user_id, display_name)

    # ── Context retrieval ──────────────────────────────────────────────────────

    def get_planning_context(self, user_id: str) -> str:
        memories  = self.retriever.get_planning_context(user_id)
        knowledge = self.retriever.get_knowledge_context("training schedule planning preferences")
        context   = build_planning_context(memories, knowledge)
        if is_context_useful(context):
            print(f"  [RAGService] Planning context: {len(memories)} memories for {user_id[:8]}...")
        return context

    def get_constraint_context(self, user_id: str) -> str:
        return build_constraint_context(self.retriever.get_constraint_context(user_id))

    def get_pedagogical_context(self, user_id: str) -> str:
        memories  = self.retriever.get_pedagogical_context(user_id)
        knowledge = self.retriever.get_knowledge_context("pedagogical rules ISO 21001")
        return build_pedagogical_context(memories, knowledge)

    def get_anomaly_context(self, user_id: str) -> str:
        return build_anomaly_context(self.retriever.get_anomaly_context(user_id))

    # ── Memory storage ─────────────────────────────────────────────────────────

    def after_planning_generated(self, user_id: str, schedule: list[dict],
                                  constraints: dict, planning_id: str = "") -> None:
        total   = len(schedule)
        groups  = list({s.get("group_name", "") for s in schedule})[:3]
        summary = f"{total} sessions, {len(groups)} group(s): {', '.join(groups)}"
        index_planning_result(user_id, "generated", summary, constraints, self.db, planning_id)

    def after_planning_validated(self, user_id: str, schedule: list[dict],
                                  constraints: dict, notes: str = "", planning_id: str = "") -> None:
        extracted = self.extractor.from_validation(schedule, constraints, notes)
        self.writer.write_many(extracted, user_id, planning_id)
        index_decision(user_id, "Planning validated", notes or "Admin approved",
                       self.db, planning_id=planning_id, importance=3)

    def after_planning_rejected(self, user_id: str, reason: str = "", planning_id: str = "") -> None:
        extracted = self.extractor.from_rejection(reason, planning_id)
        self.writer.write_many(extracted, user_id, planning_id)

    def after_move(self, user_id: str, course_title: str, from_day: str, to_day: str,
                   from_time: str, to_time: str, admin_note: str = "", planning_id: str = "") -> None:
        extracted = self.extractor.from_move(course_title, from_day, to_day,
                                              from_time, to_time, admin_note)
        self.writer.write_many(extracted, user_id, planning_id)

    def after_anomaly(self, user_id: str, anomalies: list[dict], planning_id: str = "") -> None:
        for a in anomalies:
            if a.get("severity") in ("high", "medium"):
                extracted = self.extractor.from_anomaly(
                    a.get("anomaly_type", "conflict"),
                    a.get("description", ""),
                    a.get("recommendation", ""),
                )
                self.writer.write_many(extracted, user_id, planning_id)

    def store_feedback(self, user_id: str, feedback: str,
                       context: str = "", planning_id: str = "") -> int:
        return index_feedback(user_id, feedback, self.db, context, planning_id, importance=3)

    def seed_pedagogical_rules(self, user_id: str) -> int:
        rules = [
            {"rule": "Theory sessions must precede practice sessions for the same module",  "source": "ISO 21001:2018"},
            {"rule": "Maximum 6 consecutive training hours — mandatory break required",      "source": "ISO 21001:2018"},
            {"rule": "Evaluation sessions must follow all related theory and practice",      "source": "ISO 21001:2018"},
            {"rule": "Daily training load should not exceed 8 hours",                        "source": "ISO 29993:2017"},
            {"rule": "Lunch break minimum 40 minutes after 3+ consecutive sessions",        "source": "ISO 29993:2017"},
            {"rule": "Trainer should not deliver more than 6 hours consecutively",           "source": "ISO 21001:2018"},
            {"rule": "Balance theory and practice sessions within the same week",            "source": "Pedagogical best practice"},
        ]
        ids = index_pedagogical_rules_bulk(user_id, rules, self.db)
        print(f"  [RAGService] {len(ids)} pedagogical rules seeded into Qdrant.")
        return len(ids)

    def get_summary(self, user_id: str) -> dict:
        counts   = count_user_memories(user_id, self.db)
        memories = get_user_memories(user_id, self.db, limit=100)
        return {
            "user_id": user_id,
            "total":   sum(counts.values()),
            "by_type": counts,
            "recent":  [
                {"content": m.content, "type": m.memory_type.value, "created_at": m.created_at}
                for m in sorted(memories, key=lambda x: x.created_at or "", reverse=True)[:5]
            ],
        }

    def clear_memories(self, user_id: str) -> int:
        return self.writer.clear_user(user_id)