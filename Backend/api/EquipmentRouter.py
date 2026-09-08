# api/EquipmentRouter.py
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from db.DB import SessionLocal
from Services.CRUD.Repositories.equipment_repository import EquipmentRepository
from Services.CRUD.schemas.equipment import EquipmentCreate, EquipmentUpdate, EquipmentResponse
import os
SUPERADMIN_ID = os.getenv("SUPERADMIN_ID", "00000000-0000-0000-0000-000000000001")

router = APIRouter(prefix="/equipment", tags=["Equipment"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def get_user_id(x_user_id: str = Header(default=SUPERADMIN_ID)) -> str:
    return x_user_id

@router.post("", response_model=EquipmentResponse, status_code=201)
def create_equipment(body: EquipmentCreate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return EquipmentRepository(db).create(body.model_dump(), user_id)

@router.get("", response_model=list[EquipmentResponse])
def list_equipment(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return EquipmentRepository(db).get_all(user_id)

@router.get("/{eid}", response_model=EquipmentResponse)
def get_equipment(eid: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    eq = EquipmentRepository(db).get_by_id(eid, user_id)
    if not eq: raise HTTPException(404, detail=f"Equipment {eid} not found.")
    return eq

@router.put("/{eid}", response_model=EquipmentResponse)
def update_equipment(eid: int, body: EquipmentUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    updated = EquipmentRepository(db).update(eid, body.model_dump(exclude_none=True), user_id)
    if not updated: raise HTTPException(404, detail=f"Equipment {eid} not found.")
    return updated

@router.delete("/{eid}")
def delete_equipment(eid: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    ok = EquipmentRepository(db).delete(eid, user_id)
    if not ok: raise HTTPException(404, detail=f"Equipment {eid} not found.")
    return {"success": True}