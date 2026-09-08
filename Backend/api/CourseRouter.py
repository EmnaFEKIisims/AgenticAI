# api/CourseRouter.py
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from db.DB import SessionLocal
from Services.CRUD.Repositories.course_repository import CourseRepository
from Services.CRUD.schemas.course import CourseCreate, CourseUpdate, CourseResponse
import os
SUPERADMIN_ID = os.getenv("SUPERADMIN_ID", "00000000-0000-0000-0000-000000000001")

router = APIRouter(prefix="/courses", tags=["Courses"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def get_user_id(x_user_id: str = Header(default=SUPERADMIN_ID)) -> str:
    return x_user_id

@router.post("", response_model=CourseResponse, status_code=201)
def create_course(body: CourseCreate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return CourseRepository(db).create(body.model_dump(), user_id)

@router.get("", response_model=list[CourseResponse])
def list_courses(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return CourseRepository(db).get_all(user_id)

@router.get("/{cid}", response_model=CourseResponse)
def get_course(cid: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    c = CourseRepository(db).get_by_id(cid, user_id)
    if not c: raise HTTPException(404, detail=f"Course {cid} not found.")
    return c

@router.put("/{cid}", response_model=CourseResponse)
def update_course(cid: int, body: CourseUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    updated = CourseRepository(db).update(cid, body.model_dump(exclude_none=True), user_id)
    if not updated: raise HTTPException(404, detail=f"Course {cid} not found.")
    return updated

@router.delete("/{cid}")
def delete_course(cid: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    try:
        ok = CourseRepository(db).delete(cid, user_id)
        if not ok: raise HTTPException(404, detail=f"Course {cid} not found.")
        return {"success": True}
    except ValueError as e: raise HTTPException(409, detail=str(e))