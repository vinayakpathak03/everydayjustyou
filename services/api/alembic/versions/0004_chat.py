"""Phase 3: chat_conversations, chat_messages + RLS.

Revision ID: 0004_chat
Revises: 0003_outfits
Create Date: 2026-08-01
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0004_chat"
down_revision = "0003_outfits"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_conversations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("title", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_chat_conversations_user_id", "chat_conversations", ["user_id"])

    op.create_table(
        "chat_messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_conversations.id"),
            nullable=False,
        ),
        sa.Column("role", sa.String, nullable=False),
        sa.Column("content", sa.String, nullable=False),
        sa.Column("tool_calls", postgresql.JSONB, nullable=True),
        sa.Column(
            "referenced_garment_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=True,
        ),
        sa.Column(
            "referenced_outfit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("outfits.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_chat_messages_conversation_id", "chat_messages", ["conversation_id"])

    # --- Row-Level Security ---------------------------------------------------
    op.execute("alter table chat_conversations enable row level security")
    for action, clause in [
        ("select", "using (auth.uid() = user_id)"),
        ("insert", "with check (auth.uid() = user_id)"),
        ("update", "using (auth.uid() = user_id) with check (auth.uid() = user_id)"),
        ("delete", "using (auth.uid() = user_id)"),
    ]:
        op.execute(
            f"create policy chat_conversations_owner_{action} on chat_conversations "
            f"for {action} {clause}"
        )

    op.execute("alter table chat_messages enable row level security")
    for action, clause in [("select", "using"), ("insert", "with check"), ("delete", "using")]:
        op.execute(
            f"create policy chat_messages_owner_{action} on chat_messages for {action} "
            f"{clause} (exists (select 1 from chat_conversations c "
            f"where c.id = chat_messages.conversation_id and c.user_id = auth.uid()))"
        )


def downgrade() -> None:
    op.drop_table("chat_messages")
    op.drop_table("chat_conversations")
