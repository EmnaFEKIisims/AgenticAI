# api/TrainerRouter.py
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from db.DB import SessionLocal
from Services.CRUD.Repositories.trainer_repository import TrainerRepository
from Services.CRUD.schemas.trainer import TrainerCreate, TrainerUpdate, TrainerResponse
import os
SUPERADMIN_ID = os.getenv("SUPERADMIN_ID", "00000000-0000-0000-0000-000000000001")

router = APIRouter(prefix="/trainers", tags=["Trainers"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def get_user_id(x_user_id: str = Header(default=SUPERADMIN_ID)) -> str:
    return x_user_id

@router.post("", response_model=TrainerResponse, status_code=201)
def create_trainer(body: TrainerCreate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    repo = TrainerRepository(db)
    if repo.get_by_email(body.email, user_id):
        raise HTTPException(409, detail=f"Email {body.email} already exists.")
    return repo.create(body.model_dump(), user_id)

@router.get("", response_model=list[TrainerResponse])
def list_trainers(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return TrainerRepository(db).get_all(user_id)

@router.get("/{tid}", response_model=TrainerResponse)
def get_trainer(tid: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    t = TrainerRepository(db).get_by_id(tid, user_id)
    if not t: raise HTTPException(404, detail=f"Trainer {tid} not found.")
    return t

@router.put("/{tid}", response_model=TrainerResponse)
def update_trainer(tid: int, body: TrainerUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    updated = TrainerRepository(db).update(tid, body.model_dump(exclude_none=True), user_id)
    if not updated: raise HTTPException(404, detail=f"Trainer {tid} not found.")
    return updated

@router.delete("/{tid}")
def delete_trainer(tid: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    try:
        ok = TrainerRepository(db).delete(tid, user_id)
        if not ok: raise HTTPException(404, detail=f"Trainer {tid} not found.")
        return {"success": True}
    except ValueError as e: raise HTTPException(409, detail=str(e))