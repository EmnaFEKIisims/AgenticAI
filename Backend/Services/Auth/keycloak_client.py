"""
Services/Auth/keycloak_client.py
===================================
Helpers pour parler à Keycloak : construire l'URL de login, échanger le
"code" contre des tokens, rafraîchir un token, et vérifier la signature
d'un access_token émis par Keycloak (via son endpoint JWKS).

Keycloak gère lui-même : le formulaire login/register, le mot de passe,
ET la fédération vers Google/GitHub (configurée dans l'admin console de
Keycloak, PAS dans ce code — voir les instructions fournies à côté).
Notre backend ne fait QUE :
  1. rediriger vers la page de login hébergée par Keycloak
  2. échanger le code contre un access_token/refresh_token
  3. vérifier la signature des tokens reçus sur les requêtes suivantes

Env vars requises (.env) :
  KEYCLOAK_URL            = http://localhost:8080
  KEYCLOAK_REALM          = agentic-ai
  KEYCLOAK_CLIENT_ID      = agentic-ai-backend
  KEYCLOAK_CLIENT_SECRET  = <généré par Keycloak quand tu crées le Client>
  KEYCLOAK_REDIRECT_URI   = http://localhost:8000/auth/callback
  FRONTEND_URL            = http://localhost:5173
"""

import os
import time
from urllib.parse import urlencode

import httpx
from jose import jwt, JWTError

KEYCLOAK_URL           = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM         = os.getenv("KEYCLOAK_REALM", "agentic-ai")
KEYCLOAK_CLIENT_ID     = os.getenv("KEYCLOAK_CLIENT_ID", "agentic-ai-backend")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "")
KEYCLOAK_REDIRECT_URI  = os.getenv("KEYCLOAK_REDIRECT_URI", "http://localhost:8000/auth/callback")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

REALM_BASE     = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"
AUTH_URL       = f"{REALM_BASE}/protocol/openid-connect/auth"
TOKEN_URL      = f"{REALM_BASE}/protocol/openid-connect/token"
LOGOUT_URL     = f"{REALM_BASE}/protocol/openid-connect/logout"
USERINFO_URL   = f"{REALM_BASE}/protocol/openid-connect/userinfo"
JWKS_URL       = f"{REALM_BASE}/protocol/openid-connect/certs"

# cache en mémoire des clés publiques de Keycloak (évite de refetch à chaque requête)
_jwks_cache = {"keys": None, "fetched_at": 0}
_JWKS_TTL_SECONDS = 3600


def build_login_url(state: str) -> str:
    """URL vers la page de login hébergée par Keycloak (avec les boutons Google/GitHub)."""
    params = {
        "client_id":     KEYCLOAK_CLIENT_ID,
        "redirect_uri":  KEYCLOAK_REDIRECT_URI,
        "response_type": "code",
        "scope":         "openid email profile",
        "state":         state,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def build_logout_url(redirect_uri: str = None) -> str:
    params = {"client_id": KEYCLOAK_CLIENT_ID}
    if redirect_uri:
        params["post_logout_redirect_uri"] = redirect_uri
    return f"{LOGOUT_URL}?{urlencode(params)}"


def exchange_code(code: str) -> dict:
    """Échange le code reçu sur /auth/callback contre access_token/refresh_token."""
    data = {
        "grant_type":    "authorization_code",
        "code":          code,
        "client_id":     KEYCLOAK_CLIENT_ID,
        "client_secret": KEYCLOAK_CLIENT_SECRET,
        "redirect_uri":  KEYCLOAK_REDIRECT_URI,
    }
    resp = httpx.post(TOKEN_URL, data=data, timeout=15)
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(refresh_token: str) -> dict:
    data = {
        "grant_type":    "refresh_token",
        "refresh_token": refresh_token,
        "client_id":     KEYCLOAK_CLIENT_ID,
        "client_secret": KEYCLOAK_CLIENT_SECRET,
    }
    resp = httpx.post(TOKEN_URL, data=data, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _get_jwks() -> list:
    now = time.time()
    if _jwks_cache["keys"] is not None and (now - _jwks_cache["fetched_at"]) < _JWKS_TTL_SECONDS:
        return _jwks_cache["keys"]

    resp = httpx.get(JWKS_URL, timeout=15)
    resp.raise_for_status()
    keys = resp.json()["keys"]
    _jwks_cache["keys"] = keys
    _jwks_cache["fetched_at"] = now
    return keys


def verify_access_token(token: str) -> dict:
    """
    Vérifie la signature RS256 d'un access_token émis par Keycloak et
    renvoie son payload décodé (contient sub, email, name, preferred_username...).
    Lève jose.JWTError si invalide/expiré.
    """
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    jwks = _get_jwks()
    key = next((k for k in jwks if k["kid"] == kid), None)
    if key is None:
        # la clé a peut-être tourné — on refetch une fois avant d'abandonner
        _jwks_cache["keys"] = None
        jwks = _get_jwks()
        key = next((k for k in jwks if k["kid"] == kid), None)
        if key is None:
            raise JWTError("Signing key not found in Keycloak JWKS.")

    payload = jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience=KEYCLOAK_CLIENT_ID,
        options={"verify_aud": False},  # Keycloak ne met pas toujours notre client_id dans "aud"
        issuer=REALM_BASE,
    )
    return payload