# api/RoomRouter.py
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from db.DB import SessionLocal
from Services.CRUD.Repositories.room_repository import RoomRepository
from Services.CRUD.schemas.room import RoomCreate, RoomUpdate, RoomResponse
import os
SUPERADMIN_ID = os.getenv("SUPERADMIN_ID", "00000000-0000-0000-0000-000000000001")

router = APIRouter(prefix="/rooms", tags=["Rooms"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def get_user_id(x_user_id: str = Header(default=SUPERADMIN_ID)) -> str:
    """Gets user_id from X-User-ID header. Defaults to SUPERADMIN. After Keycloak: replace with Depends(get_current_user).id"""
    return x_user_id

@router.post("", response_model=RoomResponse, status_code=201)
def create_room(body: RoomCreate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    try: return RoomRepository(db).create(body.model_dump(), user_id)
    except Exception as e: raise HTTPException(500, detail=str(e))

@router.get("", response_model=list[RoomResponse])
def list_rooms(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return RoomRepository(db).get_all(user_id)

@router.get("/{room_id}", response_model=RoomResponse)
def get_room(room_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    room = RoomRepository(db).get_by_id(room_id, user_id)
    if not room: raise HTTPException(404, detail=f"Room {room_id} not found.")
    return room

@router.put("/{room_id}", response_model=RoomResponse)
def update_room(room_id: int, body: RoomUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    updated = RoomRepository(db).update(room_id, body.model_dump(exclude_none=True), user_id)
    if not updated: raise HTTPException(404, detail=f"Room {room_id} not found.")
    return updated

@router.delete("/{room_id}")
def delete_room(room_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    try:
        ok = RoomRepository(db).delete(room_id, user_id)
        if not ok: raise HTTPException(404, detail=f"Room {room_id} not found.")
        return {"success": True}
    except ValueError as e: raise HTTPException(409, detail=str(e))