"""
repositories/user_repository.py
================================
DB operations for User model.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models.user import User, UserRole


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_or_create(self, user_id: str, display_name: str = "Administrator") -> User:
        """
        Gets an existing user or creates a new one.
        Called on every RAG request from the frontend.
        """
        user = self.get_by_id(user_id)
        if user:
            user.last_seen_at = datetime.now(timezone.utc)
            self.db.commit()
            return user

        user = User(
            id           = user_id,
            display_name = display_name,
            role         = UserRole.ADMIN,
            is_active    = True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        print(f"  [UserRepo] New user created: {user_id[:8]}... ({display_name})")
        return user

    def update(self, user_id: str, display_name: str = None, role: str = None) -> User | None:
        user = self.get_by_id(user_id)
        if not user:
            return None
        if display_name:
            user.display_name = display_name
        if role:
            user.role = UserRole(role)
        self.db.commit()
        return user

    def list_all(self, limit: int = 100) -> list[User]:
        return self.db.query(User).filter(User.is_active == True).limit(limit).all()

    def deactivate(self, user_id: str) -> bool:
        user = self.get_by_id(user_id)
        if not user:
            return False
        user.is_active = False
        self.db.commit()
        return True