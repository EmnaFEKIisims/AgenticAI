"""
Services/RAG/embedding_service.py
===================================
Transforms text into vector embeddings using sentence-transformers.

The SAME model is used for:
  - Indexing (when storing memories/chunks)
  - Retrieval (when querying for similar content)
This consistency is critical: mismatched models = wrong similarity scores.

Model: all-MiniLM-L6-v2
  - 384 dimensions
  - ~22MB — runs fully locally
  - Good quality for semantic similarity on short texts
  - No API key needed

Install: pip install sentence-transformers
"""

from __future__ import annotations
from rag.rag_config import get_embedding_fn

# Singleton embedding function (shared with ChromaDB)
_embed_fn = None


def get_embedder():
    """Returns the singleton embedding function (sentence-transformers)."""
    global _embed_fn
    if _embed_fn is None:
        _embed_fn = get_embedding_fn()
    return _embed_fn


def embed_text(text: str) -> list[float]:
    """
    Embeds a single text string into a vector.

    Args:
        text: the input text (max ~512 tokens for MiniLM)

    Returns:
        list[float] — 384-dimensional vector
    """
    embedder = get_embedder()
    # sentence-transformers embedding function expects a list
    vectors = embedder([text])
    return vectors[0]


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embeds multiple texts in a single batch (more efficient than one by one).

    Args:
        texts: list of text strings

    Returns:
        list of 384-dim vectors
    """
    if not texts:
        return []
    embedder = get_embedder()
    return embedder(texts)


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Computes cosine similarity between two vectors.
    Used for semantic deduplication in memory_writer.

    Returns float in [-1, 1] (1 = identical, 0 = unrelated, -1 = opposite).
    """
    import math
    dot   = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)