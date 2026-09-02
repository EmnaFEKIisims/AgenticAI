"""
api/UserRouter.py
==================
User management endpoints (no login required).
The frontend calls POST /users/register on first visit.

Endpoints:
  POST /users/register   → create or update user from localStorage UUID
  GET  /users/{id}       → get user info
  PUT  /users/{id}       → update display name / role
  GET  /users            → list all users (admin)
"""

import traceback
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.DB import SessionLocal
from Services.RAG.repositories.user_repository import UserRepository
from Services.RAG.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=UserResponse)
def register_user(body: UserCreate, db: Session = Depends(get_db)):
    """
    Called by the frontend on first visit (or when UUID is detected in localStorage).
    Creates a new user if the UUID doesn't exist, otherwise updates last_seen.

    Frontend sends:
      { "id": "<uuid-from-localStorage>", "display_name": "Administrator" }
    """
    try:
        repo = UserRepository(db)
        user = repo.get_or_create(body.id, body.display_name or "Administrator")
        return user
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Returns user info. Returns 404 if user doesn't exist yet."""
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(404, detail=f"User {user_id} not found. Call POST /users/register first.")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, body: UserUpdate, db: Session = Depends(get_db)):
    """Updates user display name or role."""
    try:
        user = UserRepository(db).update(user_id, body.display_name, body.role)
        if not user:
            raise HTTPException(404, detail=f"User {user_id} not found.")
        return user
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.get("", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    """Lists all active users."""
    try:
        return UserRepository(db).list_all()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))