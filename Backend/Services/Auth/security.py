"""
Services/Auth/security.py
===========================
get_current_user : vérifie l'access_token Keycloak reçu dans le header
Authorization, puis synchronise (crée/mets à jour) la copie locale de
l'utilisateur dans notre table `users` — nécessaire pour les relations
FK (memories, documents...) ailleurs dans l'app.

SUPERADMIN : tout le projet est déjà lié à un UUID fixe (SUPERADMIN_ID
dans .env). Pour que ce lien ne se casse pas une fois qu'on passe par
Keycloak, le PREMIER login dont l'email correspond à SUPERADMIN_EMAIL
(.env) "récupère" ce même UUID fixe au lieu de s'en faire attribuer un
nouveau — tout l'historique (memories, documents...) reste donc accessible.
"""

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from db.DB import SessionLocal
from models.user import User, UserRole, AuthProvider
from Services.Auth import keycloak_client

bearer_scheme = HTTPBearer(auto_error=False)

SUPERADMIN_ID    = os.getenv("SUPERADMIN_ID", "")
SUPERADMIN_EMAIL = os.getenv("SUPERADMIN_EMAIL", "").strip().lower()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _sync_local_user(db: Session, payload: dict) -> User:
    """Crée ou met à jour la copie locale de l'utilisateur à partir du token Keycloak."""
    sub          = payload["sub"]
    email        = payload.get("email")
    display_name = payload.get("name") or payload.get("preferred_username") or (email.split("@")[0] if email else "User")

    # ── Cas 1 : déjà synchronisé avant (même keycloak_sub) ──────────────────
    user = db.query(User).filter(User.keycloak_sub == sub).first()
    if user:
        user.last_seen_at = datetime.now(timezone.utc)
        if email and user.email != email:
            user.email = email
        if display_name and user.display_name != display_name:
            user.display_name = display_name
        db.commit()
        return user

    # ── Cas 2 : c'est l'email du super-admin -> on récupère/crée le compte
    #            avec l'UUID FIXE auquel tout le projet est déjà lié ────────
    if SUPERADMIN_ID and SUPERADMIN_EMAIL and email and email.strip().lower() == SUPERADMIN_EMAIL:
        superadmin = db.query(User).filter(User.id == SUPERADMIN_ID).first()
        if superadmin:
            superadmin.keycloak_sub  = sub
            superadmin.email         = email
            superadmin.display_name  = display_name
            superadmin.auth_provider = AuthProvider.KEYCLOAK.value
            superadmin.role          = UserRole.ADMIN.value
            superadmin.is_active     = True
            superadmin.is_verified   = True
            superadmin.last_seen_at  = datetime.now(timezone.utc)
            db.commit()
            print(f"  [Auth] SUPERADMIN relié à Keycloak : {display_name} ({email}) -> id={SUPERADMIN_ID}")
            return superadmin

        # la ligne n'existait pas encore -> on la crée avec l'UUID fixe
        superadmin = User(
            id            = SUPERADMIN_ID,
            keycloak_sub  = sub,
            email         = email,
            auth_provider = AuthProvider.KEYCLOAK.value,
            display_name  = display_name,
            avatar_url    = payload.get("picture"),
            role          = UserRole.ADMIN.value,
            is_active     = True,
            is_verified   = True,
        )
        db.add(superadmin)
        db.commit()
        db.refresh(superadmin)
        print(f"  [Auth] SUPERADMIN créé avec l'UUID fixe : {display_name} ({email}) -> id={SUPERADMIN_ID}")
        return superadmin

    # ── Cas 3 : utilisateur normal, premier login -> UUID généré aléatoirement ──
    user = User(
        keycloak_sub  = sub,
        email         = email,
        auth_provider = AuthProvider.KEYCLOAK.value,
        display_name  = display_name,
        avatar_url    = payload.get("picture"),
        role          = UserRole.ADMIN.value,
        is_active     = True,
        is_verified   = True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"  [Auth] Nouvel utilisateur Keycloak synchronisé localement : {display_name} ({email})")
    return user


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                             detail="Not authenticated. Send 'Authorization: Bearer <token>'.")

    try:
        payload = keycloak_client.verify_access_token(credentials.credentials)
    except JWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=f"Invalid or expired token: {e}")

    user = _sync_local_user(db, payload)

    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="This account is disabled.")
    return user


def require_role(*allowed_roles: str):
    """
    Dépendance RBAC optionnelle. Usage sur une route :
        @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
    """
    def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN,
                                 detail=f"Requires role: {', '.join(allowed_roles)}")
        return user
    return _check