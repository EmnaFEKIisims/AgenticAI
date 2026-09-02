"""
rag/rag_config.py
==================
Fixed: _ensure_collections() is called on EVERY get_qdrant() call.
This way, even if Qdrant was offline at startup, collections are
created the first time a request actually needs them.
"""

import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer

QDRANT_URL           = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBEDDING_MODEL      = "all-MiniLM-L6-v2"
EMBEDDING_DIM        = 384
COLLECTION_MEMORIES  = "agent_memories"
COLLECTION_KNOWLEDGE = "knowledge_chunks"
DEFAULT_N_RESULTS    = 5

_qdrant_client: QdrantClient | None        = None
_embed_model:   SentenceTransformer | None = None


def get_qdrant() -> QdrantClient:
    """
    Returns a Qdrant client and ensures collections exist.
    Called on every RAG operation — safe to call multiple times.
    """
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(url=QDRANT_URL)
        print(f"  [RAG] Qdrant client created → {QDRANT_URL}")

    # Always ensure collections exist (not just at creation)
    _ensure_collections(_qdrant_client)
    return _qdrant_client


def get_embed_model() -> SentenceTransformer:
    global _embed_model
    if _embed_model is None:
        print(f"  [RAG] Loading embedding model: {EMBEDDING_MODEL}...")
        _embed_model = SentenceTransformer(EMBEDDING_MODEL)
        print(f"  [RAG] ✅ Embedding model ready ({EMBEDDING_DIM} dims).")
    return _embed_model


def embed(text: str) -> list[float]:
    return get_embed_model().encode(text, normalize_embeddings=True).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return get_embed_model().encode(texts, normalize_embeddings=True).tolist()


def _ensure_collections(client: QdrantClient) -> None:
    """Creates collections if they don't exist. Safe to call repeatedly."""
    try:
        existing = {c.name for c in client.get_collections().collections}
        for name in [COLLECTION_MEMORIES, COLLECTION_KNOWLEDGE]:
            if name not in existing:
                client.create_collection(
                    collection_name = name,
                    vectors_config  = VectorParams(
                        size     = EMBEDDING_DIM,
                        distance = Distance.COSINE,
                    ),
                )
                print(f"  [RAG] ✅ Created Qdrant collection: '{name}'")
    except Exception as e:
        print(f"  [RAG] ⚠️  Qdrant not available: {e}")
        raise   # re-raise so the caller knows Qdrant is down


def test_rag_connection() -> bool:
    try:
        get_qdrant()
        embed("test")
        print("  [RAG] ✅ Qdrant + embeddings operational.")
        return True
    except Exception as e:
        print(f"  [RAG] ❌ {e}")
        return False