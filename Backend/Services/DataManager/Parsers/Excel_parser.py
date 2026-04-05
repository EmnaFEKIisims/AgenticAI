"""
agents/data_manager/parsers/excel_parser.py
============================================
Reads an Excel file (.xlsx / .xls) and returns raw dicts.

Handles:
  - Multiple sheets (each sheet parsed separately)
  - Sheet name added as "_sheet" hint for the extractor
  - Empty rows skipped
  - NaN / None values converted to empty string
  - Numeric values kept as-is (float/int)
"""

import pandas as pd


def parse_excel(filepath: str) -> list[dict]:
    """
    Reads all sheets from an Excel file.
    Each row becomes a dict. Sheet name is added as "_sheet" key
    so the LLM extractor can use it as a classification hint.

    Args:
        filepath: path to .xlsx or .xls file

    Returns:
        List of dicts, one per non-empty row across all sheets.
    """
    records = []

    try:
        xl = pd.ExcelFile(filepath)
    except Exception as e:
        raise ValueError(f"Excel file could not be opened: {e}")

    for sheet_name in xl.sheet_names:
        try:
            df = pd.read_excel(filepath, sheet_name=sheet_name, dtype=str)
        except Exception as e:
            print(f"  [Excel Parser] Warning: could not read sheet '{sheet_name}': {e}")
            continue

        # Replace NaN with empty string
        df = df.fillna("")

        # Strip whitespace from column names
        df.columns = [str(c).strip() for c in df.columns]

        for _, row in df.iterrows():
            cleaned = {k: str(v).strip() for k, v in row.items()}

            # Skip rows where all values are empty
            if not any(v for v in cleaned.values()):
                continue

            # Add sheet name as classification hint for the extractor
            cleaned["_sheet"] = sheet_name
            records.append(cleaned)

    print(f"  [Excel Parser] {len(records)} row(s) extracted from '{filepath}' "
          f"({len(xl.sheet_names)} sheet(s))")
    return records