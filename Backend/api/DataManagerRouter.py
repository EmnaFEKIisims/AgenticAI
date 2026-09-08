"""
api/data_upload_router.py
==========================
Updated: receives X-User-ID header and passes it to DataAgent.commit()
so every record inserted is linked to its owner.
"""

import os, shutil, uuid
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.DB import SessionLocal
from agents.Data_Manager import DataAgent
from Services.DataManager.Temp_storage import TempStorage
import os
SUPERADMIN_ID = os.getenv("SUPERADMIN_ID", "00000000-0000-0000-0000-000000000001")

router  = APIRouter(prefix="/data", tags=["Data Manager"])
storage = TempStorage()
agent   = DataAgent(storage)

UPLOAD_TMP_DIR     = "outputs/uploads"
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".pdf"}


def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def get_user_id(x_user_id: str = Header(default=SUPERADMIN_ID)) -> str:
    """
    Gets user_id from X-User-ID header.
    Frontend sends: headers: { 'X-User-ID': localStorage.getItem('rag_session_user_id') }
    After Keycloak: replace with current_user.id from JWT.
    """
    return x_user_id


# =============================================================================
#  Schemas
# =============================================================================

class UploadResponse(BaseModel):
    upload_id: str; filename: str; status: str
    total_raw: int; total_valid: int; total_invalid: int
    preview: list[dict]; issues: list[dict]

class PreviewResponse(BaseModel):
    upload_id: str; filename: str; status: str; total_rows: int; data: list[dict]

class ValidateResponse(BaseModel):
    success: bool; upload_id: str; message: str; inserted: dict

class RejectResponse(BaseModel):
    success: bool; upload_id: str; message: str

class UpdateRequest(BaseModel):
    data: list[dict]

class UpdateResponse(BaseModel):
    success: bool; upload_id: str; total_rows: int; message: str


# =============================================================================
#  ENDPOINT 1 — POST /data/upload
# =============================================================================

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file:    UploadFile = File(...),
    user_id: str        = Depends(get_user_id),
):
    filename = file.filename or "upload"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(415, detail=f"Unsupported format '{ext}'.")

    os.makedirs(UPLOAD_TMP_DIR, exist_ok=True)
    tmp = os.path.join(UPLOAD_TMP_DIR, f"{uuid.uuid4().hex}_{filename}")

    with open(tmp, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        result = agent.process_file(tmp, filename)
    except Exception as e:
        raise HTTPException(500, detail=f"Processing failed: {e}")
    finally:
        if os.path.exists(tmp): os.remove(tmp)

    if not result.success:
        raise HTTPException(422, detail=result.error)

    return UploadResponse(
        upload_id=result.upload_id, filename=result.filename,
        status="pending_review", total_raw=result.total_raw,
        total_valid=result.total_valid, total_invalid=result.total_invalid,
        preview=result.preview, issues=result.issues,
    )


# =============================================================================
#  ENDPOINT 2 — GET /data/preview/{id}
# =============================================================================

@router.get("/preview/{upload_id}", response_model=PreviewResponse)
def preview_data(upload_id: str):
    entry = storage.get(upload_id)
    if not entry:
        raise HTTPException(404, detail=f"Upload ID '{upload_id}' not found.")
    return PreviewResponse(
        upload_id=upload_id, filename=entry["filename"],
        status=entry["status"], total_rows=len(entry["data"]), data=entry["data"],
    )


# =============================================================================
#  ENDPOINT 3 — POST /data/validate/{id}  ← user_id passed to agent.commit()
# =============================================================================

@router.post("/validate/{upload_id}", response_model=ValidateResponse)
def validate_data(
    upload_id: str,
    db:        Session = Depends(get_db),
    user_id:   str     = Depends(get_user_id),
):
    """
    HITL approval → inserts data into DB with user_id on each record.
    """
    entry = storage.get(upload_id)
    if not entry:
        raise HTTPException(404, detail=f"Upload ID '{upload_id}' not found.")
    if entry["status"] not in ("pending_review", "corrected"):
        raise HTTPException(409, detail=f"Cannot validate with status '{entry['status']}'.")

    try:
        inserted = agent.commit(upload_id, db, user_id=user_id)   # ← user_id injected here
    except Exception as e:
        raise HTTPException(500, detail=f"DB insertion failed: {e}")

    return ValidateResponse(
        success=True, upload_id=upload_id,
        message="Data validated and inserted into the database.",
        inserted=inserted,
    )


# =============================================================================
#  ENDPOINT 4 — POST /data/reject/{id}
# =============================================================================

@router.post("/reject/{upload_id}", response_model=RejectResponse)
def reject_data(upload_id: str):
    entry = storage.get(upload_id)
    if not entry: raise HTTPException(404, detail=f"Upload ID '{upload_id}' not found.")
    agent.reject(upload_id)
    return RejectResponse(success=True, upload_id=upload_id,
                          message="Data rejected and cleared.")


# =============================================================================
#  ENDPOINT 5 — PUT /data/update/{id}
# =============================================================================

@router.put("/update/{upload_id}", response_model=UpdateResponse)
def update_data(upload_id: str, body: UpdateRequest):
    entry = storage.get(upload_id)
    if not entry: raise HTTPException(404, detail=f"Upload ID '{upload_id}' not found.")
    if entry["status"] not in ("pending_review", "corrected"):
        raise HTTPException(409, detail=f"Cannot update with status '{entry['status']}'.")
    storage.update_data(upload_id, body.data)
    storage.update_status(upload_id, "corrected")
    return UpdateResponse(success=True, upload_id=upload_id,
                          total_rows=len(body.data),
                          message=f"Updated ({len(body.data)} rows). Call /validate to insert.")