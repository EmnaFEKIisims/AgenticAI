"""
agents/data_agent.py
=====================
Brain of the Data Manager pipeline.

Orchestrates all 8 steps:
  1. Detect file type -> choose parser
  2. Parse file -> raw records
  3. Extract entities via LLM -> classified records
  4. Transform -> DB-ready dicts
  5. Validate -> filter invalid records
  6. Store temporarily -> TempStorage (status: "pending_review")
  7. Wait for HITL decision (handled by the API router)
  8. On approval -> load into DB  |  On rejection -> clear storage

The agent is called by data_upload_router.py for steps 1-6.
Steps 7-8 are triggered by the /validate and /reject endpoints.
"""

import os
from dataclasses import dataclass
from sqlalchemy.orm import Session

from Services.DataManager.Parsers.CSV_parser     import parse_csv
from Services.DataManager.Parsers.Excel_parser   import parse_excel
from Services.DataManager.Parsers.PDF_parser     import parse_pdf
from Services.DataManager.Extractor import extract_entities
from Services.DataManager.Transformer import transform
from Services.DataManager.Validator import validate, ValidationResult
from Services.DataManager.Temp_storage import TempStorage
from Services.DataManager.DB_Loader  import load_to_db


# =============================================================================
#  Result type returned after upload + processing (steps 1-6)
# =============================================================================

@dataclass
class UploadResult:
    success:        bool
    upload_id:      str
    filename:       str
    total_raw:      int           # rows extracted from file
    total_valid:    int           # rows that passed validation
    total_invalid:  int           # rows with issues
    preview:        list[dict]    # first 5 valid records (for quick display)
    issues:         list[dict]    # validation issues to show to user
    error:          str = ""


# =============================================================================
#  DATA AGENT
# =============================================================================

class DataAgent:
    """
    Orchestrates the full Data Manager pipeline.

    Usage (called by upload endpoint):
        agent  = DataAgent(storage)
        result = agent.process_file(filepath, filename)
        # result.upload_id -> used by /preview, /validate, /reject, /update

    Usage (called by validate endpoint):
        agent.commit(upload_id, db)

    Usage (called by reject endpoint):
        agent.reject(upload_id)
    """

    def __init__(self, storage: TempStorage):
        self.storage = storage

    # ── STEP 1-6 : process uploaded file ─────────────────────────────────────

    def process_file(self, filepath: str, filename: str) -> UploadResult:
        """
        Runs the full pipeline from file to temp storage.
        Returns an UploadResult the router can send back to the frontend.
        """

        print(f"\n{'='*60}")
        print(f"  [DataAgent] Processing: {filename}")
        print(f"{'='*60}")

        # ── Step 1 + 2: Detect format + Parse ──────────────────────────────
        print("\n[1/5] Parsing file...")
        try:
            raw_records = self._parse(filepath, filename)
        except Exception as e:
            return UploadResult(
                success=False, upload_id="", filename=filename,
                total_raw=0, total_valid=0, total_invalid=0,
                preview=[], issues=[], error=f"Parse error: {e}"
            )
        print(f"  -> {len(raw_records)} raw record(s) extracted.")

        if not raw_records:
            return UploadResult(
                success=False, upload_id="", filename=filename,
                total_raw=0, total_valid=0, total_invalid=0,
                preview=[], issues=[], error="No data found in file."
            )

        # ── Step 3: Extract (LLM classifies records) ───────────────────────
        print("\n[2/5] Extracting entities via LLM...")
        classified = extract_entities(raw_records)
        print(f"  -> {len(classified)} record(s) classified.")

        # ── Step 4: Transform (map to DB schema) ───────────────────────────
        print("\n[3/5] Transforming to DB schema...")
        transformed = transform(classified)

        # ── Step 5: Validate ───────────────────────────────────────────────
        print("\n[4/5] Validating records...")
        validation: ValidationResult = validate(transformed)

        # ── Step 6: Store in temp storage ──────────────────────────────────
        print("\n[5/5] Storing in temp storage (pending review)...")
        upload_id = self.storage.save(
            filename = filename,
            data     = self._flatten(validation.valid),
        )
        print(f"  -> Upload ID: {upload_id}")

        # Build issues list for frontend display
        issues_list = [
            {
                "entity_type": issue.entity_type,
                "issues":      issue.issues,
                "record":      {k: v for k, v in issue.record.items()
                                if not k.startswith("_")},
            }
            for issue in validation.issues
        ]

        # First 5 valid records as preview
        all_valid = self._flatten(validation.valid)
        preview   = [{k: v for k, v in r.items() if not k.startswith("_")}
                     for r in all_valid[:5]]

        total_valid   = len(all_valid)
        total_invalid = len(validation.issues)

        print(f"\n  [DataAgent] Done: {total_valid} valid, {total_invalid} issue(s).")

        return UploadResult(
            success       = True,
            upload_id     = upload_id,
            filename      = filename,
            total_raw     = len(raw_records),
            total_valid   = total_valid,
            total_invalid = total_invalid,
            preview       = preview,
            issues        = issues_list,
        )

    # ── STEP 8A : HITL approved -> load to DB ─────────────────────────────────

    def commit(self, upload_id: str, db: Session) -> dict:
        """
        Called when user approves the data.
        Loads from temp storage into PostgreSQL.
        Returns insertion report.
        """
        entry = self.storage.get(upload_id)
        if not entry:
            raise ValueError(f"Upload ID '{upload_id}' not found.")
        if entry["status"] not in ("pending_review", "corrected"):
            raise ValueError(f"Cannot commit data with status '{entry['status']}'.")

        print(f"\n  [DataAgent] Committing upload '{upload_id}' to DB...")
        report = load_to_db(entry["data"], db)
        self.storage.update_status(upload_id, "approved")

        print(f"  [DataAgent] Committed: {report}")
        return report

    # ── STEP 8B : HITL rejected -> clear storage ──────────────────────────────

    def reject(self, upload_id: str):
        """
        Called when user rejects the data.
        Clears the entry from temp storage.
        """
        self.storage.update_status(upload_id, "rejected")
        self.storage.delete(upload_id)
        print(f"  [DataAgent] Upload '{upload_id}' rejected and cleared.")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _parse(self, filepath: str, filename: str) -> list[dict]:
        """Detects format and dispatches to the correct parser."""
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".csv":            return parse_csv(filepath)
        elif ext in (".xlsx",".xls"): return parse_excel(filepath)
        elif ext == ".pdf":          return parse_pdf(filepath)
        else:
            raise ValueError(f"Unsupported format: {ext}")

    def _flatten(self, grouped: dict) -> list[dict]:
        """
        Flattens a grouped dict into a flat list,
        adding 'entity_type' key to each record.
        e.g. {"courses": [...], "trainers": [...]} -> [{entity_type: "course", ...}, ...]
        """
        flat = []
        for key, records in grouped.items():
            entity_type = key.rstrip("s")  # "courses" -> "course"
            for record in records:
                flat.append({"entity_type": entity_type, **record})
        return flat