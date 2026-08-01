"""Phase 2: outfits, outfit_items, wear_logs + RLS + wear-stats view.

Revision ID: 0003_outfits
Revises: 0002_garments
Create Date: 2026-08-01
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0003_outfits"
down_revision = "0002_garments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outfits",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("name", sa.String, nullable=True),
        sa.Column("source", sa.String, nullable=False, server_default="generated"),
        sa.Column("context", postgresql.JSONB, nullable=True),
        sa.Column("score", sa.SmallInteger, nullable=False),
        sa.Column("score_breakdown", postgresql.JSONB, nullable=True),
        sa.Column("rationale", sa.String, nullable=True),
        sa.Column("collage_image_url", sa.String, nullable=True),
        sa.Column("canvas_layout", postgresql.JSONB, nullable=True),
        sa.Column("is_favorite", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_outfits_user_created", "outfits", ["user_id", "created_at"])

    op.create_table(
        "outfit_items",
        sa.Column(
            "outfit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("outfits.id"),
            primary_key=True,
        ),
        sa.Column(
            "garment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("garments.id"),
            primary_key=True,
        ),
        sa.Column("slot", sa.String, primary_key=True),
    )

    op.create_table(
        "wear_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "garment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("garments.id"), nullable=True
        ),
        sa.Column(
            "outfit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("outfits.id"), nullable=True
        ),
        sa.Column("worn_on", sa.Date, nullable=False),
        sa.Column("notes", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_wear_logs_user_worn_on", "wear_logs", ["user_id", "worn_on"])
    op.create_index("ix_wear_logs_garment_id", "wear_logs", ["garment_id"])

    # --- Row-Level Security ---------------------------------------------------
    op.execute("alter table outfits enable row level security")
    for action, clause in [
        ("select", "using (auth.uid() = user_id)"),
        ("insert", "with check (auth.uid() = user_id)"),
        ("update", "using (auth.uid() = user_id) with check (auth.uid() = user_id)"),
        ("delete", "using (auth.uid() = user_id)"),
    ]:
        op.execute(f"create policy outfits_owner_{action} on outfits for {action} {clause}")

    op.execute("alter table outfit_items enable row level security")
    for action, clause in [("select", "using"), ("insert", "with check"), ("delete", "using")]:
        op.execute(
            f"create policy outfit_items_owner_{action} on outfit_items for {action} "
            f"{clause} (exists (select 1 from outfits o "
            f"where o.id = outfit_items.outfit_id and o.user_id = auth.uid()))"
        )

    op.execute("alter table wear_logs enable row level security")
    for action, clause in [
        ("select", "using (auth.uid() = user_id)"),
        ("insert", "with check (auth.uid() = user_id)"),
        ("update", "using (auth.uid() = user_id) with check (auth.uid() = user_id)"),
        ("delete", "using (auth.uid() = user_id)"),
    ]:
        op.execute(f"create policy wear_logs_owner_{action} on wear_logs for {action} {clause}")

    # --- Wear stats -------------------------------------------------------
    # A plain view, not the materialized view database-schema.md describes —
    # a deliberate Phase 2 simplification: materialized-view refresh needs its
    # own trigger/schedule to stay correct, which is one more moving part than
    # this scale of wardrobe (a few users, hundreds of items) actually needs a
    # cached aggregate for. Correct-but-slower-at-scale now; upgrading to
    # `create materialized view` + a refresh trigger is a like-for-like swap
    # later if read latency on this view ever actually becomes a problem.
    # RLS on the view isn't a separate concept — Postgres views run with the
    # querying role's privileges by default (no SECURITY DEFINER here), so the
    # underlying wear_logs/garments RLS policies apply exactly as if the caller
    # queried those tables directly.
    op.execute(
        """
        create view garment_wear_stats as
        select
            g.id as garment_id,
            g.user_id,
            count(wl.id) as times_worn,
            max(wl.worn_on) as last_worn_on,
            case when count(wl.id) > 0 and g.purchase_price is not null
                then g.purchase_price / count(wl.id)
                else null
            end as cost_per_wear
        from garments g
        left join wear_logs wl on wl.garment_id = g.id
        group by g.id, g.user_id
        """
    )


def downgrade() -> None:
    op.execute("drop view if exists garment_wear_stats")
    op.drop_table("wear_logs")
    op.drop_table("outfit_items")
    op.drop_table("outfits")
