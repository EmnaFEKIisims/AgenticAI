"""
agents/data_manager/parsers/pdf_parser.py
==========================================
Reads a PDF file and extracts structured data.

Strategy (in order):
  1. Extract tables using pdfplumber  -> structured rows (best case)
  2. Extract plain text line by line  -> fallback if no tables found
  3. Each result becomes a dict for the extractor

Handles:
  - Multi-page PDFs
  - Tables with/without headers
  - Mixed pages (some with tables, some with text)
  - Page number added as "_page" hint
"""

import pdfplumber


def parse_pdf(filepath: str) -> list[dict]:
    """
    Extracts data from a PDF file.
    Returns a list of dicts — one per table row or text line.

    Args:
        filepath: path to .pdf file

    Returns:
        List of dicts. Table rows have column header keys.
        Plain text lines have the key "_text".
    """
    records = []

    try:
        with pdfplumber.open(filepath) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):

                # ── Strategy 1: extract tables ────────────────────────────────
                tables = page.extract_tables() or []
                page_has_tables = False

                for table in tables:
                    if not table or len(table) < 2:
                        continue

                    page_has_tables = True

                    # First row = headers
                    raw_headers = table[0] or []
                    headers = [
                        str(h).strip() if h else f"col_{i}"
                        for i, h in enumerate(raw_headers)
                    ]

                    for row in table[1:]:
                        if not row:
                            continue

                        if len(row) == len(headers):
                            record = {
                                headers[i]: str(row[i] or "").strip()
                                for i in range(len(headers))
                            }
                        else:
                            # Mismatched columns — use generic keys
                            record = {
                                f"col_{i}": str(v or "").strip()
                                for i, v in enumerate(row)
                            }

                        # Skip fully empty rows
                        if not any(v for v in record.values()):
                            continue

                        record["_page"] = page_num
                        records.append(record)

                # ── Strategy 2: plain text fallback ───────────────────────────
                if not page_has_tables:
                    text = page.extract_text() or ""
                    for line in text.split("\n"):
                        line = line.strip()
                        if line:
                            records.append({
                                "_text": line,
                                "_page": page_num,
                            })

    except Exception as e:
        raise ValueError(f"PDF parsing failed: {e}")

    print(f"  [PDF Parser] {len(records)} record(s) extracted from '{filepath}'")
    return records