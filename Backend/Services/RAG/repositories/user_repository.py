"""
Services/RAG/repositories/user_repository.py
===============================================
DB operations for User model — ère Keycloak :
  - les comptes réels (local/Google/GitHub) sont synchronisés automatiquement
    par Services/Auth/security.py._sync_local_user() à chaque requête authentifiée
    (pas besoin de create_local_user / create_oauth_user ici)
  - get_or_create() reste pour le flow legacy RAG "system" (terminal mode /
    DEFAULT_TERMINAL_USER_ID), qui n'a jamais été relié à un vrai login
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models.user import User, UserRole, AuthProvider


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    # ── Lookups ─────────────────────────────────────────────────────────────

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> User | None:
        if not email:
            return None
        return self.db.query(User).filter(User.email == email).first()

    def get_by_keycloak_sub(self, sub: str) -> User | None:
        return self.db.query(User).filter(User.keycloak_sub == sub).first()

    # ── Legacy system/anonymous accounts (RAG terminal mode) ──────────────────

    def get_or_create(self, user_id: str, display_name: str = "Administrator") -> User:
        """
        Utilisé par RAGService.ensure_user() pour le flow terminal/orchestrateur,
        où il n'y a pas de vrai login — juste un UUID système fixe
        (DEFAULT_TERMINAL_USER_ID). keycloak_sub et email restent NULL ;
        Postgres autorise plusieurs NULL sous une contrainte UNIQUE, donc ça
        ne collisionne jamais avec un vrai utilisateur Keycloak.
        """
        user = self.get_by_id(user_id)
        if user:
            user.last_seen_at = datetime.now(timezone.utc)
            self.db.commit()
            return user

        user = User(
            id            = user_id,
            display_name  = display_name,
            auth_provider = AuthProvider.SYSTEM.value,
            role          = UserRole.ADMIN.value,
            is_active     = True,
            is_verified   = True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        print(f"  [UserRepo] New system user created: {user_id[:8]}... ({display_name})")
        return user

    # ── Admin / general ────────────────────────────────────────────────────────

    def update(self, user_id: str, display_name: str = None, role: str = None) -> User | None:
        user = self.get_by_id(user_id)
        if not user:
            return None
        if display_name:
            user.display_name = display_name
        if role:
            user.role = UserRole(role).value
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