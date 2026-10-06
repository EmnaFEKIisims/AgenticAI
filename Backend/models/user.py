"""
models/user.py
===============
User model — identité gérée par Keycloak (email/mdp + Google + GitHub,
tout fédéré dans Keycloak). Ce backend ne stocke PLUS de mot de passe :
Keycloak s'en occupe. On garde ici une copie locale légère de chaque
utilisateur Keycloak, nécessaire pour les clés étrangères (memories,
documents, etc.) dans le reste de l'app.

- keycloak_sub : l'identifiant unique Keycloak ("sub" du token), stable
  quel que soit le provider (local, Google, GitHub) utilisé pour se
  connecter dans Keycloak.
- L'ancien flow RAG "anonyme" (terminal mode, DEFAULT_TERMINAL_USER_ID)
  continue de marcher : UserRepository.get_or_create() crée une ligne
  avec auth_provider="system", keycloak_sub=None.
"""

import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from db.DB import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN   = "admin"
    TRAINER = "trainer"
    STUDENT = "student"
    VIEWER  = "viewer"


class AuthProvider(str, enum.Enum):
    KEYCLOAK = "keycloak"  # couvre local/Google/GitHub, tous fédérés par Keycloak
    SYSTEM   = "system"    # legacy/terminal-mode anonyme, pas de vrai login


class User(Base):
    __tablename__ = "users"

    id            = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    keycloak_sub  = Column(String(255), unique=True, nullable=True, index=True)
    email         = Column(String(255), unique=True, nullable=True, index=True)
    auth_provider = Column(String(20), nullable=False, default=AuthProvider.KEYCLOAK.value)
    avatar_url    = Column(String(500), nullable=True)

    display_name  = Column(String(100), nullable=False, default="User")
    role          = Column(String(20), nullable=False, default="admin")
    is_active     = Column(Boolean, default=True)
    is_verified   = Column(Boolean, default=True)  # Keycloak a déjà vérifié l'email

    created_at    = Column(DateTime, server_default=func.now())
    last_seen_at  = Column(DateTime, nullable=True)