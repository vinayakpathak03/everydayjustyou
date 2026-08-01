"""Two, deliberately different, ways FastAPI talks to Postgres.

`get_db` is what almost every route uses: it stamps the *authenticated caller's*
identity onto the Postgres session as `request.jwt.claims`, the same GUC Supabase's
own `auth.uid()`/`auth.role()` helper functions read from. Every RLS policy in
alembic/versions/0001_initial.py is written against those helpers, so a request
using this session can only ever see rows Postgres itself decides it's allowed to
see — not rows the application *remembers* to filter to.

`get_admin_db` is the escape hatch, and it stays a narrow one: the invite-redemption
flow needs to look up an `invites` row *before* the invitee has a session of their
own, which is a legitimate cross-user operation. Nothing else should use it.

Critical detail, easy to get backwards: setting `request.jwt.claims` does *nothing*
by itself if the underlying Postgres role is a superuser or carries BYPASSRLS —
both silently skip every RLS check regardless of GUCs. In production, `DATABASE_URL`
must authenticate as Supabase's non-superuser `authenticated` role (not the
`postgres` connection-string default, which is effectively a superuser in a
Supabase project) — `get_db` issues an explicit `SET LOCAL ROLE authenticated` for
exactly this reason, so RLS is enforced even if the connection string itself is
over-privileged. `DATABASE_URL_ADMIN` is the one place allowed to run as
`service_role` (or stay superuser). Locally, the docker-compose fallback in
infra/docker-compose.yml has no `authenticated`/`service_role` roles at all (they're
created by the full Supabase stack, not the bare Postgres image) — RLS is real but
effectively untested against this compose file; use `supabase start` (Supabase CLI)
for local testing that actually exercises isolation. See
docs/architecture/database-schema.md §9.
"""

import json
from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.security import CurrentUser

settings = get_settings()

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
admin_engine = create_async_engine(settings.database_url_admin, pool_pre_ping=True)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
AdminSessionLocal = async_sessionmaker(admin_engine, expire_on_commit=False)


async def get_db(user: CurrentUser) -> AsyncIterator[AsyncSession]:
    """Not used directly as a FastAPI dependency (needs `user` resolved first) —
    see `app.core.deps.get_user_db` for the actual `Depends(...)`-wired version."""
    async with SessionLocal() as session:
        claims = json.dumps({"sub": user.id, "role": user.role, "email": user.email})
        await session.execute(text("set local role authenticated"))
        await session.execute(
            text("select set_config('request.jwt.claims', :claims, true)"), {"claims": claims}
        )
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_admin_db() -> AsyncIterator[AsyncSession]:
    async with AdminSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
