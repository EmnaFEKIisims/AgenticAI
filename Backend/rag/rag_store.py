"""
rag/rag_store.py
=================
RAG storage — Qdrant (vectors) + PostgreSQL (metadata).

Write: embed → Qdrant.upsert → PostgreSQL.insert
Read:  embed query → Qdrant.search → return MemoryDocuments
"""

from __future__ import annotations
import uuid
from sqlalchemy.orm import Session
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

from rag.rag_config   import get_qdrant, embed, embed_batch, COLLECTION_MEMORIES, DEFAULT_N_RESULTS
from rag.memory_types import MemoryDocument, MemoryType
from models.memory    import Memory


# =============================================================================
#  WRITE
# =============================================================================

def add_memory(doc: MemoryDocument, db: Session) -> int:
    """
    1. Embeds content
    2. Stores vector in Qdrant
    3. Stores metadata in PostgreSQL
    Returns PostgreSQL row id.
    """
    vector    = embed(doc.content)
    qdrant_id = str(uuid.uuid4())

    # Store vector in Qdrant
    get_qdrant().upsert(
        collection_name = COLLECTION_MEMORIES,
        points=[PointStruct(
            id      = qdrant_id,
            vector  = vector,
            payload = {
                "user_id":     doc.user_id,
                "memory_type": doc.memory_type.value,
                "content":     doc.content,
                "planning_id": doc.planning_id or "",
                "importance":  doc.importance,
                "tags":        doc.tags,
            },
        )],
    )

    # Store metadata in PostgreSQL
    row = Memory(
        user_id     = doc.user_id,
        memory_type = doc.memory_type.value,
        content     = doc.content,
        qdrant_id   = qdrant_id,
        metadata_   = {"tags": doc.tags},
        planning_id = doc.planning_id,
        importance  = doc.importance,
        confidence  = 1.0,
        is_active   = True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    print(f"  [RAG] Stored [{doc.memory_type.value}] id={row.id} → '{doc.content[:60]}'")
    return row.id


def add_memories(docs: list[MemoryDocument], db: Session) -> list[int]:
    """Batch insert."""
    if not docs:
        return []
    vectors = embed_batch([d.content for d in docs])
    points  = []
    rows    = []

    for doc, vec in zip(docs, vectors):
        qid = str(uuid.uuid4())
        points.append(PointStruct(
            id      = qid,
            vector  = vec,
            payload = {
                "user_id":     doc.user_id,
                "memory_type": doc.memory_type.value,
                "content":     doc.content,
                "planning_id": doc.planning_id or "",
                "importance":  doc.importance,
            },
        ))
        rows.append(Memory(
            user_id     = doc.user_id,
            memory_type = doc.memory_type.value,
            content     = doc.content,
            qdrant_id   = qid,
            metadata_   = {"tags": doc.tags},
            planning_id = doc.planning_id,
            importance  = doc.importance,
            is_active   = True,
        ))

    get_qdrant().upsert(collection_name=COLLECTION_MEMORIES, points=points)
    db.add_all(rows)
    db.commit()
    print(f"  [RAG] Batch stored {len(rows)} memories.")
    return [r.id for r in rows]


def delete_memory(memory_id: int, db: Session) -> bool:
    row = db.query(Memory).filter(Memory.id == memory_id).first()
    if not row:
        return False
    if row.qdrant_id:
        try:
            get_qdrant().delete(COLLECTION_MEMORIES, points_selector=[row.qdrant_id])
        except Exception:
            pass
    db.delete(row)
    db.commit()
    return True


def delete_user_memories(user_id: str, db: Session) -> int:
    rows = db.query(Memory).filter(Memory.user_id == user_id).all()
    qids = [r.qdrant_id for r in rows if r.qdrant_id]
    if qids:
        try:
            get_qdrant().delete(COLLECTION_MEMORIES, points_selector=qids)
        except Exception:
            pass
    count = len(rows)
    for r in rows:
        db.delete(r)
    db.commit()
    return count


# =============================================================================
#  SEMANTIC SEARCH
# =============================================================================

def query_memories(
    query:          str,
    user_id:        str,
    db:             Session,
    memory_types:   list[str] | None = None,
    n_results:      int              = DEFAULT_N_RESULTS,
    min_similarity: float            = 0.3,
) -> list[MemoryDocument]:
    """
    Semantic search via Qdrant cosine similarity.
    Filters by user_id and optionally memory_type.
    """
    query_vec = embed(query)

    # Build Qdrant filter
    must = [FieldCondition(key="user_id", match=MatchValue(value=user_id))]
    if memory_types and len(memory_types) == 1:
        must.append(FieldCondition(key="memory_type", match=MatchValue(value=memory_types[0])))

    try:
        results = get_qdrant().search(
            collection_name = COLLECTION_MEMORIES,
            query_vector    = query_vec,
            query_filter    = Filter(must=must),
            limit           = n_results,
            score_threshold = min_similarity,
        )
    except Exception as e:
        print(f"  [RAG] Qdrant search error: {e}")
        return []

    # Filter by multiple memory_types if needed (Qdrant doesn't support OR in one call easily)
    if memory_types and len(memory_types) > 1:
        results = [r for r in results if r.payload.get("memory_type") in memory_types]

    docs = []
    for r in results:
        p = r.payload
        docs.append(MemoryDocument(
            doc_id      = str(r.id),
            content     = p.get("content", ""),
            memory_type = MemoryType(p.get("memory_type", "user_preference")),
            user_id     = p.get("user_id", user_id),
            planning_id = p.get("planning_id", ""),
            importance  = p.get("importance", 2),
            tags        = p.get("tags", []),
        ))
    return docs


# =============================================================================
#  NON-SEMANTIC READ
# =============================================================================

def get_user_memories(
    user_id:     str,
    db:          Session,
    memory_type: str | None = None,
    limit:       int        = 50,
) -> list[MemoryDocument]:
    q = db.query(Memory).filter(
        Memory.user_id   == user_id,
        Memory.is_active == True,
    )
    if memory_type:
        q = q.filter(Memory.memory_type == memory_type)
    rows = q.order_by(Memory.created_at.desc()).limit(limit).all()
    return [_row_to_doc(r) for r in rows]


def count_user_memories(user_id: str, db: Session) -> dict[str, int]:
    counts = {}
    for mt in MemoryType:
        n = db.query(Memory).filter(
            Memory.user_id     == user_id,
            Memory.memory_type == mt.value,
            Memory.is_active   == True,
        ).count()
        counts[mt.value] = n
    return counts


def _row_to_doc(row: Memory) -> MemoryDocument:
    meta = row.metadata_ or {}
    return MemoryDocument(
        doc_id      = str(row.id),
        content     = row.content,
        memory_type = MemoryType(row.memory_type),
        user_id     = row.user_id,
        planning_id = row.planning_id,
        importance  = row.importance,
        tags        = meta.get("tags", []),
        created_at  = row.created_at.isoformat() if row.created_at else "",
    )