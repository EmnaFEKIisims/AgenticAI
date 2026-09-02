"""
Services/RAG/chunker.py
=========================
Splits long documents into overlapping chunks for embedding.

Why chunking?
  A PDF of 100 pages = ~100,000 tokens.
  LLMs have context limits (4k-32k tokens).
  Embedding models work best on short passages (< 512 tokens).
  → Split into chunks of ~300 words with 50-word overlap.

Overlap prevents losing context at chunk boundaries:
  chunk 1: tokens  1-300
  chunk 2: tokens 250-550   ← overlap with chunk 1
  chunk 3: tokens 500-800   ← overlap with chunk 2
"""

from dataclasses import dataclass


@dataclass
class TextChunk:
    content:     str
    chunk_index: int
    page_number: int | None   = None
    section:     str | None   = None
    char_start:  int          = 0
    char_end:    int          = 0


def chunk_text(
    text:            str,
    chunk_size_words: int = 300,
    overlap_words:    int = 50,
    page_number:      int | None = None,
    section:          str | None = None,
) -> list[TextChunk]:
    """
    Splits text into overlapping chunks by word count.

    Args:
        text:             the full text to chunk
        chunk_size_words: target words per chunk (default 300 ≈ ~400 tokens)
        overlap_words:    words to overlap between chunks (avoids boundary loss)
        page_number:      optional page number (for PDF chunking)
        section:          optional section/heading label

    Returns:
        list of TextChunk objects
    """
    words  = text.split()
    chunks = []
    start  = 0
    idx    = 0

    while start < len(words):
        end        = min(start + chunk_size_words, len(words))
        chunk_text = " ".join(words[start:end])

        chunks.append(TextChunk(
            content     = chunk_text.strip(),
            chunk_index = idx,
            page_number = page_number,
            section     = section,
            char_start  = len(" ".join(words[:start])),
            char_end    = len(" ".join(words[:end])),
        ))

        if end == len(words):
            break

        start += chunk_size_words - overlap_words   # advance with overlap
        idx   += 1

    return chunks


def chunk_by_paragraph(
    text:       str,
    max_words:  int = 400,
    min_words:  int = 30,
) -> list[TextChunk]:
    """
    Splits by paragraph first (double newline), then merges or splits as needed.
    Better for structured documents (PDFs with sections).
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks     = []
    buffer     = ""
    idx        = 0

    for para in paragraphs:
        candidate = (buffer + "\n\n" + para).strip()
        words     = len(candidate.split())

        if words <= max_words:
            buffer = candidate
        else:
            if len(buffer.split()) >= min_words:
                chunks.append(TextChunk(content=buffer, chunk_index=idx))
                idx += 1
            # If paragraph itself is too long, do word-based chunking
            if len(para.split()) > max_words:
                sub_chunks = chunk_text(para, chunk_size_words=max_words)
                for sc in sub_chunks:
                    sc.chunk_index = idx
                    chunks.append(sc)
                    idx += 1
                buffer = ""
            else:
                buffer = para

    if buffer and len(buffer.split()) >= min_words:
        chunks.append(TextChunk(content=buffer, chunk_index=idx))

    return chunks


def chunk_document(text: str, strategy: str = "paragraph") -> list[TextChunk]:
    """
    Main chunking entry point.

    strategy:
      "paragraph" → better for structured docs (PDFs, reports)
      "word"      → better for continuous text
    """
    if strategy == "paragraph":
        return chunk_by_paragraph(text)
    return chunk_text(text)