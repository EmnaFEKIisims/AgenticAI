"""
Services/RAG/document_ingestor.py
====================================
Ingests external documents into the RAG knowledge base (Qdrant).

Pipeline:
  File (PDF/DOCX/TXT/raw text)
       ↓
  Text extraction
       ↓
  Chunker (split into ~300-word chunks)
       ↓
  Embedding service (embed each chunk)
       ↓
  Qdrant (store vectors)
       ↓
  PostgreSQL (store metadata: KnowledgeDocument + KnowledgeChunks)
"""

import uuid
from sqlalchemy.orm import Session
from qdrant_client.models import PointStruct

from Services.RAG.chunker import chunk_document, TextChunk
from repositories.knowledge_repository import KnowledgeRepository
from rag.rag_config import get_qdrant, embed, embed_batch, COLLECTION_KNOWLEDGE


def ingest_text(
    text:          str,
    title:         str,
    source:        str,
    document_type: str,
    db:            Session,
    strategy:      str = "paragraph",
) -> dict:
    """
    Ingests raw text into the RAG knowledge base.

    Steps:
      1. Create KnowledgeDocument record in PostgreSQL
      2. Chunk the text
      3. Embed and store each chunk in Qdrant
      4. Save chunk metadata in PostgreSQL
      5. Mark document as indexed
    """
    repo = KnowledgeRepository(db)

    doc = repo.create_document(
        title         = title,
        source        = source,
        document_type = document_type,
    )
    print(f"  [Ingestor] Created document #{doc.id}: '{title}'")

    chunks: list[TextChunk] = chunk_document(text, strategy=strategy)
    print(f"  [Ingestor] {len(chunks)} chunks created.")

    if not chunks:
        return {"document_id": doc.id, "chunks_count": 0}

    client  = get_qdrant()
    vectors = embed_batch([c.content for c in chunks])
    points  = []

    for chunk, vector in zip(chunks, vectors):
        point_id = str(uuid.uuid4())
        chunk.__dict__["chroma_id"] = point_id  # kept as generic chunk reference id
        points.append(PointStruct(
            id      = point_id,
            vector  = vector,
            payload = {
                "content":     chunk.content,
                "document_id": doc.id,
                "title":       title,
                "source":      source,
                "chunk_index": chunk.chunk_index,
                "section":     chunk.section or "",
                "page":        str(chunk.page_number or ""),
            },
        ))

    try:
        client.upsert(collection_name=COLLECTION_KNOWLEDGE, points=points)
        print(f"  [Ingestor] {len(points)} chunks stored in Qdrant.")
    except Exception as e:
        print(f"  [Ingestor] Qdrant error: {e}")

    chunk_dicts = [
        {
            "content":     c.content,
            "chroma_id":  c.__dict__.get("chroma_id"),
            "chunk_index": c.chunk_index,
            "page_number": c.page_number,
            "section":     c.section,
        }
        for c in chunks
    ]
    repo.create_chunks(doc.id, chunk_dicts)

    repo.mark_indexed(doc.id)
    print(f"  [Ingestor] ✅ Document #{doc.id} indexed successfully.")

    return {"document_id": doc.id, "chunks_count": len(chunks)}


def ingest_pdf(file_path: str, title: str, source: str, db: Session) -> dict:
    """Ingests a PDF file. Requires pdfplumber: pip install pdfplumber"""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n\n"
    except ImportError:
        raise RuntimeError("pdfplumber not installed. Run: pip install pdfplumber")
    except Exception as e:
        raise RuntimeError(f"PDF read failed: {e}")

    return ingest_text(text, title, source, "pedagogical_guide", db)


def query_knowledge(query: str, n_results: int = 5) -> list[dict]:
    """
    Searches the knowledge base for chunks relevant to a query.
    Used by prompt_builder to enrich LLM context with pedagogical rules.
    """
    client    = get_qdrant()
    query_vec = embed(query)

    results = client.search(
        collection_name = COLLECTION_KNOWLEDGE,
        query_vector    = query_vec,
        limit           = n_results,
        with_payload    = True,
    )

    return [
        {
            "content":    r.payload.get("content", ""),
            "source":     r.payload.get("source", ""),
            "title":      r.payload.get("title", ""),
            "similarity": round(r.score, 3),
        }
        for r in results
        if r.score >= 0.3
    ]