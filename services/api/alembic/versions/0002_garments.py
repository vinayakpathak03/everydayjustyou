"""Phase 1: brands, garments, garment_images, garment_embeddings + RLS.

Revision ID: 0002_garments
Revises: 0001_initial
Create Date: 2026-08-01
"""

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0002_garments"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "brands",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String, nullable=False, unique=True),
        sa.Column("tier", sa.String, nullable=True),
    )
    # No RLS on brands — shared lookup data, nothing user-owned or sensitive.

    op.create_table(
        "garments",
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
            "brand_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("brands.id"), nullable=True
        ),
        sa.Column("category", sa.String, nullable=False),
        sa.Column("subcategory", sa.String, nullable=True),
        sa.Column("primary_color", sa.String, nullable=True),
        sa.Column("secondary_colors", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("pattern", sa.String, nullable=True),
        sa.Column("fabric_guess", sa.String, nullable=True),
        sa.Column("fabric_confidence", sa.String, nullable=True),
        sa.Column("sleeve_length", sa.String, nullable=True),
        sa.Column("neckline", sa.String, nullable=True),
        sa.Column("fit", sa.String, nullable=True),
        sa.Column("season", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("occasion", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("formality_score", sa.SmallInteger, nullable=True),
        sa.Column("size", sa.String, nullable=True),
        sa.Column("color_hex", sa.String, nullable=True),
        sa.Column("purchase_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("purchase_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("purchase_source", sa.String, nullable=True),
        sa.Column("condition", sa.String, nullable=True),
        sa.Column("acquisition_type", sa.String, nullable=True),
        sa.Column("is_favorite", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("ai_description", sa.String, nullable=True),
        sa.Column("ai_confidence", postgresql.JSONB, nullable=True),
        sa.Column("status", sa.String, nullable=False, server_default="processing"),
        sa.Column("entry_mode", sa.String, nullable=False, server_default="ai_photo"),
        sa.Column("sensitive_category", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("manual_description", sa.String, nullable=True),
        sa.Column("manual_quantity", sa.SmallInteger, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "NOT sensitive_category OR entry_mode = 'manual'",
            name="ck_garments_sensitive_requires_manual",
        ),
    )
    op.create_index("ix_garments_user_category", "garments", ["user_id", "category"])
    op.create_index("ix_garments_user_archived", "garments", ["user_id", "is_archived"])

    op.create_table(
        "garment_images",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "garment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("garments.id"),
            nullable=False,
        ),
        sa.Column("kind", sa.String, nullable=False, server_default="raw"),
        sa.Column("storage_url", sa.String, nullable=False),
        sa.Column("width", sa.SmallInteger, nullable=True),
        sa.Column("height", sa.SmallInteger, nullable=True),
        sa.Column("sort_order", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("status", sa.String, nullable=False, server_default="processing"),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_garment_images_garment_id", "garment_images", ["garment_id"])

    op.create_table(
        "garment_embeddings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "garment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("garments.id"),
            nullable=False,
        ),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("embedding", Vector(768), nullable=False),
        sa.Column("model", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.execute(
        "create index ix_garment_embeddings_hnsw on garment_embeddings "
        "using hnsw (embedding vector_cosine_ops)"
    )

    # --- Row-Level Security ---------------------------------------------------
    # garments/garment_images/garment_embeddings don't carry user_id directly on
    # the child tables — ownership is via the parent garments row, so their
    # policies join back to it rather than repeating a auth.uid() = user_id check
    # that doesn't apply to those tables' own columns.

    op.execute("alter table garments enable row level security")
    for action, clause in [
        ("select", "using (auth.uid() = user_id)"),
        ("insert", "with check (auth.uid() = user_id)"),
        ("update", "using (auth.uid() = user_id) with check (auth.uid() = user_id)"),
        ("delete", "using (auth.uid() = user_id)"),
    ]:
        op.execute(f"create policy garments_owner_{action} on garments for {action} {clause}")

    op.execute("alter table garment_images enable row level security")
    for action, clause in [
        ("select", "using"),
        ("insert", "with check"),
        ("delete", "using"),
    ]:
        op.execute(
            f"create policy garment_images_owner_{action} on garment_images for {action} "
            f"{clause} (exists (select 1 from garments g where g.id = garment_images.garment_id "
            f"and g.user_id = auth.uid()))"
        )
    op.execute(
        "create policy garment_images_owner_update on garment_images for update "
        "using (exists (select 1 from garments g where g.id = garment_images.garment_id "
        "and g.user_id = auth.uid())) "
        "with check (exists (select 1 from garments g where g.id = garment_images.garment_id "
        "and g.user_id = auth.uid()))"
    )

    op.execute("alter table garment_embeddings enable row level security")
    for action, clause in [
        ("select", "using"),
        ("insert", "with check"),
        ("delete", "using"),
    ]:
        op.execute(
            f"create policy garment_embeddings_owner_{action} on garment_embeddings for {action} "
            f"{clause} (exists (select 1 from garments g "
            f"where g.id = garment_embeddings.garment_id and g.user_id = auth.uid()))"
        )


def downgrade() -> None:
    op.drop_table("garment_embeddings")
    op.drop_table("garment_images")
    op.drop_table("garments")
    op.drop_table("brands")
