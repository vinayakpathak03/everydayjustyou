from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db as _get_db


async def get_user_db(
    user: CurrentUser = Depends(get_current_user),
) -> AsyncIterator[AsyncSession]:
    """The dependency almost every route should use: an RLS-scoped session for the
    authenticated caller. See app.db.session for what this actually does."""
    async for session in _get_db(user):
        yield session
