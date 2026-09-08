# api/LearnerGroupRouter.py
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from db.DB import SessionLocal
from Services.CRUD.Repositories.learner_group_repository import LearnerGroupRepository
from Services.CRUD.schemas.learner_group import LearnerGroupCreate, LearnerGroupUpdate, LearnerGroupResponse
import os
SUPERADMIN_ID = os.getenv("SUPERADMIN_ID", "00000000-0000-0000-0000-000000000001")

router = APIRouter(prefix="/learner-groups", tags=["Learner Groups"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def get_user_id(x_user_id: str = Header(default=SUPERADMIN_ID)) -> str:
    return x_user_id

@router.post("", response_model=LearnerGroupResponse, status_code=201)
def create_group(body: LearnerGroupCreate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return LearnerGroupRepository(db).create(body.model_dump(), user_id)

@router.get("", response_model=list[LearnerGroupResponse])
def list_groups(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return LearnerGroupRepository(db).get_all(user_id)

@router.get("/{gid}", response_model=LearnerGroupResponse)
def get_group(gid: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    g = LearnerGroupRepository(db).get_by_id(gid, user_id)
    if not g: raise HTTPException(404, detail=f"Group {gid} not found.")
    return g

@router.put("/{gid}", response_model=LearnerGroupResponse)
def update_group(gid: int, body: LearnerGroupUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    updated = LearnerGroupRepository(db).update(gid, body.model_dump(exclude_none=True), user_id)
    if not updated: raise HTTPException(404, detail=f"Group {gid} not found.")
    return updated

@router.delete("/{gid}")
def delete_group(gid: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    try:
        ok = LearnerGroupRepository(db).delete(gid, user_id)
        if not ok: raise HTTPException(404, detail=f"Group {gid} not found.")
        return {"success": True}
    except ValueError as e: raise HTTPException(409, detail=str(e))