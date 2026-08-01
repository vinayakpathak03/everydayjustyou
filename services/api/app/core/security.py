from dataclasses import dataclass

import jwt
from fastapi import Depends, Header, HTTPException, status

from app.core.config import get_settings


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str | None
    role: str


def _decode_supabase_jwt(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"type": "unauthorized", "title": "Invalid or expired session", "status": 401},
        ) from exc


async def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    """Validates the Supabase-issued JWT on every request.

    This only authenticates the caller. Authorization (what they can see) is a
    database concern — see app.db.session.get_db, which sets this user's identity
    as a transaction-local claim so Postgres RLS enforces isolation, rather than
    trusting the app layer alone. See docs/architecture/database-schema.md §9.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"type": "unauthorized", "title": "Missing bearer token", "status": 401},
        )
    token = authorization.split(" ", 1)[1]
    claims = _decode_supabase_jwt(token)
    return CurrentUser(
        id=claims["sub"],
        email=claims.get("email"),
        role=claims.get("role", "authenticated"),
    )


async def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """The entire 'admin' model at this scale: an allowlist of the developer's own
    email(s), checked against the verified JWT claim. See docs/PRD.md §1a — signup
    is invite-only and the developer is the one issuing invites, not a role system."""
    settings = get_settings()
    if not user.email or user.email.lower() not in settings.admin_email_set:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"type": "forbidden", "title": "Admin-only endpoint", "status": 403},
        )
    return user


async def verify_cron_secret(x_cron_secret: str | None = Header(default=None)) -> None:
    """Auth for /internal/cron/* — a shared secret header from the GitHub Actions
    schedule: workflow, not a user JWT. See system-architecture.md §4."""
    settings = get_settings()
    if not settings.cron_shared_secret or x_cron_secret != settings.cron_shared_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"type": "unauthorized", "title": "Invalid cron secret", "status": 401},
        )
