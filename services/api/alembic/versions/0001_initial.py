"""Phase 0: users, invites, style_profiles, processing_jobs + RLS.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-01
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('create extension if not exists "pgcrypto"')
    op.execute('create extension if not exists "vector"')

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String, nullable=False, unique=True),
        sa.Column("display_name", sa.String, nullable=True),
        sa.Column("avatar_url", sa.String, nullable=True),
        sa.Column("timezone", sa.String, nullable=False, server_default="UTC"),
        sa.Column("notification_time", sa.String, nullable=True),
        sa.Column("location", postgresql.JSONB, nullable=True),
        sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "consent_dev_photo_access", sa.Boolean, nullable=False, server_default="true"
        ),
        sa.Column("tc_version", sa.String, nullable=True),
        sa.Column("tc_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invited_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # Note: `id` intentionally has no DB-level FK to auth.users — that table is
    # owned/migrated by Supabase's GoTrue service, not by this app's migrations,
    # and isn't present on the bare-Postgres local docker-compose fallback. The
    # two ids are kept in sync at the application layer (POST /auth/invites/accept
    # inserts users.id = the authenticated caller's auth.users id).

    op.create_table(
        "invites",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String, nullable=False),
        sa.Column(
            "invited_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("token", sa.String, nullable=False, unique=True),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("accepted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "style_profiles",
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True
        ),
        sa.Column("preferred_colors", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("preferred_aesthetics", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("sizes", postgresql.JSONB, nullable=True),
        sa.Column("dislikes", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("summary", sa.String, nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "processing_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("attempts", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("error", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_processing_jobs_status_created_at", "processing_jobs", ["status", "created_at"]
    )

    # --- Row-Level Security -------------------------------------------------
    # See docs/architecture/database-schema.md §9. Every policy is keyed off
    # auth.uid() (Supabase's helper reading the JWT sub claim from the session's
    # request.jwt.claims GUC — see app/db/session.py for how that GUC gets set).

    op.execute("alter table users enable row level security")
    op.execute(
        "create policy users_self_select on users for select using (auth.uid() = id)"
    )
    op.execute(
        "create policy users_self_insert on users for insert with check (auth.uid() = id)"
    )
    op.execute(
        "create policy users_self_update on users for update "
        "using (auth.uid() = id) with check (auth.uid() = id)"
    )

    op.execute("alter table invites enable row level security")
    op.execute(
        "create policy invites_owner_select on invites for select using (auth.uid() = invited_by)"
    )
    op.execute(
        "create policy invites_owner_insert on invites "
        "for insert with check (auth.uid() = invited_by)"
    )
    op.execute(
        "create policy invites_owner_update on invites for update using (auth.uid() = invited_by)"
    )
    # Deliberately no public select policy on invites — token lookup during signup
    # goes through the admin session (POST /auth/invites/accept, GET /auth/invites/{token}),
    # not a direct RLS-scoped read, since the invitee has no session yet to be RLS-scoped to.

    op.execute("alter table style_profiles enable row level security")
    for action, using_clause in [
        ("select", "using (auth.uid() = user_id)"),
        ("insert", "with check (auth.uid() = user_id)"),
        ("update", "using (auth.uid() = user_id) with check (auth.uid() = user_id)"),
        ("delete", "using (auth.uid() = user_id)"),
    ]:
        op.execute(
            f"create policy style_profiles_owner_{action} on style_profiles "
            f"for {action} {using_clause}"
        )

    op.execute("alter table processing_jobs enable row level security")
    for action, using_clause in [
        ("select", "using (auth.uid() = user_id)"),
        ("insert", "with check (auth.uid() = user_id)"),
        ("update", "using (auth.uid() = user_id) with check (auth.uid() = user_id)"),
        ("delete", "using (auth.uid() = user_id)"),
    ]:
        op.execute(
            f"create policy processing_jobs_owner_{action} on processing_jobs "
            f"for {action} {using_clause}"
        )


def downgrade() -> None:
    op.drop_table("processing_jobs")
    op.drop_table("style_profiles")
    op.drop_table("invites")
    op.drop_table("users")
