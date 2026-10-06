"""
api/AuthRouter.py
===================
Auth via Keycloak. Keycloak héberge lui-même les pages de login/register
et la fédération Google/GitHub (configurées dans son admin console, pas
ici). Ce router se contente de :
  - rediriger vers la page de login Keycloak            -> /auth/login
  - récupérer le code et l'échanger contre des tokens    -> /auth/callback
  - rafraîchir un access_token expiré                    -> /auth/refresh
  - renvoyer l'utilisateur courant                        -> /auth/me
  - déconnecter (invalide la session Keycloak)            -> /auth/logout

Monte ce router dans main.py :
    from api.AuthRouter import router as auth_router
    app.include_router(auth_router)

Note sur le "state" anti-CSRF : stocké en mémoire côté serveur (pas en
cookie) — un cookie se perd facilement sur la chaîne de redirections
multi-origines backend -> Keycloak -> Google/GitHub -> Keycloak -> backend,
selon le navigateur/les réglages de confidentialité. En mémoire process,
ça suffit pour un usage dev/mono-instance.
"""

import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.DB import SessionLocal
from fastapi.responses import RedirectResponse
from Services.Auth import keycloak_client
from Services.Auth.security import get_current_user, get_db
from models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

STATE_TTL_SECONDS = 600  # 10 min, le temps de faire le round-trip OAuth
_pending_states: dict[str, float] = {}  # state -> timestamp d'émission


def _issue_state() -> str:
    # purge les states expirés à chaque émission (évite une fuite mémoire lente)
    now = time.time()
    expired = [s for s, ts in _pending_states.items() if now - ts > STATE_TTL_SECONDS]
    for s in expired:
        _pending_states.pop(s, None)

    state = str(uuid.uuid4())
    _pending_states[state] = now
    return state


def _consume_state(state: str) -> bool:
    ts = _pending_states.pop(state, None)
    if ts is None:
        return False
    return (time.time() - ts) <= STATE_TTL_SECONDS


@router.get("/login")
def login():
    """Redirige vers la page de login Keycloak (avec les boutons Google/GitHub)."""
    state = _issue_state()
    return RedirectResponse(keycloak_client.build_login_url(state))


@router.get("/callback")
def callback(code: str, state: str, db: Session = Depends(get_db)):
    if not _consume_state(state):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                             detail="State OAuth invalide ou expiré — réessaie de te connecter depuis /auth/login.")

    try:
        tokens = keycloak_client.exchange_code(code)
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Échec de l'échange du code Keycloak : {e}")

    frontend_url = (
        f"{keycloak_client.FRONTEND_URL}/auth/callback"
        f"?access_token={tokens['access_token']}&refresh_token={tokens['refresh_token']}"
    )
    return RedirectResponse(frontend_url)


@router.post("/refresh")
def refresh(refresh_token: str):
    try:
        tokens = keycloak_client.refresh_access_token(refresh_token)
    except Exception as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=f"Refresh token invalide/expiré : {e}")
    return {
        "access_token":  tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "token_type":    "bearer",
    }


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id":            current_user.id,
        "email":         current_user.email,
        "display_name":  current_user.display_name,
        "role":          current_user.role,
        "auth_provider": current_user.auth_provider,
        "avatar_url":    current_user.avatar_url,
        "is_verified":   current_user.is_verified,
        "created_at":    current_user.created_at,
    }


@router.get("/logout")
def logout():
    """Redirige vers l'endpoint de logout Keycloak, qui termine la session SSO."""
    return RedirectResponse(keycloak_client.build_logout_url(keycloak_client.FRONTEND_URL))