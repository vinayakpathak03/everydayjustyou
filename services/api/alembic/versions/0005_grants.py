"""Grant table privileges to the `authenticated` role.

Revision ID: 0005_grants
Revises: 0004_chat
Create Date: 2026-08-02

RLS policies only restrict *which rows* a role can see/touch — they're not a
substitute for the base GRANT SELECT/INSERT/UPDATE/DELETE a role needs on the
table itself. Because every prior migration created tables through the raw
admin migration connection (not Supabase's dashboard, which auto-grants),
`authenticated` never got those base privileges, so every request-scoped
query 500'd with `asyncpg.exceptions.InsufficientPrivilegeError: permission
denied for table ...` — RLS was never even reached. Live-verified against the
deployed Supabase project.
"""

from alembic import op

revision = "0005_grants"
down_revision = "0004_chat"
branch_labels = None
depends_on = None

_RLS_TABLES = [
    "users",
    "invites",
    "style_profiles",
    "processing_jobs",
    "garments",
    "garment_images",
    "garment_embeddings",
    "outfits",
    "outfit_items",
    "wear_logs",
    "chat_conversations",
    "chat_messages",
]
_READ_ONLY = ["brands", "garment_wear_stats"]


def upgrade() -> None:
    for table in _RLS_TABLES:
        op.execute(f"grant select, insert, update, delete on {table} to authenticated")
    for table in _READ_ONLY:
        op.execute(f"grant select on {table} to authenticated")


def downgrade() -> None:
    for table in _READ_ONLY:
        op.execute(f"revoke select on {table} from authenticated")
    for table in _RLS_TABLES:
        op.execute(f"revoke select, insert, update, delete on {table} from authenticated")
