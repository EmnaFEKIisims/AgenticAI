"""
api/data_upload_router.py
==========================
Data Manager Upload API — 5 endpoints.

The router calls DataAgent — nothing else.

  POST /data/upload          -> DataAgent.process_file()
  GET  /data/preview/{id}    -> TempStorage.get()
  POST /data/validate/{id}   -> DataAgent.commit()
  POST /data/reject/{id}     -> DataAgent.reject()
  PUT  /data/update/{id}     -> TempStorage.update_data()
"""

import os
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.DB import SessionLocal
from agents.Data_Manager import DataAgent
from Services.DataManager.Temp_storage import TempStorage


router  = APIRouter(prefix="/data", tags=["Data Manager"])
storage = TempStorage()
agent   = DataAgent(storage)          # single agent instance, shared across requests

UPLOAD_TMP_DIR     = "outputs/uploads"
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".pdf"}


# =============================================================================
#  DB Dependency
# =============================================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================================================================
#  Schemas
# =============================================================================

class UploadResponse(BaseModel):
    upload_id:     str
    filename:      str
    status:        str          # "pending_review"
    total_raw:     int          # rows extracted from file
    total_valid:   int          # rows that passed validation
    total_invalid: int          # rows with issues
    preview:       list[dict]   # first 5 valid records
    issues:        list[dict]   # validation issues to show to user


class PreviewResponse(BaseModel):
    upload_id:  str
    filename:   str
    status:     str
    total_rows: int
    data:       list[dict]


class ValidateResponse(BaseModel):
    success:   bool
    upload_id: str
    message:   str
    inserted:  dict             # { "courses": 2, "trainers": 3, ... }


class RejectResponse(BaseModel):
    success:   bool
    upload_id: str
    message:   str


class UpdateRequest(BaseModel):
    data: list[dict]            # corrected rows sent by the user


class UpdateResponse(BaseModel):
    success:    bool
    upload_id:  str
    total_rows: int
    message:    str


# =============================================================================
#  ENDPOINT 1 — POST /data/upload
# =============================================================================

@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload a file (CSV, Excel, PDF) — parse, extract, validate, store",
)
async def upload_file(file: UploadFile = File(...)):
    """
    Full pipeline in one call:
    1. Parse the file (CSV / Excel / PDF)
    2. LLM extracts + classifies entities
    3. Transform to DB schema
    4. Validate fields
    5. Store in temp memory (status = "pending_review")

    Returns upload_id + preview + any validation issues.
    Next step: GET /data/preview/{id}, then POST /data/validate/{id}.
    """
    filename = file.filename or "upload"
    ext      = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported format '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Save uploaded file to disk temporarily for parsing
    os.makedirs(UPLOAD_TMP_DIR, exist_ok=True)
    tmp_path = os.path.join(UPLOAD_TMP_DIR, f"{uuid.uuid4().hex}_{filename}")

    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        result = agent.process_file(tmp_path, filename)   # DataAgent handles steps 1-6
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    if not result.success:
        raise HTTPException(status_code=422, detail=result.error)

    return UploadResponse(
        upload_id     = result.upload_id,
        filename      = result.filename,
        status        = "pending_review",
        total_raw     = result.total_raw,
        total_valid   = result.total_valid,
        total_invalid = result.total_invalid,
        preview       = result.preview,
        issues        = result.issues,
    )


# =============================================================================
#  ENDPOINT 2 — GET /data/preview/{id}
# =============================================================================

@router.get(
    "/preview/{upload_id}",
    response_model=PreviewResponse,
    summary="Preview extracted data before validation",
)
def preview_data(upload_id: str):
    """
    Returns the full extracted dataset for a given upload ID.
    Review all rows before deciding to validate, correct or reject.
    """
    entry = storage.get(upload_id)
    if not entry:
        raise HTTPException(
            status_code=404,
            detail=f"Upload ID '{upload_id}' not found or already processed."
        )

    return PreviewResponse(
        upload_id  = upload_id,
        filename   = entry["filename"],
        status     = entry["status"],
        total_rows = len(entry["data"]),
        data       = entry["data"],
    )


# =============================================================================
#  ENDPOINT 3 — POST /data/validate/{id}   ⭐ HITL
# =============================================================================

@router.post(
    "/validate/{upload_id}",
    response_model=ValidateResponse,
    summary="HITL — user approves data → insert into database",
)
def validate_data(upload_id: str, db: Session = Depends(get_db)):
    """
    Human-In-The-Loop validation.
    User approves the extracted data → DataAgent loads it into PostgreSQL.
    Status: "pending_review" or "corrected" → "approved".
    """
    entry = storage.get(upload_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Upload ID '{upload_id}' not found.")
    if entry["status"] not in ("pending_review", "corrected"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot validate data with status '{entry['status']}'."
        )

    try:
        inserted = agent.commit(upload_id, db)     # DataAgent handles DB insertion
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB insertion failed: {str(e)}")

    return ValidateResponse(
        success   = True,
        upload_id = upload_id,
        message   = "Data validated and inserted into the database.",
        inserted  = inserted,
    )


# =============================================================================
#  ENDPOINT 4 — POST /data/reject/{id}
# =============================================================================

@router.post(
    "/reject/{upload_id}",
    response_model=RejectResponse,
    summary="Reject extracted data and clear it from temp storage",
)
def reject_data(upload_id: str):
    """
    User rejects the extracted data.
    Entry is cleared from temp storage.
    Upload a new corrected file to retry.
    """
    entry = storage.get(upload_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Upload ID '{upload_id}' not found.")

    agent.reject(upload_id)                        # DataAgent handles cleanup

    return RejectResponse(
        success   = True,
        upload_id = upload_id,
        message   = "Data rejected and cleared. Upload a new file to retry.",
    )


# =============================================================================
#  ENDPOINT 5 — PUT /data/update/{id}
# =============================================================================

@router.put(
    "/update/{upload_id}",
    response_model=UpdateResponse,
    summary="Manually correct extracted data before validation",
)
def update_data(upload_id: str, body: UpdateRequest):
    """
    User corrects the extracted data manually.
    Sends the full corrected dataset — replaces current temp data.
    Status → "corrected".
    Then call POST /data/validate/{id} to insert into DB.
    """
    entry = storage.get(upload_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Upload ID '{upload_id}' not found.")
    if entry["status"] not in ("pending_review", "corrected"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot update data with status '{entry['status']}'."
        )

    storage.update_data(upload_id, body.data)
    storage.update_status(upload_id, "corrected")

    return UpdateResponse(
        success    = True,
        upload_id  = upload_id,
        total_rows = len(body.data),
        message    = f"Data updated ({len(body.data)} row(s)). Call /validate to insert into DB.",
    )