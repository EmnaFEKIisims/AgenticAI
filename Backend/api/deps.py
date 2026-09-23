"""
api/deps.py
===========
Shared FastAPI dependencies.

get_current_user_id() reads the "X-User-ID" header that the frontend's
src/services/api.ts ALREADY sends on every single request (it was just
never consumed by the Anomaly/Notification routers — that's the real bug).

Today this is a simple header read. Tomorrow, when Keycloak is wired in,
you swap ONLY this function's body for real JWT parsing — every router
that uses Depends(get_current_user_id) keeps working unchanged.

get_db() did NOT exist anywhere in your project (db/DB.py only defines
engine / SessionLocal / Base) — it's added here, next to
get_current_user_id, so both dependencies live in one place and no
existing backend file has to change.
"""

from fastapi import Header, HTTPException

from db.DB import SessionLocal


def get_db():
    """Yields a SQLAlchemy session and always closes it, even on error."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_id(
    x_user_id: str | None = Header(default=None, alias="X-User-ID"),
) -> str:
    """
    Returns the UUID (string) of the user making the request.

    Raises 401 if the header is missing — this makes it IMPOSSIBLE for a
    route to silently fall back to some default/admin id and lose the
    per-user scoping that this whole milestone is about.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=401,
            detail="Missing X-User-ID header — user is not identified.",
        )
    return x_user_id