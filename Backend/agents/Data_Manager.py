"""
agents/Data_Manager.py
=======================
Updated DataAgent:
  - Passes user_id to DB_Loader so every inserted record is linked to its owner
  - Detects constraint files as an entity type (via LLM extractor)
  - Constraint records with source="user_defined" are user-specific
  - Constraint records with source="ISO_21001" are global (user_id=None)
"""

import os
from dataclasses import dataclass
from sqlalchemy.orm import Session

from Services.DataManager.Parsers.CSV_parser     import parse_csv
from Services.DataManager.Parsers.Excel_parser   import parse_excel
from Services.DataManager.Parsers.PDF_parser     import parse_pdf
from Services.DataManager.Extractor   import extract_entities
from Services.DataManager.Transformer import transform
from Services.DataManager.Validator   import validate, ValidationResult
from Services.DataManager.Temp_storage import TempStorage
from Services.DataManager.DB_Loader   import load_to_db


@dataclass
class UploadResult:
    success:        bool
    upload_id:      str
    filename:       str
    total_raw:      int
    total_valid:    int
    total_invalid:  int
    preview:        list[dict]
    issues:         list[dict]
    error:          str = ""


class DataAgent:

    def __init__(self, storage: TempStorage):
        self.storage = storage

    # ── Steps 1-6 ─────────────────────────────────────────────────────────────

    def process_file(self, filepath: str, filename: str) -> UploadResult:
        print(f"\n{'='*60}")
        print(f"  [DataAgent] Processing: {filename}")
        print(f"{'='*60}")

        print("\n[1/5] Parsing file...")
        try:
            raw_records = self._parse(filepath, filename)
        except Exception as e:
            return UploadResult(False, "", filename, 0, 0, 0, [], [], f"Parse error: {e}")

        print(f"  -> {len(raw_records)} raw record(s).")
        if not raw_records:
            return UploadResult(False, "", filename, 0, 0, 0, [], [], "No data found.")

        print("\n[2/5] Extracting entities via LLM...")
        classified = extract_entities(raw_records)
        print(f"  -> {len(classified)} record(s) classified.")

        print("\n[3/5] Transforming to DB schema...")
        transformed = transform(classified)

        print("\n[4/5] Validating records...")
        validation: ValidationResult = validate(transformed)

        print("\n[5/5] Storing in temp storage...")
        upload_id = self.storage.save(
            filename = filename,
            data     = self._flatten(validation.valid),
        )
        print(f"  -> Upload ID: {upload_id}")

        issues_list = [
            {
                "entity_type": i.entity_type,
                "issues":      i.issues,
                "record":      {k: v for k, v in i.record.items() if not k.startswith("_")},
            }
            for i in validation.issues
        ]
        all_valid = self._flatten(validation.valid)
        preview   = [{k: v for k, v in r.items() if not k.startswith("_")} for r in all_valid[:5]]

        return UploadResult(
            success       = True,
            upload_id     = upload_id,
            filename      = filename,
            total_raw     = len(raw_records),
            total_valid   = len(all_valid),
            total_invalid = len(validation.issues),
            preview       = preview,
            issues        = issues_list,
        )

    # ── Step 8A — commit with user_id ─────────────────────────────────────────

    def commit(self, upload_id: str, db: Session, user_id: str) -> dict:
        """
        Loads approved data into DB.
        user_id is attached to every inserted record EXCEPT global ISO constraints.
        """
        entry = self.storage.get(upload_id)
        if not entry:
            raise ValueError(f"Upload ID '{upload_id}' not found.")
        if entry["status"] not in ("pending_review", "corrected"):
            raise ValueError(f"Cannot commit with status '{entry['status']}'.")

        print(f"\n  [DataAgent] Committing '{upload_id}' for user {user_id[:8]}... to DB...")
        report = load_to_db(entry["data"], db, user_id=user_id)
        self.storage.update_status(upload_id, "approved")
        print(f"  [DataAgent] Committed: {report}")
        return report

    # ── Step 8B — reject ──────────────────────────────────────────────────────

    def reject(self, upload_id: str):
        self.storage.update_status(upload_id, "rejected")
        self.storage.delete(upload_id)
        print(f"  [DataAgent] Upload '{upload_id}' rejected and cleared.")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _parse(self, filepath: str, filename: str) -> list[dict]:
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".csv":             return parse_csv(filepath)
        elif ext in (".xlsx",".xls"): return parse_excel(filepath)
        elif ext == ".pdf":           return parse_pdf(filepath)
        else: raise ValueError(f"Unsupported format: {ext}")

    def _flatten(self, grouped: dict) -> list[dict]:
        flat = []
        for key, records in grouped.items():
            entity_type = key.rstrip("s")
            for record in records:
                flat.append({"entity_type": entity_type, **record})
        return flat