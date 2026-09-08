"""
Services/RAG/document_ingestor.py
====================================
Ingests external documents into the RAG knowledge base.

Pipeline:
  File (PDF/DOCX/TXT/raw text)
       ↓
  Text extraction
       ↓
  Chunker (split into ~300-word chunks)
       ↓
  Embedding service (embed each chunk)
       ↓
  ChromaDB (store vectors)
       ↓
  PostgreSQL (store metadata: KnowledgeDocument + KnowledgeChunks)
"""

import uuid
from sqlalchemy.orm import Session

from Services.RAG.chunker import chunk_document, TextChunk
from Services.RAG.repositories.knowledge_repository import KnowledgeRepository
from rag.rag_config import get_collection


# ChromaDB collection for knowledge documents (separate from user memories)
KNOWLEDGE_COLLECTION_NAME = "knowledge_documents"


def _get_knowledge_collection():
    """Returns the ChromaDB collection for pedagogical knowledge."""
    from rag.rag_config import get_client, get_embedding_fn
    client = get_client()
    return client.get_or_create_collection(
        name               = KNOWLEDGE_COLLECTION_NAME,
        embedding_function = get_embedding_fn(),
        metadata           = {"hnsw:space": "cosine"},
    )


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
      3. Embed and store each chunk in ChromaDB
      4. Save chunk metadata in PostgreSQL
      5. Mark document as indexed

    Returns dict with document_id and chunk count.
    """
    repo = KnowledgeRepository(db)

    # Step 1: Create document record
    doc = repo.create_document(
        title         = title,
        source        = source,
        document_type = document_type,
    )
    print(f"  [Ingestor] Created document #{doc.id}: '{title}'")

    # Step 2: Chunk
    chunks: list[TextChunk] = chunk_document(text, strategy=strategy)
    print(f"  [Ingestor] {len(chunks)} chunks created.")

    if not chunks:
        return {"document_id": doc.id, "chunks_count": 0}

    # Step 3: Store in ChromaDB
    col       = _get_knowledge_collection()
    ids       = []
    documents = []
    metadatas = []

    for chunk in chunks:
        chroma_id = str(uuid.uuid4())
        ids.append(chroma_id)
        documents.append(chunk.content)
        metadatas.append({
            "document_id": doc.id,
            "title":       title,
            "source":      source,
            "chunk_index": chunk.chunk_index,
            "section":     chunk.section or "",
            "page":        str(chunk.page_number or ""),
        })
        chunk.content  # attach chroma_id to chunk for PostgreSQL save
        chunk.__dict__["chroma_id"] = chroma_id

    try:
        col.add(ids=ids, documents=documents, metadatas=metadatas)
        print(f"  [Ingestor] {len(chunks)} chunks stored in ChromaDB.")
    except Exception as e:
        print(f"  [Ingestor] ChromaDB error: {e}")

    # Step 4: Save chunk metadata in PostgreSQL
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

    # Step 5: Mark indexed
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
    col   = _get_knowledge_collection()
    total = col.count()
    if total == 0:
        return []

    results = col.query(
        query_texts = [query],
        n_results   = min(n_results, total),
        include     = ["documents", "metadatas", "distances"],
    )

    return [
        {
            "content":    doc,
            "source":     meta.get("source", ""),
            "title":      meta.get("title", ""),
            "similarity": round(1.0 - dist, 3),
        }
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
        if (1.0 - dist) >= 0.3
    ]