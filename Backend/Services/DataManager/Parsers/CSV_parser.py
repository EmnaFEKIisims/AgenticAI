"""
agents/data_manager/parsers/csv_parser.py
==========================================
Reads a CSV file and returns a list of raw dicts.
Each row becomes one dict with column headers as keys.

Handles:
  - Different delimiters (, ; tab)
  - Empty rows skipped
  - Encoding detection (UTF-8 with BOM, latin-1 fallback)
  - Strips whitespace from keys and values
"""

import csv


def parse_csv(filepath: str) -> list[dict]:
    """
    Reads a CSV file and returns a list of dicts.
    Each dict = one row, keys = column headers.

    Args:
        filepath: absolute or relative path to the .csv file

    Returns:
        List of dicts with string values. Empty rows are skipped.
    """
    records = []

    # Try common encodings
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with open(filepath, "r", encoding=encoding, newline="") as f:
                sample = f.read(4096)
                f.seek(0)

                # Auto-detect delimiter
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                except csv.Error:
                    dialect = csv.excel  # fallback to comma

                reader = csv.DictReader(f, dialect=dialect)

                for row in reader:
                    # Strip whitespace from keys and values, skip fully empty rows
                    cleaned = {
                        k.strip(): v.strip() if isinstance(v, str) else v
                        for k, v in row.items()
                        if k is not None
                    }
                    if any(v for v in cleaned.values()):  # skip empty rows
                        records.append(cleaned)

            print(f"  [CSV Parser] {len(records)} row(s) extracted from '{filepath}'")
            return records

        except UnicodeDecodeError:
            continue  # try next encoding
        except Exception as e:
            raise ValueError(f"CSV parsing failed: {e}")

    raise ValueError(f"Could not decode CSV file '{filepath}' with any supported encoding.")