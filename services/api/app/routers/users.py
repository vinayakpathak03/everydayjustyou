from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_user_db
from app.core.security import CurrentUser, get_current_user
from app.models.user import User
from app.schemas.user import ConsentIn, ConsentOut, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


async def _get_own_user(db: AsyncSession, user_id) -> User:
    row = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail={"type": "not_found", "status": 404})
    return row


@router.get("/me", response_model=UserOut)
async def get_me(
    current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_user_db)
) -> User:
    return await _get_own_user(db, current.id)


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: UserUpdate,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_user_db),
) -> User:
    user = await _get_own_user(db, current.id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.flush()
    await db.refresh(user)
    return user


@router.get("/me/consent", response_model=ConsentOut)
async def get_consent(
    current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_user_db)
) -> User:
    return await _get_own_user(db, current.id)


@router.put("/me/consent", response_model=ConsentOut)
async def set_consent(
    body: ConsentIn,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_user_db),
) -> User:
    """The onboarding gate: this is what the T&C + consent screen (PRD §7.1) calls.
    Setting this also completes onboarding — there's no separate 'finish onboarding'
    endpoint, since accepting the T&C *is* the gate everything else sits behind."""
    user = await _get_own_user(db, current.id)
    user.consent_dev_photo_access = body.consent_dev_photo_access
    user.tc_version = body.tc_version
    user.tc_accepted_at = datetime.now(UTC)
    if user.onboarding_completed_at is None:
        user.onboarding_completed_at = datetime.now(UTC)
    await db.flush()
    await db.refresh(user)
    return user
