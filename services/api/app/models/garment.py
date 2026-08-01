import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, Numeric, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# Auto-flags a garment sensitive_category=true at creation time when its category
# matches — see PRD §7.1 item 4 and database-schema.md `garments.sensitive_category`.
SENSITIVE_CATEGORIES = {"underwear", "lingerie"}


class Garment(Base):
    """The core catalog item. See database-schema.md `garments`."""

    __tablename__ = "garments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id"), nullable=True
    )

    category: Mapped[str] = mapped_column(String, nullable=False)
    subcategory: Mapped[str | None] = mapped_column(String, nullable=True)
    primary_color: Mapped[str | None] = mapped_column(String, nullable=True)
    secondary_colors: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    pattern: Mapped[str | None] = mapped_column(String, nullable=True)
    fabric_guess: Mapped[str | None] = mapped_column(String, nullable=True)
    fabric_confidence: Mapped[str | None] = mapped_column(String, nullable=True)
    sleeve_length: Mapped[str | None] = mapped_column(String, nullable=True)
    neckline: Mapped[str | None] = mapped_column(String, nullable=True)
    fit: Mapped[str | None] = mapped_column(String, nullable=True)
    season: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    occasion: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    formality_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    size: Mapped[str | None] = mapped_column(String, nullable=True)
    color_hex: Mapped[str | None] = mapped_column(String, nullable=True)

    purchase_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    purchase_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    purchase_source: Mapped[str | None] = mapped_column(String, nullable=True)
    condition: Mapped[str | None] = mapped_column(String, nullable=True)
    acquisition_type: Mapped[str | None] = mapped_column(String, nullable=True)

    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    ai_description: Mapped[str | None] = mapped_column(String, nullable=True)
    ai_confidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="processing")

    entry_mode: Mapped[str] = mapped_column(String, nullable=False, server_default="ai_photo")
    sensitive_category: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    manual_description: Mapped[str | None] = mapped_column(String, nullable=True)
    manual_quantity: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # `lazy="noload"`: never auto-queried (avoids async lazy-load pitfalls under
    # SQLAlchemy's asyncio mode). Each router endpoint that wants images populates
    # this explicitly via a separate query — see app/routers/garments.py — so it's
    # always clear whether a given response actually fetched them or not.
    images: Mapped[list["GarmentImage"]] = relationship(
        "GarmentImage", viewonly=True, lazy="noload"
    )


class GarmentImage(Base):
    """See database-schema.md `garment_images`."""

    __tablename__ = "garment_images"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    garment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("garments.id"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String, nullable=False, server_default="raw")
    storage_url: Mapped[str] = mapped_column(String, nullable=False)
    width: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    height: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="processing")
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GarmentEmbedding(Base):
    """See database-schema.md `garment_embeddings`. `kind='text_description'` is
    implemented now (Gemini `text-embedding-004`, 768-dim — see
    app/integrations/embeddings.py). `kind='image_clip'` is schema-ready but not
    yet populated by any job — see the same file for why self-hosted CLIP is
    deferred (torch memory footprint vs. free-tier RAM). Fixed at 768 dims for
    now; a same-column image embedding would need either a wider column or a
    second one once that decision is made, since pgvector indexes are fixed-width."""

    __tablename__ = "garment_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    garment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("garments.id"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
