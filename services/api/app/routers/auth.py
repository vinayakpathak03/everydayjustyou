import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_user_db
from app.core.security import CurrentUser, get_current_user, require_admin
from app.db.session import get_admin_db
from app.models.invite import Invite
from app.models.user import User
from app.schemas.invite import InviteAccept, InviteCreate, InviteOut, InviteValidateOut
from app.schemas.user import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

INVITE_TTL_DAYS = 7


@router.post("/invites", response_model=InviteOut, status_code=status.HTTP_201_CREATED)
async def create_invite(
    body: InviteCreate,
    admin: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_user_db),
) -> Invite:
    """Dev-only: this is the entire signup surface. There is no public registration
    endpoint anywhere in this API — see docs/PRD.md §1a."""
    invite = Invite(
        email=body.email.lower(),
        invited_by=uuid.UUID(admin.id),
        token=secrets.token_urlsafe(24),
        expires_at=datetime.now(UTC) + timedelta(days=INVITE_TTL_DAYS),
    )
    db.add(invite)
    await db.flush()
    await db.refresh(invite)
    return invite


@router.get("/invites/{token}", response_model=InviteValidateOut)
async def validate_invite(
    token: str, db: AsyncSession = Depends(get_admin_db)
) -> InviteValidateOut:
    """Public — no auth required. Called before the invitee has an account at all,
    to pre-fill/lock the signup form's email and reject dead links early."""
    invite = (await db.execute(select(Invite).where(Invite.token == token))).scalar_one_or_none()
    if invite is None:
        return InviteValidateOut(valid=False, reason="not_found")
    if invite.status != "pending":
        return InviteValidateOut(valid=False, reason="already_used")
    if invite.expires_at and invite.expires_at < datetime.now(UTC):
        return InviteValidateOut(valid=False, reason="expired")
    return InviteValidateOut(valid=True, email=invite.email)


@router.post("/invites/accept", response_model=UserOut)
async def accept_invite(
    body: InviteAccept,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_admin_db),
) -> User:
    """Called right after the invitee completes Supabase Auth sign-up. Uses the
    admin session because it must read an `invites` row the caller doesn't own
    (RLS would otherwise correctly refuse it) — see database-schema.md §9's note
    on this being one of the few legitimate service-role operations."""
    invite = (
        await db.execute(select(Invite).where(Invite.token == body.token))
    ).scalar_one_or_none()
    if invite is None or invite.status != "pending":
        raise HTTPException(status_code=400, detail={"type": "invalid_invite", "status": 400})
    if invite.expires_at and invite.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail={"type": "invite_expired", "status": 400})
    if current.email is None or current.email.lower() != invite.email:
        raise HTTPException(
            status_code=403,
            detail={
                "type": "email_mismatch",
                "title": "Signed-up email doesn't match the invite",
                "status": 403,
            },
        )

    existing = (await db.execute(select(User).where(User.id == current.id))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail={"type": "already_onboarded", "status": 409})

    user = User(id=uuid.UUID(current.id), email=current.email, invited_by=invite.invited_by)
    db.add(user)
    invite.status = "accepted"
    invite.accepted_by = uuid.UUID(current.id)
    await db.flush()
    await db.refresh(user)
    return user
